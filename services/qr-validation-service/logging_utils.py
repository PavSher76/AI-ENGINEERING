"""
Единая система логирования для всего проекта AI Engineering
"""

import logging
import logging.handlers
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Форматтер для структурированного логирования в JSON"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем дополнительные поля если есть
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'service'):
            log_entry['service'] = record.service
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
            
        # Добавляем исключение если есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консоли"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Добавляем эмодзи для разных уровней
        emoji_map = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        emoji = emoji_map.get(record.levelname, '📝')
        
        record.levelname = f"{color}{emoji} {record.levelname}{reset}"
        return super().format(record)


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: str = "/app/logs",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    enable_json_logging: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Настройка логирования для сервиса
    
    Args:
        service_name: Имя сервиса
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Директория для логов
        enable_file_logging: Включить файловое логирование
        enable_console_logging: Включить консольное логирование
        enable_json_logging: Включить JSON логирование
        max_file_size: Максимальный размер файла лога
        backup_count: Количество файлов для ротации
    
    Returns:
        Настроенный логгер
    """
    
    # Создаем директорию для логов
    if enable_file_logging:
        os.makedirs(log_dir, exist_ok=True)
    
    # Создаем логгер
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие хендлеры
    logger.handlers.clear()
    
    # Консольный хендлер
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        if enable_json_logging:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        logger.addHandler(console_handler)
    
    # Файловый хендлер с ротацией
    if enable_file_logging:
        log_file = os.path.join(log_dir, f"{service_name}.log")
        
        # Обычный файловый хендлер
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if enable_json_logging:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        logger.addHandler(file_handler)
        
        # Отдельный файл для ошибок
        error_log_file = os.path.join(log_dir, f"{service_name}_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter() if enable_json_logging else logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(error_handler)
    
    # Настройка уровней для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Логируем успешную настройку
    logger.info(f"🚀 Логирование настроено для сервиса {service_name}")
    logger.info(f"📁 Директория логов: {log_dir}")
    logger.info(f"📊 Уровень логирования: {log_level}")
    
    return logger


def get_logger(service_name: str) -> logging.Logger:
    """Получить логгер для сервиса"""
    return logging.getLogger(service_name)


def log_request(logger: logging.Logger, method: str, path: str, 
                status_code: int, duration: float, request_id: str = None, 
                user_id: str = None, **kwargs):
    """Логирование HTTP запроса"""
    extra = {
        'request_id': request_id,
        'user_id': user_id,
        'duration': duration,
        'method': method,
        'path': path,
        'status_code': status_code,
        **kwargs
    }
    
    if status_code >= 400:
        logger.warning(f"HTTP {method} {path} -> {status_code} ({duration:.3f}s)", extra=extra)
    else:
        logger.info(f"HTTP {method} {path} -> {status_code} ({duration:.3f}s)", extra=extra)


def log_error(logger: logging.Logger, error: Exception, context: str = "", 
              request_id: str = None, user_id: str = None, **kwargs):
    """Логирование ошибки"""
    extra = {
        'request_id': request_id,
        'user_id': user_id,
        'error_type': type(error).__name__,
        'context': context,
        **kwargs
    }
    
    logger.error(f"❌ Ошибка в {context}: {str(error)}", extra=extra, exc_info=True)


def log_performance(logger: logging.Logger, operation: str, duration: float, 
                   success: bool = True, **kwargs):
    """Логирование производительности"""
    extra = {
        'operation': operation,
        'duration': duration,
        'success': success,
        **kwargs
    }
    
    if success:
        logger.info(f"⚡ {operation} выполнено за {duration:.3f}s", extra=extra)
    else:
        logger.warning(f"⚡ {operation} не выполнено за {duration:.3f}s", extra=extra)


def log_business_event(logger: logging.Logger, event: str, **kwargs):
    """Логирование бизнес-событий"""
    extra = {
        'event': event,
        **kwargs
    }
    
    logger.info(f"📊 Бизнес-событие: {event}", extra=extra)


# Конфигурации для разных сервисов
LOGGING_CONFIGS = {
    "chat-service": {
        "log_level": "INFO",
        "enable_json_logging": False,
        "max_file_size": 20 * 1024 * 1024,  # 20MB для чата
        "backup_count": 10
    },
    "qr-validation-service": {
        "log_level": "INFO", 
        "enable_json_logging": True,
        "max_file_size": 10 * 1024 * 1024,
        "backup_count": 5
    },
    "techexpert-connector": {
        "log_level": "INFO",
        "enable_json_logging": True,
        "max_file_size": 15 * 1024 * 1024,
        "backup_count": 7
    },
    "rag-service": {
        "log_level": "DEBUG",
        "enable_json_logging": True,
        "max_file_size": 25 * 1024 * 1024,  # Больше для RAG
        "backup_count": 10
    },
    "ollama-service": {
        "log_level": "INFO",
        "enable_json_logging": False,
        "max_file_size": 10 * 1024 * 1024,
        "backup_count": 5
    },
    "outgoing-control-service": {
        "log_level": "INFO",
        "enable_json_logging": True,
        "max_file_size": 15 * 1024 * 1024,
        "backup_count": 7
    }
}


def setup_service_logging(service_name: str, **overrides) -> logging.Logger:
    """Настройка логирования для конкретного сервиса с предустановленной конфигурацией"""
    config = LOGGING_CONFIGS.get(service_name, {})
    config.update(overrides)
    
    return setup_logging(
        service_name=service_name,
        **config
    )
