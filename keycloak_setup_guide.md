# 🔐 Инструкция по настройке Keycloak для AI Engineering Platform

## 📋 Обзор

Данная инструкция описывает полную настройку Keycloak для работы с AI Engineering Platform, включая создание realm, настройку клиентов и пользователей.

## 🌐 Доступ к Keycloak

### Админ-интерфейс
- **URL**: https://localhost:9080/admin
- **Логин**: `admin`
- **Пароль**: `admin`

### Основное приложение
- **URL**: https://localhost:9300
- **Realm**: `ai-engineering`
- **Client ID**: `ai-frontend`

## 🚀 Пошаговая настройка

### Шаг 1: Вход в админ-панель

1. Откройте браузер и перейдите на https://localhost:9080/admin
2. Примите предупреждение о безопасности (самоподписанный сертификат)
3. Войдите с учетными данными:
   - **Username**: `admin`
   - **Password**: `admin`

### Шаг 2: Создание Realm (если не существует)

1. В левом верхнем углу нажмите на выпадающий список "Master"
2. Выберите "Create realm"
3. Заполните форму:
   - **Realm name**: `ai-engineering`
   - **Display name**: `AI Engineering Platform`
   - **HTML display name**: `<div class="kc-logo-text"><span>AI Engineering</span></div>`
4. Нажмите "Create"

### Шаг 3: Настройка Realm

1. Перейдите в созданный realm `ai-engineering`
2. В левом меню выберите "Realm settings"
3. Настройте основные параметры:

#### General Settings:
- **Display name**: `AI Engineering Platform`
- **HTML display name**: `<div class="kc-logo-text"><span>AI Engineering</span></div>`
- **Frontend URL**: `https://localhost:9443`

#### Login Settings:
- **User registration**: `ON` (включить регистрацию пользователей)
- **Forgot password**: `ON` (включить восстановление пароля)
- **Remember me**: `ON` (включить "Запомнить меня")
- **Verify email**: `OFF` (отключить верификацию email)

#### Security Defenses:
- **SSL required**: `None` (для разработки)
- **Login with email**: `ON` (разрешить вход по email)

### Шаг 4: Создание клиента для фронтенда

1. В левом меню выберите "Clients"
2. Нажмите "Create client"
3. Заполните форму:

#### General Settings:
- **Client type**: `OpenID Connect`
- **Client ID**: `ai-frontend`
- **Name**: `AI Frontend Client`
- **Description**: `Frontend client for AI Engineering Platform`

4. Нажмите "Next"

#### Capability config:
- **Client authentication**: `OFF` (публичный клиент)
- **Authorization**: `OFF`
- **Authentication flow**: `Standard flow`
- **Direct access grants**: `OFF`
- **Service accounts roles**: `OFF`
- **OAuth 2.0 Device Authorization Grant**: `OFF`
- **OIDC CIBA Grant**: `OFF`

5. Нажмите "Next"

#### Login settings:
- **Root URL**: `https://localhost:9300`
- **Home URL**: `https://localhost:9300`
- **Valid redirect URIs**: 
  ```
  https://localhost:9300/*
  https://localhost/*
  ```
- **Valid post logout redirect URIs**: 
  ```
  https://localhost:9300/*
  https://localhost/*
  ```
- **Web origins**: 
  ```
  https://localhost:9300
  https://localhost
  ```

6. Нажмите "Save"

### Шаг 5: Дополнительные настройки клиента

1. В настройках клиента `ai-frontend` перейдите на вкладку "Advanced settings"
2. Настройте параметры:

#### Advanced Settings:
- **Access token lifespan**: `5 minutes`
- **Client session idle timeout**: `30 minutes`
- **Client session max lifespan**: `10 hours`
- **Access token lifespan for implicit flow**: `15 minutes`

#### Fine Grain OpenID Connect Configuration:
- **Access token signature algorithm**: `RS256`
- **ID token signature algorithm**: `RS256`
- **User info signed response algorithm**: `RS256`

### Шаг 6: Создание пользователей

1. В левом меню выберите "Users"
2. Нажмите "Create new user"
3. Заполните форму:

#### User Details:
- **Username**: `admin` (или любое другое имя)
- **Email**: `admin@ai-engineering.local`
- **First name**: `Admin`
- **Last name**: `User`
- **Email verified**: `ON`
- **Enabled**: `ON`

4. Нажмите "Create"

