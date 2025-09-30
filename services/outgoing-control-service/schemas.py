"""
Pydantic схемы для API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Базовые схемы
class DocumentBase(BaseModel):
    title: str
    document_type: str
    project_id: Optional[UUID] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None

class Document(DocumentBase):
    id: UUID
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    original_text: Optional[str] = None
    extracted_text: Optional[str] = None
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Схемы для проверок
class CheckResult(BaseModel):
    check_type: str
    status: str
    score: Optional[float] = None
    errors_found: int = 0
    warnings_found: int = 0
    recommendations: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class SpellCheckRequest(BaseModel):
    text: str
    language: str = "ru"

class SpellCheckResponse(BaseModel):
    total_words: int
    errors_found: int
    suggestions: List[Dict[str, Any]]
    corrected_text: str
    confidence_score: float

class StyleAnalysisRequest(BaseModel):
    text: str
    document_type: str

class StyleAnalysisResponse(BaseModel):
    readability_score: float
    formality_score: float
    business_style_score: float
    tone_analysis: Dict[str, Any]
    recommendations: str

class EthicsCheckRequest(BaseModel):
    text: str
    context: Optional[str] = None

class EthicsCheckResponse(BaseModel):
    ethics_score: float
    violations_found: List[Dict[str, Any]]
    recommendations: str
    is_approved: bool

class TerminologyCheckRequest(BaseModel):
    text: str
    domain: str

class TerminologyCheckResponse(BaseModel):
    terms_used: List[str]
    incorrect_terms: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    accuracy_score: float

class FinalReviewRequest(BaseModel):
    document_id: UUID
    include_all_checks: bool = True

class FinalReviewResponse(BaseModel):
    overall_score: float
    can_send: bool
    critical_issues: List[str]
    minor_issues: List[str]
    recommendations: str
    reviewer_notes: Optional[str] = None

# Схемы для загрузки файлов
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    mime_type: str
    extracted_text: str

class DocumentProcessingRequest(BaseModel):
    document_id: UUID
    checks_to_perform: List[str] = ["spell_check", "style_check", "ethics_check", "terminology_check"]

class DocumentProcessingResponse(BaseModel):
    document_id: UUID
    status: str
    checks_completed: List[str]
    overall_score: Optional[float] = None
    can_send: Optional[bool] = None
    recommendations: Optional[str] = None

# Схемы для статистики
class ServiceStats(BaseModel):
    total_documents_processed: int
    documents_approved: int
    documents_rejected: int
    documents_needing_revision: int
    average_processing_time: float
    most_common_issues: List[Dict[str, Any]]
