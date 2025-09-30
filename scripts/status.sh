#!/bin/bash

# Скрипт проверки статуса AI Engineering Platform

echo "📊 Статус AI Engineering Platform"
echo "=================================="

# Проверка Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker установлен"
    docker --version
else
    echo "❌ Docker не установлен"
fi

# Проверка Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose установлен"
    docker-compose --version
else
    echo "❌ Docker Compose не установлен"
fi

# Проверка Ollama
if command -v ollama &> /dev/null; then
    echo "✅ Ollama установлен"
    ollama --version
else
    echo "⚠️  Ollama не установлен (рекомендуется для работы с ИИ)"
fi

echo ""
echo "🐳 Статус контейнеров:"
docker-compose ps

echo ""
echo "🌐 Доступные сервисы:"
echo "  Frontend: http://localhost:3000"
echo "  Keycloak: http://localhost:8080"
echo "  MinIO Console: http://localhost:9001"
echo "  RabbitMQ Management: http://localhost:15672"
echo "  PostgreSQL: localhost:5432"
echo "  Redis: localhost:6379"
echo "  ChromaDB: http://localhost:8000"

echo ""
echo "🔧 API Endpoints:"
echo "  RAG Service: http://localhost:8001"
echo "  AI-NK Service: http://localhost:8002"
echo "  Chat Service: http://localhost:8003"
echo "  Consultation Service: http://localhost:8004"
echo "  Archive Service: http://localhost:8005"
echo "  Calculation Service: http://localhost:8006"
echo "  Validation Service: http://localhost:8007"
echo "  Document Service: http://localhost:8008"
echo "  Analytics Service: http://localhost:8009"
echo "  Integration Service: http://localhost:8010"
