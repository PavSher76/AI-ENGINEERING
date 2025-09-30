"""
End-to-End тесты для полных рабочих процессов
"""

import pytest
import asyncio
import httpx
import json
from pathlib import Path

class TestE2EWorkflows:
    """E2E тесты для полных рабочих процессов"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            yield client
    
    @pytest.fixture
    def test_document(self):
        """Тестовый документ"""
        return {
            "filename": "test_engineering_document.pdf",
            "content": """
            Техническое задание на проектирование
            
            Объект: Промышленное здание
            Площадь: 1000 м²
            Этажность: 2 этажа
            Материал: Железобетон
            
            Требования:
            1. Соответствие СНиП 2.01.07-85
            2. Сейсмичность: 7 баллов
            3. Пожарная безопасность: II степень огнестойкости
            
            Расчеты:
            - Нагрузки на фундамент: 200 кН/м²
            - Пролет балок: 6 метров
            - Высота этажа: 3.6 метра
            """,
            "metadata": {
                "author": "Инженер-проектировщик",
                "project": "Промышленное здание",
                "document_type": "техническое_задание",
                "created_at": "2025-01-01T00:00:00Z"
            }
        }
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_document_processing_workflow(self, client, test_document):
        """E2E тест: полный цикл обработки документа"""
        try:
            print("\n🔄 E2E Тест: Обработка документа")
            
            # 1. Создание коллекции в RAG
            print("1️⃣ Создание коллекции...")
            collection_response = await client.post(
                "http://localhost:8001/collections",
                json={
                    "name": "e2e-test-collection",
                    "description": "Коллекция для E2E тестирования",
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            )
            assert collection_response.status_code in [200, 201, 409]
            print("✅ Коллекция создана/существует")
            
            # 2. Загрузка документа в RAG
            print("2️⃣ Загрузка документа...")
            document_response = await client.post(
                "http://localhost:8001/documents",
                json=test_document
            )
            assert document_response.status_code in [200, 201]
            document_data = document_response.json()
            document_id = document_data.get("document_id")
            print(f"✅ Документ загружен: {document_id}")
            
            # 3. Поиск документа
            print("3️⃣ Поиск документа...")
            search_response = await client.post(
                "http://localhost:8001/search",
                json={
                    "query": "промышленное здание",
                    "collection_name": "e2e-test-collection",
                    "limit": 5
                }
            )
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert "results" in search_data
            print(f"✅ Найдено результатов: {len(search_data['results'])}")
            
            # 4. Чат с контекстом документа
            print("4️⃣ Чат с контекстом...")
            chat_response = await client.post(
                "http://localhost:8003/chat/send",
                json={
                    "message": "Расскажи о требованиях к промышленному зданию",
                    "user_id": "e2e-test-user",
                    "session_id": "e2e-test-session",
                    "context": {
                        "project_id": "e2e-test-project",
                        "collection_name": "e2e-test-collection"
                    }
                }
            )
            assert chat_response.status_code in [200, 201]
            chat_data = chat_response.json()
            assert "response" in chat_data
            print("✅ Чат с контекстом работает")
            
            print("🎉 E2E тест обработки документа завершен успешно!")
            
        except httpx.ConnectError as e:
            pytest.skip(f"Сервисы недоступны: {e}")
        except Exception as e:
            pytest.fail(f"E2E тест провален: {e}")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_ai_calculation_workflow(self, client):
        """E2E тест: ИИ расчеты"""
        try:
            print("\n🔄 E2E Тест: ИИ расчеты")
            
            # 1. Получение доступных моделей
            print("1️⃣ Получение моделей...")
            models_response = await client.get("http://localhost:8012/models")
            assert models_response.status_code == 200
            models = models_response.json()
            assert len(models) > 0
            model_name = models[0]["name"]
            print(f"✅ Используем модель: {model_name}")
            
            # 2. Инженерный расчет через ИИ
            print("2️⃣ Выполнение расчета...")
            calculation_response = await client.post(
                "http://localhost:8006/calculate",
                json={
                    "calculation_type": "beam_load",
                    "parameters": {
                        "length": 6.0,
                        "width": 0.3,
                        "height": 0.5,
                        "material": "concrete",
                        "load": 200
                    },
                    "model": model_name
                }
            )
            assert calculation_response.status_code in [200, 201]
            calculation_data = calculation_response.json()
            assert "result" in calculation_data
            print("✅ Расчет выполнен")
            
            # 3. Валидация результата
            print("3️⃣ Валидация результата...")
            validation_response = await client.post(
                "http://localhost:8007/validate",
                json={
                    "data": calculation_data["result"],
                    "validation_type": "engineering_calculation",
                    "standards": ["SNIP", "GOST"]
                }
            )
            assert validation_response.status_code == 200
            validation_data = validation_response.json()
            assert "is_valid" in validation_data
            print(f"✅ Валидация: {'пройдена' if validation_data['is_valid'] else 'не пройдена'}")
            
            print("🎉 E2E тест ИИ расчетов завершен успешно!")
            
        except httpx.ConnectError as e:
            pytest.skip(f"Сервисы недоступны: {e}")
        except Exception as e:
            pytest.fail(f"E2E тест провален: {e}")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_document_quality_control_workflow(self, client):
        """E2E тест: контроль качества документов"""
        try:
            print("\n🔄 E2E Тест: Контроль качества документов")
            
            # 1. Загрузка документа для проверки
            print("1️⃣ Загрузка документа...")
            test_text = """
            Техническое задание на проектирование промышленного здания.
            
            Объект: Промышленное здание
            Площадь: 1000 м²
            Этажность: 2 этажа
            Материал: Железобетон
            
            Требования:
            1. Соответствие СНиП 2.01.07-85
            2. Сейсмичность: 7 баллов
            3. Пожарная безопасность: II степень огнестойкости
            """
            
            # 2. Проверка орфографии
            print("2️⃣ Проверка орфографии...")
            spell_response = await client.post(
                "http://localhost:8011/spell-check",
                json={"text": test_text}
            )
            assert spell_response.status_code == 200
            spell_data = spell_response.json()
            print(f"✅ Найдено ошибок: {spell_data.get('errors_found', 0)}")
            
            # 3. Анализ стиля
            print("3️⃣ Анализ стиля...")
            style_response = await client.post(
                "http://localhost:8011/style-analysis",
                json={
                    "text": test_text,
                    "document_type": "technical"
                }
            )
            assert style_response.status_code == 200
            style_data = style_response.json()
            print(f"✅ Балл стиля: {style_data.get('business_style_score', 0)}")
            
            # 4. Проверка этики
            print("4️⃣ Проверка этики...")
            ethics_response = await client.post(
                "http://localhost:8011/ethics-check",
                json={"text": test_text}
            )
            assert ethics_response.status_code == 200
            ethics_data = ethics_response.json()
            print(f"✅ Этический балл: {ethics_data.get('ethics_score', 0)}")
            
            # 5. Проверка терминологии
            print("5️⃣ Проверка терминологии...")
            term_response = await client.post(
                "http://localhost:8011/terminology-check",
                json={
                    "text": test_text,
                    "domain": "engineering"
                }
            )
            assert term_response.status_code == 200
            term_data = term_response.json()
            print(f"✅ Точность терминологии: {term_data.get('accuracy_score', 0)}%")
            
            print("🎉 E2E тест контроля качества завершен успешно!")
            
        except httpx.ConnectError as e:
            pytest.skip(f"Сервисы недоступны: {e}")
        except Exception as e:
            pytest.fail(f"E2E тест провален: {e}")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_consultation_workflow(self, client):
        """E2E тест: консультации по НТД"""
        try:
            print("\n🔄 E2E Тест: Консультации по НТД")
            
            # 1. Поиск НТД
            print("1️⃣ Поиск НТД...")
            ntd_search_response = await client.post(
                "http://localhost:8004/consultation/search",
                json={
                    "query": "СНиП 2.01.07-85",
                    "document_type": "normative",
                    "category": "loads"
                }
            )
            assert ntd_search_response.status_code == 200
            ntd_data = ntd_search_response.json()
            print(f"✅ Найдено НТД: {len(ntd_data.get('results', []))}")
            
            # 2. Получение консультации
            print("2️⃣ Получение консультации...")
            consultation_response = await client.post(
                "http://localhost:8004/consultation/ask",
                json={
                    "question": "Какие нагрузки учитываются при проектировании фундаментов?",
                    "context": {
                        "project_type": "industrial",
                        "region": "seismic_zone"
                    }
                }
            )
            assert consultation_response.status_code == 200
            consultation_data = consultation_response.json()
            assert "answer" in consultation_data
            print("✅ Консультация получена")
            
            # 3. Сохранение в архив
            print("3️⃣ Сохранение в архив...")
            archive_response = await client.post(
                "http://localhost:8005/archive/save",
                json={
                    "consultation_id": consultation_data.get("consultation_id"),
                    "category": "ntd_consultation",
                    "tags": ["СНиП", "нагрузки", "фундаменты"]
                }
            )
            assert archive_response.status_code in [200, 201]
            print("✅ Консультация сохранена в архив")
            
            print("🎉 E2E тест консультаций завершен успешно!")
            
        except httpx.ConnectError as e:
            pytest.skip(f"Сервисы недоступны: {e}")
        except Exception as e:
            pytest.fail(f"E2E тест провален: {e}")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_analytics_workflow(self, client):
        """E2E тест: аналитика и отчеты"""
        try:
            print("\n🔄 E2E Тест: Аналитика и отчеты")
            
            # 1. Сбор метрик
            print("1️⃣ Сбор метрик...")
            metrics_response = await client.get("http://localhost:8009/analytics/metrics")
            assert metrics_response.status_code == 200
            metrics_data = metrics_response.json()
            print("✅ Метрики собраны")
            
            # 2. Генерация отчета
            print("2️⃣ Генерация отчета...")
            report_response = await client.post(
                "http://localhost:8009/analytics/reports/generate",
                json={
                    "report_type": "system_performance",
                    "period": "last_24_hours",
                    "format": "json"
                }
            )
            assert report_response.status_code in [200, 201]
            report_data = report_response.json()
            assert "report_id" in report_data
            print("✅ Отчет сгенерирован")
            
            # 3. Получение отчета
            print("3️⃣ Получение отчета...")
            get_report_response = await client.get(
                f"http://localhost:8009/analytics/reports/{report_data['report_id']}"
            )
            assert get_report_response.status_code == 200
            print("✅ Отчет получен")
            
            print("🎉 E2E тест аналитики завершен успешно!")
            
        except httpx.ConnectError as e:
            pytest.skip(f"Сервисы недоступны: {e}")
        except Exception as e:
            pytest.fail(f"E2E тест провален: {e}")

class TestE2EPerformance:
    """E2E тесты производительности"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_concurrent_requests(self, client):
        """Тест параллельных запросов"""
        import asyncio
        import time
        
        print("\n🔄 E2E Тест: Параллельные запросы")
        
        # Создаем список задач для параллельного выполнения
        tasks = []
        
        # 10 параллельных запросов к разным сервисам
        for i in range(10):
            if i % 3 == 0:
                task = client.get("http://localhost:8001/health")
            elif i % 3 == 1:
                task = client.get("http://localhost:8003/health")
            else:
                task = client.get("http://localhost:8012/health")
            tasks.append(task)
        
        # Выполняем все запросы параллельно
        start_time = time.time()
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Анализируем результаты
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            total_time = end_time - start_time
            
            print(f"✅ Успешных запросов: {successful}/{len(tasks)}")
            print(f"✅ Общее время: {total_time:.2f} секунд")
            print(f"✅ Среднее время на запрос: {total_time/len(tasks):.2f} секунд")
            
            # Проверяем, что хотя бы 80% запросов успешны
            success_rate = successful / len(tasks)
            assert success_rate >= 0.8, f"Успешность {success_rate:.1%} ниже требуемых 80%"
            
        except Exception as e:
            pytest.fail(f"Тест параллельных запросов провален: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
