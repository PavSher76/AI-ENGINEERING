# Руководство по системе авторизации с Keycloak

## Обзор

Система авторизации AI Engineering Platform интегрирована с Keycloak для обеспечения безопасного доступа к сервисам. Система поддерживает как режим разработки (без обязательной авторизации), так и production режим с полной проверкой токенов.

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Keycloak      │    │   Backend       │
│   (React)       │◄──►│   (SSO)         │◄──►│   Services      │
│                 │    │                 │    │                 │
│ - AuthContext   │    │ - Realm         │    │ - JWT Verify    │
│ - Keycloak SDK  │    │ - Users         │    │ - Role Check    │
│ - Token Storage │    │ - Roles         │    │ - Permissions   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Компоненты системы

### 1. Keycloak Server
- **URL**: http://localhost:8080
- **Admin Console**: http://localhost:8080/admin
- **Realm**: ai-engineering
- **Clients**: ai-frontend, ai-backend

### 2. Backend Services
- **Chat Service**: Интегрирован с Keycloak
- **RAG Service**: Готов к интеграции
- **Другие сервисы**: Могут быть интегрированы по аналогии

### 3. Frontend
- **AuthContext**: Управление состоянием авторизации
- **Keycloak SDK**: Интеграция с Keycloak
- **Protected Routes**: Защищенные маршруты

## Настройка Keycloak

### Шаг 1: Доступ к Admin Console

1. Откройте браузер: http://localhost:8080
2. Нажмите "Administration Console"
3. Войдите: `admin` / `admin`

### Шаг 2: Создание Realm

1. Выберите "Create Realm"
2. **Realm name**: `ai-engineering`
3. **Display name**: `AI Engineering Platform`
4. Нажмите "Create"

### Шаг 3: Создание клиентов

#### Frontend Client
```
Client ID: ai-frontend
Client Protocol: openid-connect
Access Type: public
Valid Redirect URIs: http://localhost:3000/*
Web Origins: http://localhost:3000
```

#### Backend Client
```
Client ID: ai-backend
Client Protocol: openid-connect
Access Type: confidential
Service Accounts: enabled
Valid Redirect URIs: http://localhost:8001/*
```

### Шаг 4: Создание ролей

#### Realm Roles
- `admin` - Полный доступ
- `user` - Стандартный пользователь
- `developer` - Разработчик
- `analyst` - Аналитик
- `viewer` - Только просмотр

#### Client Roles
Создайте аналогичные роли для каждого клиента.

### Шаг 5: Создание пользователей

#### Администратор
```
Username: admin
Password: admin
Email: admin@ai-engineering.local
Roles: admin, user
```

#### Разработчик
```
Username: developer
Password: developer
Email: developer@ai-engineering.local
Roles: developer, user
```

#### Аналитик
```
Username: analyst
Password: analyst
Email: analyst@ai-engineering.local
Roles: analyst, user
```

#### Наблюдатель
```
Username: viewer
Password: viewer
Email: viewer@ai-engineering.local
Roles: viewer
```

## Интеграция в Backend

### 1. Установка зависимостей

```python
# requirements.txt
python-jose[cryptography]==3.3.0
cryptography==41.0.7
httpx==0.25.2
```

### 2. Создание сервиса авторизации

```python
# services/keycloak_auth.py
from services.keycloak_auth import (
    keycloak_auth,
    get_current_user,
    get_current_user_optional,
    has_role,
    require_role
)
```

### 3. Инициализация в main.py

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация Keycloak
    await keycloak_auth.initialize()
    yield
```

### 4. Защита эндпоинтов

```python
@app.get("/protected")
async def protected_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    return {"message": f"Привет, {current_user['username']}!"}

@app.put("/admin-only")
async def admin_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not has_role(current_user, "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return {"message": "Админская функция"}
```

## Интеграция в Frontend

### 1. Установка зависимостей

```bash
npm install @react-keycloak/web keycloak-js
```

### 2. Настройка Keycloak

```typescript
// services/keycloak.ts
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: process.env.REACT_APP_KEYCLOAK_URL,
  realm: process.env.REACT_APP_KEYCLOAK_REALM,
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID,
});

export default keycloak;
```

### 3. Обновление AuthContext

```typescript
// contexts/AuthContext.tsx
import { useKeycloak } from '@react-keycloak/web';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const { keycloak, initialized } = useKeycloak();
  
  // Логика авторизации через Keycloak
  // ...
};
```

### 4. Защита маршрутов

```typescript
// App.tsx
import { ReactKeycloakProvider } from '@react-keycloak/web';

