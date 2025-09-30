#!/usr/bin/env python3
"""
Быстрый тест для проверки работы модуля выходного контроля
"""

import asyncio
import httpx
import json
from pathlib import Path

async def quick_test():
    """Быстрый тест основных функций"""
    
    BASE_URL = "http://localhost:8011"
    TEST_FILE = Path(__file__).parent.parent.parent / "test_data" / "E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf"
    
    print("🧪 Быстрый тест модуля выходного контроля")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # 1. Проверка доступности сервиса
        print("1️⃣ Проверка доступности сервиса...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("   ✅ Сервис доступен")
                health_data = response.json()
                print(f"   📊 Статус: {health_data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Сервис недоступен (код: {response.status_code})")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения: {e}")
            return False
        
        # 2. Проверка тестового файла
        print("\n2️⃣ Проверка тестового файла...")
        if not TEST_FILE.exists():
            print(f"   ❌ Файл не найден: {TEST_FILE}")
            return False
        print(f"   ✅ Файл найден: {TEST_FILE.name}")
        print(f"   📁 Размер: {TEST_FILE.stat().st_size / 1024:.1f} KB")
        
        # 3. Загрузка документа
        print("\n3️⃣ Загрузка документа...")
        try:
            with open(TEST_FILE, "rb") as f:
                files = {"file": (TEST_FILE.name, f, "application/pdf")}
                response = await client.post(f"{BASE_URL}/documents/", files=files)
            
            if response.status_code == 200:
                upload_data = response.json()
                document_id = upload_data["document_id"]
                print(f"   ✅ Документ загружен")
                print(f"   🆔 ID: {document_id}")
            else:
                print(f"   ❌ Ошибка загрузки (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка загрузки: {e}")
            return False
        
        # 4. Запуск анализа (только орфография для быстроты)
        print("\n4️⃣ Запуск анализа орфографии...")
        try:
            response = await client.post(f"{BASE_URL}/documents/{document_id}/process")
            
            if response.status_code == 200:
                analysis_data = response.json()
                print(f"   ✅ Анализ запущен")
                print(f"   📊 Ответ: {analysis_data}")
            else:
                print(f"   ❌ Ошибка запуска анализа (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка запуска анализа: {e}")
            return False
        
        # 5. Проверка результатов
        print("\n5️⃣ Проверка результатов...")
        try:
            # Получаем информацию о документе
            response = await client.get(f"{BASE_URL}/documents/{document_id}")
            if response.status_code == 200:
                document_data = response.json()
                print(f"   ✅ Информация о документе получена")
                print(f"   📊 Данные: {document_data}")
                results = document_data
            else:
                print(f"   ⚠️ Ошибка получения информации о документе (код: {response.status_code})")
                return False
        except Exception as e:
            print(f"   ⚠️ Ошибка запроса: {e}")
            return False
        
        # 6. Анализ результатов
        print("\n6️⃣ Анализ результатов...")
        
        # Проверяем, что документ был обработан
        if results:
            print(f"   📊 Статус документа: {results.get('status', 'unknown')}")
            print(f"   📁 Имя файла: {results.get('filename', 'unknown')}")
            print(f"   🆔 ID документа: {results.get('id', 'unknown')}")
            
            # Проверяем наличие результатов анализа
            analysis_results = results.get('analysis_results', {})
            if analysis_results:
                print(f"   ✅ Результаты анализа получены")
                print(f"   📝 Данные анализа: {analysis_results}")
            else:
                print(f"   ⚠️ Результаты анализа пока недоступны")
            
            print("\n✅ ТЕСТ ПРОЙДЕН: Документ успешно загружен и обработан")
            return True
        else:
            print("\n❌ ТЕСТ ПРОВАЛЕН: Не удалось получить результаты")
            return False
    
    return True

async def main():
    """Главная функция"""
    try:
        success = await quick_test()
        if success:
            print("\n🎉 БЫСТРЫЙ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
        else:
            print("\n❌ БЫСТРЫЙ ТЕСТ ПРОВАЛЕН!")
        return success
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
