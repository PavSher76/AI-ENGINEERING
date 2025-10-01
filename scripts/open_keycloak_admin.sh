#!/bin/bash

# Скрипт для открытия Keycloak Admin Console

echo "🔐 Открытие Keycloak Admin Console..."
echo ""

# Проверяем, что Keycloak запущен
if ! curl -s -f http://localhost:8080/realms/master > /dev/null 2>&1; then
    echo "❌ Keycloak не запущен. Запустите его командой:"
    echo "   docker-compose up -d keycloak"
    echo ""
    exit 1
fi

echo "✅ Keycloak запущен и доступен"
echo ""
echo "🌐 Открываем админ-консоль в браузере..."
echo ""

# Открываем админ-консоль в браузере
if command -v open > /dev/null 2>&1; then
    # macOS
    open "http://localhost:8080/admin"
elif command -v xdg-open > /dev/null 2>&1; then
    # Linux
    xdg-open "http://localhost:8080/admin"
elif command -v start > /dev/null 2>&1; then
    # Windows
    start "http://localhost:8080/admin"
else
    echo "❌ Не удалось автоматически открыть браузер"
    echo "   Откройте вручную: http://localhost:8080/admin"
    exit 1
fi

echo ""
echo "📋 Данные для входа:"
echo "   Логин: admin"
echo "   Пароль: admin"
echo ""
echo "🔧 После входа выполните следующие шаги:"
echo "   1. Создайте новый realm 'ai-engineering'"
echo "   2. Создайте клиента 'ai-frontend'"
echo "   3. Создайте пользователей с ролями"
echo ""
echo "📖 Подробная инструкция: docs/KEYCLOAK_AUTH_GUIDE.md"
