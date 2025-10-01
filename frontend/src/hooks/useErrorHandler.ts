import { useState, useCallback, useRef } from 'react';
import { errorHandler, ErrorInfo } from '../utils/errorHandler.ts';

interface UseErrorHandlerOptions {
  autoRetry?: boolean;
  showDetails?: boolean;
  onError?: (error: ErrorInfo) => void;
  onRetry?: () => void;
}

export const useErrorHandler = (options: UseErrorHandlerOptions = {}) => {
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    autoRetry = false,
    showDetails = false,
    onError,
    onRetry
  } = options;

  /**
   * Обрабатывает ошибку и устанавливает состояние
   */
  const handleError = useCallback((error: any, context?: string) => {
    const errorInfo = errorHandler.handleError(error, context);
    setError(errorInfo);
    
    if (onError) {
      onError(errorInfo);
    }

    // Автоматический повтор при необходимости
    if (autoRetry && errorInfo.canRetry && errorInfo.retryDelay) {
      scheduleRetry(errorInfo.retryDelay);
    }

    return errorInfo;
  }, [autoRetry, onError]);

  /**
   * Планирует автоматический повтор
   */
  const scheduleRetry = useCallback((delay: number) => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }

    retryTimeoutRef.current = setTimeout(() => {
      if (onRetry) {
        onRetry();
      }
    }, delay);
  }, [onRetry]);

  /**
   * Выполняет операцию с обработкой ошибок и повторными попытками
   */
  const executeWithRetry = useCallback(async <T>(
    operation: () => Promise<T>,
    context?: string
  ): Promise<T | null> => {
    try {
      setIsRetrying(false);
      return await errorHandler.retry(operation, error || {
        type: 'unknown',
        message: 'Unknown error',
        userMessage: 'Неизвестная ошибка',
        suggestion: 'Попробуйте снова',
        canRetry: true
      });
    } catch (error) {
      return handleError(error, context);
    }
  }, [error, handleError]);

  /**
   * Очищает ошибку
   */
  const clearError = useCallback(() => {
    setError(null);
    setIsRetrying(false);
    
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  /**
   * Выполняет повторную попытку
   */
  const retry = useCallback(async (operation?: () => Promise<any>) => {
    if (!error?.canRetry) return;

    setIsRetrying(true);
    clearError();

    if (operation) {
      try {
        await operation();
      } catch (error) {
        handleError(error, 'retry');
      }
    } else if (onRetry) {
      onRetry();
    }
  }, [error, clearError, handleError, onRetry]);

  /**
   * Проверяет, является ли ошибка определенного типа
   */
  const isErrorType = useCallback((type: string) => {
    return error?.type === type;
  }, [error]);

  /**
   * Получает сообщение об ошибке для пользователя
   */
  const getUserMessage = useCallback(() => {
    return error?.userMessage || 'Произошла ошибка';
  }, [error]);

  /**
   * Получает предложение по решению ошибки
   */
  const getSuggestion = useCallback(() => {
    return error?.suggestion || 'Попробуйте снова';
  }, [error]);

  /**
   * Проверяет, можно ли повторить операцию
   */
  const canRetry = useCallback(() => {
    return error?.canRetry || false;
  }, [error]);

  return {
    error,
    isRetrying,
    handleError,
    executeWithRetry,
    clearError,
    retry,
    isErrorType,
    getUserMessage,
    getSuggestion,
    canRetry,
    showDetails
  };
};
