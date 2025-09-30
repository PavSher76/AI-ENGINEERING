#!/usr/bin/env python3
"""
Скрипт для запуска тестов модуля выходного контроля
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Запуск тестов"""
    
    # Проверяем, что мы в правильной директории
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 Запуск тестов модуля выходного контроля...")
    print("=" * 60)
    
    # Проверяем, что сервис запущен
    try:
        import httpx
        response = httpx.get("http://localhost:8011/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервис выходного контроля недоступен!")
            print("   Запустите сервис: docker-compose up -d outgoing-control-service")
            return False
    except Exception as e:
        print(f"❌ Не удается подключиться к сервису: {e}")
        print("   Запустите сервис: docker-compose up -d outgoing-control-service")
        return False
    
    print("✅ Сервис выходного контроля доступен")
    
    # Проверяем наличие тестового файла
    test_file = project_root / "test_data" / "E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf"
    if not test_file.exists():
        print(f"❌ Тестовый файл не найден: {test_file}")
        return False
    
    print(f"✅ Тестовый файл найден: {test_file.name}")
    
    # Устанавливаем зависимости для тестов
    print("\n📦 Установка зависимостей для тестов...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "tests/requirements.txt"
        ], check=True, capture_output=True)
        print("✅ Зависимости установлены")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False
    
    # Запускаем тесты
    print("\n🚀 Запуск тестов...")
    print("=" * 60)
    
    test_commands = [
        # Базовые тесты
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_service_health", "-v"],
        
        # Тест загрузки документа
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_upload_document", "-v"],
        
        # Тест проверки орфографии
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_spelling_check", "-v"],
        
        # Тест анализа стиля
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_style_analysis", "-v"],
        
        # Тест проверки этики
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_ethics_check", "-v"],
        
        # Тест проверки терминологии
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_terminology_check", "-v"],
        
        # Тест LLM обзора
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_llm_review", "-v"],
        
        # Полный интеграционный тест
        ["python", "-m", "pytest", "tests/outgoing_control/test_outgoing_control.py::TestOutgoingControlIntegration::test_full_document_processing_workflow", "-v", "-s"],
    ]
    
    passed_tests = 0
    total_tests = len(test_commands)
    
    for i, cmd in enumerate(test_commands, 1):
        test_name = cmd[-1].split("::")[-1]
        print(f"\n[{i}/{total_tests}] 🧪 {test_name}")
        print("-" * 40)
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ ПРОЙДЕН")
            passed_tests += 1
        except subprocess.CalledProcessError as e:
            print("❌ ПРОВАЛЕН")
            print(f"Ошибка: {e.stderr}")
    
    # Итоги
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   ✅ Пройдено: {passed_tests}/{total_tests}")
    print(f"   ❌ Провалено: {total_tests - passed_tests}/{total_tests}")
    print(f"   📈 Успешность: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} ТЕСТОВ ПРОВАЛЕНО")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
