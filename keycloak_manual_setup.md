# 🔐 Ручная настройка Keycloak для AI Engineering Platform

## Проблема
OpenID конфигурация не работает из-за неправильной настройки realm или клиента.

## Решение
Настроить Keycloak вручную через веб-интерфейс.

## Шаги настройки

### 1. Открыть Keycloak Admin
- URL: http://localhost:8080/admin
- Логин: `admin`
- Пароль: `admin`

### 2. Создать новый realm
1. Нажать на выпадающий список в левом верхнем углу (сейчас "master")
2. Выбрать "Create Realm"
3. Заполнить форму:
   - **Realm name**: `ai-engineering`
   - **Enabled**: ✅ ON
   - **SSL Required**: `None` (для разработки)
4. Нажать "Create"

### 3. Создать клиента
1. В левом меню выбрать "Clients"
2. Нажать "Create"
3. Заполнить форму:
   - **Client ID**: `ai-frontend`
   - **Client Protocol**: `openid-connect`
   - **Root URL**: `http://localhost:3000`
4. Нажать "Save"

### 4. Настроить клиента
После создания клиента настроить следующие параметры:

#### Вкладка "Settings":
- **Access Type**: `public`
- **Standard Flow Enabled**: ✅ ON
- **Implicit Flow Enabled**: ❌ OFF
- **Direct Access Grants Enabled**: ✅ ON
- **Service Accounts Enabled**: ❌ OFF
- **Authorization Enabled**: ❌ OFF

#### Вкладка "Valid Redirect URIs":
- Добавить: `http://localhost:3000/*`
- Добавить: `http://localhost:3000`

#### Вкладка "Web Origins":
- Добавить: `http://localhost:3000`
- Добавить: `*`

### 5. Создать пользователя
1. В левом меню выбрать "Users"
2. Нажать "Create new user"
3. Заполнить форму:
   - **Username**: `testuser`
   - **Email**: `test@example.com`
   - **First Name**: `Test`
   - **Last Name**: `User`
   - **Email Verified**: ✅ ON
4. Нажать "Save"

### 6. Установить пароль пользователя
1. Перейти на вкладку "Credentials"
2. Нажать "Set password"
3. Заполнить форму:
   - **Password**: `testpass`
   - **Password Confirmation**: `testpass`
   - **Temporary**: ❌ OFF
4. Нажать "Save"

### 7. Проверить настройки
1. Открыть: http://localhost:8080/realms/ai-engineering/.well-known/openid_configuration
2. Должна открыться JSON конфигурация
3. Проверить, что `issuer` содержит правильный URL

### 8. Протестировать авторизацию
1. Открыть фронтенд: http://localhost:3000
2. Попробовать войти в систему
3. Использовать тестовые данные:
   - **Username**: `testuser`
   - **Password**: `testpass`

## Альтернативное решение

Если ручная настройка не работает, можно использовать master realm:

1. Оставить realm "master"
2. Создать клиента в master realm
3. Обновить конфигурацию фронтенда:
   ```typescript
   keycloak: {
     url: 'http://localhost:8080',
     realm: 'master',
     clientId: 'ai-frontend',
   }
   ```

## Проверка статуса

После настройки проверить:
- ✅ Realm доступен: http://localhost:8080/realms/ai-engineering
- ✅ OpenID конфигурация: http://localhost:8080/realms/ai-engineering/.well-known/openid_configuration
- ✅ Фронтенд работает: http://localhost:3000
- ✅ Авторизация работает в браузере
