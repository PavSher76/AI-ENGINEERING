"""
Клиент для работы с API Техэксперт
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from models.schemas import (
    SearchRequest, DocumentResult, DocumentMeta, LatestEdition,
    SectionsResponse, SectionContent, CitationsResponse,
    TechExpertDocument, TechExpertSearchResult
)

logger = logging.getLogger(__name__)

class TechExpertClient:
    """Клиент для работы с API Техэксперт"""
    
    def __init__(self):
        self.base_url = "https://api.techexpert.ru/v1"
        self.api_key = None
        self.access_token = None
        self.token_expires_at = None
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = None
        
        # Настройки HTTP клиента
        self.timeout = httpx.Timeout(30.0)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        
    async def authenticate(self, client_id: str, client_secret: str) -> bool:
        """Аутентификация в API Техэксперт"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
                response = await client.post(
                    f"{self.base_url}/auth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "scope": "read"
                    }
                )
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Успешная аутентификация в API Техэксперт")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка аутентификации в API Техэксперт: {str(e)}")
            return False
    
    async def _ensure_authenticated(self) -> bool:
        """Проверка и обновление токена при необходимости"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            # Здесь должна быть логика получения нового токена
            # Для демонстрации используем мок-токен
            self.access_token = "mock_token"
            self.token_expires_at = datetime.now() + timedelta(hours=1)
            logger.warning("Используется мок-токен для API Техэксперт")
        
        return True
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Выполнение HTTP запроса к API"""
        await self._ensure_authenticated()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "TechExpert-Connector/1.0.0"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )
            
            # Обновляем информацию о rate limit
            if "X-RateLimit-Remaining" in response.headers:
                self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
            if "X-RateLimit-Reset" in response.headers:
                self.rate_limit_reset = datetime.fromtimestamp(
                    int(response.headers["X-RateLimit-Reset"])
                )
            
            response.raise_for_status()
            return response.json()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search_documents(self, search_request: SearchRequest) -> List[DocumentResult]:
        """Поиск документов в API Техэксперт"""
        try:
            logger.info(f"Поиск документов: {search_request.query}")
            
            # Подготавливаем параметры запроса
            params = {
                "q": search_request.query,
                "limit": search_request.limit,
                "offset": search_request.offset,
                "sort": search_request.sort_by.value
            }
            
            # Добавляем фильтры
            if search_request.filters:
                for key, value in search_request.filters.items():
                    if value is not None:
                        params[f"filter_{key}"] = value
            
            # Выполняем запрос
            response_data = await self._make_request("GET", "/documents/search", params=params)
            
            # Преобразуем результаты
            results = []
            for item in response_data.get("results", []):
                result = DocumentResult(
                    doc_id=item["doc_id"],
                    doc_title=item["doc_title"],
                    doc_family=item["doc_family"],
                    edition_year=item["edition_year"],
                    is_current=item["is_current"],
                    relevance_score=item["relevance_score"],
                    snippet=item["snippet"],
                    matched_sections=item.get("matched_sections", []),
                    source="techexpert"
                )
                results.append(result)
            
            logger.info(f"Найдено {len(results)} документов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка поиска документов: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_document_meta(
        self, 
        doc_id: str, 
        edition_id: Optional[str] = None
    ) -> Optional[DocumentMeta]:
        """Получение метаданных документа"""
        try:
            logger.info(f"Получение метаданных документа: {doc_id}")
            
            params = {}
            if edition_id:
                params["edition_id"] = edition_id
            
            response_data = await self._make_request(
                "GET", 
                f"/documents/{doc_id}/meta", 
                params=params
            )
            
            if not response_data:
                return None
            
            meta = DocumentMeta(
                doc_id=response_data["doc_id"],
                doc_title=response_data["doc_title"],
                doc_family=response_data["doc_family"],
                discipline=response_data["discipline"],
                edition_year=response_data["edition_year"],
                is_current=response_data["is_current"],
                effective_from=response_data.get("effective_from"),
                canceled_by=response_data.get("canceled_by"),
                status=response_data["status"],
                techexpert_doc_id=response_data.get("techexpert_doc_id"),
                techexpert_edition_id=response_data.get("techexpert_edition_id"),
                last_updated=datetime.fromisoformat(response_data["last_updated"]),
                source="techexpert"
            )
            
            logger.info(f"Метаданные получены для документа: {doc_id}")
            return meta
            
        except Exception as e:
            logger.error(f"Ошибка получения метаданных: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_latest_edition(self, doc_id: str) -> Optional[LatestEdition]:
        """Получение информации о последней редакции документа"""
        try:
            logger.info(f"Получение последней редакции документа: {doc_id}")
            
            response_data = await self._make_request(
                "GET", 
                f"/documents/{doc_id}/latest"
            )
            
            if not response_data:
                return None
            
            latest_edition = LatestEdition(
                doc_id=response_data["doc_id"],
                current_edition=response_data["current_edition"],
                local_edition=response_data.get("local_edition"),
                needs_update=response_data["needs_update"],
                source="techexpert"
            )
            
            logger.info(f"Последняя редакция получена для документа: {doc_id}")
            return latest_edition
            
        except Exception as e:
            logger.error(f"Ошибка получения последней редакции: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_document_sections(
        self, 
        doc_id: str, 
        edition_id: Optional[str] = None
    ) -> Optional[SectionsResponse]:
        """Получение списка разделов документа"""
        try:
            logger.info(f"Получение разделов документа: {doc_id}")
            
            params = {}
            if edition_id:
                params["edition_id"] = edition_id
            
            response_data = await self._make_request(
                "GET", 
                f"/documents/{doc_id}/sections", 
                params=params
            )
            
            if not response_data:
                return None
            
            sections_response = SectionsResponse(
                doc_id=response_data["doc_id"],
                sections=response_data["sections"],
                total_sections=response_data["total_sections"]
            )
            
            logger.info(f"Разделы получены для документа: {doc_id}")
            return sections_response
            
        except Exception as e:
            logger.error(f"Ошибка получения разделов: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_section_content(
        self, 
        doc_id: str, 
        section_id: str, 
        edition_id: Optional[str] = None,
        include_metadata: bool = True
    ) -> Optional[SectionContent]:
        """Получение содержимого раздела"""
        try:
            logger.info(f"Получение содержимого раздела: {doc_id}/{section_id}")
            
            params = {"include_metadata": include_metadata}
            if edition_id:
                params["edition_id"] = edition_id
            
            response_data = await self._make_request(
                "GET", 
                f"/documents/{doc_id}/sections/{section_id}", 
                params=params
            )
            
            if not response_data:
                return None
            
            content = SectionContent(
                doc_id=response_data["doc_id"],
                section_id=response_data["section_id"],
                section_title=response_data["section_title"],
                content=response_data["content"],
                page_from=response_data.get("page_from"),
                page_to=response_data.get("page_to"),
                metadata=response_data.get("metadata"),
                source="techexpert"
            )
            
            logger.info(f"Содержимое получено для раздела: {doc_id}/{section_id}")
            return content
            
        except Exception as e:
            logger.error(f"Ошибка получения содержимого: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_document_citations(
        self, 
        doc_id: str, 
        edition_id: Optional[str] = None,
        limit: int = 50
    ) -> Optional[CitationsResponse]:
        """Получение ссылок на документ"""
        try:
            logger.info(f"Получение ссылок на документ: {doc_id}")
            
            params = {"limit": limit}
            if edition_id:
                params["edition_id"] = edition_id
            
            response_data = await self._make_request(
                "GET", 
                f"/documents/{doc_id}/citations", 
                params=params
            )
            
            if not response_data:
                return None
            
            citations_response = CitationsResponse(
                doc_id=response_data["doc_id"],
                citations=response_data["citations"],
                total_count=response_data["total_count"]
            )
            
            logger.info(f"Ссылки получены для документа: {doc_id}")
            return citations_response
            
        except Exception as e:
            logger.error(f"Ошибка получения ссылок: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния API Техэксперт"""
        try:
            start_time = datetime.now()
            
            # Простой запрос для проверки доступности
            await self._make_request("GET", "/health")
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "up",
                "response_time_ms": response_time,
                "rate_limit_remaining": self.rate_limit_remaining,
                "rate_limit_reset": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None
            }
            
        except Exception as e:
            logger.error(f"API Техэксперт недоступен: {str(e)}")
            return {
                "status": "down",
                "response_time_ms": None,
                "error": str(e)
            }
    
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Получение информации о лимитах запросов"""
        return {
            "remaining": self.rate_limit_remaining,
            "reset_time": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None,
            "is_limited": self.rate_limit_remaining <= 10
        }
    
    async def close(self):
        """Закрытие клиента"""
        # Очистка ресурсов
        self.access_token = None
        self.token_expires_at = None
        logger.info("TechExpert клиент закрыт")
