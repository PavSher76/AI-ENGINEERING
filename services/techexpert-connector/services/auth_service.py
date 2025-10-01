"""
Сервис аутентификации для TechExpert Connector
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

class AuthService:
    """Сервис аутентификации"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = "your-secret-key-here"  # В production использовать переменную окружения
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # Мок-пользователи для демонстрации
        self.users = {
            "admin": {
                "username": "admin",
                "password_hash": self.pwd_context.hash("admin123"),
                "permissions": ["read", "write", "admin"],
                "client_id": "admin_client",
                "client_secret": "admin_secret"
            },
            "user": {
                "username": "user", 
                "password_hash": self.pwd_context.hash("user123"),
                "permissions": ["read"],
                "client_id": "user_client",
                "client_secret": "user_secret"
            }
        }
        
        logger.info("AuthService инициализирован")
    
    async def authenticate(self, client_id: str, client_secret: str, scope: str = "read") -> Dict[str, Any]:
        """Аутентификация клиента"""
        try:
            # Ищем пользователя по client_id
            user = None
            for username, user_data in self.users.items():
                if user_data["client_id"] == client_id:
                    user = user_data
                    user["username"] = username
                    break
            
            if not user:
                raise ValueError("Неверный client_id")
            
            # Проверяем client_secret
            if user["client_secret"] != client_secret:
                raise ValueError("Неверный client_secret")
            
            # Проверяем scope
            if scope not in user["permissions"]:
                raise ValueError(f"Недостаточно прав для scope: {scope}")
            
            # Создаем токен
            access_token = self._create_access_token(
                data={"sub": user["username"], "scope": scope, "admin": "admin" in user["permissions"]},
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )
            
            logger.info(f"Успешная аутентификация пользователя: {user['username']}")
            
            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "scope": scope
            }
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {str(e)}")
            raise
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Проверка токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            
            if username is None:
                raise ValueError("Неверный токен")
            
            # Проверяем, что пользователь существует
            if username not in self.users:
                raise ValueError("Пользователь не найден")
            
            user_data = self.users[username]
            
            return {
                "username": username,
                "scope": payload.get("scope", "read"),
                "admin": payload.get("admin", False),
                "permissions": user_data["permissions"]
            }
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Токен истек")
        except jwt.JWTError:
            raise ValueError("Неверный токен")
        except Exception as e:
            logger.error(f"Ошибка проверки токена: {str(e)}")
            raise
    
    def _create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Создание токена доступа"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    async def refresh_token(self, token: str) -> Dict[str, Any]:
        """Обновление токена"""
        try:
            # Проверяем текущий токен
            user_data = await self.verify_token(token)
            
            # Создаем новый токен
            new_token = self._create_access_token(
                data={
                    "sub": user_data["username"],
                    "scope": user_data["scope"],
                    "admin": user_data["admin"]
                },
                expires_delta=timedelta(minutes=self.access_token_expire_minutes)
            )
            
            logger.info(f"Токен обновлен для пользователя: {user_data['username']}")
            
            return {
                "access_token": new_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "scope": user_data["scope"]
            }
            
        except Exception as e:
            logger.error(f"Ошибка обновления токена: {str(e)}")
            raise
    
    async def revoke_token(self, token: str) -> bool:
        """Отзыв токена"""
        try:
            # В простой реализации просто проверяем токен
            await self.verify_token(token)
            
            # В production здесь должна быть логика добавления токена в blacklist
            logger.info("Токен отозван")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отзыва токена: {str(e)}")
            return False
    
    def get_user_permissions(self, username: str) -> List[str]:
        """Получение прав пользователя"""
        if username in self.users:
            return self.users[username]["permissions"]
        return []
    
    def has_permission(self, username: str, permission: str) -> bool:
        """Проверка наличия права у пользователя"""
        permissions = self.get_user_permissions(username)
        return permission in permissions
