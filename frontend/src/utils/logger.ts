// Утилита для логирования в фронтенде
export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
  userId?: string;
  sessionId?: string;
}

class Logger {
  private isDevelopment: boolean;
  private sessionId: string;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }

  private createLogEntry(level: LogLevel, category: string, message: string, data?: any, userId?: string): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      data,
      userId,
      sessionId: this.sessionId,
    };
  }

  private log(level: LogLevel, category: string, message: string, data?: any, userId?: string): void {
    const logEntry = this.createLogEntry(level, category, message, data, userId);
    
    // Логирование в консоль
    const consoleMessage = `[${logEntry.timestamp}] [${level}] [${category}] ${message}`;
    
    switch (level) {
      case LogLevel.DEBUG:
        if (this.isDevelopment) {
          console.debug(consoleMessage, data || '');
        }
        break;
      case LogLevel.INFO:
        console.info(consoleMessage, data || '');
        break;
      case LogLevel.WARN:
        console.warn(consoleMessage, data || '');
        break;
      case LogLevel.ERROR:
        console.error(consoleMessage, data || '');
        break;
    }

    // Отправка логов на сервер (если нужно)
    this.sendLogToServer(logEntry);
  }

  private async sendLogToServer(logEntry: LogEntry): Promise<void> {
    // Отправляем только важные логи на сервер
    if (logEntry.level === LogLevel.ERROR || logEntry.level === LogLevel.WARN) {
      try {
        // Здесь можно добавить отправку логов на сервер
        // await fetch('/api/logs', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(logEntry)
        // });
      } catch (error) {
        console.error('Ошибка отправки лога на сервер:', error);
      }
    }
  }

  // Методы для разных уровней логирования
  debug(category: string, message: string, data?: any, userId?: string): void {
    this.log(LogLevel.DEBUG, category, message, data, userId);
  }

  info(category: string, message: string, data?: any, userId?: string): void {
    this.log(LogLevel.INFO, category, message, data, userId);
  }

  warn(category: string, message: string, data?: any, userId?: string): void {
    this.log(LogLevel.WARN, category, message, data, userId);
  }

  error(category: string, message: string, data?: any, userId?: string): void {
    this.log(LogLevel.ERROR, category, message, data, userId);
  }

  // Специальные методы для авторизации
  authInfo(message: string, data?: any, userId?: string): void {
    this.info('AUTH', message, data, userId);
  }

  authError(message: string, data?: any, userId?: string): void {
    this.error('AUTH', message, data, userId);
  }

  authDebug(message: string, data?: any, userId?: string): void {
    this.debug('AUTH', message, data, userId);
  }

  // Специальные методы для навигации
  navigationInfo(message: string, data?: any, userId?: string): void {
    this.info('NAVIGATION', message, data, userId);
  }

  navigationError(message: string, data?: any, userId?: string): void {
    this.error('NAVIGATION', message, data, userId);
  }

  // Специальные методы для API
  apiInfo(message: string, data?: any, userId?: string): void {
    this.info('API', message, data, userId);
  }

  apiError(message: string, data?: any, userId?: string): void {
    this.error('API', message, data, userId);
  }

  // Специальные методы для производительности
  performanceInfo(message: string, data?: any, userId?: string): void {
    this.info('PERFORMANCE', message, data, userId);
  }

  // Получение session ID
  getSessionId(): string {
    return this.sessionId;
  }
}

// Экспорт экземпляра логгера
export const logger = new Logger();

// Экспорт типов
export type { LogEntry };
