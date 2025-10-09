#!/bin/bash

# Скрипт автоматической настройки Keycloak для AI Engineering Platform
# Автор: AI Assistant
# Дата: $(date)

set -e

echo "🔐 Настройка Keycloak для AI Engineering Platform"
echo "=================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка доступности Keycloak
check_keycloak() {
    log "Проверка доступности Keycloak..."
    
    if ! curl -k -s -o /dev/null -w "%{http_code}" https://localhost:9080/admin | grep -q "302\|200"; then
        error "Keycloak недоступен на https://localhost:9080/admin"
        error "Убедитесь, что сервисы запущены: docker-compose up -d"
        exit 1
    fi
    
    success "Keycloak доступен"
}

# Получение токена администратора
get_admin_token() {
    log "Получение токена администратора..."
    
    local token=$(curl -k -s -X POST "https://localhost:9080/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | jq -r '.access_token')
    
    if [ "$token" = "null" ] || [ -z "$token" ]; then
        error "Не удалось получить токен администратора"
        exit 1
    fi
    
    success "Токен получен"
    echo "$token"
}

# Проверка существования realm
check_realm() {
    local token=$1
    local realm_name="ai-engineering"
    
    log "Проверка существования realm '$realm_name'..."
    
    local realms=$(curl -k -s -X GET "https://localhost:9080/admin/realms" \
        -H "Authorization: Bearer $token" | jq -r '.[].realm')
    
    if echo "$realms" | grep -q "$realm_name"; then
        success "Realm '$realm_name' существует"
        return 0
    else
        warning "Realm '$realm_name' не найден"
        return 1
    fi
}

# Создание realm
create_realm() {
    local token=$1
    local realm_name="ai-engineering"
    
    log "Создание realm '$realm_name'..."
    
    local realm_config='{
        "realm": "'$realm_name'",
        "displayName": "AI Engineering Platform",
        "displayNameHtml": "<div class=\"kc-logo-text\"><span>AI Engineering</span></div>",
        "enabled": true,
        "sslRequired": "none",
        "registrationAllowed": true,
        "registrationEmailAsUsername": false,
        "rememberMe": true,
        "verifyEmail": false,
        "loginWithEmailAllowed": true,
        "duplicateEmailsAllowed": false,
        "resetPasswordAllowed": true,
        "editUsernameAllowed": false,
        "bruteForceProtected": false,
        "permanentLockout": false,
        "maxTemporaryLockouts": 0,
        "bruteForceStrategy": "MULTIPLE",
        "maxFailureWaitSeconds": 900,
        "minimumQuickLoginWaitSeconds": 60,
        "waitIncrementSeconds": 60,
        "quickLoginCheckMilliSeconds": 1000,
        "maxDeltaTimeSeconds": 43200,
        "failureFactor": 30,
        "defaultRole": {
            "name": "default-roles-'$realm_name'",
            "description": "${role_default-roles}",
            "composite": true,
            "clientRole": false
        },
        "requiredCredentials": ["password"],
        "otpPolicyType": "totp",
        "otpPolicyAlgorithm": "HmacSHA1",
        "otpPolicyInitialCounter": 0,
        "otpPolicyDigits": 6,
        "otpPolicyLookAheadWindow": 1,
        "otpPolicyPeriod": 30,
        "otpPolicyCodeReusable": false,
        "otpSupportedApplications": [
            "totpAppFreeOTPName",
            "totpAppGoogleName",
            "totpAppMicrosoftAuthenticatorName"
        ],
        "webAuthnPolicyRpEntityName": "keycloak",
        "webAuthnPolicySignatureAlgorithms": ["ES256"],
        "webAuthnPolicyRpId": "",
        "webAuthnPolicyAttestationConveyancePreference": "not specified",
        "webAuthnPolicyAuthenticatorAttachment": "not specified",
        "webAuthnPolicyRequireResidentKey": "not specified",
        "webAuthnPolicyUserVerificationRequirement": "not specified",
        "webAuthnPolicyCreateTimeout": 0,
        "webAuthnPolicyAvoidSameAuthenticatorRegister": false,
        "webAuthnPolicyAcceptableAaguids": [],
        "webAuthnPolicyExtraOrigins": [],
        "webAuthnPolicyPasswordlessRpEntityName": "keycloak",
        "webAuthnPolicyPasswordlessSignatureAlgorithms": ["ES256", "RS256"],
        "webAuthnPolicyPasswordlessRpId": "",
        "webAuthnPolicyPasswordlessAttestationConveyancePreference": "not specified",
        "webAuthnPolicyPasswordlessAuthenticatorAttachment": "not specified",
        "webAuthnPolicyPasswordlessRequireResidentKey": "Yes",
        "webAuthnPolicyPasswordlessUserVerificationRequirement": "required",
        "webAuthnPolicyPasswordlessCreateTimeout": 0,
        "webAuthnPolicyPasswordlessAvoidSameAuthenticatorRegister": false,
        "webAuthnPolicyPasswordlessAcceptableAaguids": [],
        "webAuthnPolicyPasswordlessExtraOrigins": [],
        "browserSecurityHeaders": {
            "contentSecurityPolicyReportOnly": "",
            "xContentTypeOptions": "nosniff",
            "referrerPolicy": "no-referrer",
            "xRobotsTag": "none",
            "xFrameOptions": "SAMEORIGIN",
            "contentSecurityPolicy": "frame-src '\''self'\''; frame-ancestors '\''self'\''; object-src '\''none'\'';",
            "xXSSProtection": "1; mode=block",
            "strictTransportSecurity": "max-age=31536000; includeSubDomains"
        },
        "smtpServer": {},
        "eventsEnabled": false,
        "eventsListeners": ["jboss-logging"],
        "enabledEventTypes": [],
        "adminEventsEnabled": false,
        "adminEventsDetailsEnabled": false,
        "internationalizationEnabled": true,
        "supportedLocales": ["ru", "en"],
        "defaultLocale": "ru",
        "browserFlow": "browser",
        "registrationFlow": "registration",
        "directGrantFlow": "direct grant",
        "resetCredentialsFlow": "reset credentials",
        "clientAuthenticationFlow": "clients",
        "dockerAuthenticationFlow": "docker auth",
        "firstBrokerLoginFlow": "first broker login",
        "attributes": {
            "cibaBackchannelTokenDeliveryMode": "poll",
            "cibaExpiresIn": "120",
            "cibaAuthRequestedUserHint": "login_hint",
            "parRequestUriLifespan": "60",
            "cibaInterval": "5",
            "realmReusableOtpCode": "false",
            "frontendUrl": "https://localhost:9443",
            "adminEventsDetailsEnabled": "false",
            "eventsEnabled": "false",
            "adminEventsEnabled": "false"
        },
        "userManagedAccessAllowed": false,
        "organizationsEnabled": false,
        "verifiableCredentialsEnabled": false,
        "adminPermissionsEnabled": false,
        "clientProfiles": {"profiles": []},
        "clientPolicies": {"policies": []}
    }'
    
    local response=$(curl -k -s -X POST "https://localhost:9080/admin/realms" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$realm_config" -w "%{http_code}")
    
    if [ "${response: -3}" = "201" ]; then
        success "Realm '$realm_name' создан"
    else
        error "Ошибка создания realm: $response"
        exit 1
    fi
}

# Проверка существования клиента
check_client() {
    local token=$1
    local realm_name="ai-engineering"
    local client_id="ai-frontend"
    
    log "Проверка существования клиента '$client_id'..."
    
    local clients=$(curl -k -s -X GET "https://localhost:9080/admin/realms/$realm_name/clients" \
        -H "Authorization: Bearer $token" | jq -r '.[].clientId')
    
    if echo "$clients" | grep -q "$client_id"; then
        success "Клиент '$client_id' существует"
        return 0
    else
        warning "Клиент '$client_id' не найден"
        return 1
    fi
}

# Создание клиента
create_client() {
    local token=$1
    local realm_name="ai-engineering"
    local client_id="ai-frontend"
    
    log "Создание клиента '$client_id'..."
    
    local client_config='{
        "clientId": "'$client_id'",
        "name": "AI Frontend Client",
        "description": "Frontend client for AI Engineering Platform",
        "enabled": true,
        "alwaysDisplayInConsole": false,
        "clientAuthenticatorType": "client-secret",
        "secret": "ai-frontend-secret",
        "redirectUris": [
            "https://localhost:9300/*",
            "https://localhost/*"
        ],
        "webOrigins": [
            "https://localhost:9300",
            "https://localhost"
        ],
        "notBefore": 0,
        "bearerOnly": false,
        "consentRequired": false,
        "standardFlowEnabled": true,
        "implicitFlowEnabled": false,
        "directAccessGrantsEnabled": false,
        "serviceAccountsEnabled": false,
        "publicClient": true,
        "frontchannelLogout": false,
        "protocol": "openid-connect",
        "attributes": {
            "saml.assertion.signature": "false",
            "saml.force.post.binding": "false",
            "saml.multivalued.roles": "false",
            "saml.encrypt": "false",
            "saml.server.signature": "false",
            "saml.server.signature.keyinfo.ext": "false",
            "exclude.session.state.from.auth.response": "false",
            "saml_force_name_id_format": "false",
            "saml.client.signature": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "saml.authnstatement": "false",
            "display.on.consent.screen": "false",
            "saml.onetimeuse.condition": "false"
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
    
    local response=$(curl -k -s -X POST "https://localhost:9080/admin/realms/$realm_name/clients" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$client_config" -w "%{http_code}")
    
    if [ "${response: -3}" = "201" ]; then
        success "Клиент '$client_id' создан"
    else
        error "Ошибка создания клиента: $response"
        exit 1
    fi
}

# Проверка существования пользователя
check_user() {
    local token=$1
    local realm_name="ai-engineering"
    local username="admin"
    
    log "Проверка существования пользователя '$username'..."
    
    local users=$(curl -k -s -X GET "https://localhost:9080/admin/realms/$realm_name/users" \
        -H "Authorization: Bearer $token" | jq -r '.[].username')
    
    if echo "$users" | grep -q "$username"; then
        success "Пользователь '$username' существует"
        return 0
    else
        warning "Пользователь '$username' не найден"
        return 1
    fi
}

# Создание пользователя
create_user() {
    local token=$1
    local realm_name="ai-engineering"
    local username="admin"
    
    log "Создание пользователя '$username'..."
    
    local user_config='{
        "username": "'$username'",
        "email": "admin@ai-engineering.local",
        "firstName": "Admin",
        "lastName": "User",
        "emailVerified": true,
        "enabled": true,
        "credentials": [{
            "type": "password",
            "value": "admin123",
            "temporary": false
        }]
    }'
    
    local response=$(curl -k -s -X POST "https://localhost:9080/admin/realms/$realm_name/users" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$user_config" -w "%{http_code}")
    
    if [ "${response: -3}" = "201" ]; then
        success "Пользователь '$username' создан"
    else
        error "Ошибка создания пользователя: $response"
        exit 1
    fi
}

# Основная функция
main() {
    log "Начало настройки Keycloak..."
    
    # Проверка доступности
    check_keycloak
    
    # Получение токена
    local token=$(get_admin_token)
    
    # Создание realm
    if ! check_realm "$token"; then
        create_realm "$token"
    fi
    
    # Создание клиента
    if ! check_client "$token"; then
        create_client "$token"
    fi
    
    # Создание пользователя
    if ! check_user "$token"; then
        create_user "$token"
    fi
    
    success "Настройка Keycloak завершена!"
    echo ""
    echo "📋 Информация для входа:"
    echo "  Frontend: https://localhost:9300"
    echo "  Keycloak Admin: https://localhost:9080/admin"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
    echo "🔧 Дополнительные настройки:"
    echo "  - Откройте https://localhost:9300"
    echo "  - Примите предупреждение о безопасности"
    echo "  - Попробуйте войти в систему"
    echo ""
    echo "📚 Документация:"
    echo "  - Подробная инструкция: keycloak_setup_guide.md"
    echo "  - Быстрая настройка: keycloak_quick_setup.md"
}

# Запуск скрипта
main "$@"
