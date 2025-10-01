FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование утилит логирования
COPY logging_utils.py ./

# Копирование кода приложения
COPY . .

# Создание директорий для логов
RUN mkdir -p /app/logs

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Открытие порта
EXPOSE 8013

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]
