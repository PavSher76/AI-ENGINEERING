"""
Сервис интеграции с RAG для анализа токенизированных документов
"""

import asyncio
import logging
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .smart_tokenizer import TokenChunk, DocumentStructure, SmartTokenizer

logger = logging.getLogger(__name__)

@dataclass
class RAGAnalysisResult:
    """Результат анализа через RAG"""
    query: str
    relevant_chunks: List[TokenChunk]
    rag_response: Dict[str, Any]
    confidence_score: float
    analysis_time: float
    sources: List[Dict[str, Any]]

@dataclass
class LLMAnalysisResult:
    """Результат анализа LLM"""
    analysis_type: str
    summary: str
    key_points: List[str]
    recommendations: List[str]
    confidence: float
    processing_time: float

class RAGIntegrationService:
    """Сервис интеграции с RAG для анализа документов"""
    
    def __init__(self):
        self.rag_service_url = "http://rag-service:8001"
        self.ollama_service_url = "http://ollama-service:8012"
        self.tokenizer = SmartTokenizer()
        
        # Настройки для анализа
        self.max_chunks_for_analysis = 10
        self.min_confidence_threshold = 0.3
        self.analysis_timeout = 30.0
        
        # Типы анализа
        self.analysis_types = {
            'summary': 'Краткое изложение документа',
            'key_points': 'Ключевые моменты и выводы',
            'requirements': 'Требования и обязательства',
            'definitions': 'Определения и термины',
            'recommendations': 'Рекомендации и предложения',
            'compliance': 'Соответствие стандартам',
            'risks': 'Риски и проблемы'
        }
    
    async def analyze_document_with_rag(
        self, 
        document_text: str, 
        user_query: str,
        filename: str = None,
        analysis_type: str = 'general'
    ) -> RAGAnalysisResult:
        """
        Анализ документа с использованием RAG
        
        Args:
            document_text: Текст документа
            user_query: Запрос пользователя
            filename: Имя файла
            analysis_type: Тип анализа
            
        Returns:
            Результат анализа через RAG
        """
        start_time = datetime.now()
        logger.info(f"🔄 Начинаем RAG анализ документа: {filename}")
        
        try:
            # 1. Токенизация документа
            token_chunks, document_structure = await self.tokenizer.tokenize_document(document_text, filename)
            logger.info(f"📄 Документ разбит на {len(token_chunks)} чанков")
            
            # 2. Загрузка чанков в RAG систему
            collection_id = await self._upload_chunks_to_rag(token_chunks, document_structure)
            logger.info(f"📤 Чанки загружены в RAG коллекцию: {collection_id}")
            
            # 3. Поиск релевантных чанков
            relevant_chunks = await self._search_relevant_chunks(user_query, collection_id, analysis_type)
            logger.info(f"🔍 Найдено {len(relevant_chunks)} релевантных чанков")
            
            # 4. Получение ответа от RAG
            rag_response = await self._get_rag_response(user_query, collection_id)
            
            # 5. Формирование результата
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            result = RAGAnalysisResult(
                query=user_query,
                relevant_chunks=relevant_chunks,
                rag_response=rag_response,
                confidence_score=rag_response.get('confidence', 0.0),
                analysis_time=analysis_time,
                sources=rag_response.get('sources', [])
            )
            
            logger.info(f"✅ RAG анализ завершен за {analysis_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка RAG анализа: {str(e)}")
            raise
    
    async def _upload_chunks_to_rag(self, chunks: List[TokenChunk], structure: DocumentStructure) -> str:
        """Загрузка чанков в RAG систему"""
        try:
            collection_id = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Создаем коллекцию
            async with aiohttp.ClientSession() as session:
                collection_data = {
                    "name": collection_id,
                    "description": f"Коллекция для документа: {structure.title}",
                    "type": "document_analysis"
                }
                
                async with session.post(
                    f"{self.rag_service_url}/collections/",
                    json=collection_data
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Не удалось создать коллекцию: {response.status}")
            
            # Загружаем чанки как документы
            for i, chunk in enumerate(chunks):
                try:
                    # Создаем временный файл для чанка
                    chunk_filename = f"chunk_{i}_{chunk.chunk_id}.txt"
                    
                    # Подготавливаем данные для загрузки
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', chunk.text.encode('utf-8'), filename=chunk_filename, content_type='text/plain')
                    form_data.add_field('collection_id', collection_id)
                    form_data.add_field('project_id', 'document_analysis')
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.rag_service_url}/documents/upload",
                            data=form_data
                        ) as response:
                            if response.status == 200:
                                logger.debug(f"Чанк {i} загружен в RAG")
                            else:
                                logger.warning(f"Ошибка загрузки чанка {i}: {response.status}")
                
                except Exception as e:
                    logger.error(f"Ошибка загрузки чанка {i}: {str(e)}")
                    continue
            
            return collection_id
            
        except Exception as e:
            logger.error(f"Ошибка загрузки чанков в RAG: {str(e)}")
            raise
    
    async def _search_relevant_chunks(
        self, 
        query: str, 
        collection_id: str, 
        analysis_type: str
    ) -> List[TokenChunk]:
        """Поиск релевантных чанков"""
        try:
            # Формируем расширенный запрос на основе типа анализа
            enhanced_query = self._enhance_query_for_analysis(query, analysis_type)
            
            search_request = {
                "query": enhanced_query,
                "collection_id": collection_id,
                "limit": self.max_chunks_for_analysis,
                "threshold": self.min_confidence_threshold
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.rag_service_url}/documents/search",
                    json=search_request
                ) as response:
                    if response.status == 200:
                        search_result = await response.json()
                        
                        # Преобразуем результаты в TokenChunk
                        relevant_chunks = []
                        for i, doc in enumerate(search_result.get('results', [])):
                            chunk = TokenChunk(
                                chunk_id=f"rag_chunk_{i}",
                                text=doc.get('content', ''),
                                token_count=len(doc.get('content', '').split()),
                                chunk_type='rag_result',
                                metadata={
                                    'doc_id': doc.get('id'),
                                    'title': doc.get('title'),
                                    'score': search_result.get('scores', [0])[i] if i < len(search_result.get('scores', [])) else 0,
                                    'source': 'rag_search'
                                },
                                start_position=0,
                                end_position=len(doc.get('content', '')),
                                importance_score=search_result.get('scores', [0])[i] if i < len(search_result.get('scores', [])) else 0
                            )
                            relevant_chunks.append(chunk)
                        
                        return relevant_chunks
                    else:
                        logger.error(f"Ошибка поиска в RAG: {response.status}")
                        return []
            
        except Exception as e:
            logger.error(f"Ошибка поиска релевантных чанков: {str(e)}")
            return []
    
    def _enhance_query_for_analysis(self, query: str, analysis_type: str) -> str:
        """Улучшение запроса для конкретного типа анализа"""
        enhancements = {
            'summary': f"{query} краткое изложение основные моменты",
            'key_points': f"{query} ключевые моменты важные выводы",
            'requirements': f"{query} требования обязательства нормы",
            'definitions': f"{query} определения термины понятия",
            'recommendations': f"{query} рекомендации предложения советы",
            'compliance': f"{query} соответствие стандарты нормативы",
            'risks': f"{query} риски проблемы опасности"
        }
        
        return enhancements.get(analysis_type, query)
    
    async def _get_rag_response(self, query: str, collection_id: str) -> Dict[str, Any]:
        """Получение ответа от RAG системы"""
        try:
            search_request = {
                "query": query,
                "collection_id": collection_id,
                "limit": 5,
                "threshold": 0.5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.rag_service_url}/documents/search",
                    json=search_request
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Ошибка получения RAG ответа: {response.status}")
                        return {"error": f"RAG service error: {response.status}"}
            
        except Exception as e:
            logger.error(f"Ошибка получения RAG ответа: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_with_llm(
        self, 
        chunks: List[TokenChunk], 
        query: str,
        analysis_type: str = 'general'
    ) -> LLMAnalysisResult:
        """
        Анализ токенизированных чанков с помощью LLM
        
        Args:
            chunks: Список токенизированных чанков
            query: Запрос пользователя
            analysis_type: Тип анализа
            
        Returns:
            Результат анализа LLM
        """
        start_time = datetime.now()
        logger.info(f"🤖 Начинаем LLM анализ {len(chunks)} чанков")
        
        try:
            # 1. Подготавливаем контекст для LLM
            context = self._prepare_llm_context(chunks, query, analysis_type)
            
            # 2. Формируем промпт для анализа
            prompt = self._create_analysis_prompt(query, analysis_type, context)
            
            # 3. Отправляем запрос к LLM
            llm_response = await self._query_llm(prompt)
            
            # 4. Парсим ответ LLM
            analysis_result = self._parse_llm_response(llm_response, analysis_type)
            
            # 5. Формируем результат
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = LLMAnalysisResult(
                analysis_type=analysis_type,
                summary=analysis_result.get('summary', ''),
                key_points=analysis_result.get('key_points', []),
                recommendations=analysis_result.get('recommendations', []),
                confidence=analysis_result.get('confidence', 0.7),
                processing_time=processing_time
            )
            
            logger.info(f"✅ LLM анализ завершен за {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка LLM анализа: {str(e)}")
            raise
    
    def _prepare_llm_context(self, chunks: List[TokenChunk], query: str, analysis_type: str) -> str:
        """Подготовка контекста для LLM"""
        # Сортируем чанки по важности
        sorted_chunks = sorted(chunks, key=lambda x: x.importance_score, reverse=True)
        
        # Берем наиболее важные чанки
        top_chunks = sorted_chunks[:self.max_chunks_for_analysis]
        
        context_parts = []
        for i, chunk in enumerate(top_chunks):
            context_parts.append(f"Фрагмент {i+1} (важность: {chunk.importance_score:.2f}):")
            context_parts.append(chunk.text)
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, query: str, analysis_type: str, context: str) -> str:
        """Создание промпта для анализа"""
        base_prompt = f"""
Вы - эксперт по анализу технических документов. Проанализируйте предоставленные фрагменты документа в контексте запроса пользователя.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {query}

ТИП АНАЛИЗА: {self.analysis_types.get(analysis_type, 'общий анализ')}

КОНТЕКСТ ДОКУМЕНТА:
{context}

Пожалуйста, предоставьте анализ в следующем формате:

КРАТКОЕ ИЗЛОЖЕНИЕ:
[Краткое изложение основных моментов, относящихся к запросу]

КЛЮЧЕВЫЕ МОМЕНТЫ:
- [Ключевой момент 1]
- [Ключевой момент 2]
- [Ключевой момент 3]

РЕКОМЕНДАЦИИ:
- [Рекомендация 1]
- [Рекомендация 2]

УВЕРЕННОСТЬ: [Оценка от 0.0 до 1.0]

Ответьте на русском языке, будьте точными и конкретными.
"""
        
        return base_prompt
    
    async def _query_llm(self, prompt: str) -> str:
        """Отправка запроса к LLM"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 2048
                    }
                }
                
                async with session.post(
                    f"{self.ollama_service_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.analysis_timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        logger.error(f"Ошибка LLM запроса: {response.status}")
                        return "Ошибка получения ответа от LLM"
            
        except asyncio.TimeoutError:
            logger.error("Таймаут LLM запроса")
            return "Превышено время ожидания ответа от LLM"
        except Exception as e:
            logger.error(f"Ошибка LLM запроса: {str(e)}")
            return f"Ошибка LLM: {str(e)}"
    
    def _parse_llm_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Парсинг ответа LLM"""
        try:
            result = {
                'summary': '',
                'key_points': [],
                'recommendations': [],
                'confidence': 0.7
            }
            
            # Простой парсинг по секциям
            sections = response.split('\n\n')
            
            for section in sections:
                section = section.strip()
                if section.startswith('КРАТКОЕ ИЗЛОЖЕНИЕ:'):
                    result['summary'] = section.replace('КРАТКОЕ ИЗЛОЖЕНИЕ:', '').strip()
                elif section.startswith('КЛЮЧЕВЫЕ МОМЕНТЫ:'):
                    points_text = section.replace('КЛЮЧЕВЫЕ МОМЕНТЫ:', '').strip()
                    result['key_points'] = [point.strip('- ').strip() for point in points_text.split('\n') if point.strip()]
                elif section.startswith('РЕКОМЕНДАЦИИ:'):
                    rec_text = section.replace('РЕКОМЕНДАЦИИ:', '').strip()
                    result['recommendations'] = [rec.strip('- ').strip() for rec in rec_text.split('\n') if rec.strip()]
                elif section.startswith('УВЕРЕННОСТЬ:'):
                    conf_text = section.replace('УВЕРЕННОСТЬ:', '').strip()
                    try:
                        result['confidence'] = float(conf_text)
                    except ValueError:
                        result['confidence'] = 0.7
            
            # Если парсинг не удался, используем весь ответ как summary
            if not result['summary'] and not result['key_points']:
                result['summary'] = response
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга LLM ответа: {str(e)}")
            return {
                'summary': response,
                'key_points': [],
                'recommendations': [],
                'confidence': 0.5
            }
    
    async def get_comprehensive_analysis(
        self, 
        document_text: str, 
        user_query: str,
        filename: str = None
    ) -> Dict[str, Any]:
        """
        Комплексный анализ документа с использованием RAG и LLM
        
        Args:
            document_text: Текст документа
            user_query: Запрос пользователя
            filename: Имя файла
            
        Returns:
            Комплексный результат анализа
        """
        logger.info(f"🔍 Начинаем комплексный анализ документа: {filename}")
        
        try:
            # 1. RAG анализ
            rag_result = await self.analyze_document_with_rag(document_text, user_query, filename)
            
            # 2. LLM анализ релевантных чанков
            llm_result = await self.analyze_with_llm(rag_result.relevant_chunks, user_query)
            
            # 3. Формируем комплексный результат
            comprehensive_result = {
                'query': user_query,
                'filename': filename,
                'rag_analysis': {
                    'confidence': rag_result.confidence_score,
                    'sources_count': len(rag_result.sources),
                    'analysis_time': rag_result.analysis_time,
                    'sources': rag_result.sources
                },
                'llm_analysis': {
                    'analysis_type': llm_result.analysis_type,
                    'summary': llm_result.summary,
                    'key_points': llm_result.key_points,
                    'recommendations': llm_result.recommendations,
                    'confidence': llm_result.confidence,
                    'processing_time': llm_result.processing_time
                },
                'document_stats': {
                    'total_chunks': len(rag_result.relevant_chunks),
                    'total_tokens': sum(chunk.token_count for chunk in rag_result.relevant_chunks),
                    'average_importance': sum(chunk.importance_score for chunk in rag_result.relevant_chunks) / len(rag_result.relevant_chunks) if rag_result.relevant_chunks else 0
                },
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_processing_time': rag_result.analysis_time + llm_result.processing_time,
                    'analysis_version': '1.0'
                }
            }
            
            logger.info(f"✅ Комплексный анализ завершен")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка комплексного анализа: {str(e)}")
            raise

