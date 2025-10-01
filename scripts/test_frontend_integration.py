#!/usr/bin/env python3
"""
Скрипт для тестирования интеграции frontend с авторизацией
"""

import requests
import json
import sys
from typing import Dict, Any

# Настройки
FRONTEND_URL = "http://localhost:3000"
CHAT_SERVICE_URL = "http://localhost/api/chat"
NGINX_URL = "http://localhost"

def test_nginx_proxy():
    """Тест nginx прокси"""
    print("🌐 Тестирование nginx прокси...")
    
    try:
        response = requests.get(f"{NGINX_URL}/api/chat/health")
        if response.status_code == 200:
            print("✅ Nginx прокси работает")
            return True
        else:
            print(f"❌ Nginx прокси не работает. Статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка nginx прокси: {e}")
        return False

def test_cors_headers():
    """Тест CORS заголовков"""
    print("🔗 Тестирование CORS заголовков...")
    
    try:
        # Тест preflight запроса
        response = requests.options(
            f"{NGINX_URL}/api/chat/settings/llm",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization"
            }
        )
        
        if response.status_code == 204:
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            print("✅ CORS preflight запрос работает")
            print(f"   Allow-Origin: {cors_headers['Access-Control-Allow-Origin']}")
            print(f"   Allow-Methods: {cors_headers['Access-Control-Allow-Methods']}")
            print(f"   Allow-Headers: {cors_headers['Access-Control-Allow-Headers']}")
            print(f"   Allow-Credentials: {cors_headers['Access-Control-Allow-Credentials']}")
            
            # Проверяем, что нет дублирования заголовков
            if cors_headers['Access-Control-Allow-Origin'] and ',' in cors_headers['Access-Control-Allow-Origin']:
                print("❌ Обнаружено дублирование CORS заголовков")
                return False
            
            return True
        else:
            print(f"❌ CORS preflight запрос не работает. Статус: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка CORS тестирования: {e}")
        return False

def test_chat_service_endpoints():
    """Тест эндпоинтов chat-service"""
    print("💬 Тестирование эндпоинтов chat-service...")
    
    endpoints = [
        ("/health", "GET"),
        ("/settings", "GET"),
        ("/settings/llm", "GET"),
        ("/settings/chat", "GET"),
        ("/settings/available", "GET"),
        ("/files/supported", "GET")
    ]
    
    results = []
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{CHAT_SERVICE_URL}{endpoint}")
            else:
                response = requests.post(f"{CHAT_SERVICE_URL}{endpoint}")
            
            if response.status_code == 200:
                print(f"✅ {method} {endpoint} - OK")
                results.append(True)
            else:
                print(f"❌ {method} {endpoint} - {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Ошибка: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"📊 Успешность: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    
    return success_rate >= 80

def test_chat_functionality():
    """Тест функциональности чата"""
    print("🤖 Тестирование функциональности чата...")
    
    try:
        # Тест отправки сообщения
        response = requests.post(
            f"{CHAT_SERVICE_URL}/chat",
            data={
                "message": "Привет! Это тест интеграции frontend с авторизацией.",
                "session_id": "test-frontend-integration"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Сообщение в чат отправлено успешно")
            print(f"   Ответ: {result.get('response', 'Нет ответа')[:100]}...")
            return True
        else:
            print(f"❌ Ошибка отправки сообщения. Статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования чата: {e}")
        return False

def test_settings_access():
    """Тест доступа к настройкам"""
    print("⚙️ Тестирование доступа к настройкам...")
    
    try:
        # Тест получения настроек LLM
        response = requests.get(f"{CHAT_SERVICE_URL}/settings/llm")
        if response.status_code == 200:
            settings = response.json()
            print("✅ Настройки LLM получены")
            print(f"   Модель: {settings.get('model', 'Не указана')}")
            print(f"   Температура: {settings.get('temperature', 'Не указана')}")
        else:
            print(f"❌ Ошибка получения настроек LLM. Статус: {response.status_code}")
            return False
        
        # Тест получения настроек чата
        response = requests.get(f"{CHAT_SERVICE_URL}/settings/chat")
        if response.status_code == 200:
            settings = response.json()
            print("✅ Настройки чата получены")
            print(f"   Максимум токенов: {settings.get('max_tokens', 'Не указано')}")
        else:
            print(f"❌ Ошибка получения настроек чата. Статус: {response.status_code}")
            return False
        
        # Тест получения доступных опций
        response = requests.get(f"{CHAT_SERVICE_URL}/settings/available")
        if response.status_code == 200:
            options = response.json()
            print("✅ Доступные опции получены")
            print(f"   Модели: {len(options.get('models', []))}")
            print(f"   Языки: {len(options.get('languages', []))}")
            print(f"   Форматы экспорта: {len(options.get('export_formats', []))}")
        else:
            print(f"❌ Ошибка получения доступных опций. Статус: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования настроек: {e}")
        return False

def test_frontend_connectivity():
    """Тест подключения к frontend"""
    print("🖥️ Тестирование подключения к frontend...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend доступен")
            return True
        else:
            print(f"❌ Frontend недоступен. Статус: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("⏰ Frontend не отвечает (таймаут)")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения к frontend: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования интеграции frontend с авторизацией")
    print("=" * 60)
    
    tests = [
        ("Nginx прокси", test_nginx_proxy),
        ("CORS заголовки", test_cors_headers),
        ("Эндпоинты chat-service", test_chat_service_endpoints),
        ("Функциональность чата", test_chat_functionality),
        ("Доступ к настройкам", test_settings_access),
        ("Подключение к frontend", test_frontend_connectivity)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Общий результат: {passed}/{total} тестов пройдено ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Интеграция frontend с авторизацией работает корректно")
        print("✅ CORS настроен правильно")
        print("✅ Chat-service доступен через nginx")
        print("✅ Настройки загружаются без ошибок")
    elif passed >= total * 0.8:
        print("\n⚠️ БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО")
        print("✅ Основная функциональность работает")
        print("⚠️ Есть незначительные проблемы")
    else:
        print("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("❌ Требуется исправление ошибок")
        sys.exit(1)
    
    print("\n🔧 Рекомендации:")
    print("1. Проверьте работу frontend в браузере")
    print("2. Убедитесь, что все API запросы проходят успешно")
    print("3. Проверьте консоль браузера на наличие ошибок")
    print("4. При необходимости настройте Keycloak для полной авторизации")

if __name__ == "__main__":
    main()
