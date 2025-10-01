# Настройка системы авторизации Frontend

## Обзор

Система авторизации frontend интегрирована с Keycloak и поддерживает как режим разработки (без обязательной авторизации), так и production режим с полной проверкой токенов.

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   Keycloak      │    │   Backend API   │
│                 │    │                 │    │                 │
│ - AuthContext   │◄──►│ - SSO           │◄──►│ - JWT Verify    │
│ - ProtectedRoute│    │ - Users         │    │ - Role Check    │
│ - API Service   │    │ - Roles         │    │ - Permissions   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Компоненты системы

### 1. Keycloak Integration (`src/services/keycloak.ts`)
- Конфигурация Keycloak
- Инициализация и обработчики событий
- Утилиты для работы с токенами и ролями

### 2. AuthContext (`src/contexts/AuthContext.tsx`)
- Управление состоянием авторизации
- Интеграция с Keycloak
- Мок-пользователь для режима разработки

### 3. ProtectedRoute (`src/components/Auth/ProtectedRoute.tsx`)
- Защищенные маршруты
- Проверка ролей и прав доступа
- Компоненты-гарды для условного рендеринга

### 4. API Service (`src/services/api.ts`)
- Автоматическое добавление токенов
- Обработка обновления токенов
- Обработка ошибок авторизации

## Настройка

### 1. Переменные окружения

Создайте файл `.env` в корне frontend проекта:

```env
# Keycloak Configuration
REACT_APP_KEYCLOAK_URL=http://localhost:8080
REACT_APP_KEYCLOAK_REALM=ai-engineering
REACT_APP_KEYCLOAK_CLIENT_ID=ai-frontend

# API Configuration
REACT_APP_API_URL=http://localhost:80/api

# Development Mode
REACT_APP_DEV_MODE=true
REACT_APP_ENABLE_KEYCLOAK=true
```

### 2. Конфигурация Keycloak

#### Создание Realm
1. Откройте http://localhost:8080/admin
2. Войдите как admin/admin
3. Создайте realm "ai-engineering"

#### Создание Client
1. В realm "ai-engineering" создайте client "ai-frontend"
2. Настройки:
   - **Client ID**: ai-frontend
   - **Client Protocol**: openid-connect
   - **Access Type**: public
   - **Valid Redirect URIs**: http://localhost:3000/*
   - **Web Origins**: http://localhost:3000

#### Создание пользователей
- **admin/admin** - Администратор
- **developer/developer** - Разработчик
- **analyst/analyst** - Аналитик
- **viewer/viewer** - Наблюдатель

### 3. Запуск приложения

```bash
cd frontend
npm install
npm start
```

## Использование

### 1. Защищенные маршруты

```tsx
import { ProtectedRoute } from './components/Auth/ProtectedRoute';

// Базовая защита
<ProtectedRoute>
  <MyComponent />
</ProtectedRoute>

// Защита с ролями
<ProtectedRoute requiredRoles={['admin', 'developer']}>
  <AdminComponent />
</ProtectedRoute>

// Защита с правами доступа
<ProtectedRoute requiredPermissions={['read', 'write']}>
  <DataComponent />
</ProtectedRoute>
```

### 2. Проверка ролей в компонентах

```tsx
import { useAuth, RoleGuard, PermissionGuard } from './contexts/AuthContext';

const MyComponent = () => {
  const { user, hasRole, hasPermission } = useAuth();

  return (
    <div>
      {hasRole('admin') && <AdminPanel />}
      
      <RoleGuard roles={['developer']}>
        <DeveloperTools />
      </RoleGuard>
      
      <PermissionGuard permissions={['write']}>
        <EditButton />
      </PermissionGuard>
    </div>
  );
};
```

### 3. API запросы с авторизацией

```tsx
import api from './services/api';

// Токен автоматически добавляется к запросам
const fetchData = async () => {
  try {
    const response = await api.get('/protected-endpoint');
    return response.data;
  } catch (error) {
    // Ошибки авторизации обрабатываются автоматически
    console.error('API Error:', error);
  }
};
```

