"""
Сервис аутентификации через Keycloak
"""

import logging
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import json
import base64

logger = logging.getLogger(__name__)

# Настройки Keycloak
KEYCLOAK_URL = "http://keycloak:8080"
KEYCLOAK_REALM = "ai-engineering"
KEYCLOAK_CLIENT_ID = "ai-backend"
KEYCLOAK_CLIENT_SECRET = "ai-backend-secret"  # В production использовать переменную окружения

# HTTP Bearer схема
security = HTTPBearer()

class KeycloakAuthService:
    """Сервис аутентификации через Keycloak"""
    
    def __init__(self):
        self.keycloak_url = KEYCLOAK_URL
        self.realm = KEYCLOAK_REALM
        self.client_id = KEYCLOAK_CLIENT_ID
        self.client_secret = KEYCLOAK_CLIENT_SECRET
        self.public_key = None
        self.jwks_uri = None
        
    async def initialize(self):
        """Инициализация сервиса - получение публичного ключа"""
        try:
            # Получаем конфигурацию OpenID Connect
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.keycloak_url}/realms/{self.realm}/.well-known/openid_configuration"
                )
                response.raise_for_status()
                config = response.json()
                
                self.jwks_uri = config.get("jwks_uri")
                logger.info(f"Keycloak JWKS URI: {self.jwks_uri}")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации Keycloak: {e}")
            # В режиме разработки продолжаем без проверки токенов
            logger.warning("Продолжаем в режиме разработки без проверки токенов")
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка JWT токена через Keycloak"""
        try:
            # В режиме разработки пропускаем проверку токенов
            if not self.jwks_uri:
                logger.warning("JWKS URI не настроен, пропускаем проверку токена")
                return self._create_mock_user()
            
            # Декодируем заголовок токена
            header = jwt.get_unverified_header(token)
            
            # Получаем публичный ключ
            public_key = await self._get_public_key(header.get("kid"))
            if not public_key:
                logger.error("Не удалось получить публичный ключ")
                return None
            
            # Проверяем токен
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"{self.keycloak_url}/realms/{self.realm}"
            )
            
            return payload
            
        except JWTError as e:
            logger.error(f"Ошибка проверки токена: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при проверке токена: {e}")
            return None
    
    async def _get_public_key(self, kid: str) -> Optional[str]:
        """Получение публичного ключа из JWKS"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri)
                response.raise_for_status()
                jwks = response.json()
                
                # Ищем ключ по kid
                for key in jwks.get("keys", []):
                    if key.get("kid") == kid:
                        # Конвертируем JWK в PEM формат
                        return self._jwk_to_pem(key)
                
                logger.error(f"Ключ с kid={kid} не найден")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения публичного ключа: {e}")
            return None
    
    def _jwk_to_pem(self, jwk: Dict[str, Any]) -> str:
        """Конвертация JWK в PEM формат"""
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import base64
            
            # Извлекаем компоненты ключа
            n = base64.urlsafe_b64decode(jwk["n"] + "==")
            e = base64.urlsafe_b64decode(jwk["e"] + "==")
            
            # Создаем RSA ключ
            public_key = rsa.RSAPublicNumbers(
                int.from_bytes(e, byteorder='big'),
                int.from_bytes(n, byteorder='big')
            ).public_key()
            
            # Конвертируем в PEM
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Ошибка конвертации JWK в PEM: {e}")
            return None
    
    def _create_mock_user(self) -> Dict[str, Any]:
        """Создание мок-пользователя для режима разработки"""
        return {
            "sub": "dev-user-1",
            "preferred_username": "developer",
            "email": "developer@ai-engineering.local",
            "given_name": "Разработчик",
            "family_name": "Системы",
            "realm_access": {
                "roles": ["admin", "user", "developer"]
            },
            "resource_access": {
                "ai-backend": {
                    "roles": ["admin", "user", "developer"]
                }
            },
            "iss": f"{self.keycloak_url}/realms/{self.realm}",
            "aud": self.client_id,
            "exp": 9999999999,  # Далекое будущее
            "iat": 1000000000,
            "auth_time": 1000000000,
            "session_state": "dev-session",
            "acr": "1",
            "azp": self.client_id,
            "scope": "openid profile email",
            "sid": "dev-session-id",
            "email_verified": True,
            "name": "Разработчик Системы",
            "preferred_username": "developer",
            "given_name": "Разработчик",
            "family_name": "Системы"
        }
    
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        try:
            payload = await self.verify_token(token)
            if not payload:
                return None
            
            return {
                "id": payload.get("sub"),
                "username": payload.get("preferred_username"),
                "email": payload.get("email"),
                "first_name": payload.get("given_name"),
                "last_name": payload.get("family_name"),
                "roles": payload.get("realm_access", {}).get("roles", []),
                "client_roles": payload.get("resource_access", {}).get("ai-backend", {}).get("roles", []),
                "email_verified": payload.get("email_verified", False)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return None

# Глобальный экземпляр сервиса
keycloak_auth = KeycloakAuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Получение текущего пользователя из токена"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Проверка токена
        user_info = await keycloak_auth.get_user_info(credentials.credentials)
        if not user_info:
            raise credentials_exception
        
        return user_info
        
    except Exception as e:
        logger.error(f"Ошибка аутентификации: {e}")
        raise credentials_exception

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Получение текущего пользователя (опционально)"""
    
    if not credentials:
        return None
    
    try:
        return await keycloak_auth.get_user_info(credentials.credentials)
    except Exception as e:
        logger.error(f"Ошибка получения пользователя: {e}")
        return None

def has_role(user: Dict[str, Any], role: str) -> bool:
    """Проверка наличия роли у пользователя"""
    if not user:
        return False
    
    roles = user.get("roles", [])
    client_roles = user.get("client_roles", [])
    
    return role in roles or role in client_roles

def has_any_role(user: Dict[str, Any], roles: list) -> bool:
    """Проверка наличия любой из ролей у пользователя"""
    if not user:
        return False
    
    user_roles = user.get("roles", [])
    user_client_roles = user.get("client_roles", [])
    all_user_roles = user_roles + user_client_roles
    
    return any(role in all_user_roles for role in roles)

def require_role(role: str):
    """Декоратор для проверки роли"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ищем пользователя в аргументах
            user = None
            for arg in args:
                if isinstance(arg, dict) and "username" in arg:
                    user = arg
                    break
            
            if not user or not has_role(user, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Недостаточно прав. Требуется роль: {role}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_role(roles: list):
    """Декоратор для проверки любой из ролей"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ищем пользователя в аргументах
            user = None
            for arg in args:
                if isinstance(arg, dict) and "username" in arg:
                    user = arg
                    break
            
            if not user or not has_any_role(user, roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Недостаточно прав. Требуется одна из ролей: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
