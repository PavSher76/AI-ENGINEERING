"""
Unit тесты для API endpoints всех сервисов
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock

class TestAPIEndpoints:
    """Unit тесты для API endpoints"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.unit
    async def test_rag_service_health(self, client):
        """Тест health endpoint RAG Service"""
        try:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")
    
    @pytest.mark.unit
    async def test_chat_service_health(self, client):
        """Тест health endpoint Chat Service"""
        try:
            response = await client.get("http://localhost:8003/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    async def test_ollama_service_health(self, client):
        """Тест health endpoint Ollama Management Service"""
        try:
            response = await client.get("http://localhost:8012/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    async def test_outgoing_control_health(self, client):
        """Тест health endpoint Outgoing Control Service"""
        try:
            response = await client.get("http://localhost:8011/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Outgoing Control Service не запущен")
    
    @pytest.mark.unit
    async def test_consultation_service_health(self, client):
        """Тест health endpoint Consultation Service"""
        try:
            response = await client.get("http://localhost:8004/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Consultation Service не запущен")
    
    @pytest.mark.unit
    async def test_archive_service_health(self, client):
        """Тест health endpoint Archive Service"""
        try:
            response = await client.get("http://localhost:8005/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Archive Service не запущен")
    
    @pytest.mark.unit
    async def test_calculation_service_health(self, client):
        """Тест health endpoint Calculation Service"""
        try:
            response = await client.get("http://localhost:8006/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Calculation Service не запущен")
    
    @pytest.mark.unit
    async def test_validation_service_health(self, client):
        """Тест health endpoint Validation Service"""
        try:
            response = await client.get("http://localhost:8007/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Validation Service не запущен")
    
    @pytest.mark.unit
    async def test_document_service_health(self, client):
        """Тест health endpoint Document Service"""
        try:
            response = await client.get("http://localhost:8008/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Document Service не запущен")
    
    @pytest.mark.unit
    async def test_analytics_service_health(self, client):
        """Тест health endpoint Analytics Service"""
        try:
            response = await client.get("http://localhost:8009/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Analytics Service не запущен")
    
    @pytest.mark.unit
    async def test_integration_service_health(self, client):
        """Тест health endpoint Integration Service"""
        try:
            response = await client.get("http://localhost:8010/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip("Integration Service не запущен")
    
    @pytest.mark.unit
    async def test_frontend_health(self, client):
        """Тест доступности Frontend"""
        try:
            response = await client.get("http://localhost:3000")
            assert response.status_code == 200
            # Проверяем, что это HTML страница
            assert "text/html" in response.headers.get("content-type", "")
        except httpx.ConnectError:
            pytest.skip("Frontend не запущен")
    
    @pytest.mark.unit
    async def test_ollama_models_endpoint(self, client):
        """Тест endpoint получения моделей Ollama"""
        try:
            response = await client.get("http://localhost:8012/models")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    async def test_ollama_status_endpoint(self, client):
        """Тест endpoint статуса Ollama"""
        try:
            response = await client.get("http://localhost:8012/status")
            assert response.status_code == 200
            data = response.json()
            assert "ollama_running" in data
        except httpx.ConnectError:
            pytest.skip("Ollama Management Service не запущен")
    
    @pytest.mark.unit
    async def test_outgoing_control_spell_check(self, client):
        """Тест endpoint проверки орфографии"""
        try:
            response = await client.post(
                "http://localhost:8011/spell-check",
                json={"text": "Тестовый текст с ошибкаа"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "errors_found" in data
        except httpx.ConnectError:
            pytest.skip("Outgoing Control Service не запущен")
    
    @pytest.mark.unit
    async def test_rag_collections_endpoint(self, client):
        """Тест endpoint коллекций RAG"""
        try:
            response = await client.get("http://localhost:8001/collections")
            assert response.status_code == 200
            data = response.json()
            assert "collections" in data
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")

class TestAPIValidation:
    """Тесты валидации API"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.unit
    async def test_invalid_endpoints(self, client):
        """Тест несуществующих endpoints"""
        try:
            # Тестируем несуществующий endpoint
            response = await client.get("http://localhost:8001/nonexistent")
            assert response.status_code == 404
        except httpx.ConnectError:
            pytest.skip("RAG Service не запущен")
    
    @pytest.mark.unit
    async def test_invalid_json_requests(self, client):
        """Тест некорректных JSON запросов"""
        try:
            # Тестируем некорректный JSON
            response = await client.post(
                "http://localhost:8011/spell-check",
                json={"invalid_field": "test"}
            )
            # Должен вернуть ошибку валидации или 422
            assert response.status_code in [400, 422]
        except httpx.ConnectError:
            pytest.skip("Outgoing Control Service не запущен")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
