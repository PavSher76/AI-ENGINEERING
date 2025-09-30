"""
Сервис для работы с документами в базе данных
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models import Document, DocumentCollection, Project, User
from schemas import DocumentCreate, CollectionCreate, CollectionResponse, DocumentResponse
from uuid import UUID

logger = logging.getLogger(__name__)

class DocumentService:
    """Сервис для работы с документами"""
    
    async def create_collection(
        self, 
        db: Session, 
        collection_data: CollectionCreate, 
        user_id: UUID
    ) -> CollectionResponse:
        """Создание новой коллекции документов"""
        try:
            # Создание коллекции
            collection = DocumentCollection(
                name=collection_data.name,
                description=collection_data.description,
                collection_type=collection_data.collection_type,
                project_id=collection_data.project_id,
                created_by=user_id
            )
            
            db.add(collection)
            db.commit()
            db.refresh(collection)
            
            # Получение количества документов
            documents_count = db.query(Document).filter(
                Document.collection_id == collection.id
            ).count()
            
            return CollectionResponse(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                collection_type=collection.collection_type,
                project_id=collection.project_id,
                created_by=collection.created_by,
                created_at=collection.created_at,
                updated_at=collection.updated_at,
                documents_count=documents_count
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка создания коллекции: {e}")
            raise
    
    async def get_collections(
        self, 
        db: Session, 
        user_id: UUID,
        project_id: Optional[UUID] = None,
        collection_type: Optional[str] = None
    ) -> List[CollectionResponse]:
        """Получение списка коллекций"""
        try:
            query = db.query(DocumentCollection)
            
            # Фильтрация по проекту
            if project_id:
                query = query.filter(DocumentCollection.project_id == project_id)
            
            # Фильтрация по типу
            if collection_type:
                query = query.filter(DocumentCollection.collection_type == collection_type)
            
            collections = query.all()
            
            # Формирование ответа с количеством документов
            result = []
            for collection in collections:
                documents_count = db.query(Document).filter(
                    Document.collection_id == collection.id
                ).count()
                
                result.append(CollectionResponse(
                    id=collection.id,
                    name=collection.name,
                    description=collection.description,
                    collection_type=collection.collection_type,
                    project_id=collection.project_id,
                    created_by=collection.created_by,
                    created_at=collection.created_at,
                    updated_at=collection.updated_at,
                    documents_count=documents_count
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения коллекций: {e}")
            raise
    
    async def create_document(
        self, 
        db: Session, 
        document_data: DocumentCreate, 
        user_id: UUID
    ) -> DocumentResponse:
        """Создание нового документа"""
        try:
            # Создание документа
            document = Document(
                title=document_data.title,
                description=document_data.description,
                file_path=document_data.file_path,
                file_size=document_data.file_size,
                mime_type=document_data.mime_type,
                document_type=document_data.document_type,
                collection_id=document_data.collection_id,
                project_id=document_data.project_id,
                version=document_data.version,
                metadata=document_data.metadata,
                created_by=user_id
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            return DocumentResponse(
                id=document.id,
                title=document.title,
                description=document.description,
                file_path=document.file_path,
                file_size=document.file_size,
                mime_type=document.mime_type,
                document_type=document.document_type,
                collection_id=document.collection_id,
                project_id=document.project_id,
                version=document.version,
                status=document.status,
                metadata=document.metadata,
                is_processed=document.is_processed,
                created_by=document.created_by,
                created_at=document.created_at,
                updated_at=document.updated_at
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка создания документа: {e}")
            raise
    
    async def get_document(self, db: Session, document_id: UUID) -> Optional[DocumentResponse]:
        """Получение документа по ID"""
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return None
            
            return DocumentResponse(
                id=document.id,
                title=document.title,
                description=document.description,
                file_path=document.file_path,
                file_size=document.file_size,
                mime_type=document.mime_type,
                document_type=document.document_type,
                collection_id=document.collection_id,
                project_id=document.project_id,
                version=document.version,
                status=document.status,
                metadata=document.metadata,
                is_processed=document.is_processed,
                created_by=document.created_by,
                created_at=document.created_at,
                updated_at=document.updated_at
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения документа: {e}")
            raise
    
    async def get_documents_by_ids(
        self, 
        db: Session, 
        document_ids: List[UUID]
    ) -> List[DocumentResponse]:
        """Получение документов по списку ID"""
        try:
            documents = db.query(Document).filter(
                Document.id.in_(document_ids)
            ).all()
            
            result = []
            for document in documents:
                result.append(DocumentResponse(
                    id=document.id,
                    title=document.title,
                    description=document.description,
                    file_path=document.file_path,
                    file_size=document.file_size,
                    mime_type=document.mime_type,
                    document_type=document.document_type,
                    collection_id=document.collection_id,
                    project_id=document.project_id,
                    version=document.version,
                    status=document.status,
                    metadata=document.metadata,
                    is_processed=document.is_processed,
                    created_by=document.created_by,
                    created_at=document.created_at,
                    updated_at=document.updated_at
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения документов по ID: {e}")
            raise
    
    async def update_document_status(
        self, 
        db: Session, 
        document_id: UUID, 
        is_processed: bool
    ):
        """Обновление статуса обработки документа"""
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.is_processed = is_processed
                db.commit()
                logger.info(f"Статус документа {document_id} обновлен: processed={is_processed}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка обновления статуса документа: {e}")
            raise
    
    async def delete_document(self, db: Session, document_id: UUID):
        """Удаление документа"""
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                db.delete(document)
                db.commit()
                logger.info(f"Документ {document_id} удален")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка удаления документа: {e}")
            raise
    
    async def get_collection_stats(self, db: Session, collection_id: UUID) -> Dict[str, Any]:
        """Получение статистики коллекции"""
        try:
            # Общее количество документов
            total_documents = db.query(Document).filter(
                Document.collection_id == collection_id
            ).count()
            
            # Общий размер файлов
            total_size = db.query(func.sum(Document.file_size)).filter(
                Document.collection_id == collection_id
            ).scalar() or 0
            
            # Количество документов по типам
            document_types = db.query(
                Document.document_type,
                func.count(Document.id)
            ).filter(
                Document.collection_id == collection_id
            ).group_by(Document.document_type).all()
            
            document_types_dict = {doc_type: count for doc_type, count in document_types}
            
            # Количество обработанных документов
            processed_documents = db.query(Document).filter(
                and_(
                    Document.collection_id == collection_id,
                    Document.is_processed == True
                )
            ).count()
            
            # Последнее обновление
            last_updated = db.query(func.max(Document.updated_at)).filter(
                Document.collection_id == collection_id
            ).scalar()
            
            return {
                'collection_id': collection_id,
                'total_documents': total_documents,
                'total_size': total_size,
                'document_types': document_types_dict,
                'processed_documents': processed_documents,
                'last_updated': last_updated
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики коллекции: {e}")
            raise
    
    async def search_documents(
        self,
        db: Session,
        query: str,
        collection_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        document_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[DocumentResponse]:
        """Полнотекстовый поиск документов"""
        try:
            search_query = db.query(Document)
            
            # Фильтрация по коллекции
            if collection_id:
                search_query = search_query.filter(Document.collection_id == collection_id)
            
            # Фильтрация по проекту
            if project_id:
                search_query = search_query.filter(Document.project_id == project_id)
            
            # Фильтрация по типам документов
            if document_types:
                search_query = search_query.filter(Document.document_type.in_(document_types))
            
            # Полнотекстовый поиск
            if query:
                search_query = search_query.filter(
                    or_(
                        Document.title.ilike(f"%{query}%"),
                        Document.description.ilike(f"%{query}%")
                    )
                )
            
            # Ограничение результатов
            documents = search_query.limit(limit).all()
            
            # Формирование ответа
            result = []
            for document in documents:
                result.append(DocumentResponse(
                    id=document.id,
                    title=document.title,
                    description=document.description,
                    file_path=document.file_path,
                    file_size=document.file_size,
                    mime_type=document.mime_type,
                    document_type=document.document_type,
                    collection_id=document.collection_id,
                    project_id=document.project_id,
                    version=document.version,
                    status=document.status,
                    metadata=document.metadata,
                    is_processed=document.is_processed,
                    created_by=document.created_by,
                    created_at=document.created_at,
                    updated_at=document.updated_at
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка поиска документов: {e}")
            raise
