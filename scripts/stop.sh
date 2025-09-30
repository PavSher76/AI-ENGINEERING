#!/bin/bash

# Скрипт остановки AI Engineering Platform

echo "🛑 Остановка AI Engineering Platform..."

# Остановка всех сервисов
echo "🐳 Остановка Docker контейнеров..."
docker-compose down

# Очистка неиспользуемых ресурсов (опционально)
read -p "Удалить неиспользуемые Docker ресурсы? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Очистка Docker ресурсов..."
    docker system prune -f
    docker volume prune -f
fi

echo "✅ AI Engineering Platform остановлена!"
