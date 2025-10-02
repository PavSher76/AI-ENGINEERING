#!/bin/bash

# Скрипт для настройки авторизации Keycloak

echo "🔐 Настройка авторизации Keycloak"
echo "================================="

# Функция для ожидания готовности Keycloak
wait_for_keycloak() {
    echo "⏳ Ожидание готовности Keycloak..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -k -s -o /dev/null -w "%{http_code}" "https://localhost:8080/realms/master" | grep -q "200"; then
            echo "✅ Keycloak готов к работе"
            return 0
        fi
        
        echo "   Попытка $attempt/$max_attempts..."
        sleep 5
        ((attempt++))
    done
    
    echo "❌ Keycloak не готов к работе"
    return 1
}

# Функция для получения токена администратора
get_admin_token() {
    echo "🔑 Получение токена администратора..."
    
    local token_response=$(curl -k -s -X POST "https://localhost:8080/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=password" \
        -d "client_id=admin-cli" \
        -d "username=admin" \
        -d "password=admin" 2>/dev/null)
    
    if echo "$token_response" | grep -q "access_token"; then
        local access_token=$(echo "$token_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Токен администратора получен"
        echo "$access_token"
        return 0
    else
        echo "❌ Не удалось получить токен администратора"
        echo "   Ответ: $token_response"
        return 1
    fi
}

# Функция для проверки существования realm
check_realm_exists() {
    local token=$1
    local realm_name="ai-engineering"
    
    echo "🔍 Проверка существования realm: $realm_name"
    
    local response=$(curl -k -s -H "Authorization: Bearer $token" \
        "https://localhost:8080/admin/realms/$realm_name" 2>/dev/null)
    
    if echo "$response" | grep -q '"realm"'; then
        echo "✅ Realm $realm_name существует"
        return 0
    else
        echo "❌ Realm $realm_name не найден"
        return 1
    fi
}

# Функция для создания realm
create_realm() {
    local token=$1
    local realm_name="ai-engineering"
    
    echo "🏗️  Создание realm: $realm_name"
    
    local realm_config='{
        "realm": "'$realm_name'",
        "displayName": "AI Engineering Platform",
        "enabled": true,
        "sslRequired": "external",
        "registrationAllowed": true,
        "loginWithEmailAllowed": true,
        "duplicateEmailsAllowed": false,
        "resetPasswordAllowed": true,
        "editUsernameAllowed": false,
        "bruteForceProtected": false,
        "defaultRoles": ["offline_access", "uma_authorization"],
        "requiredCredentials": ["password"],
        "passwordPolicy": "hashIterations(27500)"
    }'
    
    local response=$(curl -k -s -X POST \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$realm_config" \
        "https://localhost:8080/admin/realms" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "✅ Realm $realm_name создан"
        return 0
    else
        echo "❌ Ошибка создания realm: $response"
        return 1
    fi
}

# Функция для создания клиента
create_client() {
    local token=$1
    local realm_name="ai-engineering"
    local client_id="ai-frontend"
    
    echo "🔧 Создание клиента: $client_id"
    
    local client_config='{
        "clientId": "'$client_id'",
        "name": "AI Frontend Client",
        "enabled": true,
        "publicClient": true,
        "protocol": "openid-connect",
        "redirectUris": ["https://localhost:3000/*", "https://localhost/*"],
        "webOrigins": ["https://localhost:3000", "https://localhost"],
        "directAccessGrantsEnabled": true,
        "standardFlowEnabled": true,
        "fullScopeAllowed": true
    }'
    
    local response=$(curl -k -s -X POST \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$client_config" \
        "https://localhost:8080/admin/realms/$realm_name/clients" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "✅ Клиент $client_id создан"
        return 0
    else
        echo "❌ Ошибка создания клиента: $response"
        return 1
    fi
}

# Функция для создания ролей
create_roles() {
    local token=$1
    local realm_name="ai-engineering"
    
    echo "👥 Создание ролей..."
    
    local roles=("admin" "developer" "analyst" "viewer")
    
    for role in "${roles[@]}"; do
        echo "   Создание роли: $role"
        
        local role_config='{
            "name": "'$role'",
            "description": "Role for '$role' users"
        }'
        
        local response=$(curl -k -s -X POST \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$role_config" \
            "https://localhost:8080/admin/realms/$realm_name/roles" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Роль $role создана"
        else
            echo "   ❌ Ошибка создания роли $role: $response"
        fi
    done
}

# Функция для создания тестовых пользователей
create_test_users() {
    local token=$1
    local realm_name="ai-engineering"
    
    echo "👤 Создание тестовых пользователей..."
    
    # Пользователь admin
    echo "   Создание пользователя: admin"
    local admin_user='{
        "username": "admin",
        "enabled": true,
        "emailVerified": true,
        "firstName": "Admin",
        "lastName": "User",
        "email": "admin@example.com",
        "credentials": [{
            "type": "password",
            "value": "admin",
            "temporary": false
        }]
    }'
    
    local admin_response=$(curl -k -s -X POST \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$admin_user" \
        "https://localhost:8080/admin/realms/$realm_name/users" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Пользователь admin создан"
        
        # Получаем ID пользователя и назначаем роли
        local user_id=$(curl -k -s -H "Authorization: Bearer $token" \
            "https://localhost:8080/admin/realms/$realm_name/users?username=admin" | \
            grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1)
        
        if [ -n "$user_id" ]; then
            # Назначаем все роли
            local roles=("admin" "developer" "analyst" "viewer")
            for role in "${roles[@]}"; do
                curl -k -s -X POST \
                    -H "Authorization: Bearer $token" \
                    "https://localhost:8080/admin/realms/$realm_name/users/$user_id/role-mappings/realm" \
                    -H "Content-Type: application/json" \
                    -d '[{"name":"'$role'","id":"'$role'"}]' >/dev/null 2>&1
            done
            echo "   ✅ Роли назначены пользователю admin"
        fi
    else
        echo "   ❌ Ошибка создания пользователя admin: $admin_response"
    fi
    
    # Аналогично для других пользователей
    local users=("developer:developer:Developer:User:developer@example.com:developer,analyst,viewer" 
                 "analyst:analyst:Analyst:User:analyst@example.com:analyst,viewer"
                 "viewer:viewer:Viewer:User:viewer@example.com:viewer")
    
    for user_info in "${users[@]}"; do
        IFS=':' read -r username password first_name last_name email roles <<< "$user_info"
        
        echo "   Создание пользователя: $username"
        
        local user_config='{
            "username": "'$username'",
            "enabled": true,
            "emailVerified": true,
            "firstName": "'$first_name'",
            "lastName": "'$last_name'",
            "email": "'$email'",
            "credentials": [{
                "type": "password",
                "value": "'$password'",
                "temporary": false
            }]
        }'
        
        local user_response=$(curl -k -s -X POST \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$user_config" \
            "https://localhost:8080/admin/realms/$realm_name/users" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Пользователь $username создан"
            
            # Назначаем роли
            IFS=',' read -ra USER_ROLES <<< "$roles"
            for role in "${USER_ROLES[@]}"; do
                curl -k -s -X POST \
                    -H "Authorization: Bearer $token" \
                    "https://localhost:8080/admin/realms/$realm_name/users?username=$username" | \
                    grep -o '"id":"[^"]*"' | cut -d'"' -f4 | head -1 | \
                    xargs -I {} curl -k -s -X POST \
                    -H "Authorization: Bearer $token" \
                    "https://localhost:8080/admin/realms/$realm_name/users/{}/role-mappings/realm" \
                    -H "Content-Type: application/json" \
                    -d '[{"name":"'$role'","id":"'$role'"}]' >/dev/null 2>&1
            done
            echo "   ✅ Роли назначены пользователю $username"
        else
            echo "   ❌ Ошибка создания пользователя $username: $user_response"
        fi
    done
}

# Основная функция
main() {
    # Ждем готовности Keycloak
    if ! wait_for_keycloak; then
        exit 1
    fi
    
    # Получаем токен администратора
    local admin_token=$(get_admin_token)
    if [ -z "$admin_token" ]; then
        exit 1
    fi
    
    # Проверяем существование realm
    if ! check_realm_exists "$admin_token"; then
        # Создаем realm
        if ! create_realm "$admin_token"; then
            exit 1
        fi
    fi
    
    # Создаем клиента
    create_client "$admin_token"
    
    # Создаем роли
    create_roles "$admin_token"
    
    # Создаем тестовых пользователей
    create_test_users "$admin_token"
    
    echo ""
    echo "🎉 Настройка авторизации завершена!"
    echo ""
    echo "📋 Результаты:"
    echo "   • Realm: ai-engineering"
    echo "   • Client: ai-frontend"
    echo "   • Роли: admin, developer, analyst, viewer"
    echo "   • Пользователи: admin/admin, developer/developer, analyst/analyst, viewer/viewer"
    echo ""
    echo "🌐 Доступные URL:"
    echo "   • Frontend: https://localhost"
    echo "   • Keycloak Admin: https://localhost:8080/admin"
    echo "   • Keycloak Realm: https://localhost:8080/realms/ai-engineering"
}

# Запуск основной функции
main
