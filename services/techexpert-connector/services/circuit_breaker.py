"""
Circuit Breaker для TechExpert Connector
"""

import asyncio
import logging
from typing import Callable, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit Breaker для защиты от сбоев внешних сервисов"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
        logger.info(f"CircuitBreaker инициализирован: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def __enter__(self):
        """Контекстный менеджер для синхронного использования"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker переходит в состояние HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Обработка исключений в контекстном менеджере"""
        if exc_type is not None and issubclass(exc_type, self.expected_exception):
            self._record_failure()
        else:
            self._record_success()
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker переходит в состояние HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Обработка исключений в асинхронном контекстном менеджере"""
        if exc_type is not None and issubclass(exc_type, self.expected_exception):
            self._record_failure()
        else:
            self._record_success()
    
    def _should_attempt_reset(self) -> bool:
        """Проверка, следует ли попытаться сбросить circuit breaker"""
        if self.last_failure_time is None:
            return True
        
        return datetime.now() >= self.last_failure_time + timedelta(seconds=self.recovery_timeout)
    
    def _record_failure(self):
        """Запись неудачи"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker переходит в состояние OPEN после {self.failure_count} неудач")
    
    def _record_success(self):
        """Запись успеха"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker переходит в состояние CLOSED после успешного запроса")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Вызов функции через circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker переходит в состояние HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Асинхронный вызов функции через circuit breaker"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker переходит в состояние HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise
    
    def get_state(self) -> dict:
        """Получение текущего состояния circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "next_attempt_time": (
                (self.last_failure_time + timedelta(seconds=self.recovery_timeout)).isoformat()
                if self.last_failure_time and self.state == CircuitState.OPEN
                else None
            )
        }
    
    def reset(self):
        """Принудительный сброс circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker сброшен")
    
    def is_available(self) -> bool:
        """Проверка доступности сервиса"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.HALF_OPEN:
            return True
        elif self.state == CircuitState.OPEN:
            return self._should_attempt_reset()
        
        return False
