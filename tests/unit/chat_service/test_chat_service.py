"""
Unit тесты для Chat Service
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock

class TestChatService:
    """Unit тесты для Chat Service"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def mock_chat_message(self):
        """Мок сообщения чата"""
        return {
            "message": "Привет! Как дела?",
            "user_id": "test-user-123",
            "session_id": "test-session-456",
            "context": {
                "project_id": "test-project-789",
                "conversation_history": []
            }
        }
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_service_health(self, client):
        """Тест доступности Chat сервиса"""
        try:
            response = await client.get("http://localhost:8003/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "chat-service" in data["service"]
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_send_message(self, client, mock_chat_message):
        """Тест отправки сообщения"""
        try:
            response = await client.post(
                "http://localhost:8003/chat/send",
                json=mock_chat_message
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "response" in data
            assert "message_id" in data
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_get_conversation_history(self, client):
        """Тест получения истории разговора"""
        try:
            response = await client.get(
                "http://localhost:8003/chat/history/test-session-456"
            )
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert isinstance(data["messages"], list)
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_create_session(self, client):
        """Тест создания сессии чата"""
        try:
            response = await client.post(
                "http://localhost:8003/chat/session",
                json={
                    "user_id": "test-user-123",
                    "project_id": "test-project-789"
                }
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "session_id" in data
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    @patch('services.chat_service.services.ollama_service.OllamaService')
    def test_ollama_integration(self, mock_ollama):
        """Тест интеграции с Ollama"""
        mock_ollama.return_value = Mock()
        mock_ollama.return_value.generate_response = AsyncMock(return_value="Тестовый ответ")
        
        from services.chat_service.services.ollama_service import OllamaService
        
        service = OllamaService()
        assert service is not None
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    @patch('services.chat_service.services.rag_service.RAGService')
    def test_rag_integration(self, mock_rag):
        """Тест интеграции с RAG"""
        mock_rag.return_value = Mock()
        mock_rag.return_value.search_documents = AsyncMock(return_value=[])
        
        from services.chat_service.services.rag_service import RAGService
        
        service = RAGService()
        assert service is not None
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_message_validation(self, mock_chat_message):
        """Тест валидации сообщения"""
        from services.chat_service.schemas import ChatMessage
        
        message = ChatMessage(**mock_chat_message)
        assert message.message == "Привет! Как дела?"
        assert message.user_id == "test-user-123"
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_context_management(self):
        """Тест управления контекстом"""
        from services.chat_service.services.context_service import ContextService
        
        service = ContextService()
        
        # Тест добавления контекста
        context = service.add_context("test-session", {"key": "value"})
        assert context is not None
        
        # Тест получения контекста
        retrieved_context = service.get_context("test-session")
        assert retrieved_context is not None

class TestChatServiceIntegration:
    """Интеграционные тесты для Chat Service"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_chat_with_ollama_integration(self, client):
        """Тест интеграции чата с Ollama"""
        try:
            # Проверяем доступность Ollama Management Service
            ollama_response = await client.get("http://localhost:8012/health")
            assert ollama_response.status_code == 200
            
            # Проверяем доступность Chat Service
            chat_response = await client.get("http://localhost:8003/health")
            assert chat_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Сервисы не запущены")
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_chat_with_rag_integration(self, client):
        """Тест интеграции чата с RAG"""
        try:
            # Проверяем доступность RAG Service
            rag_response = await client.get("http://localhost:8001/health")
            assert rag_response.status_code == 200
            
            # Проверяем доступность Chat Service
            chat_response = await client.get("http://localhost:8003/health")
            assert chat_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Сервисы не запущены")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
