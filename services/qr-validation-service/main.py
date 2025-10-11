"""
QR валидация РД - Сервис для генерации и валидации QR-кодов рабочей документации
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import sys
from typing import List, Optional
import io
import base64
import logging
import traceback
from datetime import datetime

# Импорт утилит логирования
from logging_utils import setup_service_logging, log_request, log_error, log_performance, log_business_event

from database import init_db
from models import QRDocument, DocumentStatus
from schemas import (
    QRGenerateRequest, QRGenerateResponse, 
    QRValidateRequest, QRValidateResponse,
    DocumentStatusResponse, QRDocumentResponse
)
from services.qr_service import QRService
from services.document_service import DocumentService
from services.validation_service import ValidationService

# Настройка логирования
logger = setup_service_logging("qr-validation-service")

# Инициализация базы данных при запуске
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 QR Validation Service запускается...")
    await init_db()
    logger.info("✅ База данных инициализирована")
    logger.info("📱 QR Validation Service готов к работе")
    yield
    # Shutdown
    logger.info("🛑 QR Validation Service останавливается...")

app = FastAPI(
    title="QR валидация РД",
    description="Сервис для генерации и валидации QR-кодов рабочей документации",
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

# Middleware для логирования запросов
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = datetime.now()
    request_id = f"qr_req_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
    
    logger.info(f"📥 Входящий запрос: {request.method} {request.url.path}", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params)
    })
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        
        log_request(
            logger=logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time,
            request_id=request_id
        )
        
        return response
        
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        log_error(
            logger=logger,
            error=e,
            context=f"HTTP {request.method} {request.url.path}",
            request_id=request_id
        )
        raise

# Инициализация сервисов
qr_service = QRService()
document_service = DocumentService()
validation_service = ValidationService()

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    logger.info("🏥 Health check запрос")
    return {
        "status": "healthy",
        "service": "qr-validation-service",
        "version": "1.0.0"
    }

@app.post("/qr/generate", response_model=QRGenerateResponse)
async def generate_qr_code(request: QRGenerateRequest):
    """
    Генерация QR-кода для документа РД
    
    - **document_id**: ID документа
    - **document_type**: Тип документа (чертеж, спецификация, ведомость и т.д.)
    - **project_id**: ID проекта
    - **version**: Версия документа
    - **metadata**: Дополнительные метаданные
    """
    start_time = datetime.now()
    logger.info(f"🔧 Генерация QR-кода для документа {request.document_id}", extra={
        "document_id": request.document_id,
        "document_type": request.document_type,
        "project_id": request.project_id,
        "version": request.version
    })
    
    try:
        # Создаем или обновляем запись документа
        document = await document_service.create_or_update_document(
            document_id=request.document_id,
            document_type=request.document_type,
            project_id=request.project_id,
            version=request.version,
            document_metadata=request.metadata
        )
        
        # Генерируем QR-код
        qr_data = qr_service.generate_qr_data(document)
        qr_image = qr_service.generate_qr_image(qr_data)
        
        # Сохраняем QR-код
        qr_path = await qr_service.save_qr_code(
            document_id=request.document_id,
            qr_image=qr_image,
            version=request.version
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        log_performance(
            logger=logger,
            operation="generate_qr_code",
            duration=duration,
            success=True,
            document_id=request.document_id
        )
        
        log_business_event(
            logger=logger,
            event="qr_code_generated",
            document_id=request.document_id,
            project_id=request.project_id,
            document_type=request.document_type
        )
        
        logger.info(f"✅ QR-код успешно сгенерирован для документа {request.document_id}")
        
        return QRGenerateResponse(
            document_id=request.document_id,
            qr_code_path=qr_path,
            qr_data=qr_data,
            status="generated",
            message="QR-код успешно сгенерирован"
        )
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        log_performance(
            logger=logger,
            operation="generate_qr_code",
            duration=duration,
            success=False,
            document_id=request.document_id
        )
        log_error(
            logger=logger,
            error=e,
            context="generate_qr_code",
            document_id=request.document_id
        )
        raise HTTPException(status_code=500, detail=f"Ошибка генерации QR-кода: {str(e)}")

@app.post("/qr/validate", response_model=QRValidateResponse)
async def validate_qr_code(request: QRValidateRequest):
    """
    Валидация QR-кода документа РД
    
    - **qr_data**: Данные QR-кода для валидации
    - **validate_signature**: Проверять ли цифровую подпись
    """
    start_time = datetime.now()
    logger.info("🔍 Валидация QR-кода", extra={
        "validate_signature": request.validate_signature,
        "qr_data_length": len(request.qr_data)
    })
    
    try:
        # Парсим данные QR-кода
        qr_info = qr_service.parse_qr_data(request.qr_data)
        document_id = qr_info.get("document_id")
        
        logger.info(f"📋 Парсинг QR-кода для документа {document_id}")
        
        # Получаем информацию о документе
        document = await document_service.get_document(document_id)
        
        if not document:
            logger.warning(f"⚠️ Документ {document_id} не найден")
            return QRValidateResponse(
                is_valid=False,
                status="not_found",
                message="Документ не найден",
                document_info=None
            )
        
        # Валидируем документ
        validation_result = await validation_service.validate_document(
            document=document,
            qr_info=qr_info,
            check_signature=request.validate_signature
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        log_performance(
            logger=logger,
            operation="validate_qr_code",
            duration=duration,
            success=validation_result["is_valid"],
            document_id=document_id
        )
        
        log_business_event(
            logger=logger,
            event="qr_code_validated",
            document_id=document_id,
            is_valid=validation_result["is_valid"],
            status=validation_result["status"]
        )
        
        logger.info(f"✅ Валидация QR-кода завершена для документа {document_id}: {validation_result['status']}")
        
        return QRValidateResponse(
            is_valid=validation_result["is_valid"],
            status=validation_result["status"],
            message=validation_result["message"],
            document_info={
                "document_id": document.document_id,
                "document_type": document.document_type,
                "project_id": document.project_id,
                "version": document.version,
                "status": document.status,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "metadata": document.document_metadata
            }
        )
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        log_performance(
            logger=logger,
            operation="validate_qr_code",
            duration=duration,
            success=False
        )
        log_error(
            logger=logger,
            error=e,
            context="validate_qr_code"
        )
        raise HTTPException(status_code=500, detail=f"Ошибка валидации QR-кода: {str(e)}")

@app.post("/qr/validate-image", response_model=QRValidateResponse)
async def validate_qr_image(file: UploadFile = File(...)):
    """
    Валидация QR-кода из файла (изображение или PDF)
    
    - **file**: Файл с QR-кодом (изображение или PDF)
    """
    try:
        # Читаем файл
        file_data = await file.read()
        file_type = file.content_type or "application/octet-stream"
        
        # Извлекаем QR-код из файла
        qr_data = qr_service.extract_qr_from_file(file_data, file_type)
        
        if not qr_data:
            file_type_name = "изображении" if file_type.startswith('image/') else "PDF файле"
            return QRValidateResponse(
                is_valid=False,
                status="no_qr_found",
                message=f"QR-код не найден в {file_type_name}",
                document_info=None
            )
        
        # Валидируем QR-код
        validation_request = QRValidateRequest(
            qr_data=qr_data,
            validate_signature=True
        )
        
        return await validate_qr_code(validation_request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")

@app.get("/qr/document/{document_id}", response_model=QRDocumentResponse)
async def get_document_info(document_id: str):
    """
    Получение информации о документе по ID
    
    - **document_id**: ID документа
    """
    try:
        document = await document_service.get_document(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        return QRDocumentResponse(
            document_id=document.document_id,
            document_type=document.document_type,
            project_id=document.project_id,
            version=document.version,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            metadata=document.document_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о документе: {str(e)}")

@app.get("/qr/documents", response_model=List[QRDocumentResponse])
async def get_documents(
    project_id: Optional[str] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Получение списка документов с фильтрацией
    
    - **project_id**: Фильтр по ID проекта
    - **document_type**: Фильтр по типу документа
    - **status**: Фильтр по статусу
    - **limit**: Максимальное количество документов
    - **offset**: Смещение для пагинации
    """
    try:
        documents = await document_service.get_documents(
            project_id=project_id,
            document_type=document_type,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            QRDocumentResponse(
                document_id=doc.document_id,
                document_type=doc.document_type,
                project_id=doc.project_id,
                version=doc.version,
                status=doc.status,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                metadata=doc.document_metadata
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка документов: {str(e)}")

@app.put("/qr/document/{document_id}/status")
async def update_document_status(
    document_id: str,
    status: DocumentStatus,
    comment: Optional[str] = None
):
    """
    Обновление статуса документа
    
    - **document_id**: ID документа
    - **status**: Новый статус документа
    - **comment**: Комментарий к изменению статуса
    """
    try:
        document = await document_service.update_document_status(
            document_id=document_id,
            status=status,
            comment=comment
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        return {
            "document_id": document_id,
            "status": status,
            "message": "Статус документа обновлен",
            "updated_at": document.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления статуса: {str(e)}")

@app.get("/qr/stats")
async def get_qr_stats():
    """Получение статистики по QR-кодам и документам"""
    try:
        stats = await document_service.get_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@app.get("/qr/download/{document_id}")
async def download_qr_code(document_id: str, version: Optional[str] = None):
    """
    Скачивание QR-кода документа
    
    - **document_id**: ID документа
    - **version**: Версия документа (опционально)
    """
    try:
        qr_path = await qr_service.get_qr_code_path(document_id, version)
        
        if not qr_path or not os.path.exists(qr_path):
            raise HTTPException(status_code=404, detail="QR-код не найден")
        
        return FileResponse(
            path=qr_path,
            media_type="image/png",
            filename=f"qr_{document_id}_{version or 'latest'}.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания QR-кода: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8013)
