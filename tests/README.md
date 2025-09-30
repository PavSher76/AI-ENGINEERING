# 🧪 Тесты модуля выходного контроля

Этот каталог содержит тесты для модуля выходного контроля исходящей переписки.

## 📁 Структура

```
tests/
├── outgoing_control/
│   ├── test_outgoing_control.py    # Полные тесты модуля
│   └── test_quick.py               # Быстрый тест
├── pytest.ini                     # Конфигурация pytest
├── requirements.txt                # Зависимости для тестов
├── run_tests.py                    # Скрипт запуска тестов
└── README.md                       # Этот файл
```

## 🚀 Быстрый старт

### 1. Запуск быстрого теста

```bash
# Запуск быстрого теста (проверка орфографии)
python tests/outgoing_control/test_quick.py
```

### 2. Запуск всех тестов

```bash
# Установка зависимостей и запуск всех тестов
python tests/run_tests.py
```

### 3. Запуск через pytest

```bash
# Установка зависимостей
pip install -r tests/requirements.txt

# Запуск всех тестов
pytest tests/outgoing_control/ -v

# Запуск конкретного теста
pytest tests/outgoing_control/test_outgoing_control.py::TestOutgoingControl::test_spelling_check -v

# Запуск с подробным выводом
pytest tests/outgoing_control/ -v -s
```

## 📋 Тестовые сценарии

### 🔍 Базовые тесты

- **test_service_health** - Проверка доступности сервиса
- **test_upload_document** - Загрузка документа
- **test_get_document_list** - Получение списка документов
- **test_get_analysis_history** - Получение истории анализов

### 📝 Анализ документов

- **test_spelling_check** - Проверка орфографии
- **test_style_analysis** - Анализ стиля письма
- **test_ethics_check** - Проверка этики
- **test_terminology_check** - Проверка терминологии
- **test_llm_review** - LLM обзор документа

### 🔄 Интеграционные тесты

- **test_full_document_processing_workflow** - Полный цикл обработки документа

## 📄 Тестовые данные

Тесты используют файл `E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf` из каталога `test_data/`.

Этот документ содержит:
- ✅ Орфографические ошибки
- ✅ Стилистические проблемы
- ✅ Терминологические неточности
- ✅ Потенциальные этические проблемы

## 🎯 Ожидаемые результаты

### Для документа с грубыми ошибками:

- **Орфографические ошибки**: > 0
- **Балл стиля**: < 80
- **Этический балл**: ≥ 0
- **Финальное решение**: "reject" или "needs_revision"

## ⚙️ Конфигурация

### Переменные окружения

- `BASE_URL` - URL сервиса выходного контроля (по умолчанию: http://localhost:8011)
- `TEST_TIMEOUT` - Таймаут для тестов (по умолчанию: 60 секунд)

### Настройки pytest

Файл `pytest.ini` содержит:
- Режим asyncio
- Маркеры для категоризации тестов
- Настройки вывода

## 🐛 Отладка

### Проверка статуса сервиса

```bash
# Проверка доступности
curl http://localhost:8011/health

# Проверка списка документов
curl http://localhost:8011/documents

# Проверка истории анализов
curl http://localhost:8011/analyses
```

### Логи сервиса

```bash
# Просмотр логов
docker-compose logs -f outgoing-control-service
```

### Ручное тестирование

```bash
# Загрузка документа
curl -X POST -F "file=@test_data/E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf" \
  http://localhost:8011/upload

# Запуск анализа (замените DOCUMENT_ID)
curl -X POST http://localhost:8011/analyze/DOCUMENT_ID \
  -H "Content-Type: application/json" \
  -d '{"check_spelling": true, "check_style": true, "check_ethics": true, "check_terminology": true, "llm_review": true}'

# Получение результатов (замените ANALYSIS_ID)
curl http://localhost:8011/analysis/ANALYSIS_ID
```

## 📊 Метрики тестирования

- **Время выполнения**: ~2-3 минуты для полного цикла
- **Покрытие**: Все основные функции модуля
- **Надежность**: Автоматические повторы при таймаутах

## 🔧 Устранение неполадок

### Сервис недоступен

```bash
# Запуск сервиса
docker-compose up -d outgoing-control-service

# Проверка статуса
docker-compose ps outgoing-control-service
```

### Ошибки зависимостей

```bash
# Переустановка зависимостей
pip install -r tests/requirements.txt --force-reinstall
```

### Таймауты

- Увеличьте `TEST_TIMEOUT` в тестах
- Проверьте производительность системы
- Убедитесь, что Ollama работает на хосте

## 📈 Расширение тестов

### Добавление новых тестов

1. Создайте новый тест в `test_outgoing_control.py`
2. Добавьте маркеры pytest при необходимости
3. Обновите `run_tests.py` для включения нового теста

### Добавление новых тестовых данных

1. Поместите файлы в `test_data/`
2. Обновите тесты для использования новых файлов
3. Добавьте ожидаемые результаты в документацию

## 🤝 Вклад в разработку

При добавлении новых функций:

1. ✅ Добавьте соответствующие тесты
2. ✅ Обновите документацию
3. ✅ Проверьте совместимость с существующими тестами
4. ✅ Убедитесь, что все тесты проходят
