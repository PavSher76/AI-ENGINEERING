"""
Unit тесты для расширенного Chat Service
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock
import io

class TestEnhancedChatService:
    """Unit тесты для расширенного Chat Service"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_service_health_enhanced(self, client):
        """Тест доступности расширенного Chat Service"""
        try:
            response = await client.get("http://localhost:8003/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "2.0.0"
            assert "features_enabled" in data
            assert data["features_enabled"]["file_upload"] == True
            assert data["features_enabled"]["ocr"] == True
            assert data["features_enabled"]["settings"] == True
            assert data["features_enabled"]["export"] == True
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_get_supported_formats(self, client):
        """Тест получения поддерживаемых форматов файлов"""
        try:
            response = await client.get("http://localhost:8003/files/supported")
            assert response.status_code == 200
            data = response.json()
            assert "supported_formats" in data
            assert "max_file_size" in data
            assert "max_file_size_mb" in data
            assert data["max_file_size_mb"] == 100
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_upload_txt_file(self, client):
        """Тест загрузки TXT файла"""
        try:
            # Создаем тестовый TXT файл
            test_content = "Это тестовый документ для проверки функционала чата с ИИ."
            files = {"file": ("test.txt", test_content, "text/plain")}
            
            response = await client.post("http://localhost:8003/files/upload", files=files)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["filename"] == "test.txt"
            assert data["file_type"] == "text/plain"
            assert "content" in data
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_upload_large_file_rejection(self, client):
        """Тест отклонения слишком большого файла"""
        try:
            # Создаем файл больше 100MB (симулируем)
            large_content = "x" * (101 * 1024 * 1024)  # 101MB
            files = {"file": ("large.txt", large_content, "text/plain")}
            
            response = await client.post("http://localhost:8003/files/upload", files=files)
            assert response.status_code == 413  # Payload Too Large
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_get_llm_settings(self, client):
        """Тест получения настроек LLM"""
        try:
            response = await client.get("http://localhost:8003/settings/llm")
            assert response.status_code == 200
            data = response.json()
            assert "model" in data
            assert "temperature" in data
            assert "max_tokens" in data
            assert "system_prompt" in data
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_update_llm_settings(self, client):
        """Тест обновления настроек LLM"""
        try:
            new_settings = {
                "model": "llama3.1:8b",
                "temperature": 0.8,
                "max_tokens": 1024,
                "system_prompt": "Ты полезный ИИ-ассистент"
            }
            
            response = await client.put(
                "http://localhost:8003/settings/llm",
                json=new_settings
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["settings"]["temperature"] == 0.8
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_get_chat_settings(self, client):
        """Тест получения настроек чата"""
        try:
            response = await client.get("http://localhost:8003/settings/chat")
            assert response.status_code == 200
            data = response.json()
            assert "enable_file_upload" in data
            assert "max_file_size_mb" in data
            assert "enable_ocr" in data
            assert "export_format" in data
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_update_chat_settings(self, client):
        """Тест обновления настроек чата"""
        try:
            new_settings = {
                "enable_file_upload": True,
                "max_file_size_mb": 50,
                "enable_ocr": True,
                "ocr_language": "rus+eng",
                "export_format": "pdf"
            }
            
            response = await client.put(
                "http://localhost:8003/settings/chat",
                json=new_settings
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["settings"]["max_file_size_mb"] == 50
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_get_available_options(self, client):
        """Тест получения доступных опций"""
        try:
            response = await client.get("http://localhost:8003/settings/available")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert "languages" in data
            assert "export_formats" in data
            assert isinstance(data["models"], list)
            assert isinstance(data["languages"], list)
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_chat_with_file_upload(self, client):
        """Тест чата с загрузкой файла"""
        try:
            # Создаем тестовый файл
            test_content = "Тестовый документ для чата"
            files = {"files": ("test.txt", test_content, "text/plain")}
            
            form_data = {
                "message": "Проанализируй этот документ",
                "session_id": "test_session"
            }
            
            response = await client.post(
                "http://localhost:8003/chat",
                data=form_data,
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "response" in data
            assert data["files_processed"] == 1
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_chat_sessions_management(self, client):
        """Тест управления сессиями чата"""
        try:
            # Получаем список сессий
            response = await client.get("http://localhost:8003/chat/sessions")
            assert response.status_code == 200
            data = response.json()
            assert "sessions" in data
            assert "total_sessions" in data
            
            # Создаем новую сессию через чат
            form_data = {
                "message": "Привет!",
                "session_id": "test_session_management"
            }
            
            response = await client.post(
                "http://localhost:8003/chat",
                data=form_data
            )
            assert response.status_code == 200
            
            # Получаем конкретную сессию
            response = await client.get("http://localhost:8003/chat/sessions/test_session_management")
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert "created_at" in data
            
            # Удаляем сессию
            response = await client.delete("http://localhost:8003/chat/sessions/test_session_management")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_export_docx(self, client):
        """Тест экспорта в DOCX"""
        try:
            # Создаем тестовую сессию
            form_data = {
                "message": "Тестовое сообщение для экспорта",
                "session_id": "export_test_session"
            }
            
            response = await client.post(
                "http://localhost:8003/chat",
                data=form_data
            )
            assert response.status_code == 200
            
            # Экспортируем в DOCX
            export_data = {
                "session_id": "export_test_session",
                "filename": "test_export.docx"
            }
            
            response = await client.post(
                "http://localhost:8003/export/docx",
                data=export_data
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_export_pdf(self, client):
        """Тест экспорта в PDF"""
        try:
            # Создаем тестовую сессию
            form_data = {
                "message": "Тестовое сообщение для PDF экспорта",
                "session_id": "pdf_export_test_session"
            }
            
            response = await client.post(
                "http://localhost:8003/chat",
                data=form_data
            )
            assert response.status_code == 200
            
            # Экспортируем в PDF
            export_data = {
                "session_id": "pdf_export_test_session",
                "filename": "test_export.pdf"
            }
            
            response = await client.post(
                "http://localhost:8003/export/pdf",
                data=export_data
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_reset_settings(self, client):
        """Тест сброса настроек к значениям по умолчанию"""
        try:
            response = await client.post("http://localhost:8003/settings/reset")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "settings" in data
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")

class TestFileProcessor:
    """Тесты для FileProcessor"""
    
    @pytest.fixture
    def file_processor(self):
        from services.chat_service.services.file_processor import FileProcessor
        return FileProcessor()
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_process_txt_file(self, file_processor):
        """Тест обработки TXT файла"""
        test_content = "Это тестовый текстовый файл для проверки обработки."
        
        result = await file_processor.process_file(
            test_content.encode('utf-8'),
            "test.txt"
        )
        
        assert result["success"] == True
        assert result["filename"] == "test.txt"
        assert result["file_type"] == "text/plain"
        assert "content" in result
        assert result["content"]["text"] == test_content
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_process_markdown_file(self, file_processor):
        """Тест обработки Markdown файла"""
        test_content = "# Заголовок\n\nЭто **жирный** текст в Markdown."
        
        result = await file_processor.process_file(
            test_content.encode('utf-8'),
            "test.md"
        )
        
        assert result["success"] == True
        assert result["filename"] == "test.md"
        assert result["file_type"] == "text/markdown"
        assert "content" in result
        assert result["content"]["text"] == test_content
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_unsupported_file_type(self, file_processor):
        """Тест неподдерживаемого типа файла"""
        test_content = b"Some binary content"
        
        result = await file_processor.process_file(
            test_content,
            "test.exe"
        )
        
        assert result["success"] == False
        assert "error" in result
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_get_supported_formats(self, file_processor):
        """Тест получения поддерживаемых форматов"""
        formats = file_processor.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_get_max_file_size(self, file_processor):
        """Тест получения максимального размера файла"""
        max_size = file_processor.get_max_file_size()
        assert max_size == 100 * 1024 * 1024  # 100MB

class TestDocumentExporter:
    """Тесты для DocumentExporter"""
    
    @pytest.fixture
    def document_exporter(self):
        from services.chat_service.services.document_exporter import DocumentExporter
        return DocumentExporter()
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_export_to_docx(self, document_exporter):
        """Тест экспорта в DOCX"""
        chat_data = {
            "topic": "Тестовый чат",
            "messages": [
                {
                    "role": "user",
                    "content": "Привет!",
                    "timestamp": "2025-01-01T00:00:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Привет! Как дела?",
                    "timestamp": "2025-01-01T00:01:00Z"
                }
            ],
            "files": [],
            "llm_settings": {
                "model": "llama3.1:8b",
                "temperature": 0.7
            }
        }
        
        docx_bytes = await document_exporter.export_to_docx(chat_data)
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    async def test_export_to_pdf(self, document_exporter):
        """Тест экспорта в PDF"""
        chat_data = {
            "topic": "Тестовый чат",
            "messages": [
                {
                    "role": "user",
                    "content": "Привет!",
                    "timestamp": "2025-01-01T00:00:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Привет! Как дела?",
                    "timestamp": "2025-01-01T00:01:00Z"
                }
            ],
            "files": [],
            "llm_settings": {
                "model": "llama3.1:8b",
                "temperature": 0.7
            }
        }
        
        pdf_bytes = await document_exporter.export_to_pdf(chat_data)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

class TestSettingsService:
    """Тесты для SettingsService"""
    
    @pytest.fixture
    def settings_service(self):
        from services.chat_service.services.settings_service import SettingsService
        return SettingsService("test_settings.json")
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_get_llm_settings(self, settings_service):
        """Тест получения настроек LLM"""
        settings = settings_service.get_llm_settings()
        assert "model" in settings
        assert "temperature" in settings
        assert "max_tokens" in settings
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_update_llm_settings(self, settings_service):
        """Тест обновления настроек LLM"""
        new_settings = {
            "model": "llama3.1:8b",
            "temperature": 0.8,
            "max_tokens": 1024
        }
        
        result = settings_service.update_llm_settings(new_settings)
        assert result["success"] == True
        assert result["settings"]["temperature"] == 0.8
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_get_available_models(self, settings_service):
        """Тест получения доступных моделей"""
        models = settings_service.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "llama3.1:8b" in models
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_get_available_languages(self, settings_service):
        """Тест получения доступных языков"""
        languages = settings_service.get_available_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "rus+eng" in languages
    
    @pytest.mark.unit
    @pytest.mark.chat_service
    def test_validate_settings(self, settings_service):
        """Тест валидации настроек"""
        valid_settings = {
            "llm": {
                "model": "llama3.1:8b",
                "temperature": 0.7,
                "max_tokens": 2048
            }
        }
        
        result = settings_service.validate_settings(valid_settings)
        assert result["valid"] == True
        
        invalid_settings = {
            "llm": {
                "model": "llama3.1:8b",
                "temperature": 5.0,  # Невалидное значение
                "max_tokens": 2048
            }
        }
        
        result = settings_service.validate_settings(invalid_settings)
        assert result["valid"] == False

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
