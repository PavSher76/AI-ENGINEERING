# Система логирования AI Engineering проекта

## Обзор

В проекте AI Engineering реализована единая система логирования, которая обеспечивает:

- **Структурированное логирование** в формате JSON
- **Цветное логирование** для консоли
- **Ротацию логов** с автоматическим сжатием
- **Мониторинг в реальном времени**
- **Централизованное управление** логами всех сервисов

## Архитектура

### Компоненты системы

1. **Утилиты логирования** (`utils/logging_utils.py`)
   - Единая конфигурация для всех сервисов
   - Структурированные форматеры
   - Цветное логирование для консоли
   - Ротация файлов

2. **Мониторинг логов** (`scripts/log_monitor.py`)
   - Анализ логов в реальном времени
   - Генерация отчетов
   - Статистика по сервисам

3. **Утилиты управления** (`scripts/setup_logging.sh`)
   - Автоматическая настройка
   - Ротация логов
   - Централизованные команды

## Конфигурация сервисов

### Поддерживаемые сервисы

| Сервис | Лог файл | Ротация | JSON |
|--------|----------|---------|------|
| **chat-service** | `/app/logs/chat-service.log` | 30 дней | ❌ |
| **qr-validation-service** | `/app/logs/qr-validation-service.log` | 14 дней | ✅ |
| **techexpert-connector** | `/app/logs/techexpert-connector.log` | 21 день | ✅ |
| **rag-service** | `/app/logs/rag-service.log` | 30 дней | ✅ |
| **ollama-service** | `/app/logs/ollama-service.log` | 14 дней | ❌ |
| **outgoing-control-service** | `/app/logs/outgoing-control-service.log` | 21 день | ✅ |

### Уровни логирования

- **DEBUG** 🔍 - Детальная отладочная информация
- **INFO** ℹ️ - Общая информация о работе
- **WARNING** ⚠️ - Предупреждения
- **ERROR** ❌ - Ошибки
- **CRITICAL** 🚨 - Критические ошибки

## Использование

### Настройка логирования в сервисе

```python
from logging_utils import setup_service_logging, log_request, log_error, log_performance, log_business_event

# Настройка логирования
logger = setup_service_logging("service-name")

# Логирование запросов
log_request(
    logger=logger,
    method="GET",
    path="/api/endpoint",
    status_code=200,
    duration=0.123,
    request_id="req_123"
)

# Логирование ошибок
log_error(
    logger=logger,
    error=exception,
    context="operation_name",
    request_id="req_123"
)

# Логирование производительности
log_performance(
    logger=logger,
    operation="database_query",
    duration=0.456,
    success=True
)

# Логирование бизнес-событий
log_business_event(
    logger=logger,
    event="user_registration",
    user_id="user_123"
)
```

### Middleware для FastAPI

```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = datetime.now()
    request_id = f"req_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
    
    logger.info(f"📥 Входящий запрос: {request.method} {request.url.path}", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path
    })
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        
        log_request(
            logger=logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time,
            request_id=request_id
        )
        
        return response
        
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        log_error(
            logger=logger,
            error=e,
            context=f"HTTP {request.method} {request.url.path}",
            request_id=request_id
        )
        raise
```

## Утилиты управления

### Просмотр логов

```bash
# Просмотр логов конкретного сервиса
ai-logs chat
ai-logs qr
ai-logs techexpert
ai-logs rag
ai-logs ollama
ai-logs outgoing

# Просмотр всех ошибок
ai-logs errors

# Статус сервисов
ai-logs status

# Отчет по логам
ai-logs report
```

### Мониторинг в реальном времени

```bash
# Мониторинг конкретного сервиса
ai-log-monitor --watch --service chat-service

# Анализ логов за последние 24 часа
ai-log-monitor --service chat-service --hours 24

# Генерация отчета
ai-log-monitor --report --hours 24

# Статус всех сервисов
ai-log-monitor --status
```

### Очистка логов

```bash
# Очистка всех логов
ai-logs-clean
```

## Форматы логов

### Обычные логи (консоль)

```
2024-01-01 12:00:00 - service-name - ℹ️ INFO - 🚀 Сервис запущен
2024-01-01 12:00:01 - service-name - ❌ ERROR - Ошибка подключения к БД
```

