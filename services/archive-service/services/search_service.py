"""
Сервис для поиска и работы с аналогами
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

from schemas.archive import (
    SearchRequest, SearchResult, AnalogSearchRequest, AnalogResult
)
from services.vectorization_service import VectorizationService

logger = logging.getLogger(__name__)


class SearchService:
    """Сервис для поиска документов и аналогов"""
    
    def __init__(self, vectorization_service: VectorizationService = None):
        self.vectorization_service = vectorization_service or VectorizationService()
        
        # Конфигурация поиска
        self.search_config = {
            "text_collections": ["ae_text_m3", "ae_tables", "ae_ifc"],
            "drawing_collections": ["ae_drawings_clip"],
            "max_results_per_collection": 20,
            "rerank_limit": 50,
            "final_limit": 10
        }
    
    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """
        Выполняет поиск документов
        
        Args:
            request: Параметры поиска
            
        Returns:
            Список результатов поиска
        """
        try:
            # Определяем тип запроса
            query_type = await self._classify_query(request.query)
            
            # Выполняем поиск по соответствующим коллекциям
            all_results = []
            
            if query_type in ["text", "mixed"]:
                text_results = await self._search_text_collections(request)
                all_results.extend(text_results)
            
            if query_type in ["drawing", "mixed"]:
                drawing_results = await self._search_drawing_collections(request)
                all_results.extend(drawing_results)
            
            # Сортируем по релевантности
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            # Ограничиваем количество результатов
            final_results = all_results[:request.limit]
            
            # Добавляем presigned URLs
            for result in final_results:
                result.source_url = await self._get_presigned_url(result.metadata.source_path)
            
            logger.info(f"Найдено {len(final_results)} результатов для запроса: {request.query}")
            return final_results
        
        except Exception as e:
            logger.error(f"Ошибка при поиске: {str(e)}")
            raise
    
    async def search_analogs(self, request: AnalogSearchRequest) -> List[AnalogResult]:
        """
        Поиск аналогов оборудования
        
        Args:
            request: Параметры поиска аналогов
            
        Returns:
            Список аналогов
        """
        try:
            # Формируем поисковый запрос для аналогов
            query = self._build_analog_query(request)
            
            # Создаем фильтры
            filters = self._build_analog_filters(request)
            
            # Ищем в коллекциях с оборудованием
            analog_results = []
            
            for collection_name in ["ae_text_m3", "ae_tables", "ae_ifc"]:
                results = await self.vectorization_service.search_similar(
                    query=query,
                    collection_name=collection_name,
                    filters=filters,
                    limit=request.limit * 2  # Берем больше для фильтрации
                )
                
                # Преобразуем в AnalogResult
                for result in results:
                    analog = await self._create_analog_result(result, request)
                    if analog:
                        analog_results.append(analog)
            
            # Сортируем по схожести
            analog_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Ограничиваем количество
            final_results = analog_results[:request.limit]
            
            logger.info(f"Найдено {len(final_results)} аналогов для {request.equipment_type}")
            return final_results
        
        except Exception as e:
            logger.error(f"Ошибка при поиске аналогов: {str(e)}")
            raise
    
    async def _classify_query(self, query: str) -> str:
        """Классифицирует тип поискового запроса"""
        query_lower = query.lower()
        
        # Ключевые слова для чертежей
        drawing_keywords = ["чертеж", "drawing", "схема", "diagram", "pid", "pfd", "план", "plan"]
        
        # Ключевые слова для таблиц
        table_keywords = ["таблица", "table", "bom", "boq", "ведомость", "specification", "спецификация"]
        
        # Ключевые слова для IFC
        ifc_keywords = ["ifc", "модель", "model", "объект", "object", "элемент", "element"]
        
        drawing_score = sum(1 for keyword in drawing_keywords if keyword in query_lower)
        table_score = sum(1 for keyword in table_keywords if keyword in query_lower)
        ifc_score = sum(1 for keyword in ifc_keywords if keyword in query_lower)
        
        if drawing_score > 0 and table_score == 0 and ifc_score == 0:
            return "drawing"
        elif table_score > 0 and drawing_score == 0 and ifc_score == 0:
            return "table"
        elif ifc_score > 0 and drawing_score == 0 and table_score == 0:
            return "ifc"
        elif drawing_score > 0 or table_score > 0 or ifc_score > 0:
            return "mixed"
        else:
            return "text"
    
    async def _search_text_collections(self, request: SearchRequest) -> List[SearchResult]:
        """Поиск в текстовых коллекциях"""
        results = []
        
        for collection_name in self.search_config["text_collections"]:
            # Создаем фильтры
            filters = self._build_search_filters(request)
            
            # Выполняем поиск
            search_results = await self.vectorization_service.search_similar(
                query=request.query,
                collection_name=collection_name,
                filters=filters,
                limit=self.search_config["max_results_per_collection"]
            )
            
            # Преобразуем в SearchResult
            for result in search_results:
                search_result = await self._create_search_result(result)
                if search_result:
                    results.append(search_result)
        
        return results
    
    async def _search_drawing_collections(self, request: SearchRequest) -> List[SearchResult]:
        """Поиск в коллекциях чертежей"""
        results = []
        
        for collection_name in self.search_config["drawing_collections"]:
            # Создаем фильтры
            filters = self._build_search_filters(request)
            
            # Выполняем поиск
            search_results = await self.vectorization_service.search_similar(
                query=request.query,
                collection_name=collection_name,
                filters=filters,
                limit=self.search_config["max_results_per_collection"]
            )
            
            # Преобразуем в SearchResult
            for result in search_results:
                search_result = await self._create_search_result(result)
                if search_result:
                    results.append(search_result)
        
        return results
    
    def _build_search_filters(self, request: SearchRequest) -> Dict[str, Any]:
        """Создает фильтры для поиска"""
        filters = {}
        
        if request.project_id:
            filters["project_id"] = request.project_id
        
        if request.object_id:
            filters["object_id"] = request.object_id
        
        if request.discipline:
            filters["discipline"] = request.discipline.value
        
        if request.doc_type:
            filters["doc_type"] = request.doc_type.value
        
        if request.language:
            filters["language"] = request.language
        
        # Добавляем пользовательские фильтры
        filters.update(request.filters)
        
        return filters
    
    def _build_analog_filters(self, request: AnalogSearchRequest) -> Dict[str, Any]:
        """Создает фильтры для поиска аналогов"""
        filters = {}
        
        if request.discipline:
            filters["discipline"] = request.discipline.value
        
        if request.vendor:
            filters["vendor"] = request.vendor
        
        # Фильтры по числовым параметрам
        for param_name, param_value in request.parameters.items():
            # Для поиска аналогов используем диапазон значений
            if isinstance(param_value, (int, float)):
                # ±20% от значения
                tolerance = param_value * 0.2
                filters[f"numeric.{param_name}"] = {
                    "gte": param_value - tolerance,
                    "lte": param_value + tolerance
                }
        
        return filters
    
    def _build_analog_query(self, request: AnalogSearchRequest) -> str:
        """Формирует поисковый запрос для аналогов"""
        query_parts = [request.equipment_type]
        
        # Добавляем параметры в запрос
        for param_name, param_value in request.parameters.items():
            query_parts.append(f"{param_name} {param_value}")
        
        return " ".join(query_parts)
    
    async def _create_search_result(self, result: Dict[str, Any]) -> Optional[SearchResult]:
        """Создает SearchResult из результата поиска"""
        try:
            payload = result["payload"]
            
            # Создаем ChunkPayload
            chunk_payload = ChunkPayload(
                project_id=payload["project_id"],
                object_id=payload["object_id"],
                spp_id=payload.get("spp_id", "0000000000"),
                discipline=Discipline(payload["discipline"]),
                doc_no=payload["doc_no"],
                rev=payload["rev"],
                page=payload.get("page"),
                section=payload.get("section"),
                language=payload["language"],
                source_path=payload["source_path"],
                source_hash=payload["source_hash"],
                issued_at=payload.get("issued_at"),
                vendor=payload.get("vendor"),
                confidentiality=payload["confidentiality"],
                tags=payload.get("tags", []),
                numeric=payload.get("numeric", {}),
                permissions=payload.get("permissions", []),
                chunk_id=payload["chunk_id"]
            )
            
            return SearchResult(
                chunk_id=result["id"],
                content=payload["content"],
                score=result["score"],
                metadata=chunk_payload,
                source_url=None,  # Будет установлено позже
                context_bbox=None
            )
        
        except Exception as e:
            logger.warning(f"Ошибка при создании SearchResult: {str(e)}")
            return None
    
    async def _create_analog_result(self, result: Dict[str, Any], request: AnalogSearchRequest) -> Optional[AnalogResult]:
        """Создает AnalogResult из результата поиска"""
        try:
            payload = result["payload"]
            
            # Извлекаем параметры оборудования
            equipment_params = payload.get("numeric", {})
            
            # Вычисляем схожесть параметров
            similarity_score = self._calculate_parameter_similarity(
                request.parameters, equipment_params
            )
            
            # Комбинируем с векторной схожестью
            final_score = (result["score"] + similarity_score) / 2
            
            return AnalogResult(
                equipment_id=payload["chunk_id"],
                equipment_type=request.equipment_type,
                parameters=equipment_params,
                similarity_score=final_score,
                source_documents=[payload["doc_no"]],
                vendor=payload.get("vendor"),
                project_context=f"{payload['project_id']} - {payload['object_id']}"
            )
        
        except Exception as e:
            logger.warning(f"Ошибка при создании AnalogResult: {str(e)}")
            return None
    
    def _calculate_parameter_similarity(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> float:
        """Вычисляет схожесть параметров оборудования"""
        if not params1 or not params2:
            return 0.0
        
        similarities = []
        
        for param_name, param_value1 in params1.items():
            if param_name in params2:
                param_value2 = params2[param_name]
                
                if isinstance(param_value1, (int, float)) and isinstance(param_value2, (int, float)):
                    # Вычисляем относительную разность
                    if param_value1 != 0:
                        relative_diff = abs(param_value1 - param_value2) / abs(param_value1)
                        similarity = max(0, 1 - relative_diff)
                        similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    async def _get_presigned_url(self, source_path: str) -> Optional[str]:
        """Получает presigned URL для файла"""
        try:
            # Здесь должна быть логика получения presigned URL из MinIO
            # Пока возвращаем заглушку
            return f"https://minio.example.com/{source_path}"
        
        except Exception as e:
            logger.warning(f"Ошибка при получении presigned URL для {source_path}: {str(e)}")
            return None
