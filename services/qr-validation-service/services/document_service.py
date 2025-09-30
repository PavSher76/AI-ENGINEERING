"""
Сервис для работы с документами РД
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database import get_db
from models import QRDocument, DocumentStatus, DocumentType, DocumentVersion, Project
from schemas import DocumentStatusEnum, DocumentTypeEnum

class DocumentService:
    """Сервис для работы с документами РД"""
    
    async def create_or_update_document(
        self,
        document_id: str,
        document_type: DocumentTypeEnum,
        project_id: str,
        version: str = "1.0",
        title: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QRDocument:
        """
        Создает или обновляет документ
        
        Args:
            document_id: ID документа
            document_type: Тип документа
            project_id: ID проекта
            version: Версия документа
            title: Название документа
            description: Описание документа
            author: Автор документа
            metadata: Дополнительные метаданные
            
        Returns:
            Объект документа
        """
        db = next(get_db())
        
        try:
            # Ищем существующий документ
            document = db.query(QRDocument).filter(
                QRDocument.document_id == document_id
            ).first()
            
            if document:
                # Обновляем существующий документ
                document.version = version
                document.title = title
                document.description = description
                document.author = author
                document.metadata = metadata or {}
                document.updated_at = datetime.now()
            else:
                # Создаем новый документ
                document = QRDocument(
                    document_id=document_id,
                    document_type=DocumentType(document_type.value),
                    project_id=project_id,
                    version=version,
                    title=title,
                    description=description,
                    author=author,
                    metadata=metadata or {},
                    status=DocumentStatus.DRAFT
                )
                db.add(document)
            
            db.commit()
            db.refresh(document)
            
            return document
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_document(self, document_id: str) -> Optional[QRDocument]:
        """
        Получает документ по ID
        
        Args:
            document_id: ID документа
            
        Returns:
            Объект документа или None
        """
        db = next(get_db())
        
        try:
            document = db.query(QRDocument).filter(
                QRDocument.document_id == document_id
            ).first()
            
            return document
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def get_documents(
        self,
        project_id: Optional[str] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[QRDocument]:
        """
        Получает список документов с фильтрацией
        
        Args:
            project_id: Фильтр по ID проекта
            document_type: Фильтр по типу документа
            status: Фильтр по статусу
            limit: Максимальное количество документов
            offset: Смещение для пагинации
            
        Returns:
            Список документов
        """
        db = next(get_db())
        
        try:
            query = db.query(QRDocument)
            
            # Применяем фильтры
            if project_id:
                query = query.filter(QRDocument.project_id == project_id)
            
            if document_type:
                query = query.filter(QRDocument.document_type == DocumentType(document_type))
            
            if status:
                query = query.filter(QRDocument.status == DocumentStatus(status))
            
            # Сортируем по дате обновления
            query = query.order_by(desc(QRDocument.updated_at))
            
            # Применяем пагинацию
            documents = query.offset(offset).limit(limit).all()
            
            return documents
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatusEnum,
        comment: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Optional[QRDocument]:
        """
        Обновляет статус документа
        
        Args:
            document_id: ID документа
            status: Новый статус
            comment: Комментарий к изменению
            updated_by: Пользователь, обновивший статус
            
        Returns:
            Обновленный документ или None
        """
        db = next(get_db())
        
        try:
            document = db.query(QRDocument).filter(
                QRDocument.document_id == document_id
            ).first()
            
            if not document:
                return None
            
            # Обновляем статус
            document.status = DocumentStatus(status.value)
            document.updated_at = datetime.now()
            
            # Добавляем комментарий в метаданные
            if comment:
                if not document.metadata:
                    document.metadata = {}
                document.metadata["status_comment"] = comment
                document.metadata["status_updated_by"] = updated_by
                document.metadata["status_updated_at"] = datetime.now().isoformat()
            
            db.commit()
            db.refresh(document)
            
            return document
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по документам
        
        Returns:
            Словарь со статистикой
        """
        db = next(get_db())
        
        try:
            # Общее количество документов
            total_documents = db.query(QRDocument).count()
            
            # Количество по статусам
            status_counts = {}
            for status in DocumentStatus:
                count = db.query(QRDocument).filter(
                    QRDocument.status == status
                ).count()
                status_counts[status.value] = count
            
            # Количество по типам
            type_counts = {}
            for doc_type in DocumentType:
                count = db.query(QRDocument).filter(
                    QRDocument.document_type == doc_type
                ).count()
                type_counts[doc_type.value] = count
            
            # Последний обновленный документ
            last_updated = db.query(QRDocument).order_by(
                desc(QRDocument.updated_at)
            ).first()
            
            return {
                "total_documents": total_documents,
                "documents_by_status": status_counts,
                "documents_by_type": type_counts,
                "last_updated": last_updated.updated_at if last_updated else None
            }
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def search_documents(
        self,
        query: str,
        project_id: Optional[str] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[QRDocument]:
        """
        Поиск документов по тексту
        
        Args:
            query: Поисковый запрос
            project_id: Фильтр по ID проекта
            document_type: Фильтр по типу документа
            status: Фильтр по статусу
            limit: Максимальное количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Список найденных документов
        """
        db = next(get_db())
        
        try:
            # Базовый запрос
            search_query = db.query(QRDocument).filter(
                or_(
                    QRDocument.document_id.ilike(f"%{query}%"),
                    QRDocument.title.ilike(f"%{query}%"),
                    QRDocument.description.ilike(f"%{query}%"),
                    QRDocument.author.ilike(f"%{query}%")
                )
            )
            
            # Применяем дополнительные фильтры
            if project_id:
                search_query = search_query.filter(QRDocument.project_id == project_id)
            
            if document_type:
                search_query = search_query.filter(
                    QRDocument.document_type == DocumentType(document_type)
                )
            
            if status:
                search_query = search_query.filter(
                    QRDocument.status == DocumentStatus(status)
                )
            
            # Сортируем по релевантности (по дате обновления)
            search_query = search_query.order_by(desc(QRDocument.updated_at))
            
            # Применяем пагинацию
            documents = search_query.offset(offset).limit(limit).all()
            
            return documents
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def create_document_version(
        self,
        document_id: str,
        version: str,
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None,
        change_description: Optional[str] = None,
        author: Optional[str] = None
    ) -> DocumentVersion:
        """
        Создает новую версию документа
        
        Args:
            document_id: ID документа
            version: Версия
            file_path: Путь к файлу
            file_hash: Хеш файла
            change_description: Описание изменений
            author: Автор версии
            
        Returns:
            Объект версии документа
        """
        db = next(get_db())
        
        try:
            version_obj = DocumentVersion(
                document_id=document_id,
                version=version,
                file_path=file_path,
                file_hash=file_hash,
                change_description=change_description,
                author=author,
                status=DocumentStatus.DRAFT
            )
            
            db.add(version_obj)
            db.commit()
            db.refresh(version_obj)
            
            return version_obj
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """
        Получает все версии документа
        
        Args:
            document_id: ID документа
            
        Returns:
            Список версий документа
        """
        db = next(get_db())
        
        try:
            versions = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.created_at)).all()
            
            return versions
            
        except Exception as e:
            raise e
        finally:
            db.close()
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Удаляет документ
        
        Args:
            document_id: ID документа
            
        Returns:
            True если документ удален
        """
        db = next(get_db())
        
        try:
            document = db.query(QRDocument).filter(
                QRDocument.document_id == document_id
            ).first()
            
            if not document:
                return False
            
            # Удаляем все версии документа
            db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).delete()
            
            # Удаляем сам документ
            db.delete(document)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
