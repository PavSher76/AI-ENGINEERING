#!/bin/bash

# Скрипт настройки и запуска AI Engineering Platform

echo "🚀 Настройка AI Engineering Platform..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose."
    exit 1
fi

# Проверка наличия Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama не установлен. Пожалуйста, установите Ollama для работы с ИИ моделями."
    echo "Инструкции по установке: https://ollama.ai/"
    read -p "Продолжить без Ollama? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cat > .env << EOF
# Database
POSTGRES_DB=ai_engineering
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password

# Redis
REDIS_PASSWORD=redis_password

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# RabbitMQ
RABBITMQ_DEFAULT_USER=rabbitmq
RABBITMQ_DEFAULT_PASS=rabbitmq123

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin123

# Ollama
OLLAMA_HOST=host.docker.internal:11434

# JWT Secret
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Environment
NODE_ENV=development
EOF
    echo "✅ .env файл создан"
fi

# Создание директорий для данных
echo "📁 Создание директорий для данных..."
mkdir -p data/{postgres,redis,chroma,minio,rabbitmq,keycloak}

# Запуск сервисов
echo "🐳 Запуск Docker контейнеров..."
docker-compose up -d

# Ожидание готовности сервисов
echo "⏳ Ожидание готовности сервисов..."
sleep 30

# Инициализация базы данных
echo "🗄️  Инициализация базы данных..."
./scripts/init-db.sh

# Проверка статуса сервисов
echo "🔍 Проверка статуса сервисов..."
docker-compose ps

echo ""
echo "🎉 AI Engineering Platform успешно запущена!"
echo ""
echo "📋 Доступные сервисы:"
echo "  🌐 Frontend: http://localhost:3000"
echo "  🔐 Keycloak: http://localhost:8080 (admin/admin123)"
echo "  📊 MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo "  🐰 RabbitMQ Management: http://localhost:15672 (rabbitmq/rabbitmq123)"
echo "  🗄️  PostgreSQL: localhost:5432"
echo "  🔴 Redis: localhost:6379"
echo "  🧠 ChromaDB: http://localhost:8000"
echo ""
echo "🔧 API Endpoints:"
echo "  📚 RAG Service: http://localhost:8001"
echo "  🤖 AI-NK Service: http://localhost:8002"
echo "  💬 Chat Service: http://localhost:8003"
echo "  📖 Consultation Service: http://localhost:8004"
echo "  📁 Archive Service: http://localhost:8005"
echo "  🧮 Calculation Service: http://localhost:8006"
echo "  ✅ Validation Service: http://localhost:8007"
echo "  📄 Document Service: http://localhost:8008"
echo "  📈 Analytics Service: http://localhost:8009"
echo "  🔗 Integration Service: http://localhost:8010"
echo ""
echo "📖 Для остановки сервисов выполните: docker-compose down"
echo "📖 Для просмотра логов: docker-compose logs -f [service-name]"