const App: React.FC = () => {
  return (
    <ReactKeycloakProvider authClient={keycloak}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedLayout />}>
            {/* Защищенные маршруты */}
          </Route>
        </Routes>
      </Router>
    </ReactKeycloakProvider>
  );
};
```

## Режимы работы

### Режим разработки (Development)

В режиме разработки система работает без обязательной авторизации:

- ✅ Сервисы доступны без токенов
- ✅ Создается мок-пользователь для тестирования
- ✅ Логирование предупреждений о пропуске проверки токенов
- ⚠️ Не рекомендуется для production

### Production режим

В production режиме включена полная проверка авторизации:

- 🔐 Обязательная авторизация для всех эндпоинтов
- 🔐 Проверка JWT токенов через Keycloak
- 🔐 Проверка ролей и прав доступа
- 🔐 Автоматическое обновление токенов

## Переменные окружения

### Backend
```env
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=ai-engineering
KEYCLOAK_CLIENT_ID=ai-backend
KEYCLOAK_CLIENT_SECRET=ai-backend-secret
```

### Frontend
```env
REACT_APP_KEYCLOAK_URL=http://localhost:8080
REACT_APP_KEYCLOAK_REALM=ai-engineering
REACT_APP_KEYCLOAK_CLIENT_ID=ai-frontend
```

## Тестирование

### 1. Автоматическое тестирование

```bash
python3 scripts/test_auth.py
```

### 2. Ручное тестирование

1. **Получение токена**:
```bash
curl -X POST "http://localhost:8080/realms/ai-engineering/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin&grant_type=password&client_id=ai-frontend"
```

2. **Использование токена**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8003/chat
```

### 3. Тестирование ролей

```python
# Проверка роли администратора
if has_role(current_user, "admin"):
    # Админские функции
    pass

# Проверка нескольких ролей
if has_any_role(current_user, ["admin", "developer"]):
    # Функции для админов и разработчиков
    pass
```

## Безопасность

### 1. Рекомендации по безопасности

- 🔐 Используйте HTTPS в production
- 🔐 Настройте сильные пароли
- 🔐 Регулярно обновляйте токены
- 🔐 Ограничьте время жизни токенов
- 🔐 Используйте secure cookies

### 2. Настройка SSL

```yaml
# docker-compose.yml
environment:
  KC_HOSTNAME_STRICT_HTTPS: true
  KC_HTTP_ENABLED: false
```

### 3. Настройка токенов

```yaml
# Realm Settings → Tokens
Access token lifespan: 5 minutes
Refresh token max reuse: 0
SSO session idle timeout: 30 minutes
```

## Troubleshooting

### Проблема: "Realm does not exist"

**Решение**: Создайте realm `ai-engineering` в Keycloak Admin Console.

### Проблема: "Client not found"

**Решение**: Создайте клиентов `ai-frontend` и `ai-backend` в realm.

### Проблема: "Invalid token"

**Решение**: 
1. Проверьте время жизни токена
2. Убедитесь в правильности client_id
3. Проверьте настройки realm

### Проблема: "CORS error"

**Решение**: Настройте Web Origins в клиенте Keycloak.

### Проблема: "JWKS URI not found"

**Решение**: Проверьте доступность Keycloak и настройки realm.

## Мониторинг

### 1. Логи авторизации

```bash
# Просмотр логов chat-service
docker-compose logs chat-service | grep -i auth

# Просмотр логов Keycloak
docker-compose logs keycloak | grep -i auth
```

### 2. Метрики

- Количество успешных авторизаций
- Количество неудачных попыток входа
- Время ответа Keycloak
- Использование токенов

### 3. Алерты

Настройте алерты на:
- Высокое количество неудачных попыток входа
- Недоступность Keycloak
- Истечение токенов

## Заключение

Система авторизации с Keycloak обеспечивает:

- ✅ Централизованное управление пользователями
- ✅ Единый вход (SSO)
- ✅ Гибкая система ролей
- ✅ Безопасность и масштабируемость
- ✅ Интеграция с внешними системами

Для production использования рекомендуется:

1. Настроить SSL сертификаты
2. Изменить пароли по умолчанию
3. Настроить мониторинг
4. Реализовать резервное копирование
5. Настроить алерты безопасности
