FROM nginx:alpine

# Копирование статических файлов
COPY public/ /usr/share/nginx/html/

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Экспорт порта
EXPOSE 3000

# Команда запуска
CMD ["nginx", "-g", "daemon off;"]
