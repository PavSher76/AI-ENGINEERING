import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { User } from '../types';
import { keycloakUtils } from '../services/keycloak.ts';
import environment from '../config/environment.ts';

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

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

// Компонент для работы с Keycloak
const KeycloakAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { keycloak, initialized } = useKeycloak();
  return <AuthProviderInternal keycloak={keycloak} initialized={initialized}>{children}</AuthProviderInternal>;
};

// Компонент без Keycloak
const NoAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  return <AuthProviderInternal keycloak={null} initialized={true}>{children}</AuthProviderInternal>;
};

// Внутренний провайдер авторизации
const AuthProviderInternal: React.FC<{ 
  children: ReactNode; 
  keycloak: any; 
  initialized: boolean; 
}> = ({ children, keycloak, initialized }) => {
  
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (initialized) {
      if (keycloak?.authenticated) {
        // Извлекаем информацию о пользователе из токена Keycloak
        const userInfo = keycloakUtils.getUserInfo();
        if (userInfo) {
          const userData: User = {
            id: userInfo.id,
            username: userInfo.username,
            email: userInfo.email,
            firstName: userInfo.firstName,
            lastName: userInfo.lastName,
            roles: userInfo.roles,
            permissions: userInfo.clientRoles,
          };
          setUser(userData);
          console.log('Пользователь аутентифицирован через Keycloak:', userData);
        }
      } else if (!keycloak) {
        // Режим без Keycloak - создаем тестового пользователя
        const mockUser: User = {
          id: 'mock-user-1',
          username: 'testuser',
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          roles: ['user', 'admin'],
          permissions: ['read', 'write', 'admin'],
        };
        setUser(mockUser);
        console.log('Режим без Keycloak - используется тестовый пользователь:', mockUser);
      } else {
        // Keycloak включен, но пользователь не аутентифицирован
        setUser(null);
        console.log('Пользователь не аутентифицирован, требуется авторизация через Keycloak');
      }
      setIsLoading(false);
    }
  }, [keycloak, initialized]);

  const login = () => {
    if (keycloak?.authenticated) {
      console.log('Пользователь уже аутентифицирован');
      return;
    }
    
    if (keycloak) {
      keycloakUtils.login();
    } else {
      // В режиме без Keycloak просто устанавливаем тестового пользователя
      const mockUser: User = {
        id: 'mock-user-1',
        username: 'testuser',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        roles: ['user', 'admin'],
        permissions: ['read', 'write', 'admin'],
      };
      setUser(mockUser);
      console.log('Вход в систему (режим без Keycloak):', mockUser);
    }
  };

  const logout = () => {
    if (keycloak?.authenticated) {
      keycloakUtils.logout();
    } else {
      // В режиме без Keycloak просто очищаем пользователя
      setUser(null);
      console.log('Выход из системы (режим без Keycloak)');
    }
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    
    if (keycloak?.authenticated) {
      return keycloakUtils.hasRole(role);
    } else {
      // В режиме без Keycloak проверяем роли из mock пользователя
      return user.roles.includes(role);
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    if (keycloak?.authenticated) {
      return keycloakUtils.hasPermission(permission);
    } else {
      // В режиме без Keycloak проверяем права из mock пользователя
      return user.permissions.includes(permission);
    }
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user) return false;
    
    if (keycloak?.authenticated) {
      return keycloakUtils.hasAnyRole(roles);
    } else {
      // В режиме без Keycloak проверяем роли из mock пользователя
      return roles.some(role => user.roles.includes(role));
    }
  };

  const hasAllRoles = (roles: string[]): boolean => {
    if (!user) return false;
    
    if (keycloak?.authenticated) {
      return keycloakUtils.hasAllRoles(roles);
    } else {
      // В режиме без Keycloak проверяем роли из mock пользователя
      return roles.every(role => user.roles.includes(role));
    }
  };

  const updateToken = async (): Promise<boolean> => {
    if (keycloak?.authenticated) {
      try {
        return await keycloakUtils.updateToken();
      } catch (error) {
        console.error('Ошибка обновления токена:', error);
        return false;
      }
    } else {
      // В режиме без Keycloak токен не нужно обновлять
      return true;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: keycloak ? (keycloak?.authenticated || false) : !!user,
    isLoading,
    login,
    logout,
    hasRole,
    hasPermission,
    hasAnyRole,
    hasAllRoles,
    updateToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Основной экспорт - выбирает нужный провайдер
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const enableKeycloak = environment.features.enableKeycloak;
  
  if (enableKeycloak) {
    return <KeycloakAuthProvider>{children}</KeycloakAuthProvider>;
  } else {
    return <NoAuthProvider>{children}</NoAuthProvider>;
  }
};
