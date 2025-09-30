"""
Pydantic схемы для RAG сервиса
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID

class DocumentCreate(BaseModel):
    """Схема для создания документа"""
    title: str = Field(..., description="Название документа")
    description: Optional[str] = Field(None, description="Описание документа")
    file_path: Optional[str] = Field(None, description="Путь к файлу")
    file_size: Optional[int] = Field(None, description="Размер файла")
    mime_type: Optional[str] = Field(None, description="MIME тип файла")
    document_type: Optional[str] = Field(None, description="Тип документа")
    collection_id: Optional[UUID] = Field(None, description="ID коллекции")
    project_id: Optional[UUID] = Field(None, description="ID проекта")
    version: str = Field("1.0", description="Версия документа")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")

class DocumentResponse(BaseModel):
    """Схема ответа с информацией о документе"""
    id: UUID
    title: str
    description: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    document_type: Optional[str]
    collection_id: Optional[UUID]
    project_id: Optional[UUID]
    version: str
    status: str
    metadata: Optional[Dict[str, Any]]
    is_processed: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CollectionCreate(BaseModel):
    """Схема для создания коллекции"""
    name: str = Field(..., description="Название коллекции")
    description: Optional[str] = Field(None, description="Описание коллекции")
    collection_type: str = Field(..., description="Тип коллекции")
    project_id: Optional[UUID] = Field(None, description="ID проекта")

class CollectionResponse(BaseModel):
    """Схема ответа с информацией о коллекции"""
    id: UUID
    name: str
    description: Optional[str]
    collection_type: str
    project_id: Optional[UUID]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    documents_count: Optional[int] = Field(None, description="Количество документов в коллекции")
    
    class Config:
        from_attributes = True

class DocumentSearchRequest(BaseModel):
    """Схема запроса поиска документов"""
    query: str = Field(..., description="Поисковый запрос")
    collection_id: Optional[UUID] = Field(None, description="ID коллекции для поиска")
    project_id: Optional[UUID] = Field(None, description="ID проекта для поиска")
    limit: int = Field(10, ge=1, le=100, description="Максимальное количество результатов")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Минимальный порог сходства")
    document_types: Optional[List[str]] = Field(None, description="Фильтр по типам документов")

class DocumentSearchResponse(BaseModel):
    """Схема ответа поиска документов"""
    query: str
    results: List[DocumentResponse]
    scores: List[float]
    total: int
    search_time: Optional[float] = Field(None, description="Время выполнения поиска в секундах")

class EmbeddingRequest(BaseModel):
    """Схема запроса создания эмбеддингов"""
    text: Union[str, List[str]] = Field(..., description="Текст или список текстов для создания эмбеддингов")

class EmbeddingResponse(BaseModel):
    """Схема ответа с эмбеддингами"""
    embeddings: Union[List[float], List[List[float]]] = Field(..., description="Эмбеддинги")
    model: str = Field(..., description="Модель, использованная для создания эмбеддингов")
    dimensions: int = Field(..., description="Размерность эмбеддингов")

class DocumentChunk(BaseModel):
    """Схема чанка документа"""
    id: str
    text: str
    chunk_index: int
    document_id: UUID
    embedding: Optional[List[float]] = None

class VectorSearchResult(BaseModel):
    """Схема результата векторного поиска"""
    document_id: UUID
    chunk_id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class CollectionStats(BaseModel):
    """Схема статистики коллекции"""
    collection_id: UUID
    total_documents: int
    total_size: int
    document_types: Dict[str, int]
    processed_documents: int
    last_updated: Optional[datetime]

class DocumentProcessingStatus(BaseModel):
    """Схема статуса обработки документа"""
    document_id: UUID
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: float = Field(0.0, ge=0.0, le=1.0)
    error_message: Optional[str] = None
    processed_chunks: int = 0
    total_chunks: int = 0

class BulkUploadRequest(BaseModel):
    """Схема массовой загрузки документов"""
    collection_id: Optional[UUID] = Field(None, description="ID коллекции")
    project_id: Optional[UUID] = Field(None, description="ID проекта")
    document_type: Optional[str] = Field(None, description="Тип документов")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Общие метаданные")

class BulkUploadResponse(BaseModel):
    """Схема ответа массовой загрузки"""
    task_id: str
    total_files: int
    status: str
    message: str
