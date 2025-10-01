import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Box, CircularProgress, Typography } from '@mui/material';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  requireAllRoles?: boolean;
  fallbackPath?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  requiredPermissions = [],
  requireAllRoles = false,
  fallbackPath = '/login',
}) => {
  const { user, isAuthenticated, isLoading, hasRole, hasPermission, hasAllRoles, hasAnyRole } = useAuth();
  const location = useLocation();

  // Показываем загрузку пока проверяем авторизацию
  if (isLoading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="50vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Проверка авторизации...
        </Typography>
      </Box>
    );
  }

  // Если пользователь не аутентифицирован, перенаправляем на страницу входа
  if (!isAuthenticated || !user) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Проверяем роли
  if (requiredRoles.length > 0) {
    const hasRequiredRoles = requireAllRoles 
      ? hasAllRoles(requiredRoles)
      : hasAnyRole(requiredRoles);

    if (!hasRequiredRoles) {
      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="50vh"
          gap={2}
        >
          <Typography variant="h6" color="error">
            Недостаточно прав доступа
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Для доступа к этой странице требуются роли: {requiredRoles.join(', ')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Ваши роли: {user.roles.join(', ')}
          </Typography>
        </Box>
      );
    }
  }

  // Проверяем права доступа
  if (requiredPermissions.length > 0) {
    const hasRequiredPermissions = requiredPermissions.every(permission => 
      hasPermission(permission)
    );

    if (!hasRequiredPermissions) {
      return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="50vh"
          gap={2}
        >
          <Typography variant="h6" color="error">
            Недостаточно прав доступа
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Для доступа к этой странице требуются права: {requiredPermissions.join(', ')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Ваши права: {user.permissions.join(', ')}
          </Typography>
        </Box>
      );
    }
  }

  // Если все проверки пройдены, показываем содержимое
  return <>{children}</>;
};

// Компонент для проверки роли
export const RoleGuard: React.FC<{
  children: React.ReactNode;
  roles: string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
}> = ({ children, roles, requireAll = false, fallback = null }) => {
  const { hasRole, hasAllRoles, hasAnyRole } = useAuth();

  const hasRequiredRoles = requireAll 
    ? hasAllRoles(roles)
    : hasAnyRole(roles);

  return hasRequiredRoles ? <>{children}</> : <>{fallback}</>;
};

// Компонент для проверки прав доступа
export const PermissionGuard: React.FC<{
  children: React.ReactNode;
  permissions: string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
}> = ({ children, permissions, requireAll = false, fallback = null }) => {
  const { hasPermission } = useAuth();

  const hasRequiredPermissions = requireAll
    ? permissions.every(permission => hasPermission(permission))
    : permissions.some(permission => hasPermission(permission));

  return hasRequiredPermissions ? <>{children}</> : <>{fallback}</>;
};

// Хук для проверки доступа
export const useAccess = () => {
  const { user, hasRole, hasPermission, hasAnyRole, hasAllRoles } = useAuth();

  return {
    // Проверка роли
    hasRole: (role: string) => hasRole(role),
    
    // Проверка любой из ролей
    hasAnyRole: (roles: string[]) => hasAnyRole(roles),
    
    // Проверка всех ролей
    hasAllRoles: (roles: string[]) => hasAllRoles(roles),
    
    // Проверка права доступа
    hasPermission: (permission: string) => hasPermission(permission),
    
    // Проверка любого из прав
    hasAnyPermission: (permissions: string[]) => 
      permissions.some(permission => hasPermission(permission)),
    
    // Проверка всех прав
    hasAllPermissions: (permissions: string[]) => 
      permissions.every(permission => hasPermission(permission)),
    
    // Информация о пользователе
    user,
    isAdmin: hasRole('admin'),
    isDeveloper: hasRole('developer'),
    isAnalyst: hasRole('analyst'),
    isViewer: hasRole('viewer'),
  };
};
