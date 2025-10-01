"""
TechExpert Connector Service
Сервис для интеграции с API "Техэксперт" для работы с НТД
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from services.auth_service import AuthService
from services.techexpert_client import TechExpertClient
from services.cache_service import CacheService
from services.sync_service import SyncService
from services.circuit_breaker import CircuitBreaker
from models.schemas import (
    HealthResponse, SearchRequest, SearchResponse, DocumentMeta,
    LatestEdition, SectionsResponse, SectionContent, CitationsResponse,
    SyncStatus, SyncRequest, SyncResponse, ErrorResponse
)
from utils.logging_config import setup_logging
from utils.metrics import MetricsCollector

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Инициализация сервисов
auth_service = AuthService()
techexpert_client = TechExpertClient()
cache_service = CacheService()
sync_service = SyncService()
circuit_breaker = CircuitBreaker()
metrics = MetricsCollector()

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("🚀 TechExpert Connector запущен")
    logger.info("🔐 Аутентификация: OAuth2 + API Key")
    logger.info("🔄 Синхронизация: Online-first с fallback")
    logger.info("📊 Метрики: Prometheus + структурированные логи")
    
    # Инициализация сервисов
    await cache_service.initialize()
    await sync_service.initialize()
    
    # Запуск фоновых задач
    sync_task = asyncio.create_task(sync_service.background_sync())
    
    yield
    
    # Shutdown
    logger.info("🛑 TechExpert Connector остановлен")
    sync_task.cancel()
    await cache_service.close()

app = FastAPI(
    title="TechExpert Connector API",
    description="Сервис для интеграции с API 'Техэксперт' для работы с НТД",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования и метрик
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = datetime.now()
    request_id = f"req_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
    
    logger.info(f"📥 {request.method} {request.url.path}", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params)
    })
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"📤 {response.status_code} за {process_time:.3f}s", extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": process_time
        })
        
        # Метрики
        metrics.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
        
        return response
        
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Ошибка: {str(e)} за {process_time:.3f}s", extra={
            "request_id": request_id,
            "error": str(e),
            "process_time": process_time
        })
        
        metrics.record_error(
            method=request.method,
            path=request.url.path,
            error_type=type(e).__name__
        )
        
        raise

# Dependency для аутентификации
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получение текущего пользователя из токена"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        logger.warning(f"Ошибка аутентификации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен авторизации"
        )

# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса"""
    try:
        # Проверяем состояние всех сервисов
        techexpert_status = await techexpert_client.health_check()
        cache_status = await cache_service.health_check()
        
        overall_status = "healthy"
        if techexpert_status["status"] != "up" or cache_status["status"] != "up":
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            services={
                "techexpert_api": techexpert_status,
                "local_index": cache_status
            },
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Ошибка health check: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            services={},
            version="1.0.0"
        )

# Аутентификация
@app.post("/auth/token")
async def get_auth_token(auth_request: dict):
    """Получение токена авторизации"""
    try:
        token = await auth_service.authenticate(
            client_id=auth_request["client_id"],
            client_secret=auth_request["client_secret"],
            scope=auth_request.get("scope", "read")
        )
        return token
    except Exception as e:
        logger.error(f"Ошибка аутентификации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )

# Поиск документов
@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Поиск документов по текстовому запросу"""
    try:
        # Проверяем кэш
        cache_key = f"search:{hash(str(search_request))}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info("Результат найден в кэше")
            return SearchResponse(**cached_result)
        
        # Выполняем поиск
        start_time = datetime.now()
        
        # Пробуем онлайн поиск через circuit breaker
        try:
            with circuit_breaker:
                results = await techexpert_client.search_documents(search_request)
                source = "online"
        except Exception as e:
            logger.warning(f"Онлайн поиск недоступен: {str(e)}, используем локальный")
            results = await sync_service.search_local(search_request)
            source = "local"
        
        query_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = SearchResponse(
            results=results,
            total_count=len(results),
            page=search_request.offset // search_request.limit + 1,
            per_page=search_request.limit,
            query_time_ms=query_time,
            source=source
        )
        
        # Кэшируем результат
        await cache_service.set(cache_key, response.dict(), ttl=300)
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка поиска: {str(e)}"
        )

# Метаданные документа
@app.get("/documents/{doc_id}/meta", response_model=DocumentMeta)
async def get_document_meta(
    doc_id: str,
    edition_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Получение метаданных документа"""
    try:
        # Проверяем кэш
        cache_key = f"meta:{doc_id}:{edition_id or 'latest'}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return DocumentMeta(**cached_result)
        
        # Получаем метаданные
        try:
            with circuit_breaker:
                meta = await techexpert_client.get_document_meta(doc_id, edition_id)
                source = "techexpert"
        except Exception as e:
            logger.warning(f"Онлайн получение метаданных недоступно: {str(e)}")
            meta = await sync_service.get_local_document_meta(doc_id, edition_id)
            source = "local"
        
        if not meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )
        
        meta["source"] = source
        response = DocumentMeta(**meta)
        
        # Кэшируем результат
        await cache_service.set(cache_key, response.dict(), ttl=3600)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения метаданных: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения метаданных: {str(e)}"
        )

