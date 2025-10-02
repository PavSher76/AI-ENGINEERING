
# Отчет о тестировании AI Engineering Platform

**Дата:** Thu Oct  2 06:43:28 MSK 2025
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
