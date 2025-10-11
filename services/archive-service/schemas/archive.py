"""
Схемы данных для модуля "Объекты-аналоги и Архив"
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProjectPhase(str, Enum):
    """Фазы проекта"""
    PD = "PD"  # Проектная документация
    RD = "RD"  # Рабочая документация


class Discipline(str, Enum):
    """Инженерные дисциплины"""
    PROCESS = "process"
    PIPING = "piping"
    CIVIL = "civil"
    ELECTRICAL = "elec"
    INSTRUMENTATION = "instr"
    HVAC = "hvac"
    PROCUREMENT = "procurement"


class ConfidentialityLevel(str, Enum):
    """Уровни конфиденциальности"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


class DocumentType(str, Enum):
    """Типы документов"""
    PFD = "PFD"  # Process Flow Diagram
    PID = "P&ID"  # Piping and Instrumentation Diagram
    SPEC = "SPEC"  # Спецификация
    BOM = "BOM"  # Bill of Materials
    BOQ = "BOQ"  # Bill of Quantities
    DRAWING = "DRAWING"  # Чертеж
    IFC = "IFC"  # IFC модель
    MANUAL = "MANUAL"  # Руководство
    REPORT = "REPORT"  # Отчет


class ProcessingStatus(str, Enum):
    """Статусы обработки"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Manifest(BaseModel):
    """Манифест архива проекта"""
    project_id: str = Field(..., description="Идентификатор проекта")
    object_id: str = Field(..., description="Идентификатор объекта")
    phase: ProjectPhase = Field(..., description="Фаза проекта")
    customer: str = Field(..., description="Заказчик")
    language: List[str] = Field(default=["ru"], description="Языки документации")
    confidentiality: ConfidentialityLevel = Field(default=ConfidentialityLevel.INTERNAL)
    default_discipline: Discipline = Field(default=Discipline.PROCESS)
    ingest_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Дополнительные поля
    description: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ArchiveUploadRequest(BaseModel):
    """Запрос на загрузку архива"""
    manifest: Manifest
    archive_path: str = Field(..., description="Путь к архиву в MinIO")
    archive_size: int = Field(..., description="Размер архива в байтах")
    archive_hash: str = Field(..., description="SHA-256 хеш архива")


class ProcessingStatus(str, Enum):
    """Статусы обработки"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ProcessingJob(BaseModel):
    """Задание на обработку"""
    job_id: str
    project_id: str
    object_id: str
    status: ProcessingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Статистика обработки
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    total_vectors: int = 0


class DocumentMetadata(BaseModel):
    """Метаданные документа"""
    doc_no: str = Field(..., description="Номер документа")
    rev: str = Field(..., description="Ревизия")
    page: Optional[int] = None
    section: Optional[str] = None
    discipline: Discipline
    doc_type: DocumentType
    language: str = Field(default="ru")
    source_path: str = Field(..., description="Путь к исходному файлу")
    source_hash: str = Field(..., description="SHA-256 хеш файла")
    issued_at: Optional[datetime] = None
    vendor: Optional[str] = None
    confidentiality: ConfidentialityLevel
    tags: List[str] = Field(default_factory=list)
    
    # Числовые параметры для фильтрации
    numeric: Dict[str, Union[int, float]] = Field(default_factory=dict)
    
    # Права доступа
    permissions: List[str] = Field(default_factory=list)


class ChunkPayload(BaseModel):
    """Payload для чанка в Qdrant"""
    project_id: str
    object_id: str
    spp_id: str = Field(default="0000000000")  # Системный идентификатор
    discipline: Discipline
    doc_no: str
    rev: str
    page: Optional[int] = None
    section: Optional[str] = None
    language: str
    source_path: str
    source_hash: str
    issued_at: Optional[datetime] = None
    vendor: Optional[str] = None
    confidentiality: ConfidentialityLevel
    tags: List[str] = Field(default_factory=list)
    numeric: Dict[str, Union[int, float]] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    
    # Связи для трейсинга
    doc_id: Optional[str] = None
    chunk_id: str
    parent_chunk_id: Optional[str] = None
    ifc_guid: Optional[str] = None
    bom_row_id: Optional[str] = None


class TextChunk(BaseModel):
    """Текстовый чанк"""
    chunk_id: str
    content: str
    metadata: DocumentMetadata
    chunk_type: str = "text"
    token_count: int
    overlap: int = 0


class TableChunk(BaseModel):
    """Чанк таблицы"""
    chunk_id: str
    content: str
    metadata: DocumentMetadata
    chunk_type: str = "table"
    row_data: Dict[str, Any]
    row_hash: str


class DrawingChunk(BaseModel):
    """Чанк чертежа"""
    chunk_id: str
    content: str
    metadata: DocumentMetadata
    chunk_type: str = "drawing"
    preview_path: Optional[str] = None
    extracted_text: Optional[str] = None


class IFCChunk(BaseModel):
    """Чанк IFC объекта"""
    chunk_id: str
    content: str
    metadata: DocumentMetadata
    chunk_type: str = "ifc"
    ifc_type: str
    ifc_guid: str
    properties: Dict[str, Any]


class VectorizationRequest(BaseModel):
    """Запрос на векторизацию"""
    chunks: List[Union[TextChunk, TableChunk, DrawingChunk, IFCChunk]]
    collection_name: str
    model_name: str = "bge-m3"


class SearchRequest(BaseModel):
    """Запрос на поиск"""
    query: str
    project_id: Optional[str] = None
    object_id: Optional[str] = None
    discipline: Optional[Discipline] = None
    doc_type: Optional[DocumentType] = None
    language: str = "ru"
    limit: int = Field(default=10, ge=1, le=50)
    filters: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Результат поиска"""
    chunk_id: str
    content: str
    score: float
    metadata: ChunkPayload
    source_url: Optional[str] = None
    context_bbox: Optional[Dict[str, float]] = None


class AnalogSearchRequest(BaseModel):
    """Запрос на поиск аналогов"""
    equipment_type: str
    parameters: Dict[str, Union[int, float]]
    discipline: Optional[Discipline] = None
    vendor: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=20)


class AnalogResult(BaseModel):
    """Результат поиска аналогов"""
    equipment_id: str
    equipment_type: str
    parameters: Dict[str, Union[int, float]]
    similarity_score: float
    source_documents: List[str]
    vendor: Optional[str] = None
    project_context: str
