#!/bin/bash

# Скрипт для тестирования авторизации frontend

echo "🔐 Тестирование авторизации Frontend"
echo "===================================="

# Функция для проверки доступности сервиса
check_service() {
    local url=$1
    local name=$2
    
    echo "🔍 Проверка $name..."
    if curl -k -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "✅ $name доступен"
        return 0
    else
        echo "❌ $name недоступен"
        return 1
    fi
}

# Проверяем основные сервисы
echo "⏳ Проверка доступности сервисов..."
check_service "https://localhost" "Frontend"
check_service "https://localhost:8080" "Keycloak"
check_service "https://localhost:8080/realms/ai-engineering" "Keycloak Realm"

echo ""

# Проверяем OpenID Connect конфигурацию
echo "🔧 Проверка OpenID Connect конфигурации..."
OIDC_CONFIG=$(curl -k -s "https://localhost:8080/realms/ai-engineering/.well-known/openid_configuration" 2>/dev/null)

if [ $? -eq 0 ] && echo "$OIDC_CONFIG" | grep -q "authorization_endpoint"; then
    echo "✅ OpenID Connect конфигурация доступна"
    
    # Извлекаем важные endpoints
    AUTH_ENDPOINT=$(echo "$OIDC_CONFIG" | grep -o '"authorization_endpoint":"[^"]*"' | cut -d'"' -f4)
    TOKEN_ENDPOINT=$(echo "$OIDC_CONFIG" | grep -o '"token_endpoint":"[^"]*"' | cut -d'"' -f4)
    USERINFO_ENDPOINT=$(echo "$OIDC_CONFIG" | grep -o '"userinfo_endpoint":"[^"]*"' | cut -d'"' -f4)
    
    echo "   📍 Authorization Endpoint: $AUTH_ENDPOINT"
    echo "   📍 Token Endpoint: $TOKEN_ENDPOINT"
    echo "   📍 UserInfo Endpoint: $USERINFO_ENDPOINT"
else
    echo "❌ OpenID Connect конфигурация недоступна"
fi

echo ""

# Проверяем клиент ai-frontend
echo "🔑 Проверка клиента ai-frontend..."
CLIENT_CONFIG=$(curl -k -s "https://localhost:8080/realms/ai-engineering/clients-registrations/default/ai-frontend" 2>/dev/null)

if [ $? -eq 0 ] && echo "$CLIENT_CONFIG" | grep -q "clientId"; then
    echo "✅ Клиент ai-frontend найден"
    
    # Извлекаем информацию о клиенте
    CLIENT_ID=$(echo "$CLIENT_CONFIG" | grep -o '"clientId":"[^"]*"' | cut -d'"' -f4)
    REDIRECT_URIS=$(echo "$CLIENT_CONFIG" | grep -o '"redirectUris":\[[^]]*\]' | cut -d'[' -f2 | cut -d']' -f1)
    
    echo "   📍 Client ID: $CLIENT_ID"
    echo "   📍 Redirect URIs: $REDIRECT_URIS"
else
    echo "❌ Клиент ai-frontend не найден"
fi

echo ""

# Проверяем тестовых пользователей
echo "👥 Проверка тестовых пользователей..."
USERS=("admin" "developer" "analyst" "viewer")

for user in "${USERS[@]}"; do
    echo "🔍 Проверка пользователя: $user"
    
    # Пытаемся получить токен для пользователя
    TOKEN_RESPONSE=$(curl -k -s -X POST "https://localhost:8080/realms/ai-engineering/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=password" \
        -d "client_id=ai-frontend" \
        -d "username=$user" \
        -d "password=$user" 2>/dev/null)
    
    if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
        echo "✅ Пользователь $user может получить токен"
        
        # Извлекаем токен и проверяем информацию о пользователе
        ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$ACCESS_TOKEN" ]; then
            USERINFO=$(curl -k -s -H "Authorization: Bearer $ACCESS_TOKEN" \
                "https://localhost:8080/realms/ai-engineering/protocol/openid-connect/userinfo" 2>/dev/null)
            
            if echo "$USERINFO" | grep -q "preferred_username"; then
                USERNAME=$(echo "$USERINFO" | grep -o '"preferred_username":"[^"]*"' | cut -d'"' -f4)
                EMAIL=$(echo "$USERINFO" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
                echo "   📍 Username: $USERNAME"
                echo "   📍 Email: $EMAIL"
            fi
        fi
    else
        echo "❌ Пользователь $user не может получить токен"
        echo "   Ответ: $TOKEN_RESPONSE"
    fi
    echo ""
done

echo "🎉 Тестирование авторизации завершено!"
echo ""
echo "📋 Результаты:"
echo "   • Frontend: $(check_service "https://localhost" "Frontend" >/dev/null 2>&1 && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Keycloak: $(check_service "https://localhost:8080" "Keycloak" >/dev/null 2>&1 && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Realm: $(check_service "https://localhost:8080/realms/ai-engineering" "Keycloak Realm" >/dev/null 2>&1 && echo "✅ Доступен" || echo "❌ Недоступен")"
echo ""
echo "🌐 Доступные URL:"
echo "   • Frontend: https://localhost"
echo "   • Keycloak Admin: https://localhost:8080/admin"
echo "   • Keycloak Realm: https://localhost:8080/realms/ai-engineering"
echo ""
echo "👥 Тестовые пользователи:"
echo "   • admin/admin - Администратор"
echo "   • developer/developer - Разработчик"
echo "   • analyst/analyst - Аналитик"
echo "   • viewer/viewer - Наблюдатель"
echo ""
echo "⚠️  ВНИМАНИЕ: Используются самоподписанные сертификаты!"
echo "   В браузере появится предупреждение о безопасности."
echo "   Нажмите 'Дополнительно' -> 'Перейти на localhost (небезопасно)'"
