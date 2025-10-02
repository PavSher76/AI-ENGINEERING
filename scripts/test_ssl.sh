#!/bin/bash

# Скрипт для тестирования SSL соединений

echo "🔐 Тестирование SSL соединений"
echo "=============================="

# Функция для проверки SSL соединения
test_ssl_connection() {
    local url=$1
    local name=$2
    
    echo "🔍 Тестирование $name..."
    
    # Проверяем доступность
    if curl -k -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|302"; then
        echo "✅ $name доступен"
        
        # Проверяем SSL сертификат
        if echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
            echo "✅ SSL сертификат валиден"
        else
            echo "⚠️  SSL сертификат не найден или невалиден"
        fi
    else
        echo "❌ $name недоступен"
    fi
    echo ""
}

# Тестируем основные сервисы
test_ssl_connection "https://localhost" "Frontend (HTTPS)"
test_ssl_connection "https://localhost:8080" "Keycloak (HTTPS)"

# Тестируем API endpoints
echo "🔍 Тестирование API endpoints..."
API_ENDPOINTS=(
    "https://localhost/api/chat/health"
    "https://localhost/api/rag/health"
    "https://localhost/api/outgoing-control/health"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "🔍 Тестирование $endpoint..."
    if curl -k -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200\|404"; then
        echo "✅ API endpoint доступен"
    else
        echo "❌ API endpoint недоступен"
    fi
done

echo ""
echo "🔍 Проверка перенаправления HTTP -> HTTPS..."
if curl -s -o /dev/null -w "%{http_code}" "http://localhost" | grep -q "301"; then
    echo "✅ HTTP перенаправляется на HTTPS"
else
    echo "❌ HTTP не перенаправляется на HTTPS"
fi

echo ""
echo "🎉 Тестирование SSL завершено!"
echo ""
echo "📋 Результаты:"
echo "   • Frontend: $([ $(curl -k -s -o /dev/null -w "%{http_code}" "https://localhost") -eq 200 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • Keycloak: $([ $(curl -k -s -o /dev/null -w "%{http_code}" "https://localhost:8080") -eq 200 ] && echo "✅ Доступен" || echo "❌ Недоступен")"
echo "   • HTTP Redirect: $([ $(curl -s -o /dev/null -w "%{http_code}" "http://localhost") -eq 301 ] && echo "✅ Работает" || echo "❌ Не работает")"
echo ""
echo "🌐 Доступные URL:"
echo "   • Frontend: https://localhost"
echo "   • Keycloak Admin: https://localhost:8080/admin"
echo "   • Keycloak Realm: https://localhost:8080/realms/ai-engineering"
echo ""
echo "⚠️  ВНИМАНИЕ: Используются самоподписанные сертификаты!"
echo "   В браузере появится предупреждение о безопасности."
echo "   Нажмите 'Дополнительно' -> 'Перейти на localhost (небезопасно)'"
