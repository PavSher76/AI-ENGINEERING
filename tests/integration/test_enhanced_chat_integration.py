"""
Интеграционные тесты для расширенного Chat Service
"""

import pytest
import asyncio
import httpx
import os
import tempfile
from pathlib import Path

class TestEnhancedChatIntegration:
    """Интеграционные тесты для расширенного Chat Service"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.fixture
    def sample_files(self):
        """Создает тестовые файлы для загрузки"""
        files = {}
        
        # TXT файл
        txt_content = "Это тестовый текстовый документ для проверки функционала чата с ИИ."
        files['txt'] = ("test.txt", txt_content, "text/plain")
        
        # Markdown файл
        md_content = """# Тестовый документ

Это **жирный** текст и *курсив*.

## Список
- Пункт 1
- Пункт 2
- Пункт 3

```python
print("Hello, World!")
```
"""
        files['md'] = ("test.md", md_content, "text/markdown")
        
        return files
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_full_chat_workflow_with_files(self, client, sample_files):
        """Тест полного цикла работы чата с файлами"""
        try:
            session_id = f"integration_test_{int(asyncio.get_event_loop().time())}"
            
            # 1. Проверяем доступность сервиса
            response = await client.get("http://localhost:8003/health")
            assert response.status_code == 200
            
            # 2. Загружаем файл
            response = await client.post(
                "http://localhost:8003/files/upload",
                files={"file": sample_files['txt']}
            )
            assert response.status_code == 200
            file_result = response.json()
            assert file_result["success"] == True
            
            # 3. Отправляем сообщение с файлом
            form_data = {
                "message": "Проанализируй этот документ и расскажи, что в нем содержится",
                "session_id": session_id
            }
            
            response = await client.post(
                "http://localhost:8003/chat",
                data=form_data,
                files={"files": sample_files['txt']}
            )
            assert response.status_code == 200
            chat_result = response.json()
            assert chat_result["success"] == True
            assert chat_result["files_processed"] == 1
            
            # 4. Проверяем, что сессия создана
            response = await client.get(f"http://localhost:8003/chat/sessions/{session_id}")
            assert response.status_code == 200
            session_data = response.json()
            assert len(session_data["messages"]) == 2  # Пользователь + ИИ
            
            # 5. Экспортируем чат в DOCX
            export_data = {
                "session_id": session_id,
                "filename": f"integration_test_{session_id}.docx"
            }
            
            response = await client.post(
                "http://localhost:8003/export/docx",
                data=export_data
            )
            assert response.status_code == 200
            assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
            
            # 6. Экспортируем чат в PDF
            export_data = {
                "session_id": session_id,
                "filename": f"integration_test_{session_id}.pdf"
            }
            
            response = await client.post(
                "http://localhost:8003/export/pdf",
                data=export_data
            )
            assert response.status_code == 200
            assert "application/pdf" in response.headers["content-type"]
            
            print("✅ Полный цикл работы чата с файлами прошел успешно")
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_settings_management_workflow(self, client):
        """Тест полного цикла управления настройками"""
        try:
            # 1. Получаем текущие настройки
            response = await client.get("http://localhost:8003/settings")
            assert response.status_code == 200
            original_settings = response.json()
            
            # 2. Обновляем настройки LLM
            new_llm_settings = {
                "model": "llama3.1:8b",
                "temperature": 0.9,
                "max_tokens": 1024,
                "system_prompt": "Ты полезный ИИ-ассистент для тестирования"
            }
            
            response = await client.put(
                "http://localhost:8003/settings/llm",
                json=new_llm_settings
            )
            assert response.status_code == 200
            result = response.json()
            assert result["success"] == True
            
            # 3. Обновляем настройки чата
            new_chat_settings = {
                "enable_file_upload": True,
                "max_file_size_mb": 50,
                "enable_ocr": True,
                "ocr_language": "rus+eng",
                "export_format": "pdf"
            }
            
            response = await client.put(
                "http://localhost:8003/settings/chat",
                json=new_chat_settings
            )
            assert response.status_code == 200
            result = response.json()
            assert result["success"] == True
            
            # 4. Проверяем, что настройки сохранились
            response = await client.get("http://localhost:8003/settings/llm")
            assert response.status_code == 200
            llm_settings = response.json()
            assert llm_settings["temperature"] == 0.9
            assert llm_settings["system_prompt"] == "Ты полезный ИИ-ассистент для тестирования"
            
            response = await client.get("http://localhost:8003/settings/chat")
            assert response.status_code == 200
            chat_settings = response.json()
            assert chat_settings["max_file_size_mb"] == 50
            assert chat_settings["export_format"] == "pdf"
            
            # 5. Сбрасываем настройки
            response = await client.post("http://localhost:8003/settings/reset")
            assert response.status_code == 200
            result = response.json()
            assert result["success"] == True
            
            print("✅ Полный цикл управления настройками прошел успешно")
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_multiple_file_types_processing(self, client):
        """Тест обработки различных типов файлов"""
        try:
            session_id = f"multi_file_test_{int(asyncio.get_event_loop().time())}"
            
            # Создаем файлы разных типов
            files_to_test = [
                ("test.txt", "Простой текстовый файл", "text/plain"),
                ("test.md", "# Markdown файл\n\nС **форматированием**", "text/markdown")
            ]
            
            processed_files = []
            
            # Загружаем и обрабатываем каждый файл
            for filename, content, content_type in files_to_test:
                response = await client.post(
                    "http://localhost:8003/files/upload",
                    files={"file": (filename, content, content_type)}
                )
                assert response.status_code == 200
                result = response.json()
                assert result["success"] == True
                processed_files.append(result)
            
            # Отправляем сообщение с несколькими файлами
            form_data = {
                "message": "Проанализируй все прикрепленные файлы",
                "session_id": session_id
            }
            
            files_data = []
            for filename, content, content_type in files_to_test:
                files_data.append(("files", (filename, content, content_type)))
            
            response = await client.post(
                "http://localhost:8003/chat",
                data=form_data,
                files=files_data
            )
            assert response.status_code == 200
            chat_result = response.json()
            assert chat_result["success"] == True
            assert chat_result["files_processed"] == len(files_to_test)
            
            print("✅ Обработка различных типов файлов прошла успешно")
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_chat_session_persistence(self, client):
        """Тест сохранения и восстановления сессий чата"""
        try:
            session_id = f"persistence_test_{int(asyncio.get_event_loop().time())}"
            
            # 1. Создаем сессию с несколькими сообщениями
            messages = [
                "Привет! Как дела?",
                "Расскажи мне что-нибудь интересное",
                "Спасибо за информацию!"
            ]
            
            for i, message in enumerate(messages):
                form_data = {
                    "message": message,
                    "session_id": session_id
                }
                
                response = await client.post(
                    "http://localhost:8003/chat",
                    data=form_data
                )
                assert response.status_code == 200
                result = response.json()
                assert result["success"] == True
            
            # 2. Проверяем, что сессия сохранилась
            response = await client.get(f"http://localhost:8003/chat/sessions/{session_id}")
            assert response.status_code == 200
            session_data = response.json()
            assert len(session_data["messages"]) == len(messages) * 2  # Пользователь + ИИ для каждого сообщения
            
            # 3. Проверяем список всех сессий
            response = await client.get("http://localhost:8003/chat/sessions")
            assert response.status_code == 200
            sessions_data = response.json()
            assert session_id in sessions_data["sessions"]
            
            # 4. Экспортируем сессию
            export_data = {
                "session_id": session_id,
                "filename": f"persistence_test_{session_id}.docx"
            }
            
            response = await client.post(
                "http://localhost:8003/export/docx",
                data=export_data
            )
            assert response.status_code == 200
            
            # 5. Удаляем сессию
            response = await client.delete(f"http://localhost:8003/chat/sessions/{session_id}")
            assert response.status_code == 200
            result = response.json()
            assert result["success"] == True
            
            # 6. Проверяем, что сессия удалена
            response = await client.get(f"http://localhost:8003/chat/sessions/{session_id}")
            assert response.status_code == 404
            
            print("✅ Тест сохранения и восстановления сессий прошел успешно")
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")
    
    @pytest.mark.integration
    @pytest.mark.chat_service
    @pytest.mark.slow
    async def test_error_handling_and_validation(self, client):
        """Тест обработки ошибок и валидации"""
        try:
            # 1. Тест невалидных настроек LLM
            invalid_llm_settings = {
                "model": "llama3.1:8b",
                "temperature": 5.0,  # Невалидное значение
                "max_tokens": -100   # Невалидное значение
            }
            
            response = await client.put(
                "http://localhost:8003/settings/llm",
                json=invalid_llm_settings
            )
            # Должен вернуть ошибку валидации
            assert response.status_code in [400, 422]
            
            # 2. Тест невалидных настроек чата
            invalid_chat_settings = {
                "max_file_size_mb": -10,  # Невалидное значение
                "export_format": "invalid_format"  # Невалидный формат
            }
            
            response = await client.put(
                "http://localhost:8003/settings/chat",
                json=invalid_chat_settings
            )
            # Должен вернуть ошибку валидации
            assert response.status_code in [400, 422]
            
            # 3. Тест экспорта несуществующей сессии
            export_data = {
                "session_id": "nonexistent_session",
                "filename": "test.docx"
            }
            
            response = await client.post(
                "http://localhost:8003/export/docx",
                data=export_data
            )
            assert response.status_code == 404
            
            # 4. Тест получения несуществующей сессии
            response = await client.get("http://localhost:8003/chat/sessions/nonexistent_session")
            assert response.status_code == 404
            
            print("✅ Тест обработки ошибок и валидации прошел успешно")
            
        except httpx.ConnectError:
            pytest.skip("Chat Service не запущен")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
