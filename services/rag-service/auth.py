"""
Модуль аутентификации для RAG сервиса
"""

import logging
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from models import User
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Настройки JWT
SECRET_KEY = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTP Bearer схема
security = HTTPBearer()

class AuthService:
    """Сервис аутентификации"""
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Ошибка проверки токена: {e}")
            return None
    
    @staticmethod
    def get_user_from_token(token_payload: dict, db: Session) -> Optional[User]:
        """Получение пользователя из токена"""
        try:
            user_id = token_payload.get("sub")
            if not user_id:
                return None
            
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Проверка токена
        token_payload = AuthService.verify_token(credentials.credentials)
        if token_payload is None:
            raise credentials_exception
        
        # Получение пользователя
        user = AuthService.get_user_from_token(token_payload, db)
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception as e:
        logger.error(f"Ошибка аутентификации: {e}")
        raise credentials_exception

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получение текущего пользователя (опционально)"""
    if not credentials:
        return None
    
    try:
        token_payload = AuthService.verify_token(credentials.credentials)
        if token_payload is None:
            return None
        
        user = AuthService.get_user_from_token(token_payload, db)
        return user
        
    except Exception as e:
        logger.warning(f"Ошибка опциональной аутентификации: {e}")
        return None

def create_access_token(data: dict) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверка прав администратора"""
    # В реальной реализации здесь должна быть проверка роли пользователя
    # Пока возвращаем пользователя как есть
    return current_user