### Структурированные логи (JSON)

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "level": "INFO",
  "logger": "service-name",
  "message": "🚀 Сервис запущен",
  "module": "main",
  "function": "startup",
  "line": 42,
  "request_id": "req_123",
  "duration": 0.123,
  "user_id": "user_456"
}
```

### Логи ошибок

```json
{
  "timestamp": "2024-01-01T12:00:01",
  "level": "ERROR",
  "logger": "service-name",
  "message": "❌ Ошибка подключения к БД",
  "error_type": "ConnectionError",
  "context": "database_connection",
  "request_id": "req_123",
  "exception": "Traceback (most recent call last)..."
}
```

## Ротация логов

### Автоматическая ротация

- **Ежедневная ротация** в 00:00
- **Сжатие** старых логов (gzip)
- **Автоматическое удаление** очень старых логов
- **Разные политики** для разных сервисов

### Конфигурация logrotate

```bash
# Основные логи
/app/logs/service-name.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
}

# Логи ошибок
/app/logs/service-name_errors.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
}
```

## Мониторинг и алерты

### Метрики

- **Количество запросов** по сервисам
- **Время ответа** (среднее, медиана, 95-й процентиль)
- **Количество ошибок** по типам
- **Использование диска** для логов

### Алерты

- **Высокий уровень ошибок** (>5% от общего количества запросов)
- **Медленные запросы** (>5 секунд)
- **Отсутствие активности** сервиса (>1 часа)
- **Переполнение диска** с логами

### Дашборды

```bash
# Статус всех сервисов
ai-log-monitor --status

# Детальный отчет
ai-log-monitor --report --hours 24

# Мониторинг в реальном времени
ai-log-monitor --watch --service chat-service
```

## Интеграция с ELK Stack

### Конфигурация Filebeat

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log
  fields:
    service: ai-engineering
  fields_under_root: true
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "ai-engineering-logs-%{+yyyy.MM.dd}"
```

### Kibana дашборды

- **Обзор системы** - статус всех сервисов
- **Анализ ошибок** - топ ошибок по сервисам
- **Производительность** - время ответа и throughput
- **Бизнес-метрики** - пользовательская активность

## Безопасность

### Защита логов

- **Права доступа** 644 (только чтение для пользователей)
- **Ротация** для предотвращения переполнения
- **Шифрование** при передаче в ELK Stack
- **Маскирование** чувствительных данных

### Чувствительные данные

Автоматическое маскирование:
- Пароли и токены
- Номера телефонов
- Email адреса
- Персональные данные

## Производительность

### Оптимизация

- **Асинхронное логирование** для высоконагруженных сервисов
- **Буферизация** записей
- **Сжатие** старых логов
- **Индексирование** для быстрого поиска

### Мониторинг производительности

```bash
# Анализ производительности логирования
ai-log-monitor --service chat-service --hours 1 | grep "performance"

# Статистика по операциям
ai-log-monitor --report | grep "duration"
```

## Troubleshooting

### Частые проблемы

1. **Логи не создаются**
   ```bash
   # Проверка прав доступа
   ls -la /app/logs/
   
   # Проверка конфигурации
   ai-logs status
   ```

2. **Переполнение диска**
   ```bash
   # Очистка старых логов
   ai-logs-clean
   
   # Проверка размера логов
   du -sh /app/logs/*
   ```

3. **Медленное логирование**
   ```bash
   # Проверка производительности
   ai-log-monitor --service service-name --hours 1
   ```

### Отладка

```bash
# Включение DEBUG уровня
export LOG_LEVEL=DEBUG

# Просмотр логов в реальном времени
ai-logs service-name

# Анализ конкретной ошибки
ai-log-monitor --service service-name | grep "ERROR"
```

## Лучшие практики

### Рекомендации

1. **Используйте структурированное логирование** для важных сервисов
2. **Логируйте бизнес-события** для аналитики
3. **Не логируйте чувствительные данные**
4. **Используйте request_id** для трассировки
5. **Мониторьте производительность** логирования

### Анти-паттерны

1. **Не логируйте в цикле** без ограничений
2. **Не используйте print()** вместо logger
3. **Не логируйте пароли** и токены
4. **Не создавайте слишком много** уровней логирования
5. **Не игнорируйте** ошибки логирования

## Заключение

Система логирования AI Engineering проекта обеспечивает:

- ✅ **Полную наблюдаемость** всех сервисов
- ✅ **Централизованное управление** логами
- ✅ **Автоматическую ротацию** и очистку
- ✅ **Мониторинг в реальном времени**
- ✅ **Интеграцию с ELK Stack**
- ✅ **Безопасность и производительность**

Для получения помощи используйте:
```bash
ai-logs --help
ai-log-monitor --help
```
