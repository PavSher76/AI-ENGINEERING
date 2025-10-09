# Этап сборки
FROM node:18-alpine as build

WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --legacy-peer-deps

# Копирование исходного кода
COPY . .

# Установка переменных окружения для сборки
ENV REACT_APP_API_URL=https://localhost/api
ENV REACT_APP_KEYCLOAK_URL=https://localhost:9080
ENV REACT_APP_KEYCLOAK_REALM=ai-engineering
ENV REACT_APP_KEYCLOAK_CLIENT_ID=ai-frontend
ENV REACT_APP_ENABLE_KEYCLOAK=true

# Сборка приложения
RUN npm run build

# Этап продакшена
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/build /usr/share/nginx/html

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Создание директорий для SSL сертификатов
RUN mkdir -p /etc/ssl/certs /etc/ssl/private

# Копирование SSL сертификатов
COPY localhost.crt /etc/ssl/certs/localhost.crt
COPY localhost.key /etc/ssl/private/localhost.key

# Установка прав доступа для SSL сертификатов
RUN chmod 644 /etc/ssl/certs/localhost.crt && chmod 600 /etc/ssl/private/localhost.key

# Экспорт порта
EXPOSE 3000

# Команда запуска
CMD ["nginx", "-g", "daemon off;"]
