import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { User } from '../types';
import { keycloakUtils } from '../services/keycloak';

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
  const { keycloak, initialized } = useKeycloak();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (initialized) {
      if (keycloak.authenticated) {
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
          console.log('Пользователь аутентифицирован:', userData);
        }
      } else {
        // В режиме разработки не создаем мок-пользователя
        // Пользователь должен пройти авторизацию через Keycloak
        setUser(null);
        console.log('Пользователь не аутентифицирован, требуется авторизация через Keycloak');
      }
      setIsLoading(false);
    }
  }, [keycloak, initialized]);

  const login = () => {
    if (keycloak.authenticated) {
      console.log('Пользователь уже аутентифицирован');
      return;
    }
    keycloakUtils.login();
  };

  const logout = () => {
    if (keycloak.authenticated) {
      keycloakUtils.logout();
    } else {
      // В режиме разработки просто очищаем пользователя
      setUser(null);
      console.log('Выход из системы (режим разработки)');
    }
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    
    // Проверяем роль только если пользователь аутентифицирован через Keycloak
    if (!keycloak.authenticated) {
      return false;
    }
    
    return keycloakUtils.hasRole(role);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    
    // Проверяем права только если пользователь аутентифицирован через Keycloak
    if (!keycloak.authenticated) {
      return false;
    }
    
    return user.permissions.includes(permission);
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!user) return false;
    
    // Проверяем роли только если пользователь аутентифицирован через Keycloak
    if (!keycloak.authenticated) {
      return false;
    }
    
    return keycloakUtils.hasAnyRole(roles);
  };

  const hasAllRoles = (roles: string[]): boolean => {
    if (!user) return false;
    
    // Проверяем роли только если пользователь аутентифицирован через Keycloak
    if (!keycloak.authenticated) {
      return false;
    }
    
    return keycloakUtils.hasAllRoles(roles);
  };

  const updateToken = async (): Promise<boolean> => {
    if (!keycloak.authenticated) {
      return false;
    }
    
    try {
      return await keycloakUtils.updateToken();
    } catch (error) {
      console.error('Ошибка обновления токена:', error);
      return false;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: keycloak.authenticated || false,
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
