#!/usr/bin/env python3
"""
Векторизатор для модуля "Объекты-аналоги и Архив"
Поддерживает BGE-M3 для текста и CLIP для изображений
"""

import os
import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json
from datetime import datetime

# Векторизация
from sentence_transformers import SentenceTransformer
import torch

# Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models

# CLIP для изображений (опционально)
try:
    import clip
    CLIP_AVAILABLE = True
except ImportError:
    logging.warning("CLIP не установлен, изображения не будут векторизованы")
    CLIP_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentVectorizer:
    """
    Векторизатор документов с поддержкой множественных моделей
    """

    def __init__(self, qdrant_url: str = "http://localhost:9633"):
        self.qdrant_url = qdrant_url
        self.qdrant_client = None
        self._qdrant_available = False
        
        # Модели для эмбеддингов
        self.text_model = None
        self.clip_model = None
        self.clip_preprocess = None
        
        # Конфигурация коллекций
        self.collections = {
            "ae_text_m3": {
                "model": "bge-m3",
                "vector_size": 1024,
                "description": "Текстовые блоки (ПД/РД/спецификации)",
                "distance": Distance.COSINE
            },
            "ae_tables": {
                "model": "bge-m3", 
                "vector_size": 1024,
                "description": "Строки таблиц BoM/BoQ/ведомостей",
                "distance": Distance.COSINE
            },
            "ae_drawings_clip": {
                "model": "clip",
                "vector_size": 768,
                "description": "Изображения листов/фрагментов чертежей",
                "distance": Distance.COSINE
            },
            "ae_ifc": {
                "model": "bge-m3",
                "vector_size": 1024,
                "description": "Объекты IFC моделей",
                "distance": Distance.COSINE
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
            logger.info("Загружаем BGE-M3 модель...")
            self.text_model = SentenceTransformer('BAAI/bge-m3')
            logger.info("BGE-M3 модель загружена успешно")
            
            # Загружаем CLIP для изображений (если доступен)
            if CLIP_AVAILABLE:
                try:
                    logger.info("Загружаем CLIP модель...")
                    self.clip_model, self.clip_preprocess = clip.load("ViT-L/14", device="cpu")
                    logger.info("CLIP модель загружена успешно")
                except Exception as e:
                    logger.warning(f"Не удалось загрузить CLIP: {e}")
                    self.clip_model = None
            else:
                logger.warning("CLIP недоступен, изображения не будут векторизованы")
                self.clip_model = None
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации моделей: {str(e)}")
            raise

    async def ensure_collections_exist(self):
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
                            distance=config["distance"]
                        )
                    )
                    logger.info(f"Создана коллекция: {collection_name}")
                else:
                    logger.info(f"Коллекция уже существует: {collection_name}")
            
            except Exception as e:
                logger.error(f"Ошибка при создании коллекции {collection_name}: {str(e)}")
                raise

    async def vectorize_chunks(self, chunks: List[Dict[str, Any]], collection_name: str) -> Dict[str, Any]:
        """
        Векторизует чанки и сохраняет в Qdrant
        
        Args:
            chunks: Список чанков для векторизации
            collection_name: Имя коллекции в Qdrant
            
        Returns:
            Результат векторизации
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Неизвестная коллекция: {collection_name}")
            
            # Генерируем эмбеддинги
            embeddings = await self._generate_embeddings(chunks, collection_name)
            
            # Создаем точки для Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = f"{chunk.get('chunk_id', f'chunk_{i}')}_{i}"
                
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
                "model": self.collections[collection_name]["model"],
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при векторизации: {str(e)}")
            raise

    async def _generate_embeddings(self, chunks: List[Dict[str, Any]], collection_name: str) -> List[np.ndarray]:
        """Генерирует эмбеддинги для чанков"""
        embeddings = []
        
        if collection_name in ["ae_text_m3", "ae_tables", "ae_ifc"]:
            # Текстовые эмбеддинги с BGE-M3
            texts = []
            for chunk in chunks:
                content = chunk.get('content', '')
                if content:
                    texts.append(content)
                else:
                    texts.append("")  # Пустой текст для пустых чанков
            
            if texts:
                embeddings = self.text_model.encode(texts, convert_to_tensor=False)
            else:
                embeddings = []
                
        elif collection_name == "ae_drawings_clip":
            # CLIP эмбеддинги для изображений
            if self.clip_model is None:
                logger.warning("CLIP модель недоступна, используем текстовые эмбеддинги")
                # Fallback на текстовые эмбеддинги
                texts = []
                for chunk in chunks:
                    content = chunk.get('content', '')
                    if content:
                        texts.append(content)
                    else:
                        texts.append("")
                
                if texts:
                    embeddings = self.text_model.encode(texts, convert_to_tensor=False)
                else:
                    embeddings = []
            else:
                # Реальная CLIP векторизация (требует изображения)
                logger.warning("CLIP векторизация изображений не реализована, используем текстовые эмбеддинги")
                texts = []
                for chunk in chunks:
                    content = chunk.get('content', '')
                    if content:
                        texts.append(content)
                    else:
                        texts.append("")
                
                if texts:
                    embeddings = self.text_model.encode(texts, convert_to_tensor=False)
                else:
                    embeddings = []
        
        return embeddings

    def _create_payload(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Создает payload для точки в Qdrant"""
        payload = {
            "project_id": chunk.get("project_id", ""),
            "object_id": chunk.get("object_id", ""),
            "spp_id": chunk.get("spp_id", "0000000000"),
            "discipline": chunk.get("discipline", ""),
            "doc_no": chunk.get("doc_no", ""),
            "rev": chunk.get("rev", ""),
            "page": chunk.get("page"),
            "section": chunk.get("section"),
            "language": chunk.get("language", "ru"),
            "source_path": chunk.get("source_path", ""),
            "source_hash": chunk.get("source_hash", ""),
            "issued_at": chunk.get("issued_at"),
            "vendor": chunk.get("vendor"),
            "confidentiality": chunk.get("confidentiality", "internal"),
            "tags": chunk.get("tags", []),
            "numeric": chunk.get("numeric", {}),
            "permissions": chunk.get("permissions", []),
            "chunk_id": chunk.get("chunk_id", ""),
            "chunk_type": chunk.get("chunk_type", "text"),
            "content": chunk.get("content", ""),
            "vectorized_at": datetime.utcnow().isoformat()
        }
        
        # Добавляем специфичные поля для разных типов чанков
        if "row_data" in chunk:
            payload["row_data"] = chunk["row_data"]
        if "row_hash" in chunk:
            payload["row_hash"] = chunk["row_hash"]
        
        if "ifc_type" in chunk:
            payload["ifc_type"] = chunk["ifc_type"]
        if "ifc_guid" in chunk:
            payload["ifc_guid"] = chunk["ifc_guid"]
        if "properties" in chunk:
            payload["properties"] = chunk["properties"]
        
        if "preview_path" in chunk:
            payload["preview_path"] = chunk["preview_path"]
        
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


