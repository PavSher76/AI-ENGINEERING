#!/bin/bash

# Автоматическая настройка Keycloak для AI Engineering Platform

echo "🔐 Автоматическая настройка Keycloak"
echo "======================================"
echo ""

# Проверяем, что Keycloak запущен
echo "⏳ Проверка доступности Keycloak..."
if ! curl -s -f http://localhost:8080/realms/master > /dev/null 2>&1; then
    echo "❌ Keycloak не запущен. Запустите его командой:"
    echo "   docker-compose up -d keycloak"
    echo ""
    exit 1
fi

echo "✅ Keycloak доступен"
echo ""

# Получаем токен администратора
echo "🔑 Получение токена администратора..."
ADMIN_TOKEN=$(curl -s -X POST \
  http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Не удалось получить токен администратора"
    echo "   Проверьте, что Keycloak запущен и доступен"
    exit 1
fi

echo "✅ Токен администратора получен"
echo ""

# Создаем realm ai-engineering
echo "🏗️ Создание realm 'ai-engineering'..."
REALM_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -X POST \
  http://localhost:8080/admin/realms \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "ai-engineering",
    "enabled": true,
    "displayName": "AI Engineering Platform",
    "displayNameHtml": "<div class=\"kc-logo-text\"><span>AI Engineering</span></div>",
    "loginTheme": "keycloak",
    "accountTheme": "keycloak",
    "adminTheme": "keycloak",
    "emailTheme": "keycloak",
    "accessTokenLifespan": 300,
    "accessTokenLifespanForImplicitFlow": 900,
    "ssoSessionIdleTimeout": 1800,
    "ssoSessionMaxLifespan": 36000,
    "ssoSessionIdleTimeoutRememberMe": 0,
    "ssoSessionMaxLifespanRememberMe": 0,
    "offlineSessionIdleTimeout": 2592000,
    "offlineSessionMaxLifespanEnabled": false,
    "offlineSessionMaxLifespan": 5184000,
    "clientSessionIdleTimeout": 0,
    "clientSessionMaxLifespan": 0,
    "clientOfflineSessionIdleTimeout": 0,
    "clientOfflineSessionMaxLifespan": 0,
    "accessCodeLifespan": 60,
    "accessCodeLifespanUserAction": 300,
    "accessCodeLifespanLogin": 1800,
    "actionTokenGeneratedByAdminLifespan": 43200,
    "actionTokenGeneratedByUserLifespan": 300,
    "oauth2DeviceCodeLifespan": 600,
    "oauth2DevicePollingInterval": 5,
    "internationalizationEnabled": true,
    "supportedLocales": ["en", "ru"],
    "defaultLocale": "ru",
    "loginWithEmailAllowed": true,
    "duplicateEmailsAllowed": false,
    "resetPasswordAllowed": true,
    "editUsernameAllowed": false,
    "bruteForceProtected": false,
    "permanentLockout": false,
    "maxFailureWaitSeconds": 900,
    "minimumQuickLoginWaitSeconds": 60,
    "waitIncrementSeconds": 60,
    "quickLoginCheckMilliSeconds": 1000,
    "maxDeltaTimeSeconds": 43200,
    "failureFactor": 30,
    "defaultSignatureAlgorithm": "RS256",
    "revokeRefreshToken": false,
    "refreshTokenMaxReuse": 0,
    "accessTokenLifespanForImplicitFlow": 900,
    "ssoSessionIdleTimeout": 1800,
    "ssoSessionMaxLifespan": 36000,
    "ssoSessionIdleTimeoutRememberMe": 0,
    "ssoSessionMaxLifespanRememberMe": 0,
    "offlineSessionIdleTimeout": 2592000,
    "offlineSessionMaxLifespanEnabled": false,
    "offlineSessionMaxLifespan": 5184000,
    "clientSessionIdleTimeout": 0,
    "clientSessionMaxLifespan": 0,
    "clientOfflineSessionIdleTimeout": 0,
    "clientOfflineSessionMaxLifespan": 0,
    "accessCodeLifespan": 60,
    "accessCodeLifespanUserAction": 300,
    "accessCodeLifespanLogin": 1800,
    "actionTokenGeneratedByAdminLifespan": 43200,
    "actionTokenGeneratedByUserLifespan": 300,
    "oauth2DeviceCodeLifespan": 600,
    "oauth2DevicePollingInterval": 5
  }')

