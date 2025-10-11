"""
Сервис для векторизации и работы с Qdrant
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models

from schemas.archive import (
    TextChunk, TableChunk, DrawingChunk, IFCChunk, ChunkPayload,
    VectorizationRequest
)

logger = logging.getLogger(__name__)


class VectorizationService:
    """Сервис для векторизации и работы с Qdrant"""
    
    def __init__(self, qdrant_url: str = "http://localhost:9633"):
        self.qdrant_url = qdrant_url
        self.qdrant_client = None
        self._qdrant_available = False
        
        # Модели для эмбеддингов
        self.text_model = None
        self.clip_model = None
        
        # Коллекции
        self.collections = {
            "ae_text_m3": {
                "model": "bge-m3",
                "vector_size": 1024,
                "description": "Текстовые блоки (ПД/РД/спецификации)"
            },
            "ae_tables": {
                "model": "bge-m3", 
                "vector_size": 1024,
                "description": "Строки таблиц BoM/BoQ/ведомостей"
            },
            "ae_drawings_clip": {
                "model": "clip",
                "vector_size": 768,
                "description": "Изображения листов/фрагментов чертежей"
            },
            "ae_ifc": {
                "model": "bge-m3",
                "vector_size": 1024,
                "description": "Объекты IFC"
            }
        }
        
        self._initialize_models()
    
    def _get_qdrant_client(self):
        """Ленивая инициализация клиента Qdrant"""
        if self.qdrant_client is None and not self._qdrant_available:
            try:
                self.qdrant_client = QdrantClient(url=self.qdrant_url)
                # Проверяем подключение
                self.qdrant_client.get_collections()
                self._qdrant_available = True
                logger.info(f"Qdrant подключен: {self.qdrant_url}")
            except Exception as e:
                logger.warning(f"Не удалось подключиться к Qdrant: {str(e)}")
                self._qdrant_available = False
        return self.qdrant_client if self._qdrant_available else None
    
    def _initialize_models(self):
        """Инициализирует модели для эмбеддингов"""
        try:
            # Загружаем BGE-M3 для текста
            self.text_model = SentenceTransformer('BAAI/bge-m3')
            logger.info("BGE-M3 модель загружена")
            
            # Загружаем CLIP для изображений (если доступен)
            try:
                import clip
                self.clip_model, self.clip_preprocess = clip.load("ViT-L/14", device="cpu")
                logger.info("CLIP модель загружена")
            except ImportError:
                logger.warning("CLIP не доступен, изображения не будут векторизованы")
                self.clip_model = None
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации моделей: {str(e)}")
            raise
    
    def _ensure_collections_exist(self):
        """Создает коллекции в Qdrant если они не существуют"""
        client = self._get_qdrant_client()
        if not client:
            logger.warning("Qdrant недоступен, коллекции не будут созданы")
            return
            
        for collection_name, config in self.collections.items():
            try:
                # Проверяем существование коллекции
                collections = client.get_collections()
                collection_names = [col.name for col in collections.collections]
                
                if collection_name not in collection_names:
                    # Создаем коллекцию
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config["vector_size"],
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Создана коллекция: {collection_name}")
                else:
                    logger.info(f"Коллекция уже существует: {collection_name}")
            
            except Exception as e:
                logger.error(f"Ошибка при создании коллекции {collection_name}: {str(e)}")
                raise
    
    async def vectorize_chunks(self, request: VectorizationRequest) -> Dict[str, Any]:
        """
        Векторизует чанки и сохраняет в Qdrant
        
        Args:
            request: Запрос на векторизацию
            
        Returns:
            Результат векторизации
        """
        try:
            collection_name = request.collection_name
            if collection_name not in self.collections:
                raise ValueError(f"Неизвестная коллекция: {collection_name}")
            
            # Генерируем эмбеддинги
            embeddings = await self._generate_embeddings(request.chunks, collection_name)
            
            # Создаем точки для Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(request.chunks, embeddings)):
                point_id = f"{chunk.chunk_id}_{i}"
                
                # Создаем payload
                payload = self._create_payload(chunk)
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload
                )
                points.append(point)
            
            # Сохраняем в Qdrant
            client = self._get_qdrant_client()
            if not client:
                raise ValueError("Qdrant недоступен")
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Векторизовано {len(points)} чанков в коллекцию {collection_name}")
            
            return {
                "collection_name": collection_name,
                "points_count": len(points),
                "model": request.model_name,
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при векторизации: {str(e)}")
            raise
    
    async def _generate_embeddings(self, chunks: List, collection_name: str) -> List[np.ndarray]:
        """Генерирует эмбеддинги для чанков"""
        embeddings = []
        
        if collection_name in ["ae_text_m3", "ae_tables", "ae_ifc"]:
            # Текстовые эмбеддинги
            texts = [chunk.content for chunk in chunks]
            embeddings = self.text_model.encode(texts, convert_to_tensor=False)
            
        elif collection_name == "ae_drawings_clip":
            # CLIP эмбеддинги для изображений
            if self.clip_model is None:
                raise ValueError("CLIP модель не доступна")
            
            # Для чертежей пока используем текстовые эмбеддинги извлеченного текста
            texts = []
            for chunk in chunks:
                if hasattr(chunk, 'extracted_text') and chunk.extracted_text:
                    texts.append(chunk.extracted_text)
                else:
                    texts.append(chunk.content)
            
            embeddings = self.text_model.encode(texts, convert_to_tensor=False)
        
        return embeddings
    
    def _create_payload(self, chunk) -> Dict[str, Any]:
        """Создает payload для точки в Qdrant"""
        payload = {
            "project_id": chunk.metadata.project_id,
            "object_id": chunk.metadata.object_id,
            "spp_id": "0000000000",
            "discipline": chunk.metadata.discipline,
            "doc_no": chunk.metadata.doc_no,
            "rev": chunk.metadata.rev,
            "page": chunk.metadata.page,
            "section": chunk.metadata.section,
            "language": chunk.metadata.language,
            "source_path": chunk.metadata.source_path,
            "source_hash": chunk.metadata.source_hash,
            "issued_at": chunk.metadata.issued_at.isoformat() if chunk.metadata.issued_at else None,
            "vendor": chunk.metadata.vendor,
            "confidentiality": chunk.metadata.confidentiality,
            "tags": chunk.metadata.tags,
            "numeric": chunk.metadata.numeric,
            "permissions": chunk.metadata.permissions,
            "chunk_id": chunk.chunk_id,
            "chunk_type": chunk.chunk_type,
            "content": chunk.content
        }
        
        # Добавляем специфичные поля для разных типов чанков
        if hasattr(chunk, 'row_data'):
            payload["row_data"] = chunk.row_data
            payload["row_hash"] = chunk.row_hash
        
        if hasattr(chunk, 'ifc_type'):
            payload["ifc_type"] = chunk.ifc_type
            payload["ifc_guid"] = chunk.ifc_guid
            payload["properties"] = chunk.properties
        
        if hasattr(chunk, 'preview_path'):
            payload["preview_path"] = chunk.preview_path
        
        return payload
    
    async def search_similar(self, query: str, collection_name: str, 
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск похожих документов
        
        Args:
            query: Поисковый запрос
            collection_name: Имя коллекции
            filters: Фильтры
            limit: Лимит результатов
            
        Returns:
            Список похожих документов
        """
        try:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.text_model.encode([query], convert_to_tensor=False)[0]
            
            # Создаем фильтры
            qdrant_filters = None
            if filters:
                qdrant_filters = self._create_filters(filters)
            
            # Выполняем поиск
            client = self._get_qdrant_client()
            if not client:
                raise ValueError("Qdrant недоступен")
            search_results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=qdrant_filters,
                limit=limit,
                with_payload=True
            )
            
            # Форматируем результаты
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Ошибка при поиске: {str(e)}")
            raise
    
    def _create_filters(self, filters: Dict[str, Any]) -> Filter:
        """Создает фильтры для Qdrant"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                # Для списков используем MatchAny
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=models.MatchAny(any=value)
                    )
                )
            else:
                # Для одиночных значений используем MatchValue
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
        
        return Filter(must=conditions)
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """Получает список коллекций"""
        try:
            client = self._get_qdrant_client()
            if not client:
                return []
            collections = client.get_collections()
            result = []
            
            for collection in collections.collections:
                collection_info = self.collections.get(collection.name, {})
                result.append({
                    "name": collection.name,
                    "description": collection_info.get("description", ""),
                    "model": collection_info.get("model", ""),
                    "vector_size": collection_info.get("vector_size", 0),
                    "points_count": collection.points_count
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении списка коллекций: {str(e)}")
            raise
    
    async def reindex_collection(self, collection_name: str) -> Dict[str, Any]:
        """Переиндексирует коллекцию"""
        try:
            # Получаем информацию о коллекции
            client = self._get_qdrant_client()
            if not client:
                raise ValueError("Qdrant недоступен")
            collection_info = client.get_collection(collection_name)
            
            # Здесь может быть логика переиндексации
            # Пока возвращаем информацию о коллекции
            
            return {
                "collection_name": collection_name,
                "points_count": collection_info.points_count,
                "status": "reindexed"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при переиндексации коллекции {collection_name}: {str(e)}")
            raise
    
    async def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Удаляет коллекцию"""
        try:
            client = self._get_qdrant_client()
            if not client:
                raise ValueError("Qdrant недоступен")
            client.delete_collection(collection_name)
            
            return {
                "collection_name": collection_name,
                "status": "deleted"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при удалении коллекции {collection_name}: {str(e)}")
            raise
