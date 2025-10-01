# 🚀 Быстрый старт AI Engineering Platform

## 📋 Предварительные требования

- Docker и Docker Compose
- Node.js 18+ (для frontend разработки)
- Python 3.9+ (для backend разработки)

## ⚡ Быстрый запуск

### 1. Запуск всех сервисов
```bash
# Клонируйте репозиторий
git clone https://github.com/PavSher76/AI-ENGINEERING.git
cd AI-ENGINEERING

# Запустите все сервисы
docker-compose up -d

# Проверьте статус
docker-compose ps
```

### 2. Настройка Keycloak (авторизация)
```bash
# Откройте админ-консоль Keycloak
./scripts/open_keycloak_admin.sh

# Или вручную: http://localhost:8080/admin
# Логин: admin, Пароль: admin
```

**Создайте в Keycloak:**
1. Realm: `ai-engineering`
2. Client: `ai-frontend`
3. Пользователей с ролями (admin, developer, analyst, viewer)

### 3. Запуск Frontend (для разработки)
```bash
cd frontend
npm install
npm start
# Откроется http://localhost:3000
```

## 🌐 Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:3000 | React приложение |
| **Nginx** | http://localhost:80 | Reverse proxy |
| **Keycloak** | http://localhost:8080 | Авторизация |
| **Chat API** | http://localhost:80/api/chat | API чата |
| **MinIO** | http://localhost:9001 | Файловое хранилище |
| **RabbitMQ** | http://localhost:15672 | Очереди сообщений |

## 🔐 Тестовые пользователи

После настройки Keycloak создайте пользователей:

| Пользователь | Пароль | Роли |
|-------------|--------|------|
| admin | admin | admin, user |
| developer | developer | developer, user |
| analyst | analyst | analyst, user |
| viewer | viewer | viewer |

## 🧪 Тестирование

```bash
# Тест авторизации
python3 scripts/test_auth.py

# Тест frontend интеграции
python3 scripts/test_frontend_integration.py

# Тест Keycloak
python3 scripts/test_frontend_auth.py
```

## 📚 Документация

- [Настройка Keycloak](docs/KEYCLOAK_AUTH_GUIDE.md)
- [Настройка Frontend авторизации](docs/FRONTEND_AUTH_SETUP.md)
- [Отчет по реализации авторизации](docs/AUTH_IMPLEMENTATION_REPORT.md)

## 🛠️ Режимы работы

### Режим разработки (Development)
- ✅ Приложение доступно без входа
- ✅ Мок-пользователь для тестирования
- ✅ API работает без токенов
- ✅ Все роли разрешены

### Production режим
- 🔐 Обязательная авторизация
- 🔐 Проверка JWT токенов
- 🔐 Проверка ролей и прав
- 🔐 Автоматическое обновление токенов

## 🚨 Устранение неполадок

### Keycloak недоступен
```bash
# Перезапустите Keycloak
docker-compose restart keycloak

# Проверьте логи
docker-compose logs keycloak
```

### CORS ошибки
```bash
# Перезапустите Nginx
docker-compose restart nginx
```

### Frontend не запускается
```bash
# Очистите кэш
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

## 📞 Поддержка

- 📖 Документация: `docs/`
- 🧪 Тесты: `scripts/test_*.py`
- 🔧 Скрипты: `scripts/`

---

**🎉 Готово! Ваша AI Engineering Platform запущена и готова к работе!**
