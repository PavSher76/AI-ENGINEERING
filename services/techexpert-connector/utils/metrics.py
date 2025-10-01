"""
Сбор метрик для TechExpert Connector
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Сборщик метрик для мониторинга"""
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.error_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.cache_hits = 0
        self.cache_misses = 0
        self.circuit_breaker_state = "closed"
        
        # Ограничиваем размер истории метрик
        self.max_history_size = 1000
        self.response_time_history = deque(maxlen=self.max_history_size)
        self.error_history = deque(maxlen=self.max_history_size)
        
        # Thread-safe операции
        self._lock = threading.Lock()
        
        # Prometheus метрики (если доступны)
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
            self._setup_prometheus_metrics()
        else:
            self.registry = None
            logger.warning("Prometheus недоступен, используются внутренние метрики")
        
        logger.info("MetricsCollector инициализирован")
    
    def _setup_prometheus_metrics(self):
        """Настройка Prometheus метрик"""
        try:
            self.request_counter = Counter(
                'techexpert_requests_total',
                'Total number of requests',
                ['method', 'endpoint', 'status_code'],
                registry=self.registry
            )
            
            self.request_duration = Histogram(
                'techexpert_request_duration_seconds',
                'Request duration in seconds',
                ['method', 'endpoint'],
                registry=self.registry
            )
            
            self.error_counter = Counter(
                'techexpert_errors_total',
                'Total number of errors',
                ['error_type', 'endpoint'],
                registry=self.registry
            )
            
            self.cache_hit_counter = Counter(
                'techexpert_cache_hits_total',
                'Total number of cache hits',
                ['cache_type']
            )
            
            self.cache_miss_counter = Counter(
                'techexpert_cache_misses_total',
                'Total number of cache misses',
                ['cache_type']
            )
            
            self.circuit_breaker_gauge = Gauge(
                'techexpert_circuit_breaker_state',
                'Circuit breaker state (0=closed, 1=open, 2=half_open)',
                ['service']
            )
            
            logger.info("Prometheus метрики настроены")
            
        except Exception as e:
            logger.error(f"Ошибка настройки Prometheus метрик: {str(e)}")
            self.registry = None
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Запись метрики запроса"""
        try:
            with self._lock:
                # Внутренние метрики
                endpoint = self._normalize_endpoint(path)
                key = f"{method}:{endpoint}"
                
                self.request_count[key] += 1
                self.response_times[key].append(duration)
                self.response_time_history.append({
                    'timestamp': datetime.now(),
                    'method': method,
                    'endpoint': endpoint,
                    'duration': duration,
                    'status_code': status_code
                })
                
                # Prometheus метрики
                if self.registry:
                    self.request_counter.labels(
                        method=method,
                        endpoint=endpoint,
                        status_code=str(status_code)
                    ).inc()
                    
                    self.request_duration.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(duration)
                
        except Exception as e:
            logger.error(f"Ошибка записи метрики запроса: {str(e)}")
    
    def record_error(self, method: str, path: str, error_type: str):
        """Запись метрики ошибки"""
        try:
            with self._lock:
                # Внутренние метрики
                endpoint = self._normalize_endpoint(path)
                key = f"{method}:{endpoint}"
                
                self.error_count[key] += 1
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'method': method,
                    'endpoint': endpoint,
                    'error_type': error_type
                })
                
                # Prometheus метрики
                if self.registry:
                    self.error_counter.labels(
                        error_type=error_type,
                        endpoint=endpoint
                    ).inc()
                
        except Exception as e:
            logger.error(f"Ошибка записи метрики ошибки: {str(e)}")
    
    def record_cache_hit(self, cache_type: str = "default"):
        """Запись попадания в кэш"""
        try:
            with self._lock:
                self.cache_hits += 1
                
                if self.registry:
                    self.cache_hit_counter.labels(cache_type=cache_type).inc()
                
        except Exception as e:
            logger.error(f"Ошибка записи метрики кэша: {str(e)}")
    
    def record_cache_miss(self, cache_type: str = "default"):
        """Запись промаха кэша"""
        try:
            with self._lock:
                self.cache_misses += 1
                
                if self.registry:
                    self.cache_miss_counter.labels(cache_type=cache_type).inc()
                
        except Exception as e:
            logger.error(f"Ошибка записи метрики кэша: {str(e)}")
    
    def update_circuit_breaker_state(self, service: str, state: str):
        """Обновление состояния circuit breaker"""
        try:
            with self._lock:
                self.circuit_breaker_state = state
                
                if self.registry:
                    state_value = {"closed": 0, "open": 1, "half_open": 2}.get(state, 0)
                    self.circuit_breaker_gauge.labels(service=service).set(state_value)
                
        except Exception as e:
            logger.error(f"Ошибка обновления состояния circuit breaker: {str(e)}")
    
    def _normalize_endpoint(self, path: str) -> str:
        """Нормализация пути для группировки метрик"""
        # Заменяем параметры на плейсхолдеры
        import re
        
        # Заменяем UUID и числовые ID
        path = re.sub(r'/[0-9a-f-]{36}', '/{id}', path)  # UUID
        path = re.sub(r'/\d+', '/{id}', path)  # Числовые ID
        
        return path
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        try:
            with self._lock:
                # Вычисляем средние значения
                avg_response_times = {}
                for key, times in self.response_times.items():
                    if times:
                        avg_response_times[key] = sum(times) / len(times)
                
                # Вычисляем cache hit rate
                total_cache_requests = self.cache_hits + self.cache_misses
                cache_hit_rate = (self.cache_hits / total_cache_requests) if total_cache_requests > 0 else 0
                
                # Статистика за последний час
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_requests = [
                    req for req in self.response_time_history
                    if req['timestamp'] >= one_hour_ago
                ]
                recent_errors = [
                    err for err in self.error_history
                    if err['timestamp'] >= one_hour_ago
                ]
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "request_count": dict(self.request_count),
                    "error_count": dict(self.error_count),
                    "avg_response_times": avg_response_times,
                    "cache_stats": {
                        "hits": self.cache_hits,
                        "misses": self.cache_misses,
                        "hit_rate": cache_hit_rate
                    },
                    "circuit_breaker_state": self.circuit_breaker_state,
                    "recent_stats": {
                        "requests_last_hour": len(recent_requests),
                        "errors_last_hour": len(recent_errors),
                        "avg_response_time_last_hour": (
                            sum(req['duration'] for req in recent_requests) / len(recent_requests)
                            if recent_requests else 0
                        )
                    }
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения метрик: {str(e)}")
            return {"error": str(e)}
    
    def get_prometheus_metrics(self) -> Optional[str]:
        """Получение метрик в формате Prometheus"""
        try:
            if self.registry:
                return generate_latest(self.registry).decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Ошибка получения Prometheus метрик: {str(e)}")
            return None
    
    def reset_metrics(self):
        """Сброс всех метрик"""
        try:
            with self._lock:
                self.request_count.clear()
                self.error_count.clear()
                self.response_times.clear()
                self.cache_hits = 0
                self.cache_misses = 0
                self.response_time_history.clear()
                self.error_history.clear()
                
                logger.info("Метрики сброшены")
                
        except Exception as e:
            logger.error(f"Ошибка сброса метрик: {str(e)}")
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Получение метрик для health check"""
        try:
            with self._lock:
                # Вычисляем error rate за последний час
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_requests = [
                    req for req in self.response_time_history
                    if req['timestamp'] >= one_hour_ago
                ]
                recent_errors = [
                    err for err in self.error_history
                    if err['timestamp'] >= one_hour_ago
                ]
                
                error_rate = (
                    len(recent_errors) / len(recent_requests)
                    if recent_requests else 0
                )
                
                # Среднее время ответа за последний час
                avg_response_time = (
                    sum(req['duration'] for req in recent_requests) / len(recent_requests)
                    if recent_requests else 0
                )
                
                return {
                    "requests_last_hour": len(recent_requests),
                    "errors_last_hour": len(recent_errors),
                    "error_rate": error_rate,
                    "avg_response_time_ms": avg_response_time * 1000,
                    "cache_hit_rate": (
                        self.cache_hits / (self.cache_hits + self.cache_misses)
                        if (self.cache_hits + self.cache_misses) > 0 else 0
                    ),
                    "circuit_breaker_state": self.circuit_breaker_state
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения health метрик: {str(e)}")
            return {"error": str(e)}
