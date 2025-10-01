"""
Сервис кэширования для TechExpert Connector
"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class CacheService:
    """Сервис кэширования с поддержкой Redis и in-memory fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.use_redis = False
        self.default_ttl = 3600  # 1 час
        
        logger.info("CacheService инициализирован")
    
    async def initialize(self):
        """Инициализация сервиса кэширования"""
        try:
            if REDIS_AVAILABLE:
                # Пытаемся подключиться к Redis
                self.redis_client = redis.Redis(
                    host='redis',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # Проверяем подключение
                await self.redis_client.ping()
                self.use_redis = True
                logger.info("Подключение к Redis установлено")
                
            else:
                logger.warning("Redis недоступен, используется in-memory кэш")
                
        except Exception as e:
            logger.warning(f"Не удалось подключиться к Redis: {str(e)}, используется in-memory кэш")
            self.use_redis = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            if self.use_redis and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # In-memory кэш
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if entry["expires_at"] > datetime.now():
                        return entry["value"]
                    else:
                        # Удаляем истекшую запись
                        del self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Сохранение значения в кэш"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            if self.use_redis and self.redis_client:
                serialized_value = json.dumps(value, default=str)
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                # In-memory кэш
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[key] = {
                    "value": value,
                    "expires_at": expires_at
                }
                
                # Очищаем старые записи
                await self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.delete(key)
            else:
                # In-memory кэш
                if key in self.memory_cache:
                    del self.memory_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа в кэше"""
        try:
            if self.use_redis and self.redis_client:
                return await self.redis_client.exists(key) > 0
            else:
                # In-memory кэш
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if entry["expires_at"] > datetime.now():
                        return True
                    else:
                        # Удаляем истекшую запись
                        del self.memory_cache[key]
                
                return False
                
        except Exception as e:
            logger.error(f"Ошибка проверки существования ключа: {str(e)}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Получение TTL ключа"""
        try:
            if self.use_redis and self.redis_client:
                ttl = await self.redis_client.ttl(key)
                return ttl if ttl > 0 else None
            else:
                # In-memory кэш
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if entry["expires_at"] > datetime.now():
                        remaining = (entry["expires_at"] - datetime.now()).total_seconds()
                        return int(remaining) if remaining > 0 else None
                    else:
                        # Удаляем истекшую запись
                        del self.memory_cache[key]
                
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения TTL: {str(e)}")
            return None
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Увеличение числового значения в кэше"""
        try:
            if self.use_redis and self.redis_client:
                return await self.redis_client.incrby(key, amount)
            else:
                # In-memory кэш
                current_value = await self.get(key)
                if current_value is None:
                    new_value = amount
                else:
                    new_value = current_value + amount
                
                await self.set(key, new_value)
                return new_value
                
        except Exception as e:
            logger.error(f"Ошибка увеличения значения: {str(e)}")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        try:
            if self.use_redis and self.redis_client:
                info = await self.redis_client.info()
                return {
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            else:
                # In-memory кэш
                total_keys = len(self.memory_cache)
                expired_keys = 0
                
                for key, entry in self.memory_cache.items():
                    if entry["expires_at"] <= datetime.now():
                        expired_keys += 1
                
                return {
                    "type": "memory",
                    "total_keys": total_keys,
                    "expired_keys": expired_keys,
                    "active_keys": total_keys - expired_keys
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {str(e)}")
            return {"error": str(e)}
    
    async def clear(self) -> bool:
        """Очистка всего кэша"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.flushdb()
            else:
                # In-memory кэш
                self.memory_cache.clear()
            
            logger.info("Кэш очищен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {str(e)}")
            return False
    
    async def _cleanup_memory_cache(self):
        """Очистка истекших записей в in-memory кэше"""
        try:
            current_time = datetime.now()
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry["expires_at"] <= current_time
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            if expired_keys:
                logger.debug(f"Удалено {len(expired_keys)} истекших записей из кэша")
                
        except Exception as e:
            logger.error(f"Ошибка очистки in-memory кэша: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния кэша"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.ping()
                return {
                    "status": "up",
                    "type": "redis",
                    "response_time_ms": 0  # В реальной системе можно измерить
                }
            else:
                return {
                    "status": "up",
                    "type": "memory",
                    "keys_count": len(self.memory_cache)
                }
                
        except Exception as e:
            logger.error(f"Ошибка health check кэша: {str(e)}")
            return {
                "status": "down",
                "error": str(e)
            }
    
    async def close(self):
        """Закрытие соединения с кэшем"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Соединение с Redis закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия соединения с Redis: {str(e)}")