# Последняя редакция документа
@app.get("/documents/{doc_id}/latest", response_model=LatestEdition)
async def get_latest_edition(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получение информации о последней редакции документа"""
    try:
        # Получаем информацию о последней редакции
        try:
            with circuit_breaker:
                latest_info = await techexpert_client.get_latest_edition(doc_id)
        except Exception as e:
            logger.warning(f"Онлайн проверка редакции недоступна: {str(e)}")
            latest_info = await sync_service.get_local_latest_edition(doc_id)
        
        if not latest_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )
        
        return LatestEdition(**latest_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения последней редакции: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения последней редакции: {str(e)}"
        )

# Разделы документа
@app.get("/documents/{doc_id}/sections", response_model=SectionsResponse)
async def get_document_sections(
    doc_id: str,
    edition_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Получение списка разделов документа"""
    try:
        # Проверяем кэш
        cache_key = f"sections:{doc_id}:{edition_id or 'latest'}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return SectionsResponse(**cached_result)
        
        # Получаем разделы
        try:
            with circuit_breaker:
                sections = await techexpert_client.get_document_sections(doc_id, edition_id)
        except Exception as e:
            logger.warning(f"Онлайн получение разделов недоступно: {str(e)}")
            sections = await sync_service.get_local_document_sections(doc_id, edition_id)
        
        if not sections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден"
            )
        
        response = SectionsResponse(**sections)
        
        # Кэшируем результат
        await cache_service.set(cache_key, response.dict(), ttl=1800)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения разделов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения разделов: {str(e)}"
        )

# Содержимое раздела
@app.get("/documents/{doc_id}/sections/{section_id}", response_model=SectionContent)
async def get_section_content(
    doc_id: str,
    section_id: str,
    edition_id: Optional[str] = None,
    include_metadata: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Получение содержимого конкретного раздела"""
    try:
        # Проверяем кэш
        cache_key = f"content:{doc_id}:{section_id}:{edition_id or 'latest'}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return SectionContent(**cached_result)
        
        # Получаем содержимое
        try:
            with circuit_breaker:
                content = await techexpert_client.get_section_content(
                    doc_id, section_id, edition_id, include_metadata
                )
        except Exception as e:
            logger.warning(f"Онлайн получение содержимого недоступно: {str(e)}")
            content = await sync_service.get_local_section_content(
                doc_id, section_id, edition_id, include_metadata
            )
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Раздел не найден"
            )
        
        response = SectionContent(**content)
        
        # Кэшируем результат
        await cache_service.set(cache_key, response.dict(), ttl=3600)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения содержимого: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения содержимого: {str(e)}"
        )

# Ссылки на документ
@app.get("/documents/{doc_id}/citations", response_model=CitationsResponse)
async def get_document_citations(
    doc_id: str,
    edition_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Получение списка документов, ссылающихся на данный"""
    try:
        # Проверяем кэш
        cache_key = f"citations:{doc_id}:{edition_id or 'latest'}:{limit}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return CitationsResponse(**cached_result)
        
        # Получаем ссылки
        try:
            with circuit_breaker:
                citations = await techexpert_client.get_document_citations(
                    doc_id, edition_id, limit
                )
        except Exception as e:
            logger.warning(f"Онлайн получение ссылок недоступно: {str(e)}")
            citations = await sync_service.get_local_document_citations(
                doc_id, edition_id, limit
            )
        
        response = CitationsResponse(**citations)
        
        # Кэшируем результат
        await cache_service.set(cache_key, response.dict(), ttl=7200)
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка получения ссылок: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения ссылок: {str(e)}"
        )

# Статус синхронизации
@app.get("/sync/status", response_model=SyncStatus)
async def get_sync_status(current_user: dict = Depends(get_current_user)):
    """Получение статуса синхронизации"""
    try:
        status_info = await sync_service.get_sync_status()
        return SyncStatus(**status_info)
    except Exception as e:
        logger.error(f"Ошибка получения статуса синхронизации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статуса синхронизации: {str(e)}"
        )

# Запуск синхронизации
@app.post("/sync/trigger", response_model=SyncResponse)
async def trigger_sync(
    sync_request: SyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """Принудительный запуск синхронизации документов"""
    try:
        if not current_user.get("admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для запуска синхронизации"
            )
        
        sync_id = await sync_service.trigger_sync(sync_request)
        return SyncResponse(
            sync_id=sync_id,
            status="started",
            estimated_duration_minutes=30
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка запуска синхронизации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка запуска синхронизации: {str(e)}"
        )

# Обработка ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=exc.detail,
            code=str(exc.status_code),
            timestamp=datetime.now(),
            request_id=getattr(request.state, 'request_id', 'unknown')
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик общих исключений"""
    logger.error(f"Необработанная ошибка: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Внутренняя ошибка сервера",
            message="Произошла неожиданная ошибка",
            code="500",
            timestamp=datetime.now(),
            request_id=getattr(request.state, 'request_id', 'unknown')
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    )
