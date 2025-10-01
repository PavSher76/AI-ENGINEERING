# Этап сборки
FROM node:18-alpine as build

WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --legacy-peer-deps

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Этап продакшена
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/build /usr/share/nginx/html

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Экспорт порта
EXPOSE 3000

# Команда запуска
CMD ["nginx", "-g", "daemon off;"]
