"""
RAG Service - Сервис для работы с векторными базами данных и поиском по документам
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import os
from typing import List, Optional, Dict, Any
import logging

from database import get_db, engine
from models import Base
from schemas import (
    DocumentCreate, DocumentResponse, DocumentSearchRequest, 
    DocumentSearchResponse, CollectionCreate, CollectionResponse,
    EmbeddingRequest, EmbeddingResponse
)
from services.document_service import DocumentService
from services.embedding_service import EmbeddingService
from services.vector_service import VectorService
from services.minio_service import MinIOService
from auth import get_current_user, get_current_user_optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAG Service",
    description="Сервис для работы с векторными базами данных и поиском по документам",
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

# Инициализация сервисов
document_service = DocumentService()
embedding_service = EmbeddingService()
vector_service = VectorService()
minio_service = MinIOService()

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Запуск RAG Service...")
    await vector_service.initialize()
    await minio_service.initialize()
    logger.info("RAG Service готов к работе")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "rag-service"}

@app.post("/collections/", response_model=CollectionResponse)
async def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Создание новой коллекции документов"""
    try:
        user_id = current_user.id if current_user else "system"
        result = await document_service.create_collection(db, collection, user_id)
        return result
    except Exception as e:
        logger.error(f"Ошибка создания коллекции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/", response_model=List[CollectionResponse])
async def get_collections(
    project_id: Optional[str] = None,
    collection_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Получение списка коллекций"""
    try:
        user_id = current_user.id if current_user else "system"
        collections = await document_service.get_collections(
            db, user_id, project_id, collection_type
        )
        return collections
    except Exception as e:
        logger.error(f"Ошибка получения коллекций: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_id: str = None,
    project_id: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Загрузка и обработка документа"""
    try:
        # Сохранение файла в MinIO
        file_path = await minio_service.upload_file(file)
        
        # Создание записи в базе данных
        document_data = DocumentCreate(
            title=file.filename,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            collection_id=collection_id,
            project_id=project_id
        )
        
        user_id = current_user.id if current_user else "system"
        document = await document_service.create_document(db, document_data, user_id)
        
        # Асинхронная обработка документа для создания эмбеддингов
        background_tasks.add_task(
            process_document_for_rag,
            document.id,
            file_path,
            collection_id
        )
        
        return document
    except Exception as e:
        logger.error(f"Ошибка загрузки документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_for_rag(document_id: str, file_path: str, collection_id: str):
    """Обработка документа для создания эмбеддингов"""
    try:
        # Извлечение текста из документа
        text_content = await minio_service.extract_text(file_path)
        
        # Создание эмбеддингов
        embeddings = await embedding_service.create_embeddings(text_content)
        
        # Сохранение в векторную базу данных
        await vector_service.store_embeddings(
            document_id=document_id,
            collection_id=collection_id,
            text=text_content,
            embeddings=embeddings
        )
        
        logger.info(f"Документ {document_id} успешно обработан для RAG")
    except Exception as e:
        logger.error(f"Ошибка обработки документа {document_id}: {e}")

@app.post("/documents/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Поиск документов по семантическому сходству"""
    try:
        # Создание эмбеддинга для поискового запроса
        query_embedding = await embedding_service.create_embedding(search_request.query)
        
        # Поиск в векторной базе данных
        search_results = await vector_service.search_similar(
            query_embedding=query_embedding,
            collection_id=search_request.collection_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            threshold=search_request.threshold
        )
        
        # Получение полной информации о документах
        documents = await document_service.get_documents_by_ids(
            db, [result.document_id for result in search_results]
        )
        
        return DocumentSearchResponse(
            query=search_request.query,
            results=documents,
            scores=[result.score for result in search_results],
            total=len(documents)
        )
    except Exception as e:
        logger.error(f"Ошибка поиска документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embeddings/", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    current_user = Depends(get_current_user_optional)
):
    """Создание эмбеддингов для текста"""
    try:
        if isinstance(request.text, str):
            embeddings = await embedding_service.create_embedding(request.text)
        else:
            embeddings = await embedding_service.create_embeddings(request.text)
        
        return EmbeddingResponse(embeddings=embeddings)
    except Exception as e:
        logger.error(f"Ошибка создания эмбеддингов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Получение документа по ID"""
    try:
        document = await document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        return document
    except Exception as e:
        logger.error(f"Ошибка получения документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Удаление документа"""
    try:
        # Получение документа
        document = await document_service.get_document(db, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Удаление из векторной базы данных
        await vector_service.delete_document(document_id)
        
        # Удаление файла из MinIO
        await minio_service.delete_file(document.file_path)
        
        # Удаление записи из базы данных
        await document_service.delete_document(db, document_id)
        
        return {"message": "Документ успешно удален"}
    except Exception as e:
        logger.error(f"Ошибка удаления документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/{collection_id}/stats")
async def get_collection_stats(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Получение статистики коллекции"""
    try:
        stats = await document_service.get_collection_stats(db, collection_id)
        return stats
    except Exception as e:
        logger.error(f"Ошибка получения статистики коллекции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
