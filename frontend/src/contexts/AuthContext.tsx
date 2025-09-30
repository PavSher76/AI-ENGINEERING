import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
// import { useKeycloak } from '@react-keycloak/web';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // const { keycloak, initialized } = useKeycloak();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Для разработки создаем фиктивного пользователя
    const mockUser: User = {
      id: 'dev-user-1',
      username: 'developer',
      email: 'developer@ai-engineering.local',
      firstName: 'Разработчик',
      lastName: 'Системы',
      roles: ['admin', 'user'],
      permissions: ['read', 'write', 'admin'],
    };
    setUser(mockUser);
    setIsLoading(false);
  }, []);

  const login = () => {
    console.log('Login function called (disabled for development)');
  };

  const logout = () => {
    console.log('Logout function called (disabled for development)');
    setUser(null);
  };

  const hasRole = (role: string): boolean => {
    if (!user) return true; // Для разработки разрешаем все роли
    return user.roles.includes(role);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return true; // Для разработки разрешаем все права
    return user.permissions.includes(permission);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: true, // Всегда аутентифицирован для разработки
    isLoading,
    login,
    logout,
    hasRole,
    hasPermission,
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
