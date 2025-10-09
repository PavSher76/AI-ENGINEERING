# ⚡ Быстрая настройка Keycloak

## 🎯 Цель
Настроить Keycloak для работы с AI Engineering Platform за 5 минут.

## 🚀 Быстрые шаги

### 1. Откройте Keycloak Admin
- URL: https://localhost:9080/admin
- Логин: `admin` / Пароль: `admin`

### 2. Создайте Realm (если нужно)
- Нажмите "Create realm"
- Name: `ai-engineering`
- Display name: `AI Engineering Platform`

### 3. Создайте клиента
- Clients → Create client
- Client ID: `ai-frontend`
- Client type: `OpenID Connect`
- Client authentication: `OFF`
- Valid redirect URIs: `https://localhost:9300/*`
- Web origins: `https://localhost:9300`

### 4. Создайте пользователя
- Users → Create new user
- Username: `admin`
- Email: `admin@ai-engineering.local`
- Credentials → Set password: `admin123`

### 5. Настройте Realm
- Realm settings → General
- Frontend URL: `https://localhost:9443`
- SSL required: `None`

## ✅ Проверка
1. Откройте https://localhost:9300
2. Попробуйте войти с `admin` / `admin123`
3. Если работает - настройка завершена!

## 🚨 Если не работает
1. Проверьте логи: `docker logs ai-engineering-keycloak-1`
2. Убедитесь, что все сервисы запущены: `docker-compose ps`
3. Очистите кэш браузера
4. Попробуйте режим инкогнито

---
**Подробная инструкция**: `keycloak_setup_guide.md`
