#!/bin/bash

# Скрипт для настройки Keycloak для AI Engineering Platform
# Автоматически создает realm, клиентов и пользователей

set -e

echo "🔐 Настройка Keycloak для AI Engineering Platform..."

# Переменные
KEYCLOAK_URL="http://localhost:8080"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin"
REALM_NAME="ai-engineering"
CLIENT_ID="ai-frontend"
CLIENT_ID_BACKEND="ai-backend"

# Функция для ожидания готовности Keycloak
wait_for_keycloak() {
    echo "⏳ Ожидание готовности Keycloak..."
    for i in {1..30}; do
        if curl -s -f "$KEYCLOAK_URL/realms/master" > /dev/null 2>&1; then
            echo "✅ Keycloak готов к работе"
            return 0
        fi
        echo "Попытка $i/30..."
        sleep 10
    done
    echo "❌ Keycloak не готов к работе"
    exit 1
}

# Функция для получения токена администратора
get_admin_token() {
    echo "🔑 Получение токена администратора..."
    TOKEN_RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$ADMIN_USER" \
        -d "password=$ADMIN_PASSWORD" \
        -d "grant_type=password" \
        -d "client_id=admin-cli")
    
    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
    
    if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
        echo "❌ Не удалось получить токен администратора"
        echo "Ответ: $TOKEN_RESPONSE"
        exit 1
    fi
    
    echo "✅ Токен администратора получен"
}

# Функция для создания realm
create_realm() {
    echo "🏰 Создание realm '$REALM_NAME'..."
    
    REALM_CONFIG='{
        "realm": "'$REALM_NAME'",
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
        "offlineSessionIdleTimeout": 2592000,
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
        "bruteForceProtected": true,
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
        "ssoSessionIdleTimeoutRememberMe": 0,
        "ssoSessionMaxLifespanRememberMe": 0,
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
    }'
    
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "$KEYCLOAK_URL/admin/realms" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$REALM_CONFIG")
    
    HTTP_CODE="${RESPONSE: -3}"
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo "✅ Realm '$REALM_NAME' создан успешно"
    elif [ "$HTTP_CODE" = "409" ]; then
        echo "ℹ️ Realm '$REALM_NAME' уже существует"
    else
        echo "❌ Ошибка создания realm. HTTP код: $HTTP_CODE"
        echo "Ответ: $RESPONSE"
        exit 1
    fi
}

# Функция для создания клиента
create_client() {
    local client_id=$1
    local client_name=$2
    local is_public=$3
    local redirect_uris=$4
    
    echo "🔧 Создание клиента '$client_id'..."
    
    CLIENT_CONFIG='{
        "clientId": "'$client_id'",
        "name": "'$client_name'",
        "description": "AI Engineering Platform - '$client_name'",
        "enabled": true,
        "clientAuthenticatorType": "client-secret",
        "secret": "'$client_id'-secret",
        "redirectUris": ['$redirect_uris'],
        "webOrigins": ["http://localhost:3000", "http://localhost:80"],
        "protocol": "openid-connect",
        "attributes": {
            "access.token.lifespan": "300",
            "client.secret.creation.time": "'$(date +%s)'",
            "display.on.consent.screen": "true",
            "consent.screen.text": "AI Engineering Platform",
            "login_theme": "keycloak",
            "access.type": "'$([ "$is_public" = "true" ] && echo "public" || echo "confidential")'",
            "standard.flow.enabled": "true",
            "implicit.flow.enabled": "false",
            "direct.access.grants.enabled": "true",
            "service.accounts.enabled": "'$([ "$is_public" = "true" ] && echo "false" || echo "true")'",
            "authorization.services.enabled": "false",
            "frontchannel.logout": "true",
            "frontchannel.logout.url": "",
            "backchannel.logout.session.required": "true",
            "backchannel.logout.revoke.offline.tokens": "false"
        },
        "authenticationFlowBindingOverrides": {},
        "fullScopeAllowed": true,
        "nodeReRegistrationTimeout": -1,
        "defaultClientScopes": [
            "web-origins",
            "role_list",
            "profile",
            "roles",
            "email"
        ],
        "optionalClientScopes": [
            "address",
            "phone",
            "offline_access",
            "microprofile-jwt"
        ]
    }'
    
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$CLIENT_CONFIG")
    
    HTTP_CODE="${RESPONSE: -3}"
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo "✅ Клиент '$client_id' создан успешно"
    elif [ "$HTTP_CODE" = "409" ]; then
        echo "ℹ️ Клиент '$client_id' уже существует"
    else
        echo "❌ Ошибка создания клиента '$client_id'. HTTP код: $HTTP_CODE"
        echo "Ответ: $RESPONSE"
        exit 1
    fi
}

