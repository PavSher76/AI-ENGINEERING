# Включение авторизации в AI Engineering Platform

## Обзор

Для периода активной разработки авторизация была отключена для упрощения тестирования. Данный документ описывает, как включить авторизацию обратно для production использования.

## Изменения для включения авторизации

### 1. Backend Services

#### RAG Service (`services/rag-service/main.py`)
```python
# Заменить все вхождения:
current_user = Depends(get_current_user_optional)
# На:
current_user = Depends(get_current_user)

# И обновить логику:
user_id = current_user.id if current_user else "system"
# На:
user_id = current_user.id
```

#### Ollama Management Service (`services/ollama-service/main.py`)
```python
# Заменить все вхождения:
current_user = Depends(get_current_user_optional)
# На:
current_user = Depends(get_current_user)

# И обновить логику:
user_id = current_user.id if current_user else "system"
# На:
user_id = current_user.id
```

### 2. Frontend

#### App.tsx (`frontend/src/App.tsx`)
```typescript
// Раскомментировать:
import { ReactKeycloakProvider } from '@react-keycloak/web';
import keycloak from './services/keycloak';

// И заменить структуру приложения:
const App: React.FC = () => {
  return (
    <ReactKeycloakProvider
      authClient={keycloak}
      onEvent={keycloakEventHandler}
      LoadingComponent={<LoadingSpinner />}
    >
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AuthProvider>
            <ProjectProvider>
              <Router>
                <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                  <Routes>
                    {/* Public routes */}
                    <Route path="/login" element={<Login />} />
                    
                    {/* Protected routes */}
                    <Route path="/" element={<Layout />}>
                      <Route index element={<Navigate to="/dashboard" replace />} />
                      <Route path="dashboard" element={<Dashboard />} />
                      <Route path="chat" element={<Chat />} />
                      <Route path="documents" element={<Documents />} />
                      <Route path="calculations" element={<Calculations />} />
                      <Route path="analytics" element={<Analytics />} />
                      <Route path="reports" element={<Reports />} />
                      <Route path="settings" element={<Settings />} />
                    </Route>
                    
                    {/* Catch all route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Box>
              </Router>
            </ProjectProvider>
          </AuthProvider>
        </ThemeProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ReactKeycloakProvider>
  );
};
```

#### AuthContext (`frontend/src/contexts/AuthContext.tsx`)
```typescript
// Раскомментировать:
import { useKeycloak } from '@react-keycloak/web';

// И заменить логику:
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const { keycloak, initialized } = useKeycloak();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (initialized) {
      if (keycloak.authenticated) {
        // Extract user information from Keycloak token
        const tokenParsed = keycloak.tokenParsed;
        if (tokenParsed) {
          const userData: User = {
            id: tokenParsed.sub || '',
            username: tokenParsed.preferred_username || '',
            email: tokenParsed.email || '',
            firstName: tokenParsed.given_name || '',
            lastName: tokenParsed.family_name || '',
            roles: tokenParsed.realm_access?.roles || [],
            permissions: tokenParsed.resource_access?.['ai-frontend']?.roles || [],
          };
          setUser(userData);
        }
      }
      setIsLoading(false);
    }
  }, [keycloak, initialized]);

  const login = () => {
    keycloak.login();
  };

  const logout = () => {
    keycloak.logout();
    setUser(null);
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    return user.roles.includes(role);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: keycloak.authenticated || false,
    isLoading,
    login,
    logout,
    hasRole,
    hasPermission,
  };
```

#### API Service (`frontend/src/services/api.ts`)
```typescript
// Раскомментировать:
import keycloak from './keycloak';

// И обновить interceptors:
// Request interceptor to add auth token
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    if (keycloak.authenticated && keycloak.token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${keycloak.token}`,
      };
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await keycloak.updateToken(30);
        if (keycloak.token) {
          originalRequest.headers.Authorization = `Bearer ${keycloak.token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        keycloak.logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

#### Layout (`frontend/src/components/Layout/Layout.tsx`)
```typescript
// Раскомментировать проверку авторизации:
if (!isAuthenticated) {
  return <LoadingSpinner message="Перенаправление на страницу входа..." />;
}
```

### 3. Docker Configuration

#### docker-compose.yml
```yaml
# Раскомментировать Keycloak сервис:
keycloak:
  image: quay.io/keycloak/keycloak:latest
  ports:
    - "8080:8080"
  environment:
    KEYCLOAK_ADMIN: admin
    KEYCLOAK_ADMIN_PASSWORD: admin123
    KC_DB: postgres
    KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
    KC_DB_USERNAME: ai_user
    KC_DB_PASSWORD: ai_password
  volumes:
    - keycloak_data:/opt/keycloak/data
  depends_on:
    - postgres
  networks:
    - ai-network
  command: start-dev

# И обновить зависимости frontend:
frontend:
  # ... другие настройки
  depends_on:
    - keycloak
```

#### Nginx Configuration (`infrastructure/nginx/nginx.conf`)
```nginx
# Раскомментировать upstream:
upstream keycloak {
    server keycloak:8080;
}

# И location:
location /auth/ {
    proxy_pass http://keycloak/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Настройка Keycloak

### 1. Создание Realm
1. Откройте http://localhost:8080
2. Войдите как admin/admin123
3. Создайте новый realm "ai-engineering"

### 2. Создание Client
1. В realm "ai-engineering" создайте client "ai-frontend"
2. Настройте:
   - Client ID: ai-frontend
   - Client Protocol: openid-connect
   - Access Type: public
   - Valid Redirect URIs: http://localhost:3000/*
   - Web Origins: http://localhost:3000

### 3. Создание пользователей
1. Создайте пользователей в Users секции
2. Назначьте роли и пароли
3. Настройте группы и роли

## Переменные окружения

### Frontend (.env)
```env
REACT_APP_KEYCLOAK_URL=http://localhost:8080
REACT_APP_KEYCLOAK_REALM=ai-engineering
REACT_APP_KEYCLOAK_CLIENT_ID=ai-frontend
```

### Backend
Убедитесь, что JWT_SECRET настроен правильно в .env файлах сервисов.

## Тестирование

### 1. Запуск системы
```bash
./scripts/setup.sh
```

### 2. Проверка Keycloak
- Откройте http://localhost:8080
- Войдите в admin console
- Проверьте настройки realm и client

### 3. Проверка Frontend
- Откройте http://localhost:3000
- Должен произойти редирект на Keycloak
- Войдите с учетными данными
- Проверьте доступ к защищенным страницам

## Безопасность

### 1. Изменение паролей по умолчанию
- Измените пароль admin в Keycloak
- Настройте сильные пароли для пользователей
- Обновите JWT_SECRET в production

### 2. Настройка SSL
- Настройте SSL сертификаты для Keycloak
- Обновите redirect URIs для HTTPS
- Настройте secure cookies

### 3. Роли и права
- Создайте роли для разных типов пользователей
- Настройте права доступа к ресурсам
- Реализуйте проверку прав в API

## Troubleshooting

### Проблемы с токенами
- Проверьте настройки client в Keycloak
- Убедитесь в правильности JWT_SECRET
- Проверьте время жизни токенов

### Проблемы с редиректами
- Проверьте Valid Redirect URIs
- Убедитесь в правильности Web Origins
- Проверьте настройки CORS

### Проблемы с ролями
- Проверьте настройки realm roles
- Убедитесь в правильности client roles
- Проверьте маппинг ролей в токене
