"""
Сервис для работы с векторной базой данных Qdrant
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VectorService:
    """Сервис для работы с векторной базой данных Qdrant"""
    
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = None
        self.collections = {}
        
    async def initialize(self):
        """Инициализация Qdrant клиента"""
        try:
            logger.info(f"Подключение к Qdrant: {self.qdrant_url}")
            self.client = QdrantClient(url=self.qdrant_url)
            
            # Проверка подключения
            collections = self.client.get_collections()
            logger.info("Qdrant клиент успешно инициализирован")
            
            # Создание коллекций по умолчанию
            await self._create_default_collections()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Qdrant: {e}")
            raise
    
    async def _create_default_collections(self):
        """Создание коллекций по умолчанию"""
        collection_types = [
            'normative',      # Нормативные документы
            'chat',          # Документы чата
            'input_data',    # Исходные данные проекта
            'project',       # Документы проекта
            'archive',       # Архив и объекты аналоги
        ]
        
        for collection_type in collection_types:
            try:
                collection_name = f"documents_{collection_type}"
                collections = self.client.get_collections()
                
                # Проверяем, существует ли коллекция
                collection_exists = any(
                    col.name == collection_name 
                    for col in collections.collections
                )
                
                if not collection_exists:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=384,  # Размер вектора для sentence-transformers
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Создана коллекция: {collection_name}")
            except Exception as e:
                logger.warning(f"Ошибка создания коллекции {collection_type}: {e}")
    
    async def store_embeddings(
        self, 
        document_id: str, 
        collection_id: str, 
        text: str, 
        embeddings: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Сохранение эмбеддингов в векторную базу данных"""
        try:
            # Определение коллекции
            collection_name = self._get_collection_name(collection_id)
            
            # Подготовка метаданных
            doc_metadata = {
                "document_id": document_id,
                "collection_id": collection_id,
                "text_length": len(text),
                "text": text,
                **(metadata or {})
            }
            
            # Генерация уникального ID для чанка
            chunk_id = f"{document_id}_{uuid.uuid4().hex[:8]}"
            
            # Создание точки для Qdrant
            point = PointStruct(
                id=chunk_id,
                vector=embeddings,
                payload=doc_metadata
            )
            
            # Сохранение в Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"Эмбеддинги сохранены для документа {document_id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения эмбеддингов: {e}")
            raise
    
    async def store_chunk_embeddings(
        self,
        document_id: str,
        collection_id: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Сохранение эмбеддингов чанков"""
        try:
            collection_name = self._get_collection_name(collection_id)
            
            # Подготовка точек для batch добавления
            points = []
            
            for chunk in chunks:
                chunk_id = f"{document_id}_{chunk['chunk_index']}"
                
                chunk_metadata = {
                    "document_id": document_id,
                    "collection_id": collection_id,
                    "chunk_index": chunk['chunk_index'],
                    "text_length": len(chunk['text']),
                    "text": chunk['text'],
                    **(metadata or {})
                }
                
                point = PointStruct(
                    id=chunk_id,
                    vector=chunk['embedding'],
                    payload=chunk_metadata
                )
                points.append(point)
            
            # Batch добавление
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Сохранено {len(chunks)} чанков для документа {document_id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения чанков: {e}")
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        collection_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Поиск похожих документов"""
        try:
            results = []
            
            # Если указана конкретная коллекция
            if collection_id:
                collection_name = self._get_collection_name(collection_id)
                
                # Построение фильтра
                query_filter = None
                if collection_id:
                    query_filter = Filter(
                        must=[
                            FieldCondition(
                                key="collection_id",
                                match=MatchValue(value=collection_id)
                            )
                        ]
                    )
                
                # Поиск в коллекции
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    query_filter=query_filter,
                    with_payload=True
                )
                
                results.extend(self._process_search_results(search_results, threshold))
            
            else:
                # Поиск по всем коллекциям
                collections = self.client.get_collections()
                for collection in collections.collections:
                    try:
                        search_results = self.client.search(
                            collection_name=collection.name,
                            query_vector=query_embedding,
                            limit=limit // len(collections.collections) + 1,
                            with_payload=True
                        )
                        results.extend(self._process_search_results(search_results, threshold))
                    except Exception as e:
                        logger.warning(f"Ошибка поиска в коллекции {collection.name}: {e}")
            
            # Сортировка по релевантности
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Ограничение результатов
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            raise
    
    def _process_search_results(self, search_results: List, threshold: float) -> List[Dict[str, Any]]:
        """Обработка результатов поиска"""
        results = []
        
        for result in search_results:
            # Qdrant возвращает score напрямую
            score = result.score
            
            if score >= threshold:
                payload = result.payload
                results.append({
                    'document_id': payload.get('document_id'),
                    'chunk_id': result.id,
                    'text': payload.get('text', ''),
                    'score': score,
                    'metadata': payload
                })
        
        return results
    
    async def delete_document(self, document_id: str):
        """Удаление документа из векторной базы данных"""
        try:
            collections = self.client.get_collections()
            
            for collection in collections.collections:
                try:
                    # Поиск и удаление всех чанков документа
                    points = self.client.scroll(
                        collection_name=collection.name,
                        scroll_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="document_id",
                                    match=MatchValue(value=document_id)
                                )
                            ]
                        ),
                        limit=10000,  # Большое число для получения всех точек
                        with_payload=False
                    )[0]
                    
                    if points:
                        point_ids = [point.id for point in points]
                        self.client.delete(
                            collection_name=collection.name,
                            points_selector=point_ids
                        )
                        logger.info(f"Удалено {len(point_ids)} чанков документа {document_id} из коллекции {collection.name}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка удаления из коллекции {collection.name}: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {e}")
            raise
    
    async def get_collection_stats(self, collection_id: str) -> Dict[str, Any]:
        """Получение статистики коллекции"""
        try:
            collection_name = self._get_collection_name(collection_id)
            
            # Получение информации о коллекции
            collection_info = self.client.get_collection(collection_name)
            
            # Подсчет уникальных документов
            points = self.client.scroll(
                collection_name=collection_name,
                limit=10000,
                with_payload=True
            )[0]
            
            unique_documents = set()
            for point in points:
                if point.payload and 'document_id' in point.payload:
                    unique_documents.add(point.payload['document_id'])
            
            return {
                'collection_id': collection_id,
                'total_chunks': len(points),
                'unique_documents': len(unique_documents),
                'collection_name': collection_name,
                'vectors_count': collection_info.vectors_count
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики коллекции: {e}")
            return {
                'collection_id': collection_id,
                'total_chunks': 0,
                'unique_documents': 0,
                'error': str(e)
            }
    
    def _get_collection_name(self, collection_id: str) -> str:
        """Получение имени коллекции по ID"""
        # В реальной реализации здесь должен быть запрос к БД для получения типа коллекции
        # Пока используем общую коллекцию
        return "documents_general"
    
    async def create_collection(self, name: str, vector_size: int = 384, metadata: Optional[Dict[str, Any]] = None):
        """Создание новой коллекции"""
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Создана коллекция: {name}")
        except Exception as e:
            logger.error(f"Ошибка создания коллекции {name}: {e}")
            raise
    
    async def delete_collection(self, name: str):
        """Удаление коллекции"""
        try:
            self.client.delete_collection(collection_name=name)
            logger.info(f"Коллекция {name} удалена")
        except Exception as e:
            logger.error(f"Ошибка удаления коллекции {name}: {e}")
            raise
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Получение списка всех коллекций"""
        try:
            collections = self.client.get_collections()
            return [
                {
                    'name': col.name,
                    'vectors_count': col.vectors_count,
                    'status': col.status
                }
                for col in collections.collections
            ]
        except Exception as e:
            logger.error(f"Ошибка получения списка коллекций: {e}")
            return []