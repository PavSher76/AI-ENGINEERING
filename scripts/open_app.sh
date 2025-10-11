#!/bin/bash

# Скрипт для быстрого открытия приложения

echo "🚀 Открытие AI Engineering Platform"
echo "=================================="

# Проверяем доступность сервисов
echo "⏳ Проверка доступности сервисов..."

# Проверяем Frontend
if curl -k -s -o /dev/null -w "%{http_code}" "https://localhost" | grep -q "200"; then
    echo "✅ Frontend доступен"
else
    echo "❌ Frontend недоступен"
    echo "   Запустите: docker-compose up -d"
    exit 1
fi

# Проверяем Keycloak
if curl -k -s -o /dev/null -w "%{http_code}" "https://localhost:9080" | grep -q "200\|302"; then
    echo "✅ Keycloak доступен"
else
    echo "❌ Keycloak недоступен"
    echo "   Запустите: docker-compose up -d keycloak"
    exit 1
fi

echo ""
echo "🌐 Открытие приложения..."

# Открываем Frontend
echo "📱 Открытие Frontend: https://localhost"
open "https://localhost" 2>/dev/null || {
    echo "   Не удалось открыть браузер автоматически"
    echo "   Откройте вручную: https://localhost"
}

# Открываем Keycloak Admin (опционально)
read -p "🔐 Открыть Keycloak Admin Console? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔑 Открытие Keycloak Admin: https://localhost:9080/admin"
    open "https://localhost:9080/admin" 2>/dev/null || {
        echo "   Не удалось открыть браузер автоматически"
        echo "   Откройте вручную: https://localhost:9080/admin"
    }
fi

echo ""
echo "🎉 Приложение открыто!"
echo ""
echo "📋 Информация:"
echo "   • Frontend: https://localhost:9300"
echo "   • Keycloak Admin: https://localhost:9080/admin"
echo "   • Логин: admin, Пароль: admin"
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
