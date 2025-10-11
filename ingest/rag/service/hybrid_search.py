#!/usr/bin/env python3
"""
Гибридный поиск для модуля "Объекты-аналоги и Архив"
Объединяет BM25 (Meilisearch) + Dense (Qdrant) + Rerank
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import numpy as np

# HTTP клиенты
import httpx
import aiohttp

# Векторизация
from sentence_transformers import SentenceTransformer

# Реранкинг
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    logging.warning("CrossEncoder не установлен, реранкинг недоступен")
    RERANKER_AVAILABLE = False

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Сервис гибридного поиска с BM25 + Dense + Rerank
    """

    def __init__(self, 
                 meilisearch_url: str = "http://localhost:7700",
                 meilisearch_api_key: str = "masterKey",
                 qdrant_url: str = "http://localhost:9633",
                 rerank_model: str = "BAAI/bge-reranker-v2-m3"):
        
        self.meilisearch_url = meilisearch_url
        self.meilisearch_api_key = meilisearch_api_key
        self.qdrant_url = qdrant_url
        self.rerank_model = rerank_model
        
        # Модели
        self.text_model = None
        self.reranker = None
        
        # Веса для объединения результатов
        self.weights = {
            "bm25": 0.3,
            "dense": 0.4,
            "rerank": 0.3
        }
        
        self._initialize_models()

    def _initialize_models(self):
        """Инициализирует модели для поиска и реранкинга"""
        try:
            # Загружаем BGE-M3 для dense поиска
            logger.info("Загружаем BGE-M3 модель...")
            self.text_model = SentenceTransformer('BAAI/bge-m3')
            logger.info("BGE-M3 модель загружена")
            
            # Загружаем реранкер
            if RERANKER_AVAILABLE:
                try:
                    logger.info(f"Загружаем реранкер {self.rerank_model}...")
                    self.reranker = CrossEncoder(self.rerank_model)
                    logger.info("Реранкер загружен")
                except Exception as e:
                    logger.warning(f"Не удалось загрузить реранкер: {e}")
                    self.reranker = None
            else:
                logger.warning("Реранкер недоступен")
                self.reranker = None
                
        except Exception as e:
            logger.error(f"Ошибка при инициализации моделей: {str(e)}")
            raise

    async def hybrid_search(self, 
                          query: str,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 10,
                          bm25_limit: int = 100,
                          dense_limit: int = 100) -> List[Dict[str, Any]]:
        """
        Выполняет гибридный поиск
        
        Args:
            query: Поисковый запрос
            filters: Фильтры для поиска
            limit: Финальный лимит результатов
            bm25_limit: Лимит для BM25 поиска
            dense_limit: Лимит для dense поиска
            
        Returns:
            Список результатов с объединенными скорами
        """
        try:
            logger.info(f"Выполняем гибридный поиск для запроса: {query}")
            
            # Параллельно выполняем BM25 и dense поиск
            bm25_task = self._bm25_search(query, filters, bm25_limit)
            dense_task = self._dense_search(query, filters, dense_limit)
            
            bm25_results, dense_results = await asyncio.gather(bm25_task, dense_task)
            
            logger.info(f"BM25: {len(bm25_results)} результатов, Dense: {len(dense_results)} результатов")
            
            # Объединяем результаты
            combined_results = self._combine_results(bm25_results, dense_results, query)
            
            # Реранкинг если доступен
            if self.reranker and len(combined_results) > 0:
                combined_results = await self._rerank_results(combined_results, query)
            
            # Возвращаем топ результатов
            final_results = combined_results[:limit]
            
            logger.info(f"Гибридный поиск завершен: {len(final_results)} результатов")
            return final_results
            
        except Exception as e:
            logger.error(f"Ошибка при гибридном поиске: {str(e)}")
            raise

    async def _bm25_search(self, query: str, filters: Optional[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Выполняет BM25 поиск в Meilisearch"""
        try:
            async with httpx.AsyncClient() as client:
                # Подготавливаем запрос
                search_params = {
                    "q": query,
                    "limit": limit,
                    "attributesToRetrieve": ["*"],
                    "attributesToHighlight": ["content", "title"],
                    "showMatchesPosition": True
                }
                
                # Добавляем фильтры
                if filters:
                    filter_conditions = []
                    for key, value in filters.items():
                        if isinstance(value, list):
                            filter_conditions.append(f"{key} IN {value}")
                        else:
                            filter_conditions.append(f"{key} = {value}")
                    
                    if filter_conditions:
                        search_params["filter"] = " AND ".join(filter_conditions)
                
                # Выполняем поиск
                response = await client.post(
                    f"{self.meilisearch_url}/indexes/documents/search",
                    headers={
                        "Authorization": f"Bearer {self.meilisearch_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=search_params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for hit in data.get("hits", []):
                        results.append({
                            "id": hit.get("id"),
                            "score": hit.get("_score", 0.0),
                            "content": hit.get("content", ""),
                            "title": hit.get("title", ""),
                            "metadata": {
                                "project_id": hit.get("project_id"),
                                "object_id": hit.get("object_id"),
                                "discipline": hit.get("discipline"),
                                "doc_no": hit.get("doc_no"),
                                "rev": hit.get("rev"),
                                "page": hit.get("page"),
                                "section": hit.get("section"),
                                "source_path": hit.get("source_path"),
                                "chunk_type": hit.get("chunk_type", "text")
                            },
                            "search_type": "bm25",
                            "highlights": hit.get("_formatted", {})
                        })
                    
                    logger.info(f"BM25 поиск: {len(results)} результатов")
                    return results
                else:
                    logger.error(f"Ошибка BM25 поиска: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка при BM25 поиске: {str(e)}")
            return []

    async def _dense_search(self, query: str, filters: Optional[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Выполняет dense поиск в Qdrant"""
        try:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.text_model.encode([query], convert_to_tensor=False)[0]
            
            # Подготавливаем фильтры для Qdrant
            qdrant_filters = None
            if filters:
                qdrant_filters = self._create_qdrant_filters(filters)
            
            # Выполняем поиск в Qdrant
            async with httpx.AsyncClient() as client:
                search_payload = {
                    "vector": query_embedding.tolist(),
                    "limit": limit,
                    "with_payload": True,
                    "with_vector": False
                }
                
                if qdrant_filters:
                    search_payload["filter"] = qdrant_filters
                
                # Поиск в текстовых коллекциях
                collections = ["ae_text_m3", "ae_tables", "ae_ifc"]
                all_results = []
                
                for collection in collections:
                    try:
                        response = await client.post(
                            f"{self.qdrant_url}/collections/{collection}/points/search",
                            json=search_payload,
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            for result in data.get("result", []):
                                payload = result.get("payload", {})
                                all_results.append({
                                    "id": result.get("id"),
                                    "score": result.get("score", 0.0),
                                    "content": payload.get("content", ""),
                                    "title": f"{payload.get('doc_no', '')} - {payload.get('section', '')}",
                                    "metadata": {
                                        "project_id": payload.get("project_id"),
                                        "object_id": payload.get("object_id"),
                                        "discipline": payload.get("discipline"),
                                        "doc_no": payload.get("doc_no"),
                                        "rev": payload.get("rev"),
                                        "page": payload.get("page"),
                                        "section": payload.get("section"),
                                        "source_path": payload.get("source_path"),
                                        "chunk_type": payload.get("chunk_type", "text"),
                                        "collection": collection
                                    },
                                    "search_type": "dense"
                                })
                                
                    except Exception as e:
                        logger.warning(f"Ошибка поиска в коллекции {collection}: {e}")
                        continue
                
                # Сортируем по скору
                all_results.sort(key=lambda x: x["score"], reverse=True)
                dense_results = all_results[:limit]
                
                logger.info(f"Dense поиск: {len(dense_results)} результатов")
                return dense_results
                
        except Exception as e:
            logger.error(f"Ошибка при dense поиске: {str(e)}")
            return []

    def _create_qdrant_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Создает фильтры для Qdrant"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                conditions.append({
                    "key": key,
                    "match": {"any": value}
                })
            else:
                conditions.append({
                    "key": key,
                    "match": {"value": value}
                })
        
        return {"must": conditions} if conditions else None

    def _combine_results(self, bm25_results: List[Dict[str, Any]], 
                        dense_results: List[Dict[str, Any]], 
                        query: str) -> List[Dict[str, Any]]:
        """Объединяет результаты BM25 и dense поиска"""
        
        # Нормализуем скоры
        bm25_scores = [r["score"] for r in bm25_results]
        dense_scores = [r["score"] for r in dense_results]
        
        bm25_max = max(bm25_scores) if bm25_scores else 1.0
        dense_max = max(dense_scores) if dense_scores else 1.0
        
        # Создаем словарь для объединения по ID
        combined_dict = {}
        
        # Добавляем BM25 результаты
        for result in bm25_results:
            doc_id = result["id"]
            normalized_score = result["score"] / bm25_max if bm25_max > 0 else 0.0
            weighted_score = normalized_score * self.weights["bm25"]
            
            combined_dict[doc_id] = {
                **result,
                "bm25_score": result["score"],
                "dense_score": 0.0,
                "combined_score": weighted_score,
                "search_types": ["bm25"]
            }
        
        # Добавляем dense результаты
        for result in dense_results:
            doc_id = result["id"]
            normalized_score = result["score"] / dense_max if dense_max > 0 else 0.0
            weighted_score = normalized_score * self.weights["dense"]
            
            if doc_id in combined_dict:
                # Объединяем с существующим результатом
                combined_dict[doc_id]["dense_score"] = result["score"]
                combined_dict[doc_id]["combined_score"] += weighted_score
                combined_dict[doc_id]["search_types"].append("dense")
                
                # Обновляем контент если dense результат более релевантен
                if result["score"] > combined_dict[doc_id]["bm25_score"]:
                    combined_dict[doc_id]["content"] = result["content"]
                    combined_dict[doc_id]["metadata"].update(result["metadata"])
            else:
                # Новый результат
                combined_dict[doc_id] = {
                    **result,
                    "bm25_score": 0.0,
                    "dense_score": result["score"],
                    "combined_score": weighted_score,
                    "search_types": ["dense"]
                }
        
        # Конвертируем в список и сортируем
        combined_results = list(combined_dict.values())
        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        logger.info(f"Объединено {len(combined_results)} уникальных результатов")
        return combined_results

    async def _rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Выполняет реранкинг результатов"""
        try:
            if not self.reranker or len(results) == 0:
                return results
            
            # Подготавливаем пары для реранкинга
            pairs = []
            for result in results:
                content = result.get("content", "")
                if content:
                    pairs.append([query, content])
                else:
                    pairs.append([query, result.get("title", "")])
            
            # Выполняем реранкинг
            rerank_scores = self.reranker.predict(pairs)
            
            # Нормализуем скоры реранкинга
            rerank_max = max(rerank_scores) if len(rerank_scores) > 0 else 1.0
            
            # Обновляем результаты
            for i, result in enumerate(results):
                if i < len(rerank_scores):
                    rerank_score = rerank_scores[i] / rerank_max if rerank_max > 0 else 0.0
                    rerank_weighted = rerank_score * self.weights["rerank"]
                    
                    result["rerank_score"] = rerank_scores[i]
                    result["combined_score"] = result.get("combined_score", 0.0) + rerank_weighted
            
            # Сортируем по обновленному скору
            results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            logger.info(f"Реранкинг выполнен для {len(results)} результатов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при реранкинге: {str(e)}")
            return results

    async def search_analogs(self, 
                           equipment_description: str,
                           equipment_type: Optional[str] = None,
                           parameters: Optional[Dict[str, Any]] = None,
                           filters: Optional[Dict[str, Any]] = None,
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск аналогов оборудования
        
        Args:
            equipment_description: Описание оборудования
            equipment_type: Тип оборудования
            parameters: Числовые параметры
            filters: Дополнительные фильтры
            limit: Лимит результатов
            
        Returns:
            Список аналогов оборудования
        """
        try:
            # Расширяем запрос для поиска аналогов
            analog_query = f"{equipment_description}"
            if equipment_type:
                analog_query += f" {equipment_type}"
            
            # Добавляем параметры в запрос
            if parameters:
                param_text = " ".join([f"{k} {v}" for k, v in parameters.items()])
                analog_query += f" {param_text}"
            
            # Выполняем гибридный поиск
            results = await self.hybrid_search(
                query=analog_query,
                filters=filters,
                limit=limit
            )
            
            # Фильтруем результаты по релевантности для аналогов
            analog_results = []
            for result in results:
                # Проверяем релевантность для поиска аналогов
                content = result.get("content", "").lower()
                metadata = result.get("metadata", {})
                
                # Ключевые слова для оборудования
                equipment_keywords = [
                    "насос", "pump", "компрессор", "compressor", 
                    "теплообменник", "heat exchanger", "сосуд", "vessel",
                    "арматура", "valve", "задвижка", "gate valve"
                ]
                
                is_equipment = any(keyword in content for keyword in equipment_keywords)
                
                if is_equipment or result["combined_score"] > 0.3:
                    analog_results.append({
                        **result,
                        "equipment_type": equipment_type,
                        "parameters": parameters,
                        "relevance_score": result["combined_score"]
                    })
            
            logger.info(f"Найдено {len(analog_results)} аналогов оборудования")
            return analog_results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске аналогов: {str(e)}")
            raise


# Пример использования
async def main():
    """Пример использования гибридного поиска"""
    search_service = HybridSearchService()
    
    # Гибридный поиск
    results = await search_service.hybrid_search(
        query="центробежный насос аммиак",
        filters={"discipline": "process"},
        limit=5
    )
    
    print(f"Гибридный поиск: {len(results)} результатов")
    for i, result in enumerate(results):
        print(f"{i+1}. Score: {result['combined_score']:.3f}")
        print(f"   Content: {result['content'][:100]}...")
        print(f"   Types: {result.get('search_types', [])}")
        print()
    
    # Поиск аналогов
    analog_results = await search_service.search_analogs(
        equipment_description="центробежный насос",
        equipment_type="pump",
        parameters={"flow_rate": 1000, "head": 50},
        limit=3
    )
    
    print(f"Поиск аналогов: {len(analog_results)} результатов")
    for i, result in enumerate(analog_results):
        print(f"{i+1}. Relevance: {result['relevance_score']:.3f}")
        print(f"   Equipment: {result['content'][:100]}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
