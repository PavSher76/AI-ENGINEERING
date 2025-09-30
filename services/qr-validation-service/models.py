"""
Модели данных для QR валидации РД
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Enum, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
import uuid

Base = declarative_base()

class DocumentStatus(PyEnum):
    """Статусы документов РД"""
    DRAFT = "draft"                    # Черновик
    IN_REVIEW = "in_review"            # На рассмотрении
    APPROVED = "approved"              # Согласован
    REJECTED = "rejected"              # Отклонен
    OBSOLETE = "obsolete"              # Устарел
    ARCHIVED = "archived"              # Архивирован
    IN_CONSTRUCTION = "in_construction" # В строительстве
    COMPLETED = "completed"            # Завершен

class DocumentType(PyEnum):
    """Типы документов РД"""
    DRAWING = "drawing"                # Чертеж
    SPECIFICATION = "specification"    # Спецификация
    STATEMENT = "statement"            # Ведомость
    CALCULATION = "calculation"        # Расчет
    REPORT = "report"                  # Отчет
    CERTIFICATE = "certificate"        # Справка
    PROTOCOL = "protocol"              # Протокол
    INSTRUCTION = "instruction"        # Инструкция
    MANUAL = "manual"                  # Руководство
    OTHER = "other"                    # Прочее

class QRDocument(Base):
    """Модель документа РД с QR-кодом"""
    __tablename__ = "qr_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, unique=True, nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    project_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False, default="1.0")
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT)
    
    # Метаданные документа
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    reviewer = Column(String, nullable=True)
    approver = Column(String, nullable=True)
    
    # Технические данные
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String, nullable=True)
    
    # QR-код данные
    qr_code_path = Column(String, nullable=True)
    qr_data = Column(Text, nullable=True)
    qr_signature = Column(String, nullable=True)
    
    # Дополнительные метаданные
    metadata = Column(JSON, nullable=True, default=dict)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Статус валидации
    is_valid = Column(Boolean, default=True, nullable=False)
    validation_errors = Column(JSON, nullable=True, default=list)
    
    def __repr__(self):
        return f"<QRDocument(id={self.document_id}, type={self.document_type}, status={self.status})>"

class QRValidationLog(Base):
    """Лог валидации QR-кодов"""
    __tablename__ = "qr_validation_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    qr_data = Column(Text, nullable=False)
    
    # Результат валидации
    is_valid = Column(Boolean, nullable=False)
    validation_status = Column(String, nullable=False)
    validation_message = Column(Text, nullable=True)
    
    # Информация о валидаторе
    validator_ip = Column(String, nullable=True)
    validator_user_agent = Column(String, nullable=True)
    validator_user_id = Column(String, nullable=True)
    
    # Временная метка
    validated_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<QRValidationLog(document_id={self.document_id}, valid={self.is_valid})>"

class DocumentVersion(Base):
    """Версии документов"""
    __tablename__ = "document_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    
    # Данные версии
    file_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # QR-код для версии
    qr_code_path = Column(String, nullable=True)
    qr_data = Column(Text, nullable=True)
    
    # Метаданные версии
    change_description = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    
    # Статус версии
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DocumentVersion(document_id={self.document_id}, version={self.version})>"

class Project(Base):
    """Проекты"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Метаданные проекта
    client = Column(String, nullable=True)
    contractor = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Статус проекта
    status = Column(String, nullable=False, default="active")
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Project(id={self.project_id}, name={self.name})>"
