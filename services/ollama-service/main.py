"""
Ollama Management Service
Сервис для управления моделями Ollama
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ollama Management Service",
    description="Сервис для управления моделями Ollama",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

class ModelInfo(BaseModel):
    name: str
    size: int
    digest: str
    modified_at: str

class ModelRequest(BaseModel):
    name: str
    stream: bool = False

class ModelResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SettingsRequest(BaseModel):
    default_model: str
    available_models: List[str]

class SettingsResponse(BaseModel):
    default_model: str
    available_models: List[str]
    current_model: str

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "ollama-management-service"}

@app.get("/models", response_model=List[ModelInfo])
async def get_models():
    """Получение списка доступных моделей"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("models", []):
                models.append(ModelInfo(
                    name=model["name"],
                    size=model["size"],
                    digest=model["digest"],
                    modified_at=model["modified_at"]
                ))
            
            return models
    except httpx.RequestError as e:
        logger.error(f"Ошибка подключения к Ollama: {e}")
        raise HTTPException(status_code=503, detail="Ollama недоступен")
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения моделей")

@app.post("/models/pull", response_model=ModelResponse)
async def pull_model(model_request: ModelRequest):
    """Загрузка новой модели"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model_request.name, "stream": model_request.stream}
            )
            response.raise_for_status()
            
            return ModelResponse(
                success=True,
                message=f"Модель {model_request.name} успешно загружена",
                data={"model": model_request.name}
            )
    except httpx.RequestError as e:
        logger.error(f"Ошибка подключения к Ollama: {e}")
        raise HTTPException(status_code=503, detail="Ollama недоступен")
    except Exception as e:
        logger.error(f"Ошибка загрузки модели: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки модели")

@app.delete("/models/{model_name}", response_model=ModelResponse)
async def delete_model(model_name: str):
    """Удаление модели"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{OLLAMA_BASE_URL}/api/delete", 
                                         json={"name": model_name})
            response.raise_for_status()
            
            return ModelResponse(
                success=True,
                message=f"Модель {model_name} успешно удалена"
            )
    except httpx.RequestError as e:
        logger.error(f"Ошибка подключения к Ollama: {e}")
        raise HTTPException(status_code=503, detail="Ollama недоступен")
    except Exception as e:
        logger.error(f"Ошибка удаления модели: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления модели")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

@app.post("/models/{model_name}/generate", response_model=ModelResponse)
async def generate_text(model_name: str, request: GenerateRequest):
    """Генерация текста с использованием модели"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model_name,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "num_predict": request.max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return ModelResponse(
                success=True,
                message="Текст успешно сгенерирован",
                data={
                    "response": data.get("response", ""),
                    "model": model_name,
                    "prompt": request.prompt
                }
            )
    except httpx.RequestError as e:
        logger.error(f"Ошибка подключения к Ollama: {e}")
        raise HTTPException(status_code=503, detail="Ollama недоступен")
    except Exception as e:
        logger.error(f"Ошибка генерации текста: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации текста")

@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Получение настроек моделей"""
    try:
        # Получаем список доступных моделей
        models_response = await get_models()
        available_models = [model.name for model in models_response]
        
        # Получаем текущую модель (можно сохранять в БД или файле)
        default_model = os.getenv("DEFAULT_MODEL", "llama3.1:8b")
        
        return SettingsResponse(
            default_model=default_model,
            available_models=available_models,
            current_model=default_model
        )
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек")

@app.post("/settings", response_model=ModelResponse)
async def update_settings(settings: SettingsRequest):
    """Обновление настроек моделей"""
    try:
        # Здесь можно сохранять настройки в БД или файл
        # Пока просто возвращаем успех
        
        return ModelResponse(
            success=True,
            message="Настройки успешно обновлены",
            data={
                "default_model": settings.default_model,
                "available_models": settings.available_models
            }
        )
    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления настроек")

@app.get("/status")
async def get_ollama_status():
    """Получение статуса Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            
            return {
                "status": "connected",
                "ollama_url": OLLAMA_BASE_URL,
                "models_count": len(response.json().get("models", []))
            }
    except httpx.RequestError as e:
        logger.error(f"Ollama недоступен: {e}")
        return {
            "status": "disconnected",
            "ollama_url": OLLAMA_BASE_URL,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