## Режимы работы

### Режим разработки (Development)

В режиме разработки система работает без обязательной авторизации:

- ✅ Приложение доступно без входа в систему
- ✅ Создается мок-пользователь для тестирования
- ✅ Все роли и права разрешены
- ✅ API запросы работают без токенов

**Активация**: `REACT_APP_DEV_MODE=true`

### Production режим

В production режиме включена полная проверка авторизации:

- 🔐 Обязательная авторизация для всех защищенных маршрутов
- 🔐 Проверка JWT токенов через Keycloak
- 🔐 Проверка ролей и прав доступа
- 🔐 Автоматическое обновление токенов

**Активация**: `REACT_APP_DEV_MODE=false`

## Компоненты

### AuthContext

```tsx
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllRoles: (roles: string[]) => boolean;
  updateToken: () => Promise<boolean>;
}
```

### ProtectedRoute

```tsx
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  requireAllRoles?: boolean;
  fallbackPath?: string;
}
```

### RoleGuard

```tsx
interface RoleGuardProps {
  children: React.ReactNode;
  roles: string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
}
```

## Безопасность

### 1. Токены
- JWT токены с проверкой подписи
- Автоматическое обновление токенов
- Безопасное хранение в памяти

### 2. Роли и права
- Иерархическая система ролей
- Гранулярные права доступа
- Проверка на клиенте и сервере

### 3. CORS
- Настроенные CORS заголовки
- Безопасные redirect URIs
- Проверка origins

## Тестирование

### 1. Автоматическое тестирование

```bash
python3 scripts/test_frontend_auth.py
```

### 2. Ручное тестирование

1. **Откройте приложение**: http://localhost:3000
2. **Проверьте страницу входа**: /login
3. **Тестируйте защищенные маршруты**
4. **Проверьте API запросы**

### 3. Тестирование ролей

```tsx
// Тест роли администратора
const { hasRole } = useAuth();
console.log('Is admin:', hasRole('admin'));

// Тест множественных ролей
const { hasAnyRole } = useAuth();
console.log('Has dev or admin:', hasAnyRole(['developer', 'admin']));
```

## Troubleshooting

### Проблема: "Keycloak не инициализирован"

**Решение**: 
1. Проверьте доступность Keycloak
2. Убедитесь в правильности URL и realm
3. Проверьте настройки клиента

### Проблема: "CORS ошибка"

**Решение**:
1. Настройте Web Origins в Keycloak
2. Проверьте CORS заголовки в nginx
3. Убедитесь в правильности redirect URIs

### Проблема: "Токен не обновляется"

**Решение**:
1. Проверьте настройки времени жизни токенов
2. Убедитесь в правильности client configuration
3. Проверьте refresh token settings

### Проблема: "Роли не работают"

**Решение**:
1. Проверьте настройки ролей в Keycloak
2. Убедитесь в правильности client roles
3. Проверьте маппинг ролей в токене

## Мониторинг

### 1. Логи авторизации

```javascript
// Включение отладочных логов
localStorage.setItem('keycloak-debug', 'true');
```

### 2. Проверка токенов

```javascript
// Проверка токена в консоли браузера
console.log('Token:', keycloak.token);
console.log('Token parsed:', keycloak.tokenParsed);
console.log('User info:', keycloakUtils.getUserInfo());
```

### 3. Метрики

- Время инициализации Keycloak
- Количество успешных авторизаций
- Количество ошибок токенов
- Использование ролей

## Заключение

Система авторизации frontend обеспечивает:

- ✅ Безопасную аутентификацию через Keycloak
- ✅ Гибкую систему ролей и прав
- ✅ Защищенные маршруты и компоненты
- ✅ Автоматическое управление токенами
- ✅ Поддержку режимов разработки и production
- ✅ Современный UX с Material-UI

Для production использования рекомендуется:

1. Настроить SSL сертификаты
2. Изменить пароли по умолчанию
3. Настроить мониторинг
4. Реализовать резервное копирование
5. Настроить алерты безопасности
