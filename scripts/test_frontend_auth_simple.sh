#!/bin/bash

echo "🔐 Простой тест авторизации Frontend"
echo "===================================="

FRONTEND_URL="http://localhost:3000"
KEYCLOAK_URL="http://localhost:8080"

echo "⏳ Проверка доступности сервисов..."

# Проверка Frontend
echo "🔍 Проверка Frontend: $FRONTEND_URL"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$FRONTEND_STATUS" -eq 200 ]; then
    echo "✅ Frontend доступен (статус: $FRONTEND_STATUS)"
else
    echo "❌ Frontend недоступен (статус: $FRONTEND_STATUS)"
fi

# Проверка Keycloak
echo "🔍 Проверка Keycloak: $KEYCLOAK_URL"
KEYCLOAK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$KEYCLOAK_URL")
if [ "$KEYCLOAK_STATUS" -eq 200 ]; then
    echo "✅ Keycloak доступен (статус: $KEYCLOAK_STATUS)"
else
    echo "❌ Keycloak недоступен (статус: $KEYCLOAK_STATUS)"
fi

# Проверка Keycloak Realm
echo "🔍 Проверка Keycloak Realm: $KEYCLOAK_URL/realms/ai-engineering"
REALM_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$KEYCLOAK_URL/realms/ai-engineering")
if [ "$REALM_STATUS" -eq 200 ]; then
    echo "✅ Keycloak Realm доступен (статус: $REALM_STATUS)"
else
    echo "❌ Keycloak Realm недоступен (статус: $REALM_STATUS)"
fi

# Проверка OpenID Connect конфигурации
echo "🔍 Проверка OpenID Connect конфигурации..."
OPENID_CONFIG=$(curl -s "$KEYCLOAK_URL/realms/ai-engineering/.well-known/openid-configuration")
if echo "$OPENID_CONFIG" | jq -e . > /dev/null 2>&1; then
    echo "✅ OpenID Connect конфигурация доступна"
    ISSUER=$(echo "$OPENID_CONFIG" | jq -r '.issuer')
    echo "   Issuer: $ISSUER"
else
    echo "❌ OpenID Connect конфигурация недоступна"
fi

echo ""
echo "🎉 Тестирование завершено!"
echo ""
echo "📋 Результаты:"
echo "   • Frontend: $([ "$FRONTEND_STATUS" -eq 200 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Keycloak: $([ "$KEYCLOAK_STATUS" -eq 200 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Realm: $([ "$REALM_STATUS" -eq 200 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo ""
echo "🌐 Доступные URL:"
echo "   • Frontend: $FRONTEND_URL"
echo "   • Keycloak Admin: $KEYCLOAK_URL/admin"
echo "   • Keycloak Realm: $KEYCLOAK_URL/realms/ai-engineering"
echo ""
echo "👥 Тестовые пользователи:"
echo "   • admin/admin - Администратор"
echo "   • developer/developer - Разработчик"
echo "   • analyst/analyst - Аналитик"
echo "   • viewer/viewer - Наблюдатель"
echo ""
echo "💡 Для тестирования авторизации:"
echo "   1. Откройте $FRONTEND_URL в браузере"
echo "   2. Нажмите 'Войти через Keycloak'"
echo "   3. Используйте тестовые учетные данные"
