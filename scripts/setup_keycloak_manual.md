# Ручная настройка Keycloak для AI Engineering Platform

## Шаг 1: Доступ к Keycloak Admin Console

1. Откройте браузер и перейдите по адресу: http://localhost:8080
2. Нажмите "Administration Console"
3. Войдите с учетными данными:
   - Username: `admin`
   - Password: `admin`

## Шаг 2: Создание Realm

1. В левом верхнем углу нажмите на выпадающий список "Master"
2. Выберите "Create Realm"
3. Заполните форму:
   - **Realm name**: `ai-engineering`
   - **Display name**: `AI Engineering Platform`
   - **Enabled**: ✅ (включено)
4. Нажмите "Create"

## Шаг 3: Создание клиентов

### Frontend Client

1. В левом меню выберите "Clients"
2. Нажмите "Create client"
3. Заполните форму:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `ai-frontend`
   - **Name**: `AI Frontend`
   - **Description**: `AI Engineering Platform Frontend Client`
4. Нажмите "Next"
5. Настройте Client settings:
   - **Client authentication**: `Off` (Public client)
   - **Authorization**: `Off`
   - **Authentication flow**: `Standard flow`
   - **Direct access grants**: `On`
   - **Service accounts roles**: `Off`
   - **OAuth 2.0 Device Authorization Grant**: `Off`
   - **OIDC Compatibility Mode**: `Off`
6. Нажмите "Next"
7. Настройте Login settings:
   - **Root URL**: `http://localhost:3000`
   - **Home URL**: `http://localhost:3000`
   - **Valid redirect URIs**: 
     - `http://localhost:3000/*`
     - `http://localhost:80/*`
   - **Valid post logout redirect URIs**: 
     - `http://localhost:3000/*`
     - `http://localhost:80/*`
   - **Web origins**: 
     - `http://localhost:3000`
     - `http://localhost:80`
8. Нажмите "Save"

### Backend Client

1. Нажмите "Create client"
2. Заполните форму:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `ai-backend`
   - **Name**: `AI Backend`
   - **Description**: `AI Engineering Platform Backend Client`
3. Нажмите "Next"
4. Настройте Client settings:
   - **Client authentication**: `On` (Confidential client)
   - **Authorization**: `Off`
   - **Authentication flow**: `Standard flow`
   - **Direct access grants**: `On`
   - **Service accounts roles**: `On`
   - **OAuth 2.0 Device Authorization Grant**: `Off`
   - **OIDC Compatibility Mode**: `Off`
5. Нажмите "Next"
6. Настройте Login settings:
   - **Root URL**: `http://localhost:8001`
   - **Valid redirect URIs**: 
     - `http://localhost:8001/*`
     - `http://localhost:8003/*`
   - **Web origins**: 
     - `http://localhost:8001`
     - `http://localhost:8003`
7. Нажмите "Save"
8. Перейдите на вкладку "Credentials"
9. Скопируйте **Secret** (понадобится для backend сервисов)

## Шаг 4: Создание ролей

1. В левом меню выберите "Realm roles"
2. Нажмите "Create role"
3. Создайте следующие роли:

### Realm Roles

1. **admin**
   - Role name: `admin`
   - Description: `Administrator role with full access`

2. **user**
   - Role name: `user`
   - Description: `Standard user role`

3. **developer**
   - Role name: `developer`
   - Description: `Developer role with development access`

4. **analyst**
   - Role name: `analyst`
   - Description: `Analyst role with data analysis access`

5. **viewer**
   - Role name: `viewer`
   - Description: `Viewer role with read-only access`

## Шаг 5: Создание пользователей

1. В левом меню выберите "Users"
2. Нажмите "Create new user"

### Admin User

1. Заполните форму:
   - **Username**: `admin`
   - **Email**: `admin@ai-engineering.local`
   - **First name**: `Администратор`
   - **Last name**: `Системы`
   - **Email verified**: ✅
   - **Enabled**: ✅
2. Нажмите "Create"
3. Перейдите на вкладку "Credentials"
4. Нажмите "Set password"
5. Заполните:
   - **Password**: `admin`
   - **Password confirmation**: `admin`
   - **Temporary**: ❌ (отключено)
