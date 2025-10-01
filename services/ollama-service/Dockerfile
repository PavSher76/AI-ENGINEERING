FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование утилит логирования
COPY logging_utils.py ./

# Копирование исходного кода
COPY . .

# Создание директорий для логов
RUN mkdir -p /app/logs

# Создание непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Открытие порта
EXPOSE 8012

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]
