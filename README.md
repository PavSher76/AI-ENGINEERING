# AI Engineering Platform

Комплексная платформа для инженерной деятельности с поддержкой ИИ

## Архитектура проекта

### Подпроекты:
- **Чат с ИИ** - Интерфейс для общения с ИИ
- **Консультации НТД от ИИ** - Консультации по нормативно-технической документации
- **Объекты аналоги и Архив** - База данных объектов-аналогов
- **Инженерные расчеты** - Модуль для инженерных вычислений
- **Проверка Исходных Данных** - Валидация входных данных
- **Проверка Проектной и рабочей документации** - Анализ проектной документации
- **🆕 Выходной контроль исходящей переписки** - Автоматическая проверка документов перед отправкой

### Основные компоненты:
- **RAG Service** - Сервис для работы с векторными базами данных
- **Document Collections** - Управление коллекциями документов
- **SSO Authentication** - Единая система авторизации
- **3DEXPERIENCE/ENOVIA Integration** - Интеграция с PLM системами
- **Report Generation** - Генерация пояснительных записок
- **Analytics Module** - Глубокая аналитика проектов
- **Context Memory** - Запоминание контекста
- **Validation Module** - Валидация чертежей и IFC документов
- **Document Revision** - Система довыпуска документов
- **🆕 Outgoing Control** - Автоматическая проверка исходящих документов

## Технологический стек

- **Backend**: Python (FastAPI), Node.js
- **Frontend**: React, TypeScript
- **Database**: PostgreSQL, Redis, Vector DB (Qdrant)
- **AI**: Ollama (локально), LangChain
- **Containerization**: Docker, Docker Compose
- **Authentication**: Keycloak (SSO)
- **File Storage**: MinIO
- **Message Queue**: RabbitMQ

## 🆕 Новый модуль: Выходной контроль исходящей переписки

### Функциональность:
- **Извлечение текста** из PDF и DOCX документов с учетом таблиц
- **Проверка орфографии** через LanguageTool и PySpellChecker
- **Анализ стиля** письма (читаемость, формальность, деловой стиль)
- **Проверка этики** и соответствия корпоративным стандартам
- **Проверка терминологии** для различных областей знаний
- **Финальная проверка** через LLM с заключением о возможности отправки

### API Endpoints:
- `POST /api/outgoing-control/documents/` - Создание документа
- `POST /api/outgoing-control/documents/{id}/upload` - Загрузка файла
- `POST /api/outgoing-control/documents/{id}/process` - Полная обработка
- `POST /api/outgoing-control/final-review` - Финальная проверка с LLM
- `GET /api/outgoing-control/stats` - Статистика сервиса

### Доступ:
- **Прямой доступ:** http://localhost:8011
- **API документация:** http://localhost:8011/docs
- **Через Nginx:** http://localhost/api/outgoing-control/

## Быстрый старт

```bash
# Клонирование репозитория
git clone <repository-url>
cd AI-Engineering

# Запуск Ollama на хосте (обязательно)
ollama serve
ollama pull llama2

# Запуск всех сервисов
docker-compose up -d
```

### ⚠️ Важно: Ollama на хосте

**Ollama должен быть запущен на хосте** перед запуском контейнеров:

```bash
# Установка Ollama (если не установлен)
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama сервера
ollama serve

# Загрузка модели (в другом терминале)
ollama pull llama2
```

Все сервисы подключаются к Ollama через `host.docker.internal:11434`.

### ⚠️ Важно для разработки

**Авторизация отключена** для упрощения разработки и тестирования. Система работает без Keycloak и проверки токенов.

Для включения авторизации в production см. [docs/ENABLE_AUTH.md](docs/ENABLE_AUTH.md)

## Структура проекта

```
AI-Engineering/
├── services/                 # Микросервисы
│   ├── chat-service/        # Чат с ИИ
│   ├── consultation-service/ # Консультации НТД
│   ├── archive-service/     # Объекты аналоги и архив
│   ├── calculation-service/ # Инженерные расчеты
│   ├── validation-service/  # Проверка данных
│   ├── document-service/    # Работа с документами
│   ├── rag-service/         # RAG сервис
│   ├── analytics-service/   # Аналитика
│   ├── integration-service/ # Интеграции
│   └── outgoing-control-service/ # 🆕 Выходной контроль
├── frontend/                # Веб-интерфейс
├── shared/                  # Общие компоненты
├── infrastructure/          # Инфраструктура
├── docs/                    # Документация
└── scripts/                 # Скрипты развертывания
```

## Статус сервисов

### 🟢 Работающие сервисы (16/16):

**Инфраструктура:**
- **Frontend:** ✅ http://localhost (Nginx статический)
- **Nginx:** ✅ Reverse proxy (порт 80)
- **PostgreSQL:** ✅ База данных (порт 5432)
- **Redis:** ✅ Кэширование (порт 6379)
- **Qdrant:** ✅ Векторная БД (порты 6333-6334)
- **MinIO:** ✅ Файловое хранилище (порты 9000-9001)
- **RabbitMQ:** ✅ Очереди сообщений (порты 5672, 15672)
- **Ollama:** ✅ AI модели (порт 11434) - запускается на хосте
- **vLLM:** ✅ Высокопроизводительный LLM сервер (порт 8002)

**Микросервисы:**
- **RAG Service:** ✅ http://localhost:8001
- **Chat Service:** ✅ http://localhost:8003
- **Consultation Service:** ✅ http://localhost:8004
- **Archive Service:** ✅ http://localhost:8005
- **Calculation Service:** ✅ http://localhost:8006
- **Validation Service:** ✅ http://localhost:8007
- **Document Service:** ✅ http://localhost:8008
- **Analytics Service:** ✅ http://localhost:8009
- **Integration Service:** ✅ http://localhost:8010
- **🆕 Outgoing Control Service:** ✅ http://localhost:8011
- **🆕 Ollama Management Service:** ✅ http://localhost:8012

