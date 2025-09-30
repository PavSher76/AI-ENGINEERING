"""
Тесты для модуля выходного контроля исходящей переписки
"""

import pytest
import asyncio
import httpx
import os
from pathlib import Path
from typing import Dict, Any

# Конфигурация тестов
BASE_URL = "http://localhost:8011"
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "test_data"
TEST_FILE = "E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf"

class TestOutgoingControl:
    """Тесты для сервиса выходного контроля"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.fixture
    def test_file_path(self):
        """Путь к тестовому файлу"""
        return TEST_DATA_DIR / TEST_FILE
    
    async def test_service_health(self, client):
        """Тест доступности сервиса"""
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "outgoing-control-service" in data["service"]
    
    async def test_upload_document(self, client, test_file_path):
        """Тест загрузки документа"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            response = await client.post(f"{BASE_URL}/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "filename" in data
        assert data["filename"] == test_file_path.name
        
        return data["document_id"]
    
    async def test_document_analysis(self, client, test_file_path):
        """Тест полного анализа документа"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]
        
        # Запускаем анализ
        analysis_response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": True,
                "check_style": True,
                "check_ethics": True,
                "check_terminology": True,
                "llm_review": True
            }
        )
        
        assert analysis_response.status_code == 200
        data = analysis_response.json()
        
        # Проверяем структуру ответа
        assert "analysis_id" in data
        assert "status" in data
        assert data["status"] in ["pending", "processing", "completed"]
        
        return data["analysis_id"]
    
    async def test_get_analysis_results(self, client, test_file_path):
        """Тест получения результатов анализа"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем и анализируем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        analysis_response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": True,
                "check_style": True,
                "check_ethics": True,
                "check_terminology": True,
                "llm_review": True
            }
        )
        
        analysis_id = analysis_response.json()["analysis_id"]
        
        # Ждем завершения анализа (максимум 2 минуты)
        max_attempts = 24  # 2 минуты с интервалом 5 секунд
        for attempt in range(max_attempts):
            await asyncio.sleep(5)
            
            results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
            assert results_response.status_code == 200
            
            results = results_response.json()
            
            if results["status"] == "completed":
                # Проверяем структуру результатов
                assert "spelling_errors" in results
                assert "style_analysis" in results
                assert "ethics_check" in results
                assert "terminology_check" in results
                assert "llm_review" in results
                assert "final_decision" in results
                
                # Проверяем, что найдены ошибки (файл с грубыми ошибками)
                assert len(results["spelling_errors"]) > 0, "Должны быть найдены орфографические ошибки"
                
                # Проверяем финальное решение
                assert results["final_decision"] in ["approve", "reject", "needs_revision"]
                
                return results
            
            elif results["status"] == "failed":
                pytest.fail(f"Анализ завершился с ошибкой: {results.get('error', 'Неизвестная ошибка')}")
        
        pytest.fail("Анализ не завершился в течение 2 минут")
    
    async def test_spelling_check(self, client, test_file_path):
        """Тест проверки орфографии"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Запускаем только проверку орфографии
        response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": True,
                "check_style": False,
                "check_ethics": False,
                "check_terminology": False,
                "llm_review": False
            }
        )
        
        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]
        
        # Ждем завершения
        await asyncio.sleep(10)
        
        results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
        results = results_response.json()
        
        if results["status"] == "completed":
            # Проверяем, что найдены орфографические ошибки
            assert len(results["spelling_errors"]) > 0
            assert all("error" in error for error in results["spelling_errors"])
            assert all("suggestion" in error for error in results["spelling_errors"])
    
    async def test_style_analysis(self, client, test_file_path):
        """Тест анализа стиля"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Запускаем анализ стиля
        response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": False,
                "check_style": True,
                "check_ethics": False,
                "check_terminology": False,
                "llm_review": False
            }
        )
        
        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]
        
        # Ждем завершения
        await asyncio.sleep(10)
        
        results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
        results = results_response.json()
        
        if results["status"] == "completed":
            # Проверяем структуру анализа стиля
            style_analysis = results["style_analysis"]
            assert "readability_score" in style_analysis
            assert "formality_level" in style_analysis
            assert "tone" in style_analysis
            assert "business_style_score" in style_analysis
            assert "recommendations" in style_analysis
    
    async def test_ethics_check(self, client, test_file_path):
        """Тест проверки этики"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Запускаем проверку этики
        response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": False,
                "check_style": False,
                "check_ethics": True,
                "check_terminology": False,
                "llm_review": False
            }
        )
        
        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]
        
        # Ждем завершения
        await asyncio.sleep(10)
        
        results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
        results = results_response.json()
        
        if results["status"] == "completed":
            # Проверяем структуру проверки этики
            ethics_check = results["ethics_check"]
            assert "discrimination_check" in ethics_check
            assert "harassment_check" in ethics_check
            assert "inappropriate_language" in ethics_check
            assert "confidentiality_check" in ethics_check
            assert "conflict_of_interest" in ethics_check
            assert "overall_score" in ethics_check
    
    async def test_terminology_check(self, client, test_file_path):
        """Тест проверки терминологии"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Запускаем проверку терминологии
        response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": False,
                "check_style": False,
                "check_ethics": False,
                "check_terminology": True,
                "llm_review": False
            }
        )
        
        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]
        
        # Ждем завершения
        await asyncio.sleep(10)
        
        results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
        results = results_response.json()
        
        if results["status"] == "completed":
            # Проверяем структуру проверки терминологии
            terminology_check = results["terminology_check"]
            assert "engineering_terms" in terminology_check
            assert "legal_terms" in terminology_check
            assert "business_terms" in terminology_check
            assert "inconsistencies" in terminology_check
            assert "suggestions" in terminology_check
    
    async def test_llm_review(self, client, test_file_path):
        """Тест LLM обзора"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Запускаем LLM обзор
        response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": False,
                "check_style": False,
                "check_ethics": False,
                "check_terminology": False,
                "llm_review": True
            }
        )
        
        assert response.status_code == 200
        analysis_id = response.json()["analysis_id"]
        
        # Ждем завершения
        await asyncio.sleep(15)  # LLM обзор может занять больше времени
        
        results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
        results = results_response.json()
        
        if results["status"] == "completed":
            # Проверяем структуру LLM обзора
            llm_review = results["llm_review"]
            assert "false_errors_detection" in llm_review
            assert "overall_assessment" in llm_review
            assert "recommendations" in llm_review
            assert "confidence_score" in llm_review
    
    async def test_get_document_list(self, client):
        """Тест получения списка документов"""
        response = await client.get(f"{BASE_URL}/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    async def test_get_analysis_history(self, client):
        """Тест получения истории анализов"""
        response = await client.get(f"{BASE_URL}/analyses")
        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert isinstance(data["analyses"], list)

# Интеграционные тесты
class TestOutgoingControlIntegration:
    """Интеграционные тесты для полного цикла обработки"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=120.0) as client:
            yield client
    
    @pytest.fixture
    def test_file_path(self):
        return TEST_DATA_DIR / TEST_FILE
    
    async def test_full_document_processing_workflow(self, client, test_file_path):
        """Тест полного цикла обработки документа с грубыми ошибками"""
        if not test_file_path.exists():
            pytest.skip(f"Тестовый файл не найден: {test_file_path}")
        
        # 1. Загружаем документ
        with open(test_file_path, "rb") as f:
            files = {"file": (test_file_path.name, f, "application/pdf")}
            upload_response = await client.post(f"{BASE_URL}/upload", files=files)
        
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]
        
        # 2. Запускаем полный анализ
        analysis_response = await client.post(
            f"{BASE_URL}/analyze/{document_id}",
            json={
                "check_spelling": True,
                "check_style": True,
                "check_ethics": True,
                "check_terminology": True,
                "llm_review": True
            }
        )
        
        assert analysis_response.status_code == 200
        analysis_id = analysis_response.json()["analysis_id"]
        
        # 3. Ждем завершения анализа
        max_attempts = 30  # 2.5 минуты
        results = None
        
        for attempt in range(max_attempts):
            await asyncio.sleep(5)
            
            results_response = await client.get(f"{BASE_URL}/analysis/{analysis_id}")
            assert results_response.status_code == 200
            
            results = results_response.json()
            
            if results["status"] == "completed":
                break
            elif results["status"] == "failed":
                pytest.fail(f"Анализ завершился с ошибкой: {results.get('error')}")
        
        assert results is not None, "Анализ не завершился в отведенное время"
        assert results["status"] == "completed"
        
        # 4. Проверяем результаты анализа
        # Документ с грубыми ошибками должен быть отклонен или требовать доработки
        assert results["final_decision"] in ["reject", "needs_revision"]
        
        # Проверяем наличие ошибок
        assert len(results["spelling_errors"]) > 0, "Должны быть найдены орфографические ошибки"
        
        # Проверяем качество стиля (должно быть низким для документа с ошибками)
        style_score = results["style_analysis"]["business_style_score"]
        assert style_score < 80, f"Стиль документа должен быть оценен низко, получен балл: {style_score}"
        
        # Проверяем этику
        ethics_score = results["ethics_check"]["overall_score"]
        assert ethics_score >= 0, "Этический балл должен быть неотрицательным"
        
        # Проверяем терминологию
        assert "terminology_check" in results
        assert "inconsistencies" in results["terminology_check"]
        
        # Проверяем LLM обзор
        assert "llm_review" in results
        assert "overall_assessment" in results["llm_review"]
        
        print(f"\n📊 Результаты анализа документа '{test_file_path.name}':")
        print(f"   📝 Орфографические ошибки: {len(results['spelling_errors'])}")
        print(f"   🎨 Балл стиля: {style_score}")
        print(f"   ⚖️ Этический балл: {ethics_score}")
        print(f"   🤖 Финальное решение: {results['final_decision']}")
        
        return results

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"])
