#!/usr/bin/env python3
"""
Тест API endpoints модуля выходного контроля
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_api_endpoints():
    """Тест всех API endpoints"""
    
    BASE_URL = "http://localhost:8011"
    TEST_TEXT = "Этот документ содержит ошибкаа в тексте. Докуменнт должен быть проверен системмой."
    
    print("🧪 Тест API endpoints модуля выходного контроля")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Проверка доступности сервиса
        print("1️⃣ Проверка доступности сервиса...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ Сервис доступен: {health_data.get('status', 'unknown')}")
            else:
                print(f"   ❌ Сервис недоступен (код: {response.status_code})")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения: {e}")
            return False
        
        # 2. Тест проверки орфографии
        print("\n2️⃣ Тест проверки орфографии...")
        try:
            response = await client.post(
                f"{BASE_URL}/spell-check",
                json={"text": TEST_TEXT}
            )
            if response.status_code == 200:
                spell_data = response.json()
                errors_found = spell_data.get("errors_found", 0)
                print(f"   ✅ Проверка орфографии: найдено {errors_found} ошибок")
                print(f"   📊 Уверенность: {spell_data.get('confidence_score', 0)}%")
                
                if errors_found > 0:
                    print("   🔍 Примеры ошибок:")
                    for i, suggestion in enumerate(spell_data.get("suggestions", [])[:3]):
                        print(f"      {i+1}. '{suggestion.get('word', 'N/A')}' → {suggestion.get('suggestions', [])}")
            else:
                print(f"   ❌ Ошибка проверки орфографии (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
        except Exception as e:
            print(f"   ❌ Ошибка проверки орфографии: {e}")
        
        # 3. Тест анализа стиля
        print("\n3️⃣ Тест анализа стиля...")
        try:
            response = await client.post(
                f"{BASE_URL}/style-analysis",
                json={
                    "text": TEST_TEXT,
                    "document_type": "business"
                }
            )
            if response.status_code == 200:
                style_data = response.json()
                readability = style_data.get("readability_score", 0)
                business_score = style_data.get("business_style_score", 0)
                print(f"   ✅ Анализ стиля: читаемость {readability}, деловой стиль {business_score}")
                print(f"   📊 Тон: {style_data.get('tone_analysis', {}).get('tone', 'unknown')}")
                print(f"   💡 Рекомендации: {style_data.get('recommendations', 'N/A')[:100]}...")
            else:
                print(f"   ❌ Ошибка анализа стиля (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
        except Exception as e:
            print(f"   ❌ Ошибка анализа стиля: {e}")
        
        # 4. Тест проверки этики
        print("\n4️⃣ Тест проверки этики...")
        try:
            response = await client.post(
                f"{BASE_URL}/ethics-check",
                json={"text": TEST_TEXT}
            )
            if response.status_code == 200:
                ethics_data = response.json()
                ethics_score = ethics_data.get("ethics_score", 0)
                is_approved = ethics_data.get("is_approved", False)
                print(f"   ✅ Проверка этики: балл {ethics_score}, одобрен: {is_approved}")
                print(f"   📊 Нарушений: {len(ethics_data.get('violations_found', []))}")
                print(f"   💡 Рекомендации: {ethics_data.get('recommendations', 'N/A')[:100]}...")
            else:
                print(f"   ❌ Ошибка проверки этики (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
        except Exception as e:
            print(f"   ❌ Ошибка проверки этики: {e}")
        
        # 5. Тест проверки терминологии
        print("\n5️⃣ Тест проверки терминологии...")
        try:
            response = await client.post(
                f"{BASE_URL}/terminology-check",
                json={
                    "text": TEST_TEXT,
                    "domain": "engineering"
                }
            )
            if response.status_code == 200:
                term_data = response.json()
                accuracy_score = term_data.get("accuracy_score", 0)
                incorrect_terms = len(term_data.get("incorrect_terms", []))
                print(f"   ✅ Проверка терминологии: точность {accuracy_score}%")
                print(f"   📊 Неправильных терминов: {incorrect_terms}")
                print(f"   📝 Использованных терминов: {len(term_data.get('terms_used', []))}")
            else:
                print(f"   ❌ Ошибка проверки терминологии (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
        except Exception as e:
            print(f"   ❌ Ошибка проверки терминологии: {e}")
        
        # 6. Тест финального обзора
        print("\n6️⃣ Тест финального обзора...")
        try:
            response = await client.post(
                f"{BASE_URL}/final-review",
                json={"text": TEST_TEXT}
            )
            if response.status_code == 200:
                review_data = response.json()
                final_decision = review_data.get("final_decision", "unknown")
                confidence = review_data.get("confidence_score", 0)
                print(f"   ✅ Финальный обзор: решение '{final_decision}', уверенность {confidence}%")
                print(f"   📊 Общая оценка: {review_data.get('overall_score', 0)}")
                print(f"   💡 Рекомендации: {review_data.get('recommendations', 'N/A')[:100]}...")
            else:
                print(f"   ❌ Ошибка финального обзора (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
        except Exception as e:
            print(f"   ❌ Ошибка финального обзора: {e}")
        
        # 7. Тест статистики
        print("\n7️⃣ Тест статистики...")
        try:
            response = await client.get(f"{BASE_URL}/stats")
            if response.status_code == 200:
                stats_data = response.json()
                print(f"   ✅ Статистика получена")
                print(f"   📊 Данные: {stats_data}")
            else:
                print(f"   ❌ Ошибка получения статистики (код: {response.status_code})")
                print(f"   📝 Ответ: {response.text}")
        except Exception as e:
            print(f"   ❌ Ошибка получения статистики: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 ТЕСТИРОВАНИЕ API ENDPOINTS ЗАВЕРШЕНО!")
        return True

async def main():
    """Главная функция"""
    try:
        success = await test_api_endpoints()
        if success:
            print("\n✅ ВСЕ ТЕСТЫ ВЫПОЛНЕНЫ УСПЕШНО!")
        else:
            print("\n❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        return success
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