### Доступные интерфейсы:
- **🆕 Веб-интерфейс:** http://localhost:3000 (React фронтенд)
- **Основной интерфейс:** http://localhost (Nginx)
- **API документация:** http://localhost:8003/docs (Chat Service)
- **🆕 Outgoing Control API:** http://localhost:8011/docs
- **🆕 vLLM API:** http://localhost:8002/docs
- **🆕 Ollama Management API:** http://localhost:8012/docs
- **RabbitMQ Management:** http://localhost:15672
- **MinIO Console:** http://localhost:9001

## Примеры использования

### Выходной контроль документов:

```bash
# 1. Создание документа
curl -X POST "http://localhost:8011/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Деловое письмо клиенту",
    "document_type": "letter"
  }'

# 2. Загрузка файла
curl -X POST "http://localhost:8011/documents/{document_id}/upload" \
  -F "file=@business_letter.pdf"

# 3. Полная обработка документа
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

# 4. Финальная проверка с LLM
curl -X POST "http://localhost:8011/final-review" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "uuid-here",
    "include_all_checks": true
  }'
```

### Результат проверки:
```json
{
  "overall_score": 85.5,
  "can_send": true,
  "critical_issues": [],
  "minor_issues": ["Повысить формальность стиля"],
  "recommendations": "Документ готов к отправке с небольшими улучшениями"
}
```

## 🆕 Новый веб-интерфейс

Реализован полноценный React фронтенд с современным дизайном и навигацией:

### Возможности:
- **📊 Дашборд** - Мониторинг состояния всех сервисов в реальном времени
- **🧭 Навигационное меню** - Удобный доступ ко всем модулям системы
- **📱 Адаптивный дизайн** - Работает на всех устройствах
- **⚡ Быстрая навигация** - React Router для мгновенных переходов
- **🎨 Современный UI** - Красивый и интуитивный интерфейс

### Модули в интерфейсе:
- **Дашборд** - Обзор системы и статус сервисов
- **Чат с ИИ** - Интерфейс для общения с ИИ
- **Консультации НТД** - Нормативно-техническая документация
- **Объекты аналоги** - Архив и база данных
- **Инженерные расчеты** - Вычисления и анализ
- **Проверка данных** - Валидация входных данных
- **Документы** - Управление документами
- **Аналитика** - Отчетность и аналитика
- **Интеграции** - PLM и внешние системы
- **Выходной контроль** - Проверка исходящих документов
- **Настройки** - Конфигурация системы

### Доступ:
- **Веб-интерфейс:** http://localhost:3000
- **Дашборд:** http://localhost:3000/ (главная страница)

## 🔄 Миграция на Qdrant

Проект успешно мигрирован с ChromaDB на Qdrant - современную векторную базу данных с улучшенной производительностью и функциональностью.

### Преимущества Qdrant:
- **Высокая производительность** - оптимизированные алгоритмы поиска
- **Масштабируемость** - поддержка кластеризации и репликации
- **Гибкость** - расширенные возможности фильтрации и метаданных
- **Современный API** - REST и gRPC интерфейсы
- **Активная разработка** - регулярные обновления и новые функции

### Коллекции в Qdrant:
- `documents_normative` - Нормативные документы
- `documents_chat` - Документы чата
- `documents_input_data` - Исходные данные проекта
- `documents_project` - Документы проекта
- `documents_archive` - Архив и объекты аналоги

### Доступ к Qdrant:
- **HTTP API:** http://localhost:6333
- **gRPC API:** http://localhost:6334
- **Web UI:** http://localhost:6333/dashboard (если включен)

## 🚀 Интеграция vLLM

Добавлен высокопроизводительный LLM сервер vLLM для работы с Ollama:

### Преимущества vLLM:
- **Высокая производительность** - Оптимизированное обслуживание LLM
- **Совместимость с OpenAI** - Стандартный OpenAI API
- **Масштабируемость** - Поддержка множественных запросов
- **Эффективность** - Оптимизированное использование GPU/CPU
- **Простота интеграции** - Легкая интеграция с существующими сервисами

### Конфигурация:
- **Порт:** 8002 (внешний) → 8000 (внутренний)
- **Модель:** llama2 (по умолчанию)
- **API:** OpenAI-совместимый интерфейс
- **Интеграция:** Все сервисы используют vLLM, который подключается к Ollama на хосте
- **Ollama:** Запускается на хосте, vLLM подключается через `host.docker.internal:11434`

### Доступ к vLLM:
- **API:** http://localhost:8002
- **Документация:** http://localhost:8002/docs
- **OpenAI совместимость:** http://localhost:8002/v1

## 🤖 Тестирование ИИ

### Проверка работы ИИ через Ollama Management Service:

```bash
# Проверка статуса Ollama
curl http://localhost:8012/status

# Получение списка доступных моделей
curl http://localhost:8012/models

# Тестирование генерации текста
curl -X POST "http://localhost:8012/models/llama3.1:8b/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Привет! Как дела?", "max_tokens": 50}'
```

### Доступные модели:
- **llama3.1:8b** - Основная модель (по умолчанию)
- **llama2:latest** - Альтернативная модель
- **gpt-oss-optimized:latest** - Оптимизированная модель
- **gpt-oss:latest** - Базовая модель
- **bge-m3:latest** - Модель для эмбеддингов
- **gpt-oss:20b** - Большая модель (20B параметров)

## Лицензия

MIT License
