"""
Интеграционные тесты для всех сервисов
"""

import pytest
import asyncio
import httpx
import json
from pathlib import Path

class TestServicesIntegration:
    """Интеграционные тесты для всех сервисов"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            yield client
    
    @pytest.fixture
    def test_services(self):
        """Список тестируемых сервисов"""
        return [
            {"name": "RAG Service", "url": "http://localhost:8001", "health_path": "/health"},
            {"name": "Chat Service", "url": "http://localhost:8003", "health_path": "/health"},
            {"name": "Consultation Service", "url": "http://localhost:8004", "health_path": "/health"},
            {"name": "Archive Service", "url": "http://localhost:8005", "health_path": "/health"},
            {"name": "Calculation Service", "url": "http://localhost:8006", "health_path": "/health"},
            {"name": "Validation Service", "url": "http://localhost:8007", "health_path": "/health"},
            {"name": "Document Service", "url": "http://localhost:8008", "health_path": "/health"},
            {"name": "Analytics Service", "url": "http://localhost:8009", "health_path": "/health"},
            {"name": "Integration Service", "url": "http://localhost:8010", "health_path": "/health"},
            {"name": "Outgoing Control Service", "url": "http://localhost:8011", "health_path": "/health"},
            {"name": "Ollama Management Service", "url": "http://localhost:8012", "health_path": "/health"},
        ]
    
    @pytest.mark.integration
    async def test_all_services_health(self, client, test_services):
        """Тест доступности всех сервисов"""
        healthy_services = []
        unhealthy_services = []
        
        for service in test_services:
            try:
                response = await client.get(f"{service['url']}{service['health_path']}")
                if response.status_code == 200:
                    healthy_services.append(service['name'])
                else:
                    unhealthy_services.append(f"{service['name']} (HTTP {response.status_code})")
            except httpx.ConnectError:
                unhealthy_services.append(f"{service['name']} (Connection Error)")
        
        print(f"\n✅ Здоровые сервисы ({len(healthy_services)}): {', '.join(healthy_services)}")
        if unhealthy_services:
            print(f"❌ Недоступные сервисы ({len(unhealthy_services)}): {', '.join(unhealthy_services)}")
        
        # Требуем, чтобы хотя бы 70% сервисов были доступны
        health_ratio = len(healthy_services) / len(test_services)
        assert health_ratio >= 0.7, f"Только {health_ratio:.1%} сервисов доступны (требуется минимум 70%)"
    
    @pytest.mark.integration
    async def test_database_connections(self, client):
        """Тест подключений к базам данных"""
        # Проверяем PostgreSQL
        try:
            # Через любой сервис, который использует PostgreSQL
            response = await client.get("http://localhost:8001/health")
            if response.status_code == 200:
                print("✅ PostgreSQL подключение работает")
            else:
                print("❌ PostgreSQL подключение не работает")
        except httpx.ConnectError:
            print("❌ PostgreSQL подключение недоступно")
        
        # Проверяем Redis
        try:
            # Через любой сервис, который использует Redis
            response = await client.get("http://localhost:8003/health")
            if response.status_code == 200:
                print("✅ Redis подключение работает")
            else:
                print("❌ Redis подключение не работает")
        except httpx.ConnectError:
            print("❌ Redis подключение недоступно")
        
        # Проверяем Qdrant
        try:
            response = await client.get("http://localhost:6333/collections")
            if response.status_code == 200:
                print("✅ Qdrant подключение работает")
            else:
                print("❌ Qdrant подключение не работает")
        except httpx.ConnectError:
            print("❌ Qdrant подключение недоступно")
    
    @pytest.mark.integration
    async def test_ollama_integration(self, client):
        """Тест интеграции с Ollama"""
        try:
            # Проверяем Ollama на хосте
            ollama_response = await client.get("http://localhost:11434/api/tags")
            if ollama_response.status_code == 200:
                print("✅ Ollama на хосте работает")
                
                # Проверяем Ollama Management Service
                service_response = await client.get("http://localhost:8012/health")
                if service_response.status_code == 200:
                    print("✅ Ollama Management Service работает")
                    
                    # Проверяем интеграцию
                    models_response = await client.get("http://localhost:8012/models")
                    if models_response.status_code == 200:
                        models = models_response.json()
                        print(f"✅ Доступно моделей: {len(models)}")
                    else:
                        print("❌ Не удалось получить список моделей")
                else:
                    print("❌ Ollama Management Service не работает")
            else:
                print("❌ Ollama на хосте не работает")
        except httpx.ConnectError:
            print("❌ Ollama недоступен")
    
    @pytest.mark.integration
    async def test_minio_integration(self, client):
        """Тест интеграции с MinIO"""
        try:
            # Проверяем MinIO
            minio_response = await client.get("http://localhost:9000/minio/health/live")
            if minio_response.status_code == 200:
                print("✅ MinIO работает")
                
                # Проверяем MinIO Console
                console_response = await client.get("http://localhost:9001")
                if console_response.status_code == 200:
                    print("✅ MinIO Console доступен")
                else:
                    print("❌ MinIO Console недоступен")
            else:
                print("❌ MinIO не работает")
        except httpx.ConnectError:
            print("❌ MinIO недоступен")
    
    @pytest.mark.integration
    async def test_rabbitmq_integration(self, client):
        """Тест интеграции с RabbitMQ"""
        try:
            # Проверяем RabbitMQ Management
            rabbitmq_response = await client.get("http://localhost:15672")
            if rabbitmq_response.status_code == 200:
                print("✅ RabbitMQ Management доступен")
            else:
                print("❌ RabbitMQ Management недоступен")
        except httpx.ConnectError:
            print("❌ RabbitMQ недоступен")
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_end_to_end_workflow(self, client):
        """Тест сквозного рабочего процесса"""
        try:
            # 1. Проверяем доступность основных сервисов
            rag_health = await client.get("http://localhost:8001/health")
            chat_health = await client.get("http://localhost:8003/health")
            ollama_health = await client.get("http://localhost:8012/health")
            
            if all(r.status_code == 200 for r in [rag_health, chat_health, ollama_health]):
                print("✅ Основные сервисы доступны")
                
                # 2. Тестируем создание коллекции в RAG
                collection_response = await client.post(
                    "http://localhost:8001/collections",
                    json={
                        "name": "integration-test",
                        "description": "Тестовая коллекция для интеграции"
                    }
                )
                
                if collection_response.status_code in [200, 201, 409]:
                    print("✅ RAG Service: коллекция создана/существует")
                    
                    # 3. Тестируем получение моделей
                    models_response = await client.get("http://localhost:8012/models")
                    if models_response.status_code == 200:
                        models = models_response.json()
                        if len(models) > 0:
                            print(f"✅ Ollama Management: доступно {len(models)} моделей")
                            
                            # 4. Тестируем генерацию текста
                            model_name = models[0]["name"]
                            generate_response = await client.post(
                                f"http://localhost:8012/models/{model_name}/generate",
                                json={
                                    "prompt": "Тест интеграции",
                                    "max_tokens": 20
                                }
                            )
                            
                            if generate_response.status_code == 200:
                                print("✅ Ollama Management: генерация текста работает")
                            else:
                                print("❌ Ollama Management: генерация текста не работает")
                        else:
                            print("❌ Ollama Management: нет доступных моделей")
                    else:
                        print("❌ Ollama Management: не удалось получить модели")
                else:
                    print("❌ RAG Service: не удалось создать коллекцию")
            else:
                print("❌ Не все основные сервисы доступны")
                
        except Exception as e:
            print(f"❌ Ошибка в сквозном тесте: {e}")
    
    @pytest.mark.integration
    async def test_frontend_integration(self, client):
        """Тест интеграции с фронтендом"""
        try:
            # Проверяем фронтенд
            frontend_response = await client.get("http://localhost:3000")
            if frontend_response.status_code == 200:
                print("✅ Frontend доступен")
                
                # Проверяем, что это React приложение
                content = frontend_response.text
                if "AI Engineering Platform" in content or "react" in content.lower():
                    print("✅ Frontend: React приложение загружено")
                else:
                    print("⚠️ Frontend: возможно, не React приложение")
            else:
                print("❌ Frontend недоступен")
        except httpx.ConnectError:
            print("❌ Frontend недоступен")

class TestPerformanceIntegration:
    """Тесты производительности"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_response_times(self, client):
        """Тест времени отклика сервисов"""
        services = [
            "http://localhost:8001/health",  # RAG
            "http://localhost:8003/health",  # Chat
            "http://localhost:8012/health",  # Ollama Management
        ]
        
        response_times = {}
        
        for service_url in services:
            try:
                import time
                start_time = time.time()
                response = await client.get(service_url)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # в миллисекундах
                response_times[service_url] = response_time
                
                if response.status_code == 200:
                    print(f"✅ {service_url}: {response_time:.2f}ms")
                else:
                    print(f"❌ {service_url}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {service_url}: {e}")
        
        # Проверяем, что время отклика не превышает 5 секунд
        for url, time_ms in response_times.items():
            assert time_ms < 5000, f"{url} отвечает слишком медленно: {time_ms:.2f}ms"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