#### Установка пароля:
1. Перейдите на вкладку "Credentials"
2. Нажмите "Set password"
3. Введите пароль (например: `admin123`)
4. Отключите "Temporary" (чтобы пароль не был временным)
5. Нажмите "Save"

### Шаг 7: Создание ролей (опционально)

1. В левом меню выберите "Realm roles"
2. Нажмите "Create role"
3. Создайте роли:
   - **admin** - для администраторов
   - **user** - для обычных пользователей
   - **engineer** - для инженеров

### Шаг 8: Назначение ролей пользователям

1. Перейдите в "Users" → выберите пользователя
2. Перейдите на вкладку "Role mapping"
3. Нажмите "Assign role"
4. Выберите нужные роли и нажмите "Assign"

## 🔧 Дополнительные настройки

### Настройка тем оформления

1. В "Realm settings" → "Themes"
2. Настройте темы:
   - **Login theme**: `keycloak`
   - **Account theme**: `keycloak`
   - **Admin theme**: `keycloak`
   - **Email theme**: `keycloak`

### Настройка локализации

1. В "Realm settings" → "Localization"
2. Включите "Internationalization enabled"
3. Добавьте поддерживаемые локали:
   - `ru` (русский)
   - `en` (английский)
4. Установите "Default locale": `ru`

### Настройка событий (опционально)

1. В "Realm settings" → "Events"
2. Включите "Save events"
3. Выберите типы событий для логирования:
   - `LOGIN`
   - `LOGOUT`
   - `LOGIN_ERROR`
   - `REGISTER`

## 🧪 Тестирование настройки

### Проверка OpenID конфигурации

```bash
curl -k -s https://localhost:9080/realms/ai-engineering/.well-known/openid_configuration | jq .issuer
```

### Проверка клиента

```bash
curl -k -s -X GET "https://localhost:9080/admin/realms/ai-engineering/clients" \
  -H "Authorization: Bearer $(curl -k -s -X POST "https://localhost:9080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | jq -r '.access_token')" \
  | jq '.[] | select(.clientId=="ai-frontend")'
```

### Проверка фронтенда

1. Откройте https://localhost:9300
2. Примите предупреждение о безопасности
3. Попробуйте войти в систему
4. Проверьте, что авторизация работает корректно

## 🚨 Устранение неполадок

### Проблема: "HTTPS required"
**Решение**: Убедитесь, что в настройках realm установлено "SSL required": `None`

### Проблема: "Invalid redirect URI"
**Решение**: Проверьте, что в настройках клиента правильно указаны "Valid redirect URIs"

### Проблема: "Client not found"
**Решение**: Убедитесь, что клиент `ai-frontend` создан и включен

### Проблема: "User not found"
**Решение**: Проверьте, что пользователь создан и включен в realm

### Проблема: "Access denied"
**Решение**: Проверьте настройки ролей и их назначение пользователям

## 📝 Конфигурационные файлы

### Переменные окружения для фронтенда

```bash
REACT_APP_KEYCLOAK_URL=https://localhost:9443
REACT_APP_KEYCLOAK_REALM=ai-engineering
REACT_APP_KEYCLOAK_CLIENT_ID=ai-frontend
```

### Конфигурация Keycloak в docker-compose.yml

```yaml
keycloak:
  environment:
    KC_HOSTNAME_URL: https://localhost:9443
    KC_HOSTNAME_ADMIN_URL: https://localhost:9443
    KC_HTTPS_ENABLED: true
    KC_HTTP_ENABLED: false
```

## 🔒 Безопасность

### Для продакшена

1. **Измените пароли по умолчанию**
2. **Включите SSL required**: `External`
3. **Настройте HTTPS сертификаты**
4. **Ограничьте доступ к админ-панели**
5. **Настройте мониторинг и логирование**

### Рекомендации

- Используйте сложные пароли
- Регулярно обновляйте Keycloak
- Настройте резервное копирование
- Мониторьте логи на предмет подозрительной активности

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи Keycloak: `docker logs ai-engineering-keycloak-1`
2. Проверьте логи nginx: `docker logs ai-engineering-nginx-1`
3. Проверьте логи фронтенда в браузере (F12 → Console)
4. Убедитесь, что все сервисы запущены: `docker-compose ps`

---

**Примечание**: Данная инструкция предназначена для среды разработки. Для продакшена требуются дополнительные настройки безопасности.
