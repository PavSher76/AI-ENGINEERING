# Руководство по развертыванию AI Engineering Platform

## Требования к системе

### Минимальные требования
- **ОС**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10/11
- **RAM**: 8 GB (рекомендуется 16 GB)
- **CPU**: 4 ядра (рекомендуется 8 ядер)
- **Диск**: 50 GB свободного места
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Рекомендуемые требования
- **RAM**: 32 GB
- **CPU**: 16 ядер
- **Диск**: 200 GB SSD
- **Сеть**: 1 Gbps

## Установка зависимостей

### 1. Установка Docker

#### Ubuntu/Debian
```bash
# Обновление пакетов
sudo apt update

# Установка зависимостей
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

#### macOS
```bash
# Установка через Homebrew
brew install --cask docker

# Или скачать Docker Desktop с официального сайта
# https://www.docker.com/products/docker-desktop
```

#### Windows
1. Скачайте Docker Desktop с официального сайта
2. Установите и запустите Docker Desktop
3. Включите WSL 2 integration

### 2. Установка Docker Compose

#### Ubuntu/Debian
```bash
sudo apt install docker-compose-plugin
```

#### macOS/Windows
Docker Compose входит в состав Docker Desktop

### 3. Установка Ollama (рекомендуется)

#### Linux/macOS
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
1. Скачайте установщик с https://ollama.ai/download
2. Запустите установщик

## Развертывание системы

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd AI-Engineeting
```

### 2. Настройка окружения
```bash
# Создание .env файла
cp .env.example .env

# Редактирование переменных окружения
nano .env
```

### 3. Запуск системы
```bash
# Запуск всех сервисов
./scripts/setup.sh

# Или вручную
docker-compose up -d
```

### 4. Проверка статуса
```bash
# Проверка статуса контейнеров
./scripts/status.sh

# Или
docker-compose ps
```

## Настройка Ollama

### 1. Запуск Ollama
```bash
ollama serve
```

### 2. Загрузка моделей
```bash
# Загрузка базовой модели
ollama pull llama2

# Загрузка модели для эмбеддингов
ollama pull nomic-embed-text

# Проверка установленных моделей
ollama list
```

### 3. Настройка моделей в системе
Отредактируйте файл `.env`:
```env
DEFAULT_MODEL=llama2
EMBEDDING_MODEL=nomic-embed-text
```

## Настройка Keycloak

### 1. Доступ к Keycloak
- URL: http://localhost:8080
- Логин: admin
- Пароль: admin123

### 2. Создание realm
1. Войдите в Keycloak
2. Создайте новый realm "ai-engineering"
3. Настройте realm согласно требованиям

### 3. Создание клиента
1. Создайте клиента "ai-frontend"
2. Настройте redirect URIs
3. Включите Client authentication

### 4. Создание пользователей
1. Создайте пользователей в realm
2. Назначьте роли
3. Настройте пароли

## Настройка MinIO

### 1. Доступ к MinIO Console
- URL: http://localhost:9001
- Логин: minioadmin
- Пароль: minioadmin123

### 2. Создание buckets
1. Создайте bucket "ai-engineering"
2. Настройте политики доступа
3. Включите версионирование

## Мониторинг и логирование

### 1. Просмотр логов
```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f rag-service

# Логи с временными метками
docker-compose logs -f -t
```

### 2. Мониторинг ресурсов
```bash
# Использование ресурсов
docker stats

# Информация о контейнерах
docker-compose ps
```

### 3. Health checks
```bash
# Проверка здоровья сервисов
curl http://localhost:8001/health  # RAG Service
curl http://localhost:8012/health  # Ollama Management Service
curl http://localhost:3000         # Frontend
```

## Резервное копирование

### 1. Backup базы данных
```bash
# Создание backup
docker-compose exec postgres pg_dump -U ai_user ai_engineering > backup.sql

# Восстановление из backup
docker-compose exec -T postgres psql -U ai_user ai_engineering < backup.sql
```

### 2. Backup файлов
```bash
# Копирование данных MinIO
docker cp $(docker-compose ps -q minio):/data ./minio-backup

# Копирование данных Qdrant
docker cp $(docker-compose ps -q qdrant):/qdrant/storage ./qdrant-backup
```

### 3. Backup конфигурации
```bash
# Копирование конфигурационных файлов
tar -czf config-backup.tar.gz docker-compose.yml .env infrastructure/
```

## Обновление системы

### 1. Обновление кода
```bash
# Остановка системы
./scripts/stop.sh

# Обновление кода
git pull origin main

# Пересборка образов
docker-compose build --no-cache

# Запуск системы
./scripts/setup.sh
```

### 2. Обновление зависимостей
```bash
# Обновление Docker образов
docker-compose pull

# Перезапуск сервисов
docker-compose up -d
```

## Устранение неполадок

### 1. Проблемы с запуском
```bash
# Проверка логов
docker-compose logs

# Проверка статуса контейнеров
docker-compose ps

# Перезапуск сервисов
docker-compose restart
```

### 2. Проблемы с сетью
```bash
# Проверка сетей Docker
docker network ls

# Проверка подключения между контейнерами
docker-compose exec rag-service ping ollama-service
```

### 3. Проблемы с базой данных
```bash
# Проверка подключения к PostgreSQL
docker-compose exec postgres psql -U ai_user -d ai_engineering -c "SELECT 1;"

# Проверка таблиц
docker-compose exec postgres psql -U ai_user -d ai_engineering -c "\dt"
```

### 4. Проблемы с Ollama
```bash
# Проверка статуса Ollama
curl http://localhost:11434/api/tags

# Перезапуск Ollama
ollama serve
```

## Безопасность

### 1. Изменение паролей по умолчанию
```bash
# Изменение паролей в .env файле
nano .env
```

### 2. Настройка SSL
```bash
# Генерация SSL сертификатов
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Настройка Nginx для SSL
# Отредактируйте infrastructure/nginx/nginx.conf
```

### 3. Настройка файрвола
```bash
# Настройка UFW (Ubuntu)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## Производительность

### 1. Оптимизация Docker
```bash
# Очистка неиспользуемых ресурсов
docker system prune -a

# Ограничение ресурсов для контейнеров
# Отредактируйте docker-compose.yml
```

### 2. Оптимизация базы данных
```bash
# Настройка PostgreSQL
# Отредактируйте infrastructure/postgres/postgresql.conf
```

### 3. Мониторинг производительности
```bash
# Установка мониторинга
docker-compose -f docker-compose.monitoring.yml up -d
```

## Масштабирование

### 1. Горизонтальное масштабирование
```bash
# Масштабирование сервисов
docker-compose up -d --scale rag-service=3
docker-compose up -d --scale ollama-service=2
```

### 2. Настройка Load Balancer
```bash
# Настройка Nginx для балансировки нагрузки
# Отредактируйте infrastructure/nginx/nginx.conf
```

### 3. Кластеризация
```bash
# Настройка Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml ai-engineering
```