if [ "$REALM_RESPONSE" = "201" ]; then
    echo "✅ Realm 'ai-engineering' создан"
else
    echo "⚠️ Realm 'ai-engineering' уже существует или ошибка создания (код: $REALM_RESPONSE)"
fi

echo ""

# Создаем клиента ai-frontend
echo "🔧 Создание клиента 'ai-frontend'..."
CLIENT_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -X POST \
  http://localhost:8080/admin/realms/ai-engineering/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "ai-frontend",
    "enabled": true,
    "publicClient": true,
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": false,
    "redirectUris": ["http://localhost:3000/*", "http://localhost:80/*"],
    "webOrigins": ["http://localhost:3000", "http://localhost:80"],
    "protocol": "openid-connect",
    "attributes": {
      "access.token.lifespan": "300",
      "client.session.idle.timeout": "0",
      "client.session.max.lifespan": "0",
      "pkce.code.challenge.method": "S256"
    }
  }')

if [ "$CLIENT_RESPONSE" = "201" ]; then
    echo "✅ Клиент 'ai-frontend' создан"
else
    echo "⚠️ Клиент 'ai-frontend' уже существует или ошибка создания (код: $CLIENT_RESPONSE)"
fi

echo ""

# Создаем роли
echo "👥 Создание ролей..."
ROLES=("admin" "developer" "analyst" "viewer")

for role in "${ROLES[@]}"; do
    ROLE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
      -X POST \
      http://localhost:8080/admin/realms/ai-engineering/roles \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"name\": \"$role\", \"description\": \"Role: $role\"}")
    
    if [ "$ROLE_RESPONSE" = "201" ]; then
        echo "✅ Роль '$role' создана"
    else
        echo "⚠️ Роль '$role' уже существует или ошибка создания (код: $ROLE_RESPONSE)"
    fi
done

echo ""

# Создаем пользователей
echo "👤 Создание тестовых пользователей..."

# Пользователь admin
ADMIN_USER_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
  -X POST \
  http://localhost:8080/admin/realms/ai-engineering/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "enabled": true,
    "firstName": "Администратор",
    "lastName": "Системы",
    "email": "admin@ai-engineering.local",
    "credentials": [{
      "type": "password",
      "value": "admin",
      "temporary": false
    }]
  }')

if [ "$ADMIN_USER_RESPONSE" = "201" ]; then
    echo "✅ Пользователь 'admin' создан"
    
    # Назначаем роль admin
    USER_ID=$(curl -s \
      http://localhost:8080/admin/realms/ai-engineering/users?username=admin \
      -H "Authorization: Bearer $ADMIN_TOKEN" | \
      python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null)
    
    if [ ! -z "$USER_ID" ]; then
        curl -s -X POST \
          http://localhost:8080/admin/realms/ai-engineering/users/$USER_ID/role-mappings/realm \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d '[{"id": "'$(curl -s http://localhost:8080/admin/realms/ai-engineering/roles/admin -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)'", "name": "admin"}]' > /dev/null
        echo "✅ Роль 'admin' назначена пользователю 'admin'"
    fi
else
    echo "⚠️ Пользователь 'admin' уже существует или ошибка создания (код: $ADMIN_USER_RESPONSE)"
fi

echo ""

echo "🎉 Настройка Keycloak завершена!"
echo ""
echo "📋 Созданные ресурсы:"
echo "   ✅ Realm: ai-engineering"
echo "   ✅ Client: ai-frontend"
echo "   ✅ Роли: admin, developer, analyst, viewer"
echo "   ✅ Пользователь: admin/admin"
echo ""
echo "🌐 Доступ к админ-консоли: http://localhost:8080/admin"
echo "🔐 Логин: admin, Пароль: admin"
echo ""
echo "🧪 Тестирование:"
echo "   python3 scripts/test_auth.py"
echo ""
