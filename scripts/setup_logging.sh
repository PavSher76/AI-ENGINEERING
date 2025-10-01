#!/bin/bash

# Скрипт настройки логирования для AI Engineering проекта

set -e

echo "🔧 Настройка системы логирования AI Engineering..."

# Создание директорий для логов
echo "📁 Создание директорий для логов..."
mkdir -p /app/logs
mkdir -p /app/configs
mkdir -p /app/scripts

# Установка прав доступа
echo "🔐 Настройка прав доступа..."
chmod 755 /app/logs
chmod 644 /app/logs/*.log 2>/dev/null || true

# Копирование конфигурации logrotate
echo "📋 Настройка ротации логов..."
if [ -f "/app/configs/logrotate.conf" ]; then
    cp /app/configs/logrotate.conf /etc/logrotate.d/ai-engineering
    echo "✅ Конфигурация logrotate установлена"
else
    echo "⚠️ Файл конфигурации logrotate не найден"
fi

# Создание cron задачи для ротации логов
echo "⏰ Настройка автоматической ротации логов..."
cat > /etc/cron.daily/ai-engineering-logs << 'EOF'
#!/bin/bash
# Ротация логов AI Engineering проекта

LOG_DIR="/app/logs"
DATE=$(date +%Y%m%d)

# Создание архива старых логов
find $LOG_DIR -name "*.log.*" -mtime +30 -delete

# Сжатие старых логов
find $LOG_DIR -name "*.log.*" -not -name "*.gz" -exec gzip {} \;

# Очистка очень старых архивов
find $LOG_DIR -name "*.log.*.gz" -mtime +90 -delete

echo "$(date): Ротация логов AI Engineering выполнена" >> $LOG_DIR/rotation.log
EOF

chmod +x /etc/cron.daily/ai-engineering-logs

# Создание скрипта мониторинга
echo "📊 Настройка мониторинга логов..."
if [ -f "/app/scripts/log_monitor.py" ]; then
    chmod +x /app/scripts/log_monitor.py
    echo "✅ Скрипт мониторинга настроен"
else
    echo "⚠️ Скрипт мониторинга не найден"
fi

# Создание символических ссылок для удобства
echo "🔗 Создание символических ссылок..."
ln -sf /app/scripts/log_monitor.py /usr/local/bin/ai-log-monitor 2>/dev/null || true

# Настройка rsyslog для централизованного логирования (опционально)
echo "📡 Настройка централизованного логирования..."
cat > /etc/rsyslog.d/50-ai-engineering.conf << 'EOF'
# Конфигурация rsyslog для AI Engineering проекта

# Логи Chat Service
:programname, isequal, "chat-service" /app/logs/chat-service.log
& stop

# Логи QR Validation Service  
:programname, isequal, "qr-validation-service" /app/logs/qr-validation-service.log
& stop

# Логи TechExpert Connector
:programname, isequal, "techexpert-connector" /app/logs/techexpert-connector.log
& stop

# Логи RAG Service
:programname, isequal, "rag-service" /app/logs/rag-service.log
& stop

# Логи Ollama Service
:programname, isequal, "ollama-service" /app/logs/ollama-service.log
& stop

# Логи Outgoing Control Service
:programname, isequal, "outgoing-control-service" /app/logs/outgoing-control-service.log
& stop
EOF

# Перезапуск rsyslog
systemctl restart rsyslog 2>/dev/null || true

# Создание скрипта для просмотра логов
echo "👁️ Создание утилит для просмотра логов..."
cat > /usr/local/bin/ai-logs << 'EOF'
#!/bin/bash
# Утилита для просмотра логов AI Engineering

case "$1" in
    "chat")
        tail -f /app/logs/chat-service.log
        ;;
    "qr")
        tail -f /app/logs/qr-validation-service.log
        ;;
    "techexpert")
        tail -f /app/logs/techexpert-connector.log
        ;;
    "rag")
        tail -f /app/logs/rag-service.log
        ;;
    "ollama")
        tail -f /app/logs/ollama-service.log
        ;;
    "outgoing")
        tail -f /app/logs/outgoing-control-service.log
        ;;
    "errors")
        echo "=== ОШИБКИ CHAT SERVICE ==="
        tail -20 /app/logs/chat-service_errors.log 2>/dev/null || echo "Нет ошибок"
        echo ""
        echo "=== ОШИБКИ QR VALIDATION SERVICE ==="
        tail -20 /app/logs/qr-validation-service_errors.log 2>/dev/null || echo "Нет ошибок"
        echo ""
        echo "=== ОШИБКИ TECHEXPERT CONNECTOR ==="
        tail -20 /app/logs/techexpert-connector_errors.log 2>/dev/null || echo "Нет ошибок"
        echo ""
        echo "=== ОШИБКИ RAG SERVICE ==="
        tail -20 /app/logs/rag-service_errors.log 2>/dev/null || echo "Нет ошибок"
        echo ""
        echo "=== ОШИБКИ OLLAMA SERVICE ==="
        tail -20 /app/logs/ollama-service_errors.log 2>/dev/null || echo "Нет ошибок"
        echo ""
        echo "=== ОШИБКИ OUTGOING CONTROL SERVICE ==="
        tail -20 /app/logs/outgoing-control-service_errors.log 2>/dev/null || echo "Нет ошибок"
        ;;
    "status")
        python3 /app/scripts/log_monitor.py --status
        ;;
    "report")
        python3 /app/scripts/log_monitor.py --report
        ;;
    *)
        echo "Использование: ai-logs {chat|qr|techexpert|rag|ollama|outgoing|errors|status|report}"
        echo ""
        echo "Команды:"
        echo "  chat      - Логи Chat Service"
        echo "  qr        - Логи QR Validation Service"
        echo "  techexpert - Логи TechExpert Connector"
        echo "  rag       - Логи RAG Service"
        echo "  ollama    - Логи Ollama Service"
        echo "  outgoing  - Логи Outgoing Control Service"
        echo "  errors    - Все ошибки"
        echo "  status    - Статус сервисов"
        echo "  report    - Отчет по логам"
        ;;
esac
EOF

chmod +x /usr/local/bin/ai-logs

# Создание скрипта для очистки логов
echo "🧹 Создание утилиты очистки логов..."
cat > /usr/local/bin/ai-logs-clean << 'EOF'
#!/bin/bash
# Утилита для очистки логов AI Engineering

echo "🧹 Очистка логов AI Engineering..."

# Подтверждение
read -p "Вы уверены, что хотите очистить все логи? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено"
    exit 1
fi

# Очистка основных логов
find /app/logs -name "*.log" -exec truncate -s 0 {} \;

# Удаление старых ротированных логов
find /app/logs -name "*.log.*" -mtime +7 -delete

echo "✅ Логи очищены"
EOF

chmod +x /usr/local/bin/ai-logs-clean

# Создание конфигурации для ELK Stack (опционально)
echo "📊 Создание конфигурации для ELK Stack..."
cat > /app/configs/filebeat.yml << 'EOF'
# Конфигурация Filebeat для AI Engineering проекта

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

processors:
- add_host_metadata:
    when.not.contains.tags: forwarded
EOF

# Создание README для логирования
echo "📖 Создание документации по логированию..."
cat > /app/logs/README.md << 'EOF'
# Логи AI Engineering проекта

## Структура логов

- `chat-service.log` - Основные логи Chat Service
- `chat-service_errors.log` - Ошибки Chat Service
- `qr-validation-service.log` - Основные логи QR Validation Service
- `qr-validation-service_errors.log` - Ошибки QR Validation Service
- `techexpert-connector.log` - Основные логи TechExpert Connector
- `techexpert-connector_errors.log` - Ошибки TechExpert Connector
- `rag-service.log` - Основные логи RAG Service
- `rag-service_errors.log` - Ошибки RAG Service
- `ollama-service.log` - Основные логи Ollama Service
- `ollama-service_errors.log` - Ошибки Ollama Service
- `outgoing-control-service.log` - Основные логи Outgoing Control Service
- `outgoing-control-service_errors.log` - Ошибки Outgoing Control Service

## Утилиты

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
```

### Очистка логов
```bash
# Очистка всех логов
ai-logs-clean
```

## Ротация логов

Логи автоматически ротируются ежедневно с помощью logrotate:
- Основные логи: 7-30 дней (в зависимости от сервиса)
- Логи ошибок: 7-30 дней
- Сжатие старых логов
- Автоматическое удаление очень старых логов

## Форматы логов

### Обычные логи
```
2024-01-01 12:00:00 - service-name - INFO - message
```

### Структурированные логи (JSON)
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "level": "INFO",
  "logger": "service-name",
  "message": "message",
  "request_id": "req_123",
  "duration": 0.123
}
```

## Мониторинг

- Используйте `ai-logs status` для проверки статуса сервисов
- Используйте `ai-logs errors` для просмотра ошибок
- Используйте `ai-log-monitor --report` для детального анализа
EOF

echo ""
echo "✅ Настройка логирования завершена!"
echo ""
echo "📋 Доступные команды:"
echo "  ai-logs {service}  - Просмотр логов сервиса"
echo "  ai-logs errors     - Просмотр всех ошибок"
echo "  ai-logs status     - Статус сервисов"
echo "  ai-logs report     - Отчет по логам"
echo "  ai-logs-clean      - Очистка логов"
echo ""
echo "📊 Мониторинг:"
echo "  ai-log-monitor --watch --service {service}  - Мониторинг в реальном времени"
echo "  ai-log-monitor --report                     - Генерация отчета"
echo ""
echo "📁 Логи находятся в: /app/logs/"
echo "📖 Документация: /app/logs/README.md"
