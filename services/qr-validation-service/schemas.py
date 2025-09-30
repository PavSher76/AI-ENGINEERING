"""
Pydantic схемы для QR валидации РД
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DocumentStatusEnum(str, Enum):
    """Статусы документов РД"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"
    IN_CONSTRUCTION = "in_construction"
    COMPLETED = "completed"

class DocumentTypeEnum(str, Enum):
    """Типы документов РД"""
    DRAWING = "drawing"
    SPECIFICATION = "specification"
    STATEMENT = "statement"
    CALCULATION = "calculation"
    REPORT = "report"
    CERTIFICATE = "certificate"
    PROTOCOL = "protocol"
    INSTRUCTION = "instruction"
    MANUAL = "manual"
    OTHER = "other"

# Запросы
class QRGenerateRequest(BaseModel):
    """Запрос на генерацию QR-кода"""
    document_id: str = Field(..., description="Уникальный ID документа")
    document_type: DocumentTypeEnum = Field(..., description="Тип документа")
    project_id: str = Field(..., description="ID проекта")
    version: str = Field(default="1.0", description="Версия документа")
    title: Optional[str] = Field(None, description="Название документа")
    description: Optional[str] = Field(None, description="Описание документа")
    author: Optional[str] = Field(None, description="Автор документа")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные метаданные")
    
    @validator('document_id')
    def validate_document_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Document ID не может быть пустым')
        return v.strip()
    
    @validator('project_id')
    def validate_project_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Project ID не может быть пустым')
        return v.strip()

class QRValidateRequest(BaseModel):
    """Запрос на валидацию QR-кода"""
    qr_data: str = Field(..., description="Данные QR-кода для валидации")
    validate_signature: bool = Field(default=True, description="Проверять ли цифровую подпись")
    
    @validator('qr_data')
    def validate_qr_data(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('QR данные не могут быть пустыми')
        return v.strip()

class DocumentStatusUpdateRequest(BaseModel):
    """Запрос на обновление статуса документа"""
    status: DocumentStatusEnum = Field(..., description="Новый статус документа")
    comment: Optional[str] = Field(None, description="Комментарий к изменению статуса")
    updated_by: Optional[str] = Field(None, description="Пользователь, обновивший статус")

# Ответы
class QRGenerateResponse(BaseModel):
    """Ответ на генерацию QR-кода"""
    document_id: str = Field(..., description="ID документа")
    qr_code_path: str = Field(..., description="Путь к файлу QR-кода")
    qr_data: str = Field(..., description="Данные QR-кода")
    status: str = Field(..., description="Статус генерации")
    message: str = Field(..., description="Сообщение о результате")

class DocumentInfo(BaseModel):
    """Информация о документе"""
    document_id: str
    document_type: DocumentTypeEnum
    project_id: str
    version: str
    status: DocumentStatusEnum
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class QRValidateResponse(BaseModel):
    """Ответ на валидацию QR-кода"""
    is_valid: bool = Field(..., description="Валиден ли QR-код")
    status: str = Field(..., description="Статус валидации")
    message: str = Field(..., description="Сообщение о результате валидации")
    document_info: Optional[DocumentInfo] = Field(None, description="Информация о документе")

class QRDocumentResponse(BaseModel):
    """Ответ с информацией о документе"""
    document_id: str
    document_type: DocumentTypeEnum
    project_id: str
    version: str
    status: DocumentStatusEnum
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class DocumentStatusResponse(BaseModel):
    """Ответ со статусом документа"""
    document_id: str
    status: DocumentStatusEnum
    message: str
    updated_at: datetime

class QRStatsResponse(BaseModel):
    """Статистика по QR-кодам"""
    total_documents: int = Field(..., description="Общее количество документов")
    documents_by_status: Dict[str, int] = Field(..., description="Количество документов по статусам")
    documents_by_type: Dict[str, int] = Field(..., description="Количество документов по типам")
    total_validations: int = Field(..., description="Общее количество валидаций")
    successful_validations: int = Field(..., description="Успешные валидации")
    failed_validations: int = Field(..., description="Неуспешные валидации")
    last_validation: Optional[datetime] = Field(None, description="Последняя валидация")

class ValidationLogResponse(BaseModel):
    """Лог валидации"""
    id: str
    document_id: str
    is_valid: bool
    validation_status: str
    validation_message: Optional[str]
    validated_at: datetime
    validator_ip: Optional[str]
    validator_user_id: Optional[str]

class ProjectResponse(BaseModel):
    """Информация о проекте"""
    id: str
    project_id: str
    name: str
    description: Optional[str]
    client: Optional[str]
    contractor: Optional[str]
    location: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Вспомогательные схемы
class QRData(BaseModel):
    """Структура данных QR-кода"""
    document_id: str
    document_type: str
    project_id: str
    version: str
    timestamp: datetime
    signature: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    """Результат валидации"""
    is_valid: bool
    status: str
    message: str
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class DocumentSearchRequest(BaseModel):
    """Запрос на поиск документов"""
    project_id: Optional[str] = None
    document_type: Optional[DocumentTypeEnum] = None
    status: Optional[DocumentStatusEnum] = None
    author: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class DocumentSearchResponse(BaseModel):
    """Ответ на поиск документов"""
    documents: List[QRDocumentResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
