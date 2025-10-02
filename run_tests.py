#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов проекта
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - УСПЕШНО")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ПРОВАЛЕН")
        print(f"Ошибка: {e.stderr}")
        return False

def check_services():
    """Проверяет доступность сервисов"""
    print("🔍 Проверка доступности сервисов...")
    
    services = [
        ("http://localhost:8001/health", "RAG Service"),
        ("http://localhost:8003/health", "Chat Service"),
        ("http://localhost:8012/health", "Ollama Management Service"),
        ("http://localhost:8011/health", "Outgoing Control Service"),
    ]
    
    available_services = []
    for url, name in services:
        try:
            import httpx
            response = httpx.get(url, timeout=5)
            if response.status_code == 200:
                available_services.append(name)
                print(f"✅ {name} - доступен")
            else:
                print(f"❌ {name} - недоступен (HTTP {response.status_code})")
        except Exception:
            print(f"❌ {name} - недоступен")
    
    return len(available_services) >= 2  # Требуем минимум 2 сервиса

def run_tests(test_type="all", coverage=True, parallel=False):
    """Запускает тесты"""
    
    # Проверяем, что мы в правильной директории
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 Запуск тестов AI Engineering Platform")
    print("=" * 60)
    
    # Создаем директории для отчетов
    os.makedirs("reports", exist_ok=True)
    os.makedirs("htmlcov", exist_ok=True)
    
    # Базовые параметры pytest
    base_args = [
        "python3", "-m", "pytest",
        "-v",
        "--tb=short",
        "--disable-warnings",
        "--color=yes"
    ]
    
    # Добавляем покрытие кода
    if coverage:
        base_args.extend([
            "--cov=services",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])
    
    # Добавляем HTML отчет
    base_args.extend([
        "--html=reports/report.html",
        "--self-contained-html",
        "--json-report",
        "--json-report-file=reports/report.json"
    ])
    
    # Параллельное выполнение
    if parallel:
        base_args.extend(["-n", "auto"])
    
    # Выбираем тесты для запуска
    if test_type == "unit":
        base_args.extend(["tests/unit/", "-m", "unit"])
        description = "Unit тесты"
    elif test_type == "integration":
        base_args.extend(["tests/integration/", "-m", "integration"])
        description = "Интеграционные тесты"
    elif test_type == "e2e":
        base_args.extend(["tests/e2e/", "-m", "e2e"])
        description = "E2E тесты"
    elif test_type == "outgoing_control":
        base_args.extend(["tests/outgoing_control/", "-m", "outgoing_control"])
        description = "Тесты выходного контроля"
    else:  # all
        base_args.extend(["tests/"])
        description = "Все тесты"
    
    # Запускаем тесты
    success = run_command(" ".join(base_args), description)
    
    return success

def run_code_quality():
    """Запускает проверки качества кода"""
    print("\n🔍 Проверка качества кода...")
    
    checks = [
        ("flake8 services/ --count --select=E9,F63,F7,F82 --show-source --statistics", "Lint Python код"),
        ("black --check services/", "Форматирование Python кода"),
        ("isort --check-only services/", "Импорты Python кода"),
    ]
    
    all_passed = True
    for command, description in checks:
        if not run_command(command, description):
            all_passed = False
    
    return all_passed

def generate_report():
    """Генерирует сводный отчет"""
    print("\n📊 Генерация отчета...")
    
    report_content = f"""
# Отчет о тестировании AI Engineering Platform

**Дата:** {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}
**Версия:** 1.0

## 📁 Структура тестов

- **Unit тесты:** tests/unit/
- **Интеграционные тесты:** tests/integration/
- **E2E тесты:** tests/e2e/
- **Тесты выходного контроля:** tests/outgoing_control/

## 🎯 Покрытие кода

Требуется: **70%+**
Результат: См. htmlcov/index.html

## 📊 Результаты тестов

- **HTML отчет:** reports/report.html
- **JSON отчет:** reports/report.json
- **Покрытие кода:** htmlcov/index.html

## 🚀 Запуск тестов

```bash
# Все тесты
python run_tests.py

# Только unit тесты
python run_tests.py --type unit

# Только интеграционные тесты
python run_tests.py --type integration

# Только E2E тесты
python run_tests.py --type e2e

# Без покрытия кода
python run_tests.py --no-coverage

# Параллельно
python run_tests.py --parallel
```

## 🔧 CI/CD

GitHub Actions workflow настроен в `.github/workflows/ci-cd.yml`

## 📈 Метрики

- **Общее количество тестов:** См. отчеты
- **Время выполнения:** См. отчеты
- **Покрытие кода:** См. htmlcov/index.html
"""
    
    with open("reports/README.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("✅ Отчет сгенерирован: reports/README.md")

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Запуск тестов AI Engineering Platform")
    parser.add_argument("--type", choices=["all", "unit", "integration", "e2e", "outgoing_control"], 
                       default="all", help="Тип тестов для запуска")
    parser.add_argument("--no-coverage", action="store_true", help="Отключить измерение покрытия")
    parser.add_argument("--parallel", action="store_true", help="Параллельное выполнение")
    parser.add_argument("--quality", action="store_true", help="Запустить проверки качества кода")
    parser.add_argument("--check-services", action="store_true", help="Проверить доступность сервисов")
    
    args = parser.parse_args()
    
    # Проверяем доступность сервисов
    if args.check_services:
        if not check_services():
            print("⚠️ Не все сервисы доступны, но продолжаем тестирование")
    
    # Запускаем проверки качества кода
    if args.quality:
        if not run_code_quality():
            print("❌ Проверки качества кода провалены")
            sys.exit(1)
    
    # Запускаем тесты
    success = run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        parallel=args.parallel
    )
    
    # Генерируем отчет
    generate_report()
    
    # Выводим итоги
    print("\n" + "=" * 60)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("📊 Отчеты доступны в директории reports/")
        print("📈 Покрытие кода: htmlcov/index.html")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("🔍 Проверьте отчеты в директории reports/")
        sys.exit(1)

if __name__ == "__main__":
    main()
