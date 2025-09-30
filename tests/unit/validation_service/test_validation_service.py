"""
Unit тесты для Validation Service
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock

class TestValidationService:
    """Unit тесты для Validation Service"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def mock_validation_request(self):
        """Мок запроса на валидацию"""
        return {
            "data": {
                "length": 6.0,
                "width": 0.3,
                "height": 0.5,
                "load": 200
            },
            "validation_type": "engineering_calculation",
            "standards": ["SNIP", "GOST"]
        }
    
    @pytest.mark.unit
    @pytest.mark.validation_service
    async def test_service_health(self, client):
        """Тест доступности Validation сервиса"""
        try:
            response = await client.get("http://localhost:8007/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "validation-service" in data["service"]
        except httpx.ConnectError:
            pytest.skip("Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.validation_service
    async def test_validate_data(self, client, mock_validation_request):
        """Тест валидации данных"""
        try:
            response = await client.post(
                "http://localhost:8007/validate",
                json=mock_validation_request
            )
            assert response.status_code == 200
            data = response.json()
            assert "is_valid" in data
            assert "errors" in data
            assert "warnings" in data
        except httpx.ConnectError:
            pytest.skip("Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.validation_service
    async def test_get_validation_rules(self, client):
        """Тест получения правил валидации"""
        try:
            response = await client.get("http://localhost:8007/validation-rules")
            assert response.status_code == 200
            data = response.json()
            assert "rules" in data
            assert isinstance(data["rules"], list)
        except httpx.ConnectError:
            pytest.skip("Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.validation_service
    def test_validation_request_validation(self, mock_validation_request):
        """Тест валидации запроса валидации"""
        from services.validation_service.schemas import ValidationRequest
        
        request = ValidationRequest(**mock_validation_request)
        assert request.validation_type == "engineering_calculation"
        assert "SNIP" in request.standards

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
