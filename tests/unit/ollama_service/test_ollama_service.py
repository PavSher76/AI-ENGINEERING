"""
Unit тесты для Ollama Management Service
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock

class TestOllamaService:
    """Unit тесты для Ollama Management Service"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def mock_model_info(self):
        """Мок информации о модели"""
        return {
            "name": "llama3.1:8b",
            "size": 4720000000,
            "digest": "sha256:abc123",
            "modified_at": "2025-01-01T00:00:00Z"
        }
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    async def test_service_health(self, client):
        """Тест доступности Ollama Management сервиса"""
        try:
            response = await client.get("http://localhost:8012/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "ollama-management-service" in data["service"]
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    async def test_get_models(self, client):
        """Тест получения списка моделей"""
        try:
            response = await client.get("http://localhost:8012/models")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # Проверяем, что есть хотя бы одна модель
            if len(data) > 0:
                model = data[0]
                assert "name" in model
                assert "size" in model
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    async def test_get_model_info(self, client):
        """Тест получения информации о модели"""
        try:
            response = await client.get("http://localhost:8012/models/llama3.1:8b")
            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "size" in data
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    async def test_generate_text(self, client):
        """Тест генерации текста"""
        try:
            response = await client.post(
                "http://localhost:8012/models/llama3.1:8b/generate",
                json={
                    "prompt": "Привет! Как дела?",
                    "max_tokens": 50
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "model" in data
            assert data["model"] == "llama3.1:8b"
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    async def test_set_default_model(self, client):
        """Тест установки модели по умолчанию"""
        try:
            response = await client.post(
                "http://localhost:8012/models/default",
                json={"model_name": "llama3.1:8b"}
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "default_model" in data
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    async def test_get_status(self, client):
        """Тест получения статуса Ollama"""
        try:
            response = await client.get("http://localhost:8012/status")
            assert response.status_code == 200
            data = response.json()
            assert "ollama_running" in data
            assert "models_count" in data
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    @patch('services.ollama_service.main.httpx.AsyncClient')
    def test_ollama_client_initialization(self, mock_client):
        """Тест инициализации клиента Ollama"""
        mock_client.return_value = AsyncMock()
        
        from services.ollama_service.main import OllamaClient
        
        client = OllamaClient()
        assert client is not None
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    def test_model_validation(self, mock_model_info):
        """Тест валидации модели"""
        from services.ollama_service.schemas import ModelInfo
        
        model = ModelInfo(**mock_model_info)
        assert model.name == "llama3.1:8b"
        assert model.size == 4720000000
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    def test_generation_request_validation(self):
        """Тест валидации запроса генерации"""
        from services.ollama_service.schemas import GenerateRequest
        
        request = GenerateRequest(
            prompt="Тестовый промпт",
            max_tokens=100
        )
        assert request.prompt == "Тестовый промпт"
        assert request.max_tokens == 100
    
    @pytest.mark.unit
    @pytest.mark.ollama_service
    @pytest.mark.slow
    async def test_full_model_workflow(self, client):
        """Тест полного цикла работы с моделью"""
        try:
            # 1. Получаем список моделей
            models_response = await client.get("http://localhost:8012/models")
            assert models_response.status_code == 200
            models = models_response.json()
            
            if len(models) > 0:
                model_name = models[0]["name"]
                
                # 2. Получаем информацию о модели
                info_response = await client.get(f"http://localhost:8012/models/{model_name}")
                assert info_response.status_code == 200
                
                # 3. Генерируем текст
                generate_response = await client.post(
                    f"http://localhost:8012/models/{model_name}/generate",
                    json={
                        "prompt": "Кратко расскажи о преимуществах ИИ",
                        "max_tokens": 100
                    }
                )
                assert generate_response.status_code == 200
                
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")

class TestOllamaServiceIntegration:
    """Интеграционные тесты для Ollama Management Service"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.ollama_service
    @pytest.mark.slow
    async def test_ollama_host_integration(self, client):
        """Тест интеграции с Ollama на хосте"""
        try:
            # Проверяем доступность Ollama на хосте
            ollama_response = await client.get("http://localhost:11434/api/tags")
            assert ollama_response.status_code == 200
            
            # Проверяем доступность Ollama Management Service
            service_response = await client.get("http://localhost:8012/health")
            assert service_response.status_code == 200
            
        except httpx.ConnectError:
            pytest.skip("Ollama на хосте не запущен")
    
    @pytest.mark.integration
    @pytest.mark.ollama_service
    @pytest.mark.slow
    async def test_model_management_integration(self, client):
        """Тест интеграции управления моделями"""
        try:
            # Получаем модели через Ollama Management Service
            service_models = await client.get("http://localhost:8012/models")
            assert service_models.status_code == 200
            
            # Получаем модели напрямую через Ollama
            ollama_models = await client.get("http://localhost:11434/api/tags")
            assert ollama_models.status_code == 200
            
            # Проверяем, что количество моделей совпадает
            service_count = len(service_models.json())
            ollama_count = len(ollama_models.json().get("models", []))
            assert service_count == ollama_count
            
        except httpx.ConnectError:
            pytest.skip("Ollama на хосте не запущен")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
