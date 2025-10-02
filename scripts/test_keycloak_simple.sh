#!/bin/bash

# Простой тест Keycloak

echo "🔐 Тестирование Keycloak"
echo "========================"
echo ""

# Проверяем доступность Keycloak
echo "⏳ Проверка доступности Keycloak..."
if curl -s -f http://localhost:8080/realms/master > /dev/null 2>&1; then
    echo "✅ Keycloak доступен"
else
    echo "❌ Keycloak недоступен"
    exit 1
fi

echo ""

# Проверяем админ-консоль
echo "🌐 Проверка админ-консоли..."
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/admin)
if [ "$ADMIN_STATUS" = "302" ] || [ "$ADMIN_STATUS" = "200" ]; then
    echo "✅ Админ-консоль доступна (статус: $ADMIN_STATUS)"
else
    echo "❌ Админ-консоль недоступна (статус: $ADMIN_STATUS)"
fi

echo ""

# Проверяем получение токена
echo "🔑 Проверка получения токена..."
TOKEN_RESPONSE=$(curl -s -X POST \
  http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli")

if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Токен получен успешно"
    echo "   Токен: $(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'][:50] + '...')" 2>/dev/null)"
else
    echo "❌ Не удалось получить токен"
    echo "   Ответ: $TOKEN_RESPONSE"
fi

echo ""

# Проверяем OpenID Connect конфигурацию
echo "🔧 Проверка OpenID Connect конфигурации..."
OIDC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/realms/master/.well-known/openid_configuration)
if [ "$OIDC_STATUS" = "200" ]; then
    echo "✅ OpenID Connect конфигурация доступна"
else
    echo "❌ OpenID Connect конфигурация недоступна (статус: $OIDC_STATUS)"
fi

echo ""
echo "🎉 Тестирование завершено!"
echo ""
echo "📋 Результаты:"
echo "   • Keycloak: $(curl -s -f http://localhost:8080/realms/master > /dev/null 2>&1 && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Админ-консоль: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/admin | grep -q "200\|302" && echo "✅ Доступна" || echo "❌ Недоступна")"
echo "   • Токены: $(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" | grep -q "access_token" && echo "✅ Работают" || echo "❌ Не работают")"
echo "   • OpenID Connect: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/realms/master/.well-known/openid_configuration | grep -q "200" && echo "✅ Доступен" || echo "❌ Недоступен")"
echo ""
echo "🌐 Админ-консоль: http://localhost:8080/admin"
echo "🔐 Логин: admin, Пароль: admin"
