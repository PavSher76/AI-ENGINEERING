"""
Модели данных для сервиса выходного контроля исходящей переписки
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

class OutgoingDocument(Base):
    """Модель исходящего документа"""
    __tablename__ = "outgoing_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=False)  # 'letter', 'email', 'report', 'proposal'
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    original_text = Column(Text)
    extracted_text = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="pending")  # 'pending', 'processing', 'approved', 'rejected', 'needs_revision'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    checks = relationship("DocumentCheck", back_populates="document")
    project = relationship("Project")
    creator = relationship("User")

class DocumentCheck(Base):
    """Модель проверки документа"""
    __tablename__ = "document_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("outgoing_documents.id"))
    check_type = Column(String(100), nullable=False)  # 'spell_check', 'style_check', 'ethics_check', 'logic_check', 'terminology_check'
    status = Column(String(50), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    result = Column(JSON)  # Результаты проверки
    score = Column(Float)  # Оценка качества (0-100)
    recommendations = Column(Text)  # Рекомендации по улучшению
    errors_found = Column(Integer, default=0)
    warnings_found = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Связи
    document = relationship("OutgoingDocument", back_populates="checks")

class SpellCheckResult(Base):
    """Модель результата проверки орфографии"""
    __tablename__ = "spell_check_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("outgoing_documents.id"))
    language = Column(String(10), default="ru")  # 'ru', 'en'
    total_words = Column(Integer)
    errors_found = Column(Integer)
    suggestions = Column(JSON)  # Предложения по исправлению
    corrected_text = Column(Text)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class StyleAnalysisResult(Base):
    """Модель результата анализа стиля"""
    __tablename__ = "style_analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("outgoing_documents.id"))
    readability_score = Column(Float)  # Индекс читаемости
    formality_score = Column(Float)  # Уровень формальности
    business_style_score = Column(Float)  # Соответствие деловому стилю
    tone_analysis = Column(JSON)  # Анализ тона
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class EthicsCheckResult(Base):
    """Модель результата проверки этики"""
    __tablename__ = "ethics_check_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("outgoing_documents.id"))
    ethics_score = Column(Float)  # Оценка этичности (0-100)
    violations_found = Column(JSON)  # Найденные нарушения
    recommendations = Column(Text)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TerminologyCheckResult(Base):
    """Модель результата проверки терминологии"""
    __tablename__ = "terminology_check_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("outgoing_documents.id"))
    domain = Column(String(100))  # Область знаний
    terms_used = Column(JSON)  # Использованные термины
    incorrect_terms = Column(JSON)  # Неправильно использованные термины
    suggestions = Column(JSON)  # Предложения по замене
    accuracy_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class FinalReview(Base):
    """Модель финального заключения"""
    __tablename__ = "final_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("outgoing_documents.id"))
    overall_score = Column(Float)  # Общая оценка
    can_send = Column(Boolean, default=False)  # Можно ли отправлять
    critical_issues = Column(JSON)  # Критические проблемы
    minor_issues = Column(JSON)  # Мелкие проблемы
    recommendations = Column(Text)  # Общие рекомендации
    reviewer_notes = Column(Text)  # Заметки рецензента
    created_at = Column(DateTime, default=datetime.utcnow)

# Базовые модели
class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Project(Base):
    """Модель проекта"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
