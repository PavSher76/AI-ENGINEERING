"""
Конфигурация базы данных
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_password@postgres:5432/ai_engineering")

# Создание движка базы данных
engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
