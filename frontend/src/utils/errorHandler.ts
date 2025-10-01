/**
 * Умный обработчик ошибок для чата с ИИ
 */

export interface ErrorInfo {
  type: 'network' | 'server' | 'validation' | 'file' | 'auth' | 'timeout' | 'unknown';
  code?: string | number;
  message: string;
  userMessage: string;
  suggestion: string;
  canRetry: boolean;
  retryDelay?: number;
  details?: any;
}

export interface RetryOptions {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

export class SmartErrorHandler {
  private static instance: SmartErrorHandler;
  private retryOptions: RetryOptions = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2
  };

  public static getInstance(): SmartErrorHandler {
    if (!SmartErrorHandler.instance) {
      SmartErrorHandler.instance = new SmartErrorHandler();
    }
    return SmartErrorHandler.instance;
  }

  /**
   * Обрабатывает ошибку и возвращает информацию для пользователя
   */
  public handleError(error: any, context?: string): ErrorInfo {
    console.error('SmartErrorHandler:', error, context);

    // Сетевые ошибки
    if (this.isNetworkError(error)) {
      return this.handleNetworkError(error);
    }

    // Ошибки сервера
    if (this.isServerError(error)) {
      return this.handleServerError(error);
    }

    // Ошибки валидации
    if (this.isValidationError(error)) {
      return this.handleValidationError(error);
    }

    // Ошибки файлов
    if (this.isFileError(error)) {
      return this.handleFileError(error);
    }

    // Ошибки авторизации
    if (this.isAuthError(error)) {
      return this.handleAuthError(error);
    }

    // Таймауты
    if (this.isTimeoutError(error)) {
      return this.handleTimeoutError(error);
    }

    // Неизвестные ошибки
    return this.handleUnknownError(error);
  }

  /**
   * Выполняет повторную попытку с экспоненциальной задержкой
   */
  public async retry<T>(
    operation: () => Promise<T>,
    errorInfo: ErrorInfo,
    attempt: number = 1
  ): Promise<T> {
    if (attempt > this.retryOptions.maxRetries) {
      throw new Error(`Превышено максимальное количество попыток (${this.retryOptions.maxRetries})`);
    }

    try {
      return await operation();
    } catch (error) {
      if (attempt < this.retryOptions.maxRetries && errorInfo.canRetry) {
        const delay = Math.min(
          this.retryOptions.baseDelay * Math.pow(this.retryOptions.backoffMultiplier, attempt - 1),
          this.retryOptions.maxDelay
        );

        console.log(`Повторная попытка ${attempt + 1}/${this.retryOptions.maxRetries} через ${delay}ms`);
        
        await this.sleep(delay);
        return this.retry(operation, errorInfo, attempt + 1);
      }
      throw error;
    }
  }

  /**
   * Проверяет, является ли ошибка сетевой
   */
  private isNetworkError(error: any): boolean {
    return (
      error.code === 'NETWORK_ERROR' ||
      error.message?.includes('Network Error') ||
      error.message?.includes('ERR_NETWORK') ||
      error.message?.includes('ERR_INTERNET_DISCONNECTED') ||
      error.message?.includes('ERR_CONNECTION_REFUSED') ||
      error.message?.includes('ERR_CONNECTION_TIMED_OUT') ||
      !navigator.onLine
    );
  }

  /**
   * Проверяет, является ли ошибка серверной
   */
  private isServerError(error: any): boolean {
    return (
      error.response?.status >= 500 ||
      error.response?.status === 404 ||
      error.response?.status === 503 ||
      error.response?.status === 502 ||
      error.response?.status === 504
    );
  }

  /**
   * Проверяет, является ли ошибка ошибкой валидации
   */
  private isValidationError(error: any): boolean {
    return (
      error.response?.status === 400 ||
      error.response?.status === 422 ||
      error.message?.includes('validation') ||
      error.message?.includes('invalid')
    );
  }

  /**
   * Проверяет, является ли ошибка ошибкой файла
   */
  private isFileError(error: any): boolean {
    return (
      error.response?.status === 413 ||
      error.message?.includes('file') ||
      error.message?.includes('upload') ||
      error.message?.includes('size')
    );
  }

  /**
   * Проверяет, является ли ошибка ошибкой авторизации
   */
  private isAuthError(error: any): boolean {
    return (
      error.response?.status === 401 ||
      error.response?.status === 403 ||
      error.message?.includes('unauthorized') ||
      error.message?.includes('forbidden')
    );
  }

  /**
   * Проверяет, является ли ошибка таймаутом
   */
  private isTimeoutError(error: any): boolean {
    return (
      error.code === 'ECONNABORTED' ||
      error.message?.includes('timeout') ||
      error.message?.includes('TIMEOUT')
    );
  }