6. Нажмите "Save"
7. Перейдите на вкладку "Role mapping"
8. Нажмите "Assign role"
9. Выберите роли: `admin`, `user`
10. Нажмите "Assign"

### Developer User

1. Создайте пользователя:
   - **Username**: `developer`
   - **Email**: `developer@ai-engineering.local`
   - **First name**: `Разработчик`
   - **Last name**: `Системы`
   - **Password**: `developer`
2. Назначьте роли: `developer`, `user`

### Analyst User

1. Создайте пользователя:
   - **Username**: `analyst`
   - **Email**: `analyst@ai-engineering.local`
   - **First name**: `Аналитик`
   - **Last name**: `Данных`
   - **Password**: `analyst`
2. Назначьте роли: `analyst`, `user`

### Viewer User

1. Создайте пользователя:
   - **Username**: `viewer`
   - **Email**: `viewer@ai-engineering.local`
   - **First name**: `Наблюдатель`
   - **Last name**: `Системы`
   - **Password**: `viewer`
2. Назначьте роли: `viewer`

## Шаг 6: Настройка Client Roles

### Frontend Client Roles

1. Перейдите в "Clients" → "ai-frontend"
2. Перейдите на вкладку "Roles"
3. Создайте роли:
   - `admin`
   - `user`
   - `developer`
   - `analyst`
   - `viewer`

### Backend Client Roles

1. Перейдите в "Clients" → "ai-backend"
2. Перейдите на вкладку "Roles"
3. Создайте роли:
   - `admin`
   - `user`
   - `developer`
   - `analyst`
   - `viewer`

## Шаг 7: Настройка Realm Settings

1. В левом меню выберите "Realm settings"
2. Перейдите на вкладку "General"
3. Настройте:
   - **Display name**: `AI Engineering Platform`
   - **HTML display name**: `<div class="kc-logo-text"><span>AI Engineering</span></div>`
   - **Frontend URL**: `http://localhost:3000`
   - **Admin URL**: `http://localhost:8080`
   - **Enabled**: ✅
   - **User managed access**: ❌
   - **Login with email**: ✅
   - **Duplicate emails**: ❌
   - **Login theme**: `keycloak`
   - **Account theme**: `keycloak`
   - **Admin theme**: `keycloak`
   - **Email theme**: `keycloak`
   - **Internationalization**: ✅
   - **Supported locales**: `English, Russian`
   - **Default locale**: `Russian`

4. Перейдите на вкладку "Login"
5. Настройте:
   - **User registration**: ✅
   - **Forgot password**: ✅
   - **Remember me**: ✅
   - **Verify email**: ❌
   - **Login with email**: ✅
   - **Duplicate emails**: ❌
   - **Require SSL**: `None` (для разработки)

6. Перейдите на вкладку "Tokens"
7. Настройте:
   - **Access token lifespan**: `5 minutes`
   - **Access token lifespan for implicit flow**: `15 minutes`
   - **Client session idle timeout**: `30 minutes`
   - **Client session max lifespan**: `10 hours`
   - **SSO session idle timeout**: `30 minutes`
   - **SSO session max lifespan**: `10 hours`
   - **Offline session idle timeout**: `30 days`
   - **Access code lifespan**: `1 minute`
   - **Access code lifespan user action**: `5 minutes`
   - **Refresh token max reuse**: `0`

## Шаг 8: Проверка настройки

### Тест входа

1. Откройте новую вкладку браузера
2. Перейдите по адресу: http://localhost:8080/realms/ai-engineering/account
3. Войдите с учетными данными: `admin/admin`
4. Проверьте, что вход прошел успешно

### Тест API

1. Получите токен через API:
```bash
curl -X POST "http://localhost:8080/realms/ai-engineering/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=ai-frontend"
```

## Готово!

После выполнения всех шагов у вас будет настроенный Keycloak с:

- ✅ Realm `ai-engineering`
- ✅ Frontend client `ai-frontend`
- ✅ Backend client `ai-backend`
- ✅ Роли: admin, user, developer, analyst, viewer
- ✅ Пользователи: admin/admin, developer/developer, analyst/analyst, viewer/viewer
- ✅ Настроенные токены и сессии

## Следующие шаги

1. Интегрировать Keycloak в frontend приложение
2. Настроить авторизацию в backend сервисах
3. Протестировать полный цикл аутентификации
