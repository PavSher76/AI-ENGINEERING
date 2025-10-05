#!/bin/bash

echo "🔍 Мониторинг логов фронтенда"
echo "=============================="

# Функция для мониторинга логов
monitor_logs() {
    echo "📊 Мониторинг логов фронтенда в реальном времени..."
    echo "   Нажмите Ctrl+C для выхода"
    echo ""
    
    # Мониторинг логов фронтенда
    docker-compose logs -f frontend 2>/dev/null | while read line; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] $line"
    done
}

# Функция для показа последних логов
show_recent_logs() {
    echo "📋 Последние логи фронтенда:"
    echo "============================"
    docker-compose logs --tail=50 frontend
}

# Функция для фильтрации логов по типу
filter_logs() {
    local filter_type=$1
    echo "🔍 Фильтрация логов по типу: $filter_type"
    echo "=========================================="
    
    case $filter_type in
        "auth")
            docker-compose logs frontend | grep -i "auth\|keycloak\|login\|logout"
            ;;
        "error")
            docker-compose logs frontend | grep -i "error\|failed\|exception"
            ;;
        "navigation")
            docker-compose logs frontend | grep -i "navigation\|route\|page"
            ;;
        "api")
            docker-compose logs frontend | grep -i "api\|request\|response"
            ;;
        *)
            echo "❌ Неизвестный тип фильтра: $filter_type"
            echo "   Доступные типы: auth, error, navigation, api"
            ;;
    esac
}

# Функция для анализа логов
analyze_logs() {
    echo "📊 Анализ логов фронтенда"
    echo "========================"
    
    # Подсчет ошибок
    error_count=$(docker-compose logs frontend | grep -i "error\|failed\|exception" | wc -l)
    echo "🔴 Количество ошибок: $error_count"
    
    # Подсчет успешных авторизаций
    auth_success=$(docker-compose logs frontend | grep -i "successful.*auth\|auth.*success" | wc -l)
    echo "✅ Успешные авторизации: $auth_success"
    
    # Подсчет неудачных авторизаций
    auth_failed=$(docker-compose logs frontend | grep -i "auth.*error\|login.*failed" | wc -l)
    echo "❌ Неудачные авторизации: $auth_failed"
    
    # Подсчет переходов на страницы
    navigation_count=$(docker-compose logs frontend | grep -i "navigation\|route\|page" | wc -l)
    echo "🧭 Переходы на страницы: $navigation_count"
    
    # Подсчет API запросов
    api_count=$(docker-compose logs frontend | grep -i "api\|request\|response" | wc -l)
    echo "🌐 API запросы: $api_count"
    
    echo ""
    echo "📈 Статистика:"
    echo "   Всего логов: $(docker-compose logs frontend | wc -l)"
    
    # Проверка на деление на ноль
    if [ $((auth_success + auth_failed)) -gt 0 ]; then
        success_rate=$(( auth_success * 100 / (auth_success + auth_failed) ))
        echo "   Успешность авторизации: ${success_rate}%"
    else
        echo "   Успешность авторизации: N/A (нет данных)"
    fi
}

# Функция для экспорта логов
export_logs() {
    local output_file="frontend_logs_$(date +%Y%m%d_%H%M%S).log"
    echo "📤 Экспорт логов в файл: $output_file"
    echo "====================================="
    
    docker-compose logs frontend > "$output_file"
    echo "✅ Логи экспортированы в файл: $output_file"
}

# Функция для очистки логов
clear_logs() {
    echo "🗑️  Очистка логов фронтенда"
    echo "=========================="
    echo "⚠️  ВНИМАНИЕ: Это действие удалит все логи!"
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose logs --tail=0 frontend > /dev/null 2>&1
        echo "✅ Логи очищены"
    else
        echo "❌ Операция отменена"
    fi
}

# Главное меню
show_menu() {
    echo ""
    echo "🔍 Мониторинг логов фронтенда"
    echo "=============================="
    echo "1. Мониторинг в реальном времени"
    echo "2. Показать последние логи"
    echo "3. Фильтрация логов"
    echo "4. Анализ логов"
    echo "5. Экспорт логов"
    echo "6. Очистка логов"
    echo "7. Выход"
    echo ""
}

# Основная логика
main() {
    while true; do
        show_menu
        read -p "Выберите опцию (1-7): " choice
        
        case $choice in
            1)
                monitor_logs
                ;;
            2)
                show_recent_logs
                ;;
            3)
                echo "Доступные типы фильтрации:"
                echo "  - auth (авторизация)"
                echo "  - error (ошибки)"
                echo "  - navigation (навигация)"
                echo "  - api (API запросы)"
                read -p "Введите тип фильтрации: " filter_type
                filter_logs "$filter_type"
                ;;
            4)
                analyze_logs
                ;;
            5)
                export_logs
                ;;
            6)
                clear_logs
                ;;
            7)
                echo "👋 До свидания!"
                exit 0
                ;;
            *)
                echo "❌ Неверный выбор. Попробуйте снова."
                ;;
        esac
        
        echo ""
        read -p "Нажмите Enter для продолжения..."
    done
}

# Проверка аргументов командной строки
if [ $# -eq 0 ]; then
    main
else
    case $1 in
        "monitor")
            monitor_logs
            ;;
        "recent")
            show_recent_logs
            ;;
        "filter")
            filter_logs "$2"
            ;;
        "analyze")
            analyze_logs
            ;;
        "export")
            export_logs
            ;;
        "clear")
            clear_logs
            ;;
        *)
            echo "Использование: $0 [monitor|recent|filter <type>|analyze|export|clear]"
            echo ""
            echo "Примеры:"
            echo "  $0 monitor          # Мониторинг в реальном времени"
            echo "  $0 recent           # Последние логи"
            echo "  $0 filter auth      # Фильтрация по авторизации"
            echo "  $0 analyze          # Анализ логов"
            echo "  $0 export           # Экспорт логов"
            echo "  $0 clear            # Очистка логов"
            ;;
    esac
fi
