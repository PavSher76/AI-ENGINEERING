"""
Конфигурация логирования для TechExpert Connector
"""

import logging
import sys
import os
from datetime import datetime
import structlog

def setup_logging():
    """Настройка структурированного логирования"""
    
    # Создаем директорию для логов
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Настройка structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'{log_dir}/techexpert-connector.log', mode='a')
        ]
    )
    
    # Настройка уровней для разных модулей
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Создаем логгер для приложения
    logger = structlog.get_logger("techexpert-connector")
    logger.info("Логирование настроено", 
                log_dir=log_dir,
                level="INFO")
    
    return logger
