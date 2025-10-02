#!/bin/bash

echo "🔐 Полный тест системы авторизации"
echo "=================================="

FRONTEND_URL="http://localhost:3000"
KEYCLOAK_URL="http://localhost:8080"
REALM_NAME="ai-engineering"
CLIENT_ID="ai-frontend"

# Функция для проверки доступности URL
check_url() {
  local name=$1
  local url=$2
  local expected_status_codes=$3
  local status=$(curl -s -o /dev/null -w "%{http_code}" "$url")

  if [[ " $expected_status_codes " =~ " $status " ]]; then
    echo "✅ $name доступен (статус: $status)"
    return 0
  else
    echo "❌ $name недоступен (статус: $status)"
    return 1
  fi
}

# Функция для получения токена пользователя
get_user_token() {
  local username=$1
  local password=$2
  
  response=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$username" \
    -d "password=$password" \
    -d "grant_type=password" \
    -d "client_id=$CLIENT_ID")
  
  echo "$response" | jq -r '.access_token'
}

echo "⏳ Проверка доступности сервисов..."

# Проверка Frontend
check_url "Frontend" "$FRONTEND_URL" "200 302"
FRONTEND_STATUS=$?

# Проверка Keycloak
check_url "Keycloak" "$KEYCLOAK_URL" "200 302"
KEYCLOAK_STATUS=$?

# Проверка Keycloak Realm
check_url "Keycloak Realm" "$KEYCLOAK_URL/realms/$REALM_NAME" "200 302"
REALM_STATUS=$?

echo ""
echo "🔧 Проверка OpenID Connect конфигурации..."
OPENID_CONFIG=$(curl -s "$KEYCLOAK_URL/realms/$REALM_NAME/.well-known/openid-configuration")
if echo "$OPENID_CONFIG" | jq -e . > /dev/null 2>&1; then
  echo "✅ OpenID Connect конфигурация доступна"
  ISSUER=$(echo "$OPENID_CONFIG" | jq -r '.issuer')
  echo "   Issuer: $ISSUER"
else
  echo "❌ OpenID Connect конфигурация недоступна"
fi

echo ""
echo "👥 Проверка тестовых пользователей..."
TEST_USERS=(
  "admin:admin"
  "developer:developer"
  "analyst:analyst"
  "viewer:viewer"
)

AUTHENTICATED_USERS=0
for USER_PAIR in "${TEST_USERS[@]}"; do
  IFS=':' read -r USERNAME PASSWORD <<< "$USER_PAIR"
  echo "🔍 Проверка пользователя: $USERNAME"
  TOKEN=$(get_user_token "$USERNAME" "$PASSWORD")
  
  if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo "✅ Пользователь $USERNAME может получить токен"
    AUTHENTICATED_USERS=$((AUTHENTICATED_USERS + 1))
  else
    echo "❌ Пользователь $USERNAME не может получить токен"
  fi
done

echo ""
echo "🎉 Тестирование завершено!"
echo ""
echo "📋 Результаты:"
echo "   • Frontend: $([ $FRONTEND_STATUS -eq 0 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Keycloak: $([ $KEYCLOAK_STATUS -eq 0 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Realm: $([ $REALM_STATUS -eq 0 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Аутентифицированные пользователи: $AUTHENTICATED_USERS/4"
echo ""
echo "🌐 Доступные URL:"
echo "   • Frontend: $FRONTEND_URL"
echo "   • Keycloak Admin: $KEYCLOAK_URL/admin"
echo "   • Keycloak Realm: $KEYCLOAK_URL/realms/$REALM_NAME"
echo ""
echo "👥 Тестовые пользователи:"
echo "   • admin/admin - Администратор"
echo "   • developer/developer - Разработчик"
echo "   • analyst/analyst - Аналитик"
echo "   • viewer/viewer - Наблюдатель"
echo ""
echo "💡 Для тестирования в браузере:"
echo "   1. Откройте $FRONTEND_URL"
echo "   2. Нажмите 'Войти через Keycloak'"
echo "   3. Используйте тестовые учетные данные"
echo ""

if [ $AUTHENTICATED_USERS -eq 4 ] && [ $FRONTEND_STATUS -eq 0 ] && [ $KEYCLOAK_STATUS -eq 0 ]; then
  echo "🎊 СИСТЕМА АВТОРИЗАЦИИ РАБОТАЕТ КОРРЕКТНО!"
  echo "   Все компоненты функционируют как ожидается."
else
  echo "⚠️  Есть проблемы с системой авторизации."
  echo "   Проверьте логи сервисов для диагностики."
fi