# Пример использования
async def main():
    """Пример использования векторизатора"""
    vectorizer = DocumentVectorizer()
    
    # Создаем коллекции
    await vectorizer.ensure_collections_exist()
    
    # Пример чанков для векторизации
    sample_chunks = [
        {
            "chunk_id": "chunk_1",
            "content": "Центробежный насос для перекачки аммиака",
            "project_id": "EC-Karat-2021",
            "object_id": "NH3-ATR-3500tpd",
            "discipline": "process",
            "doc_no": "AI-ENG-PID-001",
            "rev": "A",
            "chunk_type": "text"
        },
        {
            "chunk_id": "chunk_2", 
            "content": "Теплообменник кожухотрубный TEMA E",
            "project_id": "EC-Karat-2021",
            "object_id": "NH3-ATR-3500tpd",
            "discipline": "process",
            "doc_no": "AI-ENG-SPEC-100",
            "rev": "A",
            "chunk_type": "text"
        }
    ]
    
    # Векторизуем чанки
    result = await vectorizer.vectorize_chunks(sample_chunks, "ae_text_m3")
    print(f"Результат векторизации: {result}")
    
    # Поиск
    search_results = await vectorizer.search_similar("насос аммиак", "ae_text_m3", limit=5)
    print(f"Результаты поиска: {len(search_results)} найдено")
    
    for result in search_results:
        print(f"Score: {result['score']:.3f}, Content: {result['payload']['content'][:50]}...")


if __name__ == "__main__":
    asyncio.run(main())
