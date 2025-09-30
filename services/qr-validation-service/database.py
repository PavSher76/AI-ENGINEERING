"""
Настройка базы данных для QR валидации РД
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import os
from typing import Generator

# Настройки базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@postgres:5432/ai_engineering"
)

# Создание движка базы данных
engine = create_engine(DATABASE_URL, echo=False)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Генератор сессий базы данных
    
    Yields:
        Session: Сессия базы данных
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """
    Инициализация базы данных
    Создает все таблицы если они не существуют
    """
    from models import Base
    
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ База данных QR валидации РД инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        raise e

def create_tables():
    """
    Создает все таблицы в базе данных
    """
    from models import Base
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Удаляет все таблицы из базы данных
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)
