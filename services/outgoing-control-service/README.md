# Outgoing Control Service

Сервис выходного контроля исходящей переписки для AI Engineering Platform.

## Функциональность

### Основные возможности:
- **Извлечение текста** из PDF и DOCX документов с учетом таблиц
- **Проверка орфографии** через LanguageTool и PySpellChecker
- **Анализ стиля** письма (читаемость, формальность, деловой стиль)
- **Проверка этики** и соответствия корпоративным стандартам
- **Проверка терминологии** для различных областей знаний
- **Финальная проверка** через LLM (Ollama/OpenAI) с заключением о возможности отправки

### Поддерживаемые форматы:
- PDF (с извлечением таблиц)
- DOCX (с извлечением таблиц)
- TXT (обычный текст)

### Области терминологии:
- Engineering (инженерия)
- Legal (юриспруденция)
- Business (бизнес)

## API Endpoints

### Управление документами
- `POST /documents/` - Создать документ
- `GET /documents/` - Получить список документов
- `GET /documents/{id}` - Получить документ по ID
- `PUT /documents/{id}` - Обновить документ
- `POST /documents/{id}/upload` - Загрузить файл документа

### Проверки
- `POST /spell-check` - Проверка орфографии
- `POST /style-analysis` - Анализ стиля
- `POST /ethics-check` - Проверка этики
- `POST /terminology-check` - Проверка терминологии
- `POST /final-review` - Финальная проверка с LLM

### Обработка
- `POST /documents/{id}/process` - Полная обработка документа
- `GET /stats` - Статистика сервиса

## Конфигурация

### Переменные окружения:
- `DATABASE_URL` - URL базы данных PostgreSQL
- `REDIS_URL` - URL Redis для кэширования
- `OLLAMA_URL` - URL Ollama сервера (по умолчанию: http://ollama:11434)
- `OPENAI_API_KEY` - API ключ OpenAI (опционально)
- `OPENAI_BASE_URL` - Базовый URL OpenAI API

### Зависимости:
- PostgreSQL - для хранения данных
- Redis - для кэширования
- Ollama - для LLM проверок (рекомендуется)
- LanguageTool - для проверки грамматики (требует Java)

## Использование

### 1. Создание документа
```bash
curl -X POST "http://localhost:8011/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Деловое письмо",
    "document_type": "letter",
    "project_id": "uuid-here"
  }'
```

### 2. Загрузка файла
```bash
curl -X POST "http://localhost:8011/documents/{document_id}/upload" \
  -F "file=@document.pdf"
```

### 3. Полная обработка
```bash
curl -X POST "http://localhost:8011/documents/{document_id}/process" \
  -H "Content-Type: application/json" \
  -d '{
    "checks_to_perform": [
      "spell_check",
      "style_check", 
      "ethics_check",
      "terminology_check"
    ]
  }'
```

### 4. Финальная проверка
```bash
curl -X POST "http://localhost:8011/final-review" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "uuid-here",
    "include_all_checks": true
  }'
```

## Результаты проверок

### Орфография
- Общее количество слов
- Количество ошибок
- Предложения по исправлению
- Исправленный текст
- Оценка уверенности

### Стиль
- Индекс читаемости (0-100)
- Уровень формальности (0-100)
- Соответствие деловому стилю (0-100)
- Анализ тона (позитивный/негативный/нейтральный)
- Рекомендации по улучшению

### Этичность
- Общая оценка этичности (0-100)
- Найденные нарушения
- Соответствие корпоративным стандартам
- Рекомендации
- Можно ли одобрить документ

### Терминология
- Использованные термины
- Неправильно использованные термины
- Предложения по замене
- Оценка точности (0-100)

### Финальное заключение
- Общая оценка (0-100)
- Можно ли отправлять документ
- Критические проблемы
- Мелкие проблемы
- Общие рекомендации

## Архитектура

Сервис построен на FastAPI и включает следующие компоненты:

- **DocumentProcessor** - извлечение текста из файлов
- **SpellCheckService** - проверка орфографии и грамматики
- **StyleAnalyzer** - анализ стиля письма
- **EthicsChecker** - проверка этичности
- **TerminologyChecker** - проверка терминологии
- **LLMIntegration** - интеграция с LLM для финальной проверки

## Мониторинг

- `GET /health` - проверка здоровья сервиса
- `GET /stats` - статистика обработки документов
- Логирование через structlog
- Метрики производительности

## Разработка

### Запуск в режиме разработки:
```bash
cd services/outgoing-control-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8011 --reload
```

### Тестирование:
```bash
pytest
```

### Docker:
```bash
docker-compose up outgoing-control-service
```
