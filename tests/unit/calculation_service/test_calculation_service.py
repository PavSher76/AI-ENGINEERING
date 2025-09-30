"""
Unit тесты для Calculation Service
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock

class TestCalculationService:
    """Unit тесты для Calculation Service"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def mock_calculation_request(self):
        """Мок запроса на расчет"""
        return {
            "calculation_type": "beam_load",
            "parameters": {
                "length": 6.0,
                "width": 0.3,
                "height": 0.5,
                "material": "concrete",
                "load": 200
            },
            "model": "llama3.1:8b"
        }
    
    @pytest.mark.unit
    @pytest.mark.calculation_service
    async def test_service_health(self, client):
        """Тест доступности Calculation сервиса"""
        try:
            response = await client.get("http://localhost:8006/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "calculation-service" in data["service"]
        except httpx.ConnectError:
            pytest.skip("Calculation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.calculation_service
    async def test_perform_calculation(self, client, mock_calculation_request):
        """Тест выполнения расчета"""
        try:
            response = await client.post(
                "http://localhost:8006/calculate",
                json=mock_calculation_request
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "result" in data
            assert "calculation_id" in data
        except httpx.ConnectError:
            pytest.skip("Calculation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.calculation_service
    async def test_get_calculation_types(self, client):
        """Тест получения типов расчетов"""
        try:
            response = await client.get("http://localhost:8006/calculation-types")
            assert response.status_code == 200
            data = response.json()
            assert "types" in data
            assert isinstance(data["types"], list)
        except httpx.ConnectError:
            pytest.skip("Calculation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.calculation_service
    async def test_get_calculation_history(self, client):
        """Тест получения истории расчетов"""
        try:
            response = await client.get("http://localhost:8006/calculations")
            assert response.status_code == 200
            data = response.json()
            assert "calculations" in data
            assert isinstance(data["calculations"], list)
        except httpx.ConnectError:
            pytest.skip("Calculation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.calculation_service
    def test_calculation_validation(self, mock_calculation_request):
        """Тест валидации запроса расчета"""
        from services.calculation_service.schemas import CalculationRequest
        
        request = CalculationRequest(**mock_calculation_request)
        assert request.calculation_type == "beam_load"
        assert request.parameters["length"] == 6.0
    
    @pytest.mark.unit
    @pytest.mark.calculation_service
    @patch('services.calculation_service.services.ollama_service.OllamaService')
    def test_ollama_integration(self, mock_ollama):
        """Тест интеграции с Ollama"""
        mock_ollama.return_value = Mock()
        mock_ollama.return_value.generate_response = AsyncMock(return_value="Расчет выполнен")
        
        from services.calculation_service.services.ollama_service import OllamaService
        
        service = OllamaService()
        assert service is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