# Функция для создания пользователя
create_user() {
    local username=$1
    local password=$2
    local email=$3
    local first_name=$4
    local last_name=$5
    local roles=$6
    
    echo "👤 Создание пользователя '$username'..."
    
    USER_CONFIG='{
        "username": "'$username'",
        "email": "'$email'",
        "firstName": "'$first_name'",
        "lastName": "'$last_name'",
        "enabled": true,
        "emailVerified": true,
        "credentials": [{
            "type": "password",
            "value": "'$password'",
            "temporary": false
        }],
        "realmRoles": ['$roles'],
        "clientRoles": {
            "'$CLIENT_ID'": ['$roles']
        }
    }'
    
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$USER_CONFIG")
    
    HTTP_CODE="${RESPONSE: -3}"
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo "✅ Пользователь '$username' создан успешно"
    elif [ "$HTTP_CODE" = "409" ]; then
        echo "ℹ️ Пользователь '$username' уже существует"
    else
        echo "❌ Ошибка создания пользователя '$username'. HTTP код: $HTTP_CODE"
        echo "Ответ: $RESPONSE"
        exit 1
    fi
}

# Функция для создания ролей
create_roles() {
    echo "🎭 Создание ролей..."
    
    # Realm roles
    REALM_ROLES='["admin", "user", "developer", "analyst", "viewer"]'
    
    for role in admin user developer analyst viewer; do
        ROLE_CONFIG='{
            "name": "'$role'",
            "description": "AI Engineering Platform - '$role' role",
            "composite": false,
            "clientRole": false
        }'
        
        RESPONSE=$(curl -s -w "%{http_code}" -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$ROLE_CONFIG")
        
        HTTP_CODE="${RESPONSE: -3}"
        
        if [ "$HTTP_CODE" = "201" ]; then
            echo "✅ Роль '$role' создана успешно"
        elif [ "$HTTP_CODE" = "409" ]; then
            echo "ℹ️ Роль '$role' уже существует"
        else
            echo "❌ Ошибка создания роли '$role'. HTTP код: $HTTP_CODE"
        fi
    done
}

# Основная функция
main() {
    echo "🚀 Запуск настройки Keycloak..."
    
    # Проверяем наличие jq
    if ! command -v jq &> /dev/null; then
        echo "❌ jq не установлен. Установите jq для работы скрипта."
        echo "macOS: brew install jq"
        echo "Ubuntu/Debian: sudo apt-get install jq"
        exit 1
    fi
    
    # Ожидаем готовности Keycloak
    wait_for_keycloak
    
    # Получаем токен администратора
    get_admin_token
    
    # Создаем realm
    create_realm
    
    # Создаем роли
    create_roles
    
    # Создаем клиентов
    create_client "$CLIENT_ID" "AI Frontend" "true" '"http://localhost:3000/*", "http://localhost:80/*"'
    create_client "$CLIENT_ID_BACKEND" "AI Backend" "false" '"http://localhost:8001/*", "http://localhost:8003/*"'
    
    # Создаем пользователей
    create_user "admin" "admin" "admin@ai-engineering.local" "Администратор" "Системы" '["admin", "user"]'
    create_user "developer" "developer" "developer@ai-engineering.local" "Разработчик" "Системы" '["developer", "user"]'
    create_user "analyst" "analyst" "analyst@ai-engineering.local" "Аналитик" "Данных" '["analyst", "user"]'
    create_user "viewer" "viewer" "viewer@ai-engineering.local" "Наблюдатель" "Системы" '["viewer"]'
    
    echo ""
    echo "🎉 Настройка Keycloak завершена успешно!"
    echo ""
    echo "📋 Информация для входа:"
    echo "   URL: $KEYCLOAK_URL"
    echo "   Realm: $REALM_NAME"
    echo "   Admin Console: $KEYCLOAK_URL/admin"
    echo ""
    echo "👥 Пользователи для тестирования:"
    echo "   admin/admin - Администратор"
    echo "   developer/developer - Разработчик"
    echo "   analyst/analyst - Аналитик"
    echo "   viewer/viewer - Наблюдатель"
    echo ""
    echo "🔧 Клиенты:"
    echo "   Frontend: $CLIENT_ID"
    echo "   Backend: $CLIENT_ID_BACKEND"
    echo ""
    echo "🌐 Frontend URL: http://localhost:3000"
    echo "🔐 Keycloak Admin: $KEYCLOAK_URL/admin (admin/admin)"
}

# Запуск
main "$@"
