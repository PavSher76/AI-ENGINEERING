"""
Улучшенная RAG-система для консультаций по НТД
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, Range, 
    SearchRequest, VectorParams, Distance
)

from models.schemas import (
    QueryIntent, SearchResult, RAGResponse, DocumentChunk,
    QueryRewrite, IntentClassification
)

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Улучшенная RAG-система с гибридным поиском и re-ranking"""
    
    def __init__(self, qdrant_client: QdrantClient):
        self.qdrant = qdrant_client
        self.collection_name = "normative_documents"
        
        # Модели для эмбеддингов и re-ranking
        self.embedding_model = SentenceTransformer('intfloat/multilingual-e5-large')
        self.rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Настройки поиска
        self.hybrid_weights = {"vector": 0.6, "bm25": 0.4}
        self.rerank_top_k = 50
        self.final_top_k = 10
        self.similarity_threshold = 0.7
        
        # Кэш для переформулировок запросов
        self.query_cache = {}
        
        # Паттерны для извлечения ссылок на документы
        self.document_patterns = [
            r'ГОСТ\s+(\d+(?:\.\d+)*)-(\d{4})',
            r'СП\s+(\d+(?:\.\d+)*)\.(\d{4})',
            r'ФНП-(\d{3})-(\d{4})',
            r'ПУЭ\s+(\d+(?:\.\d+)*)',
            r'СНиП\s+(\d+(?:\.\d+)*)-(\d{4})',
            r'п\.\s*(\d+(?:\.\d+)*)',
            r'раздел\s+(\d+(?:\.\d+)*)',
            r'пункт\s+(\d+(?:\.\d+)*)'
        ]
        
        logger.info("Улучшенная RAG-система инициализирована")
    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> RAGResponse:
        """Основной метод обработки запроса"""
        start_time = datetime.now()
        
        try:
            # 1. Переформулировка запроса
            query_rewrites = await self._rewrite_query(query)
            logger.info(f"Сгенерировано {len(query_rewrites)} переформулировок")
            
            # 2. Классификация намерения
            intent = await self._classify_intent(query, query_rewrites)
            logger.info(f"Определено намерение: {intent.intent_type}")
            
            # 3. Извлечение ссылок на документы
            document_refs = self._extract_document_references(query)
            if document_refs:
                logger.info(f"Найдены ссылки на документы: {document_refs}")
            
            # 4. Гибридный поиск
            search_results = await self._hybrid_search(
                query_rewrites, intent, document_refs, user_context
            )
            logger.info(f"Найдено {len(search_results)} результатов поиска")
            
            # 5. Re-ranking
            reranked_results = await self._rerank_results(
                query, search_results, intent
            )
            logger.info(f"После re-ranking: {len(reranked_results)} результатов")
            
            # 6. Генерация ответа
            response = await self._generate_response(
                query, reranked_results, intent, user_context
            )
            
            # 7. Добавление метаданных
            processing_time = (datetime.now() - start_time).total_seconds()
            response.processing_time_ms = processing_time * 1000
            response.query_rewrites = query_rewrites
            response.intent_classification = intent
            response.document_references = document_refs
            
            logger.info(f"Запрос обработан за {processing_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {str(e)}")
            return RAGResponse(
                query=query,
                answer="Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.",
                sources=[],
                confidence=0.0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                error=str(e)
            )
    
    async def _rewrite_query(self, query: str) -> List[QueryRewrite]:
        """Переформулировка запроса с синонимами и расширениями"""
        try:
            # Проверяем кэш
            cache_key = f"rewrite:{hash(query)}"
            if cache_key in self.query_cache:
                return self.query_cache[cache_key]
            
            rewrites = []
            
            # 1. Оригинальный запрос
            rewrites.append(QueryRewrite(
                text=query,
                type="original",
                confidence=1.0
            ))
            
            # 2. Расширение синонимами
            synonym_expansions = self._expand_with_synonyms(query)
            rewrites.extend(synonym_expansions)
            
            # 3. Переформулировка для разных типов поиска
            reformulations = self._reformulate_for_search_types(query)
            rewrites.extend(reformulations)
            
            # 4. Нормализация терминов
            normalized = self._normalize_terms(query)
            if normalized != query:
                rewrites.append(QueryRewrite(
                    text=normalized,
                    type="normalized",
                    confidence=0.9
                ))
            
            # Кэшируем результат
            self.query_cache[cache_key] = rewrites
            
            return rewrites
            
        except Exception as e:
            logger.error(f"Ошибка переформулировки запроса: {str(e)}")
            return [QueryRewrite(text=query, type="original", confidence=1.0)]
    
    def _expand_with_synonyms(self, query: str) -> List[QueryRewrite]:
        """Расширение запроса синонимами"""
        synonyms = {
            "область применения": ["сфера действия", "распространяется на", "применяется к"],
            "требования": ["нормы", "правила", "предписания"],
            "определение": ["понятие", "термин", "дефиниция"],
            "проектирование": ["проектировка", "разработка проекта"],
            "монтаж": ["установка", "сборка"],
            "эксплуатация": ["использование", "применение"],
            "обслуживание": ["техобслуживание", "сервис"],
            "безопасность": ["защита", "охрана"],
            "пожарная безопасность": ["ПБ", "противопожарная защита"],
            "электробезопасность": ["электротехническая безопасность"],
            "автоматизация": ["автоматизированные системы", "АСУ"],
            "контроль": ["мониторинг", "надзор"],
            "измерение": ["замер", "определение"],
            "испытание": ["тестирование", "проверка"],
            "сертификация": ["сертификация", "аттестация"]
        }
        
        rewrites = []
        for term, synonyms_list in synonyms.items():
            if term.lower() in query.lower():
                for synonym in synonyms_list:
                    expanded_query = query.replace(term, f"{term} {synonym}")
                    rewrites.append(QueryRewrite(
                        text=expanded_query,
                        type="synonym_expansion",
                        confidence=0.8
                    ))
        
        return rewrites[:3]  # Ограничиваем количество
    
    def _reformulate_for_search_types(self, query: str) -> List[QueryRewrite]:
        """Переформулировка для разных типов поиска"""
        rewrites = []
        
        # Для поиска определений
        if any(word in query.lower() for word in ["что такое", "определение", "означает"]):
            rewrites.append(QueryRewrite(
                text=f"определение {query}",
                type="definition_search",
                confidence=0.9
            ))
        
        # Для поиска требований
        if any(word in query.lower() for word in ["требования", "нормы", "правила"]):
            rewrites.append(QueryRewrite(
                text=f"требования {query}",
                type="requirement_search",
                confidence=0.9
            ))
        
        # Для поиска области применения
        if any(word in query.lower() for word in ["применяется", "распространяется", "область"]):
            rewrites.append(QueryRewrite(
                text=f"область применения {query}",
                type="scope_search",
                confidence=0.9
            ))
        
        return rewrites
    
    def _normalize_terms(self, query: str) -> str:
        """Нормализация терминов в запросе"""
        # Нормализация единиц измерения
        query = re.sub(r'(\d+)\s*мм', r'\1 мм', query)
        query = re.sub(r'(\d+)\s*м', r'\1 м', query)
        query = re.sub(r'(\d+)\s*кВ', r'\1 кВ', query)
        query = re.sub(r'(\d+)\s*А', r'\1 А', query)
        
        # Нормализация ссылок на документы
        query = re.sub(r'ГОСТ\s+(\d+(?:\.\d+)*)-(\d{4})', r'ГОСТ \1-\2', query)
        query = re.sub(r'СП\s+(\d+(?:\.\d+)*)\.(\d{4})', r'СП \1.\2', query)
        
        return query
    
    async def _classify_intent(self, query: str, rewrites: List[QueryRewrite]) -> IntentClassification:
        """Классификация намерения пользователя"""
        try:
            # Простая классификация на основе ключевых слов
            query_lower = query.lower()
            
            # Определения
            if any(word in query_lower for word in ["что такое", "определение", "означает", "термин"]):
                return IntentClassification(
                    intent_type="definition",
                    confidence=0.9,
                    parameters={"search_type": "definition"}
                )
            
            # Область применения
            if any(word in query_lower for word in ["область применения", "сфера действия", "распространяется"]):
                return IntentClassification(
                    intent_type="scope",
                    confidence=0.9,
                    parameters={"search_type": "scope"}
                )
            
            # Требования
            if any(word in query_lower for word in ["требования", "нормы", "правила", "предписания"]):
                return IntentClassification(
                    intent_type="requirement",
                    confidence=0.9,
                    parameters={"search_type": "requirement"}
                )
            
            # Ссылки на документы
            if any(re.search(pattern, query) for pattern in self.document_patterns):
                return IntentClassification(
                    intent_type="reference",
                    confidence=0.8,
                    parameters={"search_type": "reference"}
                )
            
            # Сравнение
            if any(word in query_lower for word in ["разница", "отличие", "сравнение", "изменения"]):
                return IntentClassification(
                    intent_type="comparison",
                    confidence=0.8,
                    parameters={"search_type": "comparison"}
                )
            
            # Актуальность
            if any(word in query_lower for word in ["актуален", "действующий", "последняя редакция"]):
                return IntentClassification(
                    intent_type="relevance",
                    confidence=0.8,
                    parameters={"search_type": "relevance"}
                )
            
            # По умолчанию - общий поиск
            return IntentClassification(
                intent_type="general",
                confidence=0.6,
                parameters={"search_type": "general"}
            )
            
        except Exception as e:
            logger.error(f"Ошибка классификации намерения: {str(e)}")
            return IntentClassification(
                intent_type="general",
                confidence=0.5,
                parameters={"search_type": "general"}
            )
    
    def _extract_document_references(self, query: str) -> List[Dict[str, str]]:
        """Извлечение ссылок на документы из запроса"""
        references = []
        
        for pattern in self.document_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if "ГОСТ" in pattern:
                    references.append({
                        "type": "ГОСТ",
                        "number": match.group(1),
                        "year": match.group(2),
                        "full_reference": match.group(0)
                    })
                elif "СП" in pattern:
                    references.append({
                        "type": "СП",
                        "number": match.group(1),
                        "year": match.group(2),
                        "full_reference": match.group(0)
                    })
                elif "п." in pattern or "пункт" in pattern:
                    references.append({
                        "type": "clause",
                        "number": match.group(1),
                        "full_reference": match.group(0)
                    })
        
        return references
    
    async def _hybrid_search(
        self, 
        query_rewrites: List[QueryRewrite],
        intent: IntentClassification,
        document_refs: List[Dict[str, str]],
        user_context: Optional[Dict]
    ) -> List[SearchResult]:
        """Гибридный поиск (векторный + BM25)"""
        try:
            all_results = []
            
            # Если есть прямые ссылки на документы, ищем их в первую очередь
            if document_refs:
                direct_results = await self._search_by_references(document_refs)
                all_results.extend(direct_results)
            
            # Выполняем поиск по переформулировкам
            for rewrite in query_rewrites[:3]:  # Ограничиваем количество
                # Векторный поиск
                vector_results = await self._vector_search(rewrite.text, intent)
                
                # BM25 поиск
                bm25_results = await self._bm25_search(rewrite.text, intent)
                
                # Объединяем результаты с весами
                combined_results = self._combine_search_results(
                    vector_results, bm25_results, rewrite.confidence
                )
                
                all_results.extend(combined_results)
            
            # Удаляем дубликаты и сортируем по релевантности
            unique_results = self._deduplicate_results(all_results)
            
            return unique_results[:self.rerank_top_k]
            
        except Exception as e:
            logger.error(f"Ошибка гибридного поиска: {str(e)}")
            return []
    
    async def _vector_search(self, query: str, intent: IntentClassification) -> List[SearchResult]:
        """Векторный поиск с использованием эмбеддингов"""
        try:
            # Генерируем эмбеддинг для запроса
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Подготавливаем фильтры
            filters = self._build_filters(intent)
            
            # Выполняем поиск
            search_requests = [
                SearchRequest(
                    vector=query_embedding.tolist(),
                    limit=30,
                    with_payload=True,
                    filter=filters
                )
            ]
            
            results = self.qdrant.search_batch(
                collection_name=self.collection_name,
                requests=search_requests
            )[0]
            
            # Преобразуем результаты
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    doc_id=result.payload["doc_id"],
                    doc_title=result.payload["doc_title"],
                    doc_family=result.payload["doc_family"],
                    section=result.payload.get("section", ""),
                    clause=result.payload.get("clause", ""),
                    content=result.payload.get("content", ""),
                    score=result.score,
                    search_type="vector",
                    metadata=result.payload
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Ошибка векторного поиска: {str(e)}")
            return []
    
    async def _bm25_search(self, query: str, intent: IntentClassification) -> List[SearchResult]:
        """BM25 поиск (здесь используем простую текстовую фильтрацию)"""
        try:
            # Для демонстрации используем простой текстовый поиск
            # В реальной системе здесь должен быть полноценный BM25
            
            filters = self._build_filters(intent)
            
            # Простой поиск по тексту
            results = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter=filters,
                limit=30,
                with_payload=True
            )[0]
            
            # Фильтруем по релевантности текста
            search_results = []
            query_words = set(query.lower().split())
            
            for result in results:
                content_words = set(result.payload.get("content", "").lower().split())
                title_words = set(result.payload.get("doc_title", "").lower().split())
                
                # Простой подсчет совпадений
                content_matches = len(query_words.intersection(content_words))
                title_matches = len(query_words.intersection(title_words))
                
                # Имитируем BM25 score
                bm25_score = (content_matches * 0.7 + title_matches * 0.3) / len(query_words)
                
                if bm25_score > 0.1:  # Минимальный порог
                    search_results.append(SearchResult(
                        doc_id=result.payload["doc_id"],
                        doc_title=result.payload["doc_title"],
                        doc_family=result.payload["doc_family"],
                        section=result.payload.get("section", ""),
                        clause=result.payload.get("clause", ""),
                        content=result.payload.get("content", ""),
                        score=bm25_score,
                        search_type="bm25",
                        metadata=result.payload
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Ошибка BM25 поиска: {str(e)}")
            return []
    
    def _build_filters(self, intent: IntentClassification) -> Optional[Filter]:
        """Построение фильтров на основе намерения"""
        conditions = []
        
        # Базовые фильтры
        conditions.append(FieldCondition(
            key="is_current",
            match=MatchValue(value=True)
        ))
        
        conditions.append(FieldCondition(
            key="status",
            match=MatchValue(value="active")
        ))
        
        # Фильтры по типу намерения
        if intent.intent_type == "definition":
            conditions.append(FieldCondition(
                key="content_type",
                match=MatchValue(value="definition")
            ))
        elif intent.intent_type == "requirement":
            conditions.append(FieldCondition(
                key="content_type",
                match=MatchValue(value="requirement")
            ))
        
        return Filter(must=conditions) if conditions else None
    
    def _combine_search_results(
        self, 
        vector_results: List[SearchResult],
        bm25_results: List[SearchResult],
        query_confidence: float
    ) -> List[SearchResult]:
        """Объединение результатов векторного и BM25 поиска"""
        # Создаем словарь для объединения результатов
        combined = {}
        
        # Добавляем векторные результаты
        for result in vector_results:
            key = f"{result.doc_id}_{result.section}_{result.clause}"
            combined[key] = result
            result.score *= self.hybrid_weights["vector"] * query_confidence
        
        # Добавляем BM25 результаты
        for result in bm25_results:
            key = f"{result.doc_id}_{result.section}_{result.clause}"
            if key in combined:
                # Объединяем скоры
                combined[key].score += result.score * self.hybrid_weights["bm25"] * query_confidence
                combined[key].search_type = "hybrid"
            else:
                result.score *= self.hybrid_weights["bm25"] * query_confidence
                combined[key] = result
        
        # Сортируем по скору
        return sorted(combined.values(), key=lambda x: x.score, reverse=True)
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Удаление дубликатов из результатов поиска"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = f"{result.doc_id}_{result.section}_{result.clause}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return sorted(unique_results, key=lambda x: x.score, reverse=True)
    
    async def _rerank_results(
        self, 
        query: str, 
        results: List[SearchResult],
        intent: IntentClassification
    ) -> List[SearchResult]:
        """Re-ranking результатов с помощью cross-encoder"""
        try:
            if not results:
                return results
            
            # Подготавливаем пары запрос-документ для cross-encoder
            query_doc_pairs = []
            for result in results:
                # Формируем текст документа для re-ranking
                doc_text = f"{result.doc_title} {result.section} {result.clause} {result.content}"
                query_doc_pairs.append([query, doc_text])
            
            # Получаем скоры от cross-encoder
            rerank_scores = self.rerank_model.predict(query_doc_pairs)
            
            # Обновляем скоры результатов
            for i, result in enumerate(results):
                # Комбинируем оригинальный скор с re-rank скором
                result.rerank_score = float(rerank_scores[i])
                result.final_score = (result.score * 0.3 + result.rerank_score * 0.7)
            
            # Сортируем по финальному скору
            reranked = sorted(results, key=lambda x: x.final_score, reverse=True)
            
            return reranked[:self.final_top_k]
            
        except Exception as e:
            logger.error(f"Ошибка re-ranking: {str(e)}")
            return results[:self.final_top_k]
    
    async def _generate_response(
        self, 
        query: str, 
        results: List[SearchResult],
        intent: IntentClassification,
        user_context: Optional[Dict]
    ) -> RAGResponse:
        """Генерация ответа на основе найденных результатов"""
        try:
            if not results:
                return RAGResponse(
                    query=query,
                    answer="К сожалению, в предоставленных источниках не найдено информации для ответа на ваш вопрос. Попробуйте переформулировать запрос или уточнить область поиска.",
                    sources=[],
                    confidence=0.0,
                    processing_time_ms=0
                )
            
            # Формируем контекст для генерации ответа
            context_chunks = []
            sources = []
            
            for result in results:
                if result.final_score >= self.similarity_threshold:
                    context_chunks.append({
                        "doc_title": result.doc_title,
                        "section": result.section,
                        "clause": result.clause,
                        "content": result.content[:500],  # Ограничиваем длину
                        "score": result.final_score
                    })
                    
                    sources.append({
                        "doc_id": result.doc_id,
                        "doc_title": result.doc_title,
                        "doc_family": result.doc_family,
                        "section": result.section,
                        "clause": result.clause,
                        "relevance_score": result.final_score
                    })
            
            if not context_chunks:
                return RAGResponse(
                    query=query,
                    answer="Найденные результаты не соответствуют достаточному уровню релевантности. Попробуйте уточнить ваш запрос.",
                    sources=sources,
                    confidence=0.3,
                    processing_time_ms=0
                )
            
            # Генерируем ответ на основе шаблона
            answer = self._generate_structured_answer(query, context_chunks, intent)
            
            # Вычисляем общую уверенность
            confidence = min(0.95, max(0.1, sum(chunk["score"] for chunk in context_chunks) / len(context_chunks)))
            
            return RAGResponse(
                query=query,
                answer=answer,
                sources=sources,
                confidence=confidence,
                processing_time_ms=0  # Будет установлено позже
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {str(e)}")
            return RAGResponse(
                query=query,
                answer="Произошла ошибка при генерации ответа. Попробуйте переформулировать вопрос.",
                sources=[],
                confidence=0.0,
                processing_time_ms=0,
                error=str(e)
            )
    
    def _generate_structured_answer(
        self, 
        query: str, 
        context_chunks: List[Dict],
        intent: IntentClassification
    ) -> str:
        """Генерация структурированного ответа"""
        
        # Определяем тип ответа на основе намерения
        if intent.intent_type == "definition":
            return self._generate_definition_answer(context_chunks)
        elif intent.intent_type == "scope":
            return self._generate_scope_answer(context_chunks)
        elif intent.intent_type == "requirement":
            return self._generate_requirement_answer(context_chunks)
        elif intent.intent_type == "reference":
            return self._generate_reference_answer(context_chunks)
        elif intent.intent_type == "comparison":
            return self._generate_comparison_answer(context_chunks)
        elif intent.intent_type == "relevance":
            return self._generate_relevance_answer(context_chunks)
        else:
            return self._generate_general_answer(context_chunks)
    
    def _generate_definition_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация ответа на определение"""
        answer_parts = []
        
        # Краткий ответ
        if context_chunks:
            main_chunk = context_chunks[0]
            answer_parts.append(f"**Определение:** {main_chunk['content'][:200]}...")
        
        # Источники
        answer_parts.append("\n**Источники:**")
        for chunk in context_chunks[:3]:
            answer_parts.append(f"• {chunk['doc_title']}, {chunk['section']} {chunk['clause']}")
        
        return "\n".join(answer_parts)
    
    def _generate_scope_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация ответа об области применения"""
        answer_parts = []
        
        # Краткий ответ
        if context_chunks:
            main_chunk = context_chunks[0]
            answer_parts.append(f"**Область применения:** {main_chunk['content'][:200]}...")
        
        # Источники
        answer_parts.append("\n**Источники:**")
        for chunk in context_chunks[:3]:
            answer_parts.append(f"• {chunk['doc_title']}, {chunk['section']} {chunk['clause']}")
        
        return "\n".join(answer_parts)
    
    def _generate_requirement_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация ответа о требованиях"""
        answer_parts = []
        
        # Краткий ответ
        if context_chunks:
            main_chunk = context_chunks[0]
            answer_parts.append(f"**Требования:** {main_chunk['content'][:200]}...")
        
        # Дополнительные требования
        if len(context_chunks) > 1:
            answer_parts.append("\n**Дополнительные требования:**")
            for chunk in context_chunks[1:3]:
                answer_parts.append(f"• {chunk['content'][:150]}...")
        
        # Источники
        answer_parts.append("\n**Источники:**")
        for chunk in context_chunks[:3]:
            answer_parts.append(f"• {chunk['doc_title']}, {chunk['section']} {chunk['clause']}")
        
        return "\n".join(answer_parts)
    
    def _generate_reference_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация ответа со ссылкой на документ"""
        answer_parts = []
        
        # Прямая ссылка
        if context_chunks:
            main_chunk = context_chunks[0]
            answer_parts.append(f"**{main_chunk['doc_title']}, {main_chunk['section']} {main_chunk['clause']}:**")
            answer_parts.append(main_chunk['content'][:300])
        
        return "\n".join(answer_parts)
    
    def _generate_comparison_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация ответа на сравнение"""
        answer_parts = []
        
        # Сравнение документов
        if context_chunks:
            answer_parts.append("**Сравнение документов:**")
            for chunk in context_chunks[:3]:
                answer_parts.append(f"• **{chunk['doc_title']}:** {chunk['content'][:150]}...")
        
        return "\n".join(answer_parts)
    
    def _generate_relevance_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация ответа об актуальности"""
        answer_parts = []
        
        # Статус актуальности
        if context_chunks:
            main_chunk = context_chunks[0]
            answer_parts.append(f"**Актуальность:** {main_chunk['content'][:200]}...")
        
        # Источники
        answer_parts.append("\n**Источники:**")
        for chunk in context_chunks[:3]:
            answer_parts.append(f"• {chunk['doc_title']}, {chunk['section']} {chunk['clause']}")
        
        return "\n".join(answer_parts)
    
    def _generate_general_answer(self, context_chunks: List[Dict]) -> str:
        """Генерация общего ответа"""
        answer_parts = []
        
        # Основной ответ
        if context_chunks:
            main_chunk = context_chunks[0]
            answer_parts.append(f"**Ответ:** {main_chunk['content'][:250]}...")
        
        # Дополнительная информация
        if len(context_chunks) > 1:
            answer_parts.append("\n**Дополнительная информация:**")
            for chunk in context_chunks[1:3]:
                answer_parts.append(f"• {chunk['content'][:150]}...")
        
        # Источники
        answer_parts.append("\n**Источники:**")
        for chunk in context_chunks[:3]:
            answer_parts.append(f"• {chunk['doc_title']}, {chunk['section']} {chunk['clause']}")
        
        return "\n".join(answer_parts)
    
    async def _search_by_references(self, references: List[Dict[str, str]]) -> List[SearchResult]:
        """Поиск по прямым ссылкам на документы"""
        results = []
        
        for ref in references:
            try:
                # Строим фильтр для конкретного документа
                conditions = [
                    FieldCondition(
                        key="doc_family",
                        match=MatchValue(value=ref["type"])
                    ),
                    FieldCondition(
                        key="is_current",
                        match=MatchValue(value=True)
                    )
                ]
                
                if "number" in ref:
                    conditions.append(FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=f"{ref['type'].lower()}-{ref['number']}-{ref.get('year', '')}")
                    ))
                
                filter_condition = Filter(must=conditions)
                
                # Выполняем поиск
                search_results = self.qdrant.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=filter_condition,
                    limit=10,
                    with_payload=True
                )[0]
                
                # Преобразуем результаты
                for result in search_results:
                    results.append(SearchResult(
                        doc_id=result.payload["doc_id"],
                        doc_title=result.payload["doc_title"],
                        doc_family=result.payload["doc_family"],
                        section=result.payload.get("section", ""),
                        clause=result.payload.get("clause", ""),
                        content=result.payload.get("content", ""),
                        score=1.0,  # Высокий скор для прямых ссылок
                        search_type="reference",
                        metadata=result.payload
                    ))
                
            except Exception as e:
                logger.error(f"Ошибка поиска по ссылке {ref}: {str(e)}")
                continue
        
        return results
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик системы"""
        try:
            # Получаем статистику коллекции
            collection_info = self.qdrant.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "total_documents": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance,
                "hybrid_weights": self.hybrid_weights,
                "rerank_top_k": self.rerank_top_k,
                "final_top_k": self.final_top_k,
                "similarity_threshold": self.similarity_threshold,
                "query_cache_size": len(self.query_cache)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения метрик: {str(e)}")
            return {"error": str(e)}
    
    async def clear_cache(self):
        """Очистка кэша"""
        self.query_cache.clear()
        logger.info("Кэш переформулировок очищен")
