"""
Модели данных для RAG сервиса
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

class DocumentCollection(Base):
    """Модель коллекции документов"""
    __tablename__ = "document_collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    collection_type = Column(String(100), nullable=False)  # 'normative', 'chat', 'input_data', 'project', 'archive', 'analogues'
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    documents = relationship("Document", back_populates="collection")
    project = relationship("Project", back_populates="collections")
    creator = relationship("User", back_populates="created_collections")

class Document(Base):
    """Модель документа"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    document_type = Column(String(100))  # 'drawing', 'specification', 'report', 'calculation', 'normative'
    collection_id = Column(UUID(as_uuid=True), ForeignKey("document_collections.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    version = Column(String(50), default="1.0")
    status = Column(String(50), default="draft")
    document_metadata = Column(JSON)  # Дополнительные метаданные
    is_processed = Column(Boolean, default=False)  # Обработан ли для RAG
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    collection = relationship("DocumentCollection", back_populates="documents")
    project = relationship("Project", back_populates="documents")
    creator = relationship("User", back_populates="created_documents")

class Project(Base):
    """Модель проекта"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_code = Column(String(100), unique=True, nullable=False)
    status = Column(String(50), default="active")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    collections = relationship("DocumentCollection", back_populates="project")
    documents = relationship("Document", back_populates="project")

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    keycloak_id = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    created_collections = relationship("DocumentCollection", back_populates="creator")
    created_documents = relationship("Document", back_populates="creator")

class DocumentEmbedding(Base):
    """Модель для хранения эмбеддингов документов"""
    __tablename__ = "document_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_id = Column(String(255), nullable=False)  # ID чанка текста
    chunk_text = Column(Text, nullable=False)
    embedding_vector = Column(JSON)  # Вектор эмбеддинга
    chunk_index = Column(Integer)  # Порядковый номер чанка
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    document = relationship("Document")

class SearchHistory(Base):
    """Модель истории поиска"""
    __tablename__ = "search_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("document_collections.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    results_count = Column(Integer)
    search_params = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User")
    collection = relationship("DocumentCollection")
    project = relationship("Project")
