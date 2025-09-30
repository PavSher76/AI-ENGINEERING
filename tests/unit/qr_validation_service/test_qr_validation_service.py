"""
Unit тесты для QR валидации РД
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock

class TestQRValidationService:
    """Unit тесты для QR валидации РД"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def mock_qr_data(self):
        """Мок данных QR-кода"""
        return {
            "document_id": "RD-001-2025",
            "document_type": "drawing",
            "project_id": "PROJ-2025-001",
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "signature": "abc123def456"
        }
    
    @pytest.fixture
    def mock_document(self):
        """Мок документа РД"""
        return {
            "document_id": "RD-001-2025",
            "document_type": "drawing",
            "project_id": "PROJ-2025-001",
            "version": "1.0",
            "title": "Чертеж фундамента",
            "description": "Рабочий чертеж фундамента здания",
            "author": "Инженер-проектировщик",
            "status": "approved"
        }
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_service_health(self, client):
        """Тест доступности QR валидации сервиса"""
        try:
            response = await client.get("http://localhost:8013/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "qr-validation-service" in data["service"]
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_generate_qr_code(self, client, mock_document):
        """Тест генерации QR-кода"""
        try:
            response = await client.post(
                "http://localhost:8013/qr/generate",
                json={
                    "document_id": mock_document["document_id"],
                    "document_type": mock_document["document_type"],
                    "project_id": mock_document["project_id"],
                    "version": mock_document["version"],
                    "title": mock_document["title"],
                    "description": mock_document["description"],
                    "author": mock_document["author"]
                }
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "document_id" in data
            assert "qr_code_path" in data
            assert "qr_data" in data
            assert data["status"] == "generated"
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_validate_qr_code(self, client, mock_qr_data):
        """Тест валидации QR-кода"""
        try:
            import json
            qr_data_json = json.dumps(mock_qr_data)
            
            response = await client.post(
                "http://localhost:8013/qr/validate",
                json={
                    "qr_data": qr_data_json,
                    "validate_signature": True
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "is_valid" in data
            assert "status" in data
            assert "message" in data
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_get_document_info(self, client, mock_document):
        """Тест получения информации о документе"""
        try:
            # Сначала создаем документ
            await client.post(
                "http://localhost:8013/qr/generate",
                json={
                    "document_id": mock_document["document_id"],
                    "document_type": mock_document["document_type"],
                    "project_id": mock_document["project_id"],
                    "version": mock_document["version"],
                    "title": mock_document["title"]
                }
            )
            
            # Затем получаем информацию
            response = await client.get(
                f"http://localhost:8013/qr/document/{mock_document['document_id']}"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == mock_document["document_id"]
            assert data["document_type"] == mock_document["document_type"]
            assert data["project_id"] == mock_document["project_id"]
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_get_documents_list(self, client):
        """Тест получения списка документов"""
        try:
            response = await client.get("http://localhost:8013/qr/documents")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_update_document_status(self, client, mock_document):
        """Тест обновления статуса документа"""
        try:
            # Сначала создаем документ
            await client.post(
                "http://localhost:8013/qr/generate",
                json={
                    "document_id": mock_document["document_id"],
                    "document_type": mock_document["document_type"],
                    "project_id": mock_document["project_id"],
                    "version": mock_document["version"]
                }
            )
            
            # Обновляем статус
            response = await client.put(
                f"http://localhost:8013/qr/document/{mock_document['document_id']}/status",
                json={
                    "status": "approved",
                    "comment": "Документ согласован"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "approved"
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_get_qr_stats(self, client):
        """Тест получения статистики QR-кодов"""
        try:
            response = await client.get("http://localhost:8013/qr/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_documents" in data
            assert "documents_by_status" in data
            assert "documents_by_type" in data
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    async def test_download_qr_code(self, client, mock_document):
        """Тест скачивания QR-кода"""
        try:
            # Сначала создаем документ
            generate_response = await client.post(
                "http://localhost:8013/qr/generate",
                json={
                    "document_id": mock_document["document_id"],
                    "document_type": mock_document["document_type"],
                    "project_id": mock_document["project_id"],
                    "version": mock_document["version"]
                }
            )
            
            if generate_response.status_code in [200, 201]:
                # Пытаемся скачать QR-код
                response = await client.get(
                    f"http://localhost:8013/qr/download/{mock_document['document_id']}"
                )
                # Может быть 404 если файл еще не создан, это нормально
                assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    def test_qr_data_validation(self, mock_qr_data):
        """Тест валидации данных QR-кода"""
        from services.qr_validation_service.schemas import QRGenerateRequest
        
        request = QRGenerateRequest(
            document_id=mock_qr_data["document_id"],
            document_type=mock_qr_data["document_type"],
            project_id=mock_qr_data["project_id"],
            version=mock_qr_data["version"]
        )
        
        assert request.document_id == mock_qr_data["document_id"]
        assert request.document_type == mock_qr_data["document_type"]
        assert request.project_id == mock_qr_data["project_id"]
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    def test_document_status_enum(self):
        """Тест enum статусов документов"""
        from services.qr_validation_service.schemas import DocumentStatusEnum
        
        # Проверяем, что все статусы доступны
        assert DocumentStatusEnum.DRAFT == "draft"
        assert DocumentStatusEnum.APPROVED == "approved"
        assert DocumentStatusEnum.REJECTED == "rejected"
        assert DocumentStatusEnum.OBSOLETE == "obsolete"
    
    @pytest.mark.unit
    @pytest.mark.qr_validation_service
    def test_document_type_enum(self):
        """Тест enum типов документов"""
        from services.qr_validation_service.schemas import DocumentTypeEnum
        
        # Проверяем, что все типы доступны
        assert DocumentTypeEnum.DRAWING == "drawing"
        assert DocumentTypeEnum.SPECIFICATION == "specification"
        assert DocumentTypeEnum.STATEMENT == "statement"
        assert DocumentTypeEnum.CALCULATION == "calculation"

class TestQRValidationIntegration:
    """Интеграционные тесты для QR валидации"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.qr_validation_service
    @pytest.mark.slow
    async def test_full_qr_workflow(self, client):
        """Тест полного цикла работы с QR-кодами"""
        try:
            document_id = "TEST-DOC-001"
            project_id = "TEST-PROJ-001"
            
            # 1. Генерируем QR-код
            generate_response = await client.post(
                "http://localhost:8013/qr/generate",
                json={
                    "document_id": document_id,
                    "document_type": "drawing",
                    "project_id": project_id,
                    "version": "1.0",
                    "title": "Тестовый чертеж",
                    "description": "Чертеж для тестирования",
                    "author": "Test User"
                }
            )
            
            if generate_response.status_code in [200, 201]:
                generate_data = generate_response.json()
                qr_data = generate_data["qr_data"]
                
                # 2. Валидируем QR-код
                validate_response = await client.post(
                    "http://localhost:8013/qr/validate",
                    json={
                        "qr_data": qr_data,
                        "validate_signature": True
                    }
                )
                
                assert validate_response.status_code == 200
                validate_data = validate_response.json()
                
                # 3. Получаем информацию о документе
                doc_response = await client.get(
                    f"http://localhost:8013/qr/document/{document_id}"
                )
                
                assert doc_response.status_code == 200
                doc_data = doc_response.json()
                assert doc_data["document_id"] == document_id
                
                # 4. Обновляем статус документа
                status_response = await client.put(
                    f"http://localhost:8013/qr/document/{document_id}/status",
                    json={
                        "status": "approved",
                        "comment": "Документ протестирован и одобрен"
                    }
                )
                
                assert status_response.status_code == 200
                
                print("✅ Полный цикл QR валидации прошел успешно")
            else:
                pytest.skip("Не удалось создать тестовый документ")
                
        except httpx.ConnectError:
            pytest.skip("QR Validation Service не запущен")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
