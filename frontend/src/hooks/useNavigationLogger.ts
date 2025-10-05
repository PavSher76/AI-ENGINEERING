import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { logger } from '../utils/logger.ts';
import { useAuth } from '../contexts/AuthContext.tsx';

// Хук для логирования навигации
export const useNavigationLogger = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  // Логирование изменений маршрута
  useEffect(() => {
    const startTime = performance.now();
    
    logger.navigationInfo('Переход на страницу', {
      pathname: location.pathname,
      search: location.search,
      hash: location.hash,
      state: location.state,
      userId: user?.id,
      isAuthenticated,
      sessionId: logger.getSessionId()
    });

    // Логирование времени загрузки страницы
    const handleLoad = () => {
      const loadTime = performance.now() - startTime;
      logger.performanceInfo('Страница загружена', {
        pathname: location.pathname,
        loadTime: Math.round(loadTime),
        userId: user?.id,
        sessionId: logger.getSessionId()
      });
    };

    // Добавляем обработчик загрузки
    window.addEventListener('load', handleLoad);
    
    // Очищаем обработчик при размонтировании
    return () => {
      window.removeEventListener('load', handleLoad);
    };
  }, [location, user, isAuthenticated]);

  // Функция для программной навигации с логированием
  const navigateWithLogging = (to: string, options?: any) => {
    logger.navigationInfo('Программный переход', {
      from: location.pathname,
      to,
      options,
      userId: user?.id,
      isAuthenticated,
      sessionId: logger.getSessionId()
    });
    
    navigate(to, options);
  };

  // Функция для логирования попыток доступа к защищенным страницам
  const logProtectedAccess = (requiredRoles: string[], hasAccess: boolean) => {
    logger.navigationInfo('Попытка доступа к защищенной странице', {
      pathname: location.pathname,
      requiredRoles,
      userRoles: user?.roles || [],
      hasAccess,
      userId: user?.id,
      isAuthenticated,
      sessionId: logger.getSessionId()
    });
  };

  // Функция для логирования ошибок навигации
  const logNavigationError = (error: Error, context?: any) => {
    logger.navigationError('Ошибка навигации', {
      error: error.message,
      stack: error.stack,
      pathname: location.pathname,
      context,
      userId: user?.id,
      isAuthenticated,
      sessionId: logger.getSessionId()
    });
  };

  return {
    navigateWithLogging,
    logProtectedAccess,
    logNavigationError,
  };
};

export default useNavigationLogger;
