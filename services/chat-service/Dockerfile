FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для OCR и обработки файлов
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app

# Создание директорий для временных файлов и логов
RUN mkdir -p /app/temp /app/uploads /app/logs && chown -R app:app /app
USER app

# Экспорт порта
EXPOSE 8003

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
