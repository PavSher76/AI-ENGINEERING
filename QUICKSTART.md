# Быстрый старт AI Engineering Platform

## 🚀 Запуск за 5 минут

### 1. Установка зависимостей

#### Docker и Docker Compose
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# macOS
brew install --cask docker

# Windows
# Скачайте Docker Desktop с https://www.docker.com/products/docker-desktop
```

#### Ollama (для работы с ИИ)
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Скачайте с https://ollama.ai/download
```

### 2. Запуск системы

```bash
# Клонирование проекта
git clone <repository-url>
cd AI-Engineeting

# Запуск всех сервисов
./scripts/setup.sh
```

### 3. Настройка Ollama

```bash
# Запуск Ollama
ollama serve

# В новом терминале - загрузка модели
ollama pull llama2
```

### 4. Доступ к системе

После успешного запуска система будет доступна по адресам:

- **🌐 Frontend**: http://localhost:3000
- **📊 MinIO**: http://localhost:9001 (minioadmin/minioadmin123)
- **🐰 RabbitMQ**: http://localhost:15672 (rabbitmq/rabbitmq123)

### ⚠️ Авторизация отключена

Для упрощения разработки **авторизация отключена**. Система работает без Keycloak и проверки токенов. Все функции доступны без входа в систему.

## 📋 Первые шаги

### 1. Доступ к системе
1. Откройте http://localhost:3000
2. Система откроется без запроса авторизации
3. Вы автоматически войдете как "Разработчик Системы"

### 2. Создание проекта
1. В панели управления выберите "Создать проект"
2. Заполните информацию о проекте
3. Выберите созданный проект в боковом меню

### 3. Загрузка документов
1. Перейдите в раздел "Документы"
2. Создайте коллекцию документов
3. Загрузите файлы (PDF, DOCX, TXT)

### 4. Чат с ИИ
1. Перейдите в раздел "Чат с ИИ"
2. Задайте вопрос по загруженным документам
3. ИИ проанализирует документы и даст ответ

## 🔧 Полезные команды

```bash
# Проверка статуса
./scripts/status.sh

# Остановка системы
./scripts/stop.sh

# Просмотр логов
docker-compose logs -f

# Перезапуск сервисов
docker-compose restart
```

## 🆘 Решение проблем

### Система не запускается
```bash
# Проверьте, что Docker запущен
docker --version
docker-compose --version

# Проверьте логи
docker-compose logs
```

### Ollama не работает
```bash
# Проверьте статус Ollama
ollama list

# Перезапустите Ollama
ollama serve
```

### Проблемы с базой данных
```bash
# Пересоздайте базу данных
docker-compose down -v
docker-compose up -d
./scripts/init-db.sh
```

## 📚 Дополнительная информация

- **Архитектура**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Развертывание**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **API документация**: http://localhost:8001/docs (RAG Service)
- **API документация**: http://localhost:8012/docs (Ollama Management Service)

## 🎯 Что дальше?

1. **Изучите API**: Используйте Swagger UI для изучения доступных endpoints
2. **Настройте модели**: Загрузите дополнительные модели Ollama
3. **Интегрируйте данные**: Подключите ваши существующие системы
4. **Настройте безопасность**: Измените пароли по умолчанию
5. **Масштабируйте**: Настройте кластер для production использования

## 💡 Советы

- Начните с загрузки небольшого количества документов для тестирования
- Используйте разные типы коллекций для организации документов
- Экспериментируйте с различными моделями Ollama
- Настройте мониторинг для отслеживания производительности

---

**Готово!** 🎉 Ваша AI Engineering Platform готова к работе!
