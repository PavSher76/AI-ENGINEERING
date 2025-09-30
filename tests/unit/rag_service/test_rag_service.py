"""
Unit тесты для RAG Service
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

class TestRAGService:
    """Unit тесты для RAG Service"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def mock_document(self):
        """Мок документа для тестов"""
        return {
            "id": "test-doc-123",
            "filename": "test_document.pdf",
            "content": "Тестовый документ для проверки RAG функциональности",
            "metadata": {
                "author": "Test Author",
                "created_at": "2025-01-01T00:00:00Z",
                "file_type": "pdf"
            }
        }
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    async def test_service_health(self, client):
        """Тест доступности RAG сервиса"""
        try:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "rag-service" in data["service"]
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    async def test_create_collection(self, client):
        """Тест создания коллекции"""
        try:
            response = await client.post(
                "http://localhost:8001/collections",
                json={
                    "name": "test-collection",
                    "description": "Тестовая коллекция",
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            )
            assert response.status_code in [200, 201, 409]  # 409 если уже существует
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    async def test_list_collections(self, client):
        """Тест получения списка коллекций"""
        try:
            response = await client.get("http://localhost:8001/collections")
            assert response.status_code == 200
            data = response.json()
            assert "collections" in data
            assert isinstance(data["collections"], list)
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    async def test_search_documents(self, client):
        """Тест поиска документов"""
        try:
            response = await client.post(
                "http://localhost:8001/search",
                json={
                    "query": "тестовый документ",
                    "collection_name": "test-collection",
                    "limit": 10
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    @patch('services.rag_service.services.vector_service.QdrantClient')
    def test_vector_service_initialization(self, mock_qdrant):
        """Тест инициализации векторного сервиса"""
        mock_qdrant.return_value = Mock()
        
        from services.rag_service.services.vector_service import VectorService
        
        service = VectorService()
        assert service is not None
        mock_qdrant.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    @patch('services.rag_service.services.embedding_service.SentenceTransformer')
    def test_embedding_service_initialization(self, mock_transformer):
        """Тест инициализации сервиса эмбеддингов"""
        mock_transformer.return_value = Mock()
        
        from services.rag_service.services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        assert service is not None
        mock_transformer.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    def test_document_processing(self, mock_document):
        """Тест обработки документа"""
        from services.rag_service.services.document_service import DocumentService
        
        service = DocumentService()
        
        # Тест извлечения текста
        text = service.extract_text(mock_document["content"])
        assert isinstance(text, str)
        assert len(text) > 0
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    def test_metadata_validation(self, mock_document):
        """Тест валидации метаданных"""
        from services.rag_service.schemas import DocumentMetadata
        
        metadata = DocumentMetadata(**mock_document["metadata"])
        assert metadata.author == "Test Author"
        assert metadata.file_type == "pdf"
    
    @pytest.mark.unit
    @pytest.mark.rag_service
    @pytest.mark.slow
    async def test_full_document_workflow(self, client, mock_document):
        """Тест полного цикла работы с документом"""
        try:
            # 1. Создание коллекции
            collection_response = await client.post(
                "http://localhost:8001/collections",
                json={
                    "name": "workflow-test",
                    "description": "Тест полного цикла"
                }
            )
            
            # 2. Загрузка документа (мок)
            upload_response = await client.post(
                "http://localhost:8001/documents",
                json=mock_document
            )
            
            # 3. Поиск документа
            search_response = await client.post(
                "http://localhost:8001/search",
                json={
                    "query": "тестовый",
                    "collection_name": "workflow-test"
                }
            )
            
            assert search_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")

class TestRAGServiceIntegration:
    """Интеграционные тесты для RAG Service"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.rag_service
    @pytest.mark.slow
    async def test_rag_with_qdrant_integration(self, client):
        """Тест интеграции RAG с Qdrant"""
        try:
            # Проверяем доступность Qdrant
            qdrant_response = await client.get("http://localhost:6333/collections")
            assert qdrant_response.status_code == 200
            
            # Проверяем доступность RAG
            rag_response = await client.get("http://localhost:8001/health")
            assert rag_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Сервисы не запущены")
    
    @pytest.mark.integration
    @pytest.mark.rag_service
    @pytest.mark.slow
    async def test_rag_with_minio_integration(self, client):
        """Тест интеграции RAG с MinIO"""
        try:
            # Проверяем доступность MinIO
            minio_response = await client.get("http://localhost:9000/minio/health/live")
            assert minio_response.status_code == 200
            
            # Проверяем доступность RAG
            rag_response = await client.get("http://localhost:8001/health")
            assert rag_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Сервисы не запущены")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
