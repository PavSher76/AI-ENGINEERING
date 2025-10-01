"""
Сервис для работы с LLM через ollama-service
"""

import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """Сервис для взаимодействия с LLM через ollama-service"""
    
    def __init__(self, ollama_service_url: str = "http://ollama-service:8012"):
        self.ollama_service_url = ollama_service_url
        self.timeout = httpx.Timeout(300.0)  # 5 минут по умолчанию
        
    async def generate_response(
        self,
        prompt: str,
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        system_prompt: str = "",
        timeout: Optional[float] = None
    ) -> str:
        """
        Генерирует ответ от LLM
        
        Args:
            prompt: Промпт для LLM
            model: Модель LLM
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            top_p: Top-p параметр
            top_k: Top-k параметр
            repeat_penalty: Штраф за повторения
            system_prompt: Системный промпт
            timeout: Таймаут в секундах
            
        Returns:
            Ответ от LLM
        """
        logger.info(f"🤖 Генерация ответа LLM. Модель: {model}, Токены: {max_tokens}")
        
        # Устанавливаем таймаут
        request_timeout = timeout or 300.0
        timeout_config = httpx.Timeout(request_timeout)
        
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                payload = {
                    "prompt": prompt,
                    "max_tokens": max_tokens
                }
                
                logger.debug(f"Отправка запроса к ollama-service: {payload}")
                
                response = await client.post(
                    f"{self.ollama_service_url}/models/{model}/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Ollama-service возвращает ответ в data.response
                    llm_response = result.get("data", {}).get("response", result.get("response", ""))
                    logger.info(f"✅ Ответ LLM получен. Длина: {len(llm_response)}")
                    return llm_response if llm_response else "Ошибка: пустой ответ от LLM"
                else:
                    error_msg = f"Ошибка ollama-service: {response.status_code} - {response.text}"
                    logger.error(f"❌ {error_msg}")
                    return f"Ошибка получения ответа от LLM: {error_msg}"
                    
        except httpx.TimeoutException:
            error_msg = f"Таймаут запроса к LLM ({request_timeout}s)"
            logger.error(f"⏰ {error_msg}")
            return f"Таймаут: {error_msg}"
        except httpx.ConnectError:
            error_msg = "Не удалось подключиться к ollama-service"
            logger.error(f"🔌 {error_msg}")
            return f"Ошибка подключения: {error_msg}"
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return f"Ошибка: {error_msg}"
    
    async def generate_streaming_response(
        self,
        prompt: str,
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        system_prompt: str = "",
        timeout: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Генерирует потоковый ответ от LLM
        
        Args:
            prompt: Промпт для LLM
            model: Модель LLM
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            top_p: Top-p параметр
            top_k: Top-k параметр
            repeat_penalty: Штраф за повторения
            system_prompt: Системный промпт
            timeout: Таймаут в секундах
            
        Yields:
            Части ответа от LLM
        """
        logger.info(f"🌊 Потоковая генерация ответа LLM. Модель: {model}")
        
        # Устанавливаем таймаут
        request_timeout = timeout or 300.0
        timeout_config = httpx.Timeout(request_timeout)
        
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                payload = {
                    "prompt": prompt,
                    "max_tokens": max_tokens
                }
                
                async with client.stream(
                    "POST",
                    f"{self.ollama_service_url}/models/{model}/generate",
                    json=payload
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = response.json()
                                    if "response" in data:
                                        yield data["response"]
                                except:
                                    # Если не JSON, возвращаем как есть
                                    yield line
                    else:
                        error_msg = f"Ошибка ollama-service: {response.status_code}"
                        logger.error(f"❌ {error_msg}")
                        yield f"Ошибка: {error_msg}"
                        
        except httpx.TimeoutException:
            error_msg = f"Таймаут потокового запроса к LLM ({request_timeout}s)"
            logger.error(f"⏰ {error_msg}")
            yield f"Таймаут: {error_msg}"
        except httpx.ConnectError:
            error_msg = "Не удалось подключиться к ollama-service"
            logger.error(f"🔌 {error_msg}")
            yield f"Ошибка подключения: {error_msg}"
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            logger.error(f"💥 {error_msg}")
            yield f"Ошибка: {error_msg}"
    
    async def get_available_models(self) -> list:
        """
        Получает список доступных моделей
        
        Returns:
            Список доступных моделей
        """
        logger.info("📋 Получение списка доступных моделей")
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(f"{self.ollama_service_url}/models")
                
                if response.status_code == 200:
                    result = response.json()
                    # Ollama-service возвращает массив моделей напрямую
                    if isinstance(result, list):
                        models = [model.get("name", model) if isinstance(model, dict) else model for model in result]
                    else:
                        models = result.get("models", [])
                    
                    logger.info(f"✅ Получено {len(models)} моделей: {models}")
                    return models
                else:
                    logger.error(f"❌ Ошибка получения моделей: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"💥 Ошибка получения моделей: {str(e)}")
            return []
    
    async def check_model_availability(self, model: str) -> bool:
        """
        Проверяет доступность модели
        
        Args:
            model: Название модели
            
        Returns:
            True если модель доступна
        """
        logger.info(f"🔍 Проверка доступности модели: {model}")
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(f"{self.ollama_service_url}/models/{model}")
                
                if response.status_code == 200:
                    logger.info(f"✅ Модель {model} доступна")
                    return True
                else:
                    logger.warning(f"⚠️ Модель {model} недоступна: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"💥 Ошибка проверки модели {model}: {str(e)}")
            return False