  /**
   * Обрабатывает сетевые ошибки
   */
  private handleNetworkError(error: any): ErrorInfo {
    if (!navigator.onLine) {
      return {
        type: 'network',
        code: 'OFFLINE',
        message: 'Нет подключения к интернету',
        userMessage: 'Отсутствует подключение к интернету',
        suggestion: 'Проверьте подключение к интернету и попробуйте снова',
        canRetry: true,
        retryDelay: 5000
      };
    }

    return {
      type: 'network',
      code: 'NETWORK_ERROR',
      message: error.message || 'Ошибка сети',
      userMessage: 'Проблема с подключением к серверу',
      suggestion: 'Проверьте подключение к интернету и попробуйте снова',
      canRetry: true,
      retryDelay: 2000
    };
  }

  /**
   * Обрабатывает ошибки сервера
   */
  private handleServerError(error: any): ErrorInfo {
    const status = error.response?.status;
    const statusText = error.response?.statusText;

    switch (status) {
      case 500:
        return {
          type: 'server',
          code: 500,
          message: 'Internal Server Error',
          userMessage: 'Внутренняя ошибка сервера',
          suggestion: 'Попробуйте позже или обратитесь в поддержку',
          canRetry: true,
          retryDelay: 5000
        };
      case 502:
        return {
          type: 'server',
          code: 502,
          message: 'Bad Gateway',
          userMessage: 'Сервер временно недоступен',
          suggestion: 'Попробуйте через несколько минут',
          canRetry: true,
          retryDelay: 10000
        };
      case 503:
        return {
          type: 'server',
          code: 503,
          message: 'Service Unavailable',
          userMessage: 'Сервис временно недоступен',
          suggestion: 'Попробуйте позже',
          canRetry: true,
          retryDelay: 15000
        };
      case 504:
        return {
          type: 'server',
          code: 504,
          message: 'Gateway Timeout',
          userMessage: 'Превышено время ожидания ответа сервера',
          suggestion: 'Попробуйте снова или обратитесь в поддержку',
          canRetry: true,
          retryDelay: 5000
        };
      case 404:
        return {
          type: 'server',
          code: 404,
          message: 'Not Found',
          userMessage: 'Запрашиваемый ресурс не найден',
          suggestion: 'Проверьте правильность запроса',
          canRetry: false
        };
      default:
        return {
          type: 'server',
          code: status,
          message: statusText || 'Server Error',
          userMessage: 'Ошибка сервера',
          suggestion: 'Попробуйте позже или обратитесь в поддержку',
          canRetry: true,
          retryDelay: 5000
        };
    }
  }

  /**
   * Обрабатывает ошибки валидации
   */
  private handleValidationError(error: any): ErrorInfo {
    const details = error.response?.data?.detail;
    
    if (Array.isArray(details)) {
      const messages = details.map((d: any) => d.msg || d.message).join(', ');
      return {
        type: 'validation',
        code: 400,
        message: messages,
        userMessage: 'Ошибка в данных запроса',
        suggestion: 'Проверьте правильность введенных данных',
        canRetry: false,
        details
      };
    }

    return {
      type: 'validation',
      code: 400,
      message: details || error.message,
      userMessage: 'Некорректные данные',
      suggestion: 'Проверьте правильность введенных данных',
      canRetry: false
    };
  }

  /**
   * Обрабатывает ошибки файлов
   */
  private handleFileError(error: any): ErrorInfo {
    if (error.response?.status === 413) {
      return {
        type: 'file',
        code: 413,
        message: 'File too large',
        userMessage: 'Файл слишком большой',
        suggestion: 'Выберите файл размером менее 100 МБ',
        canRetry: false
      };
    }

    return {
      type: 'file',
      code: 'FILE_ERROR',
      message: error.message || 'File processing error',
      userMessage: 'Ошибка обработки файла',
      suggestion: 'Проверьте формат и размер файла',
      canRetry: true,
      retryDelay: 2000
    };
  }

  /**
   * Обрабатывает ошибки авторизации
   */
  private handleAuthError(error: any): ErrorInfo {
    return {
      type: 'auth',
      code: error.response?.status || 401,
      message: error.message || 'Authentication error',
      userMessage: 'Ошибка авторизации',
      suggestion: 'Войдите в систему заново',
      canRetry: false
    };
  }

  /**
   * Обрабатывает ошибки таймаута
   */
  private handleTimeoutError(error: any): ErrorInfo {
    return {
      type: 'timeout',
      code: 'TIMEOUT',
      message: error.message || 'Request timeout',
      userMessage: 'Превышено время ожидания',
      suggestion: 'Попробуйте снова или уменьшите размер файла',
      canRetry: true,
      retryDelay: 3000
    };
  }

  /**
   * Обрабатывает неизвестные ошибки
   */
  private handleUnknownError(error: any): ErrorInfo {
    return {
      type: 'unknown',
      code: 'UNKNOWN',
      message: error.message || 'Unknown error',
      userMessage: 'Произошла неизвестная ошибка',
      suggestion: 'Попробуйте обновить страницу или обратитесь в поддержку',
      canRetry: true,
      retryDelay: 5000
    };
  }

  /**
   * Задержка выполнения
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Обновляет настройки повторных попыток
   */
  public updateRetryOptions(options: Partial<RetryOptions>): void {
    this.retryOptions = { ...this.retryOptions, ...options };
  }
}

// Экспорт экземпляра
export const errorHandler = SmartErrorHandler.getInstance();
