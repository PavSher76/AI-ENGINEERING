"""
Основной файл приложения Archive Service
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from schemas.archive import (
    ArchiveUploadRequest, ProcessingJob, SearchRequest, SearchResult,
    AnalogSearchRequest, AnalogResult
)
from models.database import init_db
from services.archive_service import ArchiveService
from services.minio_service import MinIOService
from services.document_parser import DocumentParser
from services.vectorization_service import VectorizationService
from services.search_service import SearchService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные сервисы
minio_service = None
document_parser = None
vectorization_service = None
search_service = None

def get_archive_service():
    """Ленивое получение ArchiveService"""
    global minio_service
    if minio_service is None:
        minio_service = MinIOService(
            endpoint="localhost:9900",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
    return ArchiveService(minio_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и очистка ресурсов"""
    global minio_service, archive_service, document_parser, vectorization_service, search_service
    
    # Инициализация сервисов
    try:
        # Инициализация базы данных
        init_db()
        logger.info("База данных инициализирована")
        
        # Инициализируем только базовые сервисы
        document_parser = DocumentParser()
        vectorization_service = VectorizationService()
        search_service = SearchService(vectorization_service)
        
        # ArchiveService будет создаваться лениво при необходимости
        
        logger.info("Archive Service инициализирован")
        
    except Exception as e:
        logger.error(f"Ошибка инициализации: {str(e)}")
        raise
    
    yield
    
    # Очистка ресурсов
    logger.info("Archive Service завершает работу")


app = FastAPI(
    title="Archive Service",
    description="Сервис для работы с архивами инженерной документации",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "archive-service"}


@app.post("/archives/upload", response_model=dict)
async def upload_archive(
    request: ArchiveUploadRequest,
    background_tasks: BackgroundTasks
):
    """
    Загружает архив проекта для обработки
    
    Args:
        request: Запрос на загрузку архива
        background_tasks: Фоновые задачи
        
    Returns:
        ID задания на обработку
    """
    try:
        archive_service = get_archive_service()
        job_id = await archive_service.upload_archive(request)
        
        # Запускаем обработку в фоне
        background_tasks.add_task(archive_service.process_archive, job_id)
        
        return {
            "job_id": job_id,
            "status": "accepted",
            "message": "Архив принят на обработку"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке архива: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=ProcessingJob)
async def get_processing_job(job_id: str):
    """
    Получает статус задания на обработку
    
    Args:
        job_id: ID задания
        
    Returns:
        Информация о задании
    """
    try:
        # Здесь должна быть логика получения задания из БД
        # Пока возвращаем заглушку
        return ProcessingJob(
            job_id=job_id,
            project_id="test_project",
            object_id="test_object",
            status="processing",
            created_at="2025-10-11T10:00:00Z"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении задания {job_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Задание не найдено")


@app.get("/jobs", response_model=list[ProcessingJob])
async def list_processing_jobs(
    project_id: str = None,
    status: str = None,
    limit: int = 10
):
    """
    Получает список заданий на обработку
    
    Args:
        project_id: Фильтр по проекту
        status: Фильтр по статусу
        limit: Лимит результатов
        
    Returns:
        Список заданий
    """
    try:
        # Здесь должна быть логика получения заданий из БД
        # Пока возвращаем заглушку
        return []
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка заданий: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=list[SearchResult])
async def search_documents(request: SearchRequest):
    """
    Поиск документов по текстовому запросу
    
    Args:
        request: Параметры поиска
        
    Returns:
        Список результатов поиска
    """
    try:
        results = await search_service.search(request)
        return results
        
    except Exception as e:
        logger.error(f"Ошибка при поиске: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/analogs", response_model=list[AnalogResult])
async def search_analogs(request: AnalogSearchRequest):
    """
    Поиск аналогов оборудования
    
    Args:
        request: Параметры поиска аналогов
        
    Returns:
        Список аналогов
    """
    try:
        results = await search_service.search_analogs(request)
        return results
        
    except Exception as e:
        logger.error(f"Ошибка при поиске аналогов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects", response_model=list[dict])
async def list_projects():
    """
    Получает список проектов
    
    Returns:
        Список проектов
    """
    try:
        # Здесь должна быть логика получения проектов из БД
        # Пока возвращаем заглушку
        return [
            {
                "project_id": "EC-Karat-2021",
                "object_id": "NH3-ATR-3500tpd",
                "name": "EC-Karat-2021 - NH3-ATR-3500tpd",
                "phase": "PD",
                "customer": "EuroChem",
                "created_at": "2025-10-11T10:00:00Z"
            }
        ]
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка проектов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/documents", response_model=list[dict])
async def list_project_documents(project_id: str):
    """
    Получает список документов проекта
    
    Args:
        project_id: ID проекта
        
    Returns:
        Список документов
    """
    try:
        # Здесь должна быть логика получения документов из БД
        # Пока возвращаем заглушку
        return [
            {
                "doc_no": "AI-ENG-PID-001",
                "rev": "A",
                "doc_type": "P&ID",
                "discipline": "process",
                "status": "processed",
                "chunks_count": 15
            }
        ]
        
    except Exception as e:
        logger.error(f"Ошибка при получении документов проекта {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections", response_model=list[dict])
async def list_collections():
    """
    Получает список коллекций в Qdrant
    
    Returns:
        Список коллекций
    """
    try:
        collections = await vectorization_service.list_collections()
        return collections
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка коллекций: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collections/{collection_name}/reindex")
async def reindex_collection(collection_name: str):
    """
    Переиндексирует коллекцию
    
    Args:
        collection_name: Имя коллекции
        
    Returns:
        Результат переиндексации
    """
    try:
        result = await vectorization_service.reindex_collection(collection_name)
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при переиндексации коллекции {collection_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)