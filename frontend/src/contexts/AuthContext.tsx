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

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Проверяем, включен ли Keycloak
  const enableKeycloak = environment.features.enableKeycloak;
  
  // Всегда вызываем useKeycloak, но используем результат только если Keycloak включен
  const keycloakHook = useKeycloak();
  const { keycloak, initialized } = enableKeycloak ? keycloakHook : { keycloak: null, initialized: true };
  
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (initialized) {
      if (enableKeycloak && keycloak?.authenticated) {
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
      } else if (!enableKeycloak) {
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
  }, [keycloak, initialized, enableKeycloak]);

  const login = () => {
    if (enableKeycloak && keycloak?.authenticated) {
      console.log('Пользователь уже аутентифицирован');
      return;
    }
    
    if (enableKeycloak) {
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
    if (enableKeycloak && keycloak?.authenticated) {
      keycloakUtils.logout();
    } else {
      // В режиме без Keycloak просто очищаем пользователя
      setUser(null);
      console.log('Выход из системы (режим без Keycloak)');
    }
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    
    if (enableKeycloak && keycloak?.authenticated) {
      return keycloakUtils.hasRole(role);
    } else {
      // В режиме без Keycloak проверяем роли из mock пользователя
      return user.roles.includes(role);
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    if (enableKeycloak && keycloak?.authenticated) {
      return user.permissions.includes(permission);
    } else {
      // В режиме без Keycloak проверяем права из mock пользователя
      return user.permissions.includes(permission);
    }
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user) return false;
    
    if (enableKeycloak && keycloak?.authenticated) {
      return keycloakUtils.hasAnyRole(roles);
    } else {
      // В режиме без Keycloak проверяем роли из mock пользователя
      return roles.some(role => user.roles.includes(role));
    }
  };

  const hasAllRoles = (roles: string[]): boolean => {
    if (!user) return false;
    
    if (enableKeycloak && keycloak?.authenticated) {
      return keycloakUtils.hasAllRoles(roles);
    } else {
      // В режиме без Keycloak проверяем роли из mock пользователя
      return roles.every(role => user.roles.includes(role));
    }
  };

  const updateToken = async (): Promise<boolean> => {
    if (enableKeycloak && keycloak?.authenticated) {
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
    isAuthenticated: enableKeycloak ? (keycloak?.authenticated || false) : !!user,
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
