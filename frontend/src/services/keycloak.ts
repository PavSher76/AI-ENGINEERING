import Keycloak from 'keycloak-js';
import environment from '../config/environment.ts';
import { logger } from '../utils/logger.ts';

// Конфигурация Keycloak
const keycloakConfig = {
  url: environment.keycloak.url,
  realm: environment.keycloak.realm,
  clientId: environment.keycloak.clientId,
};

// Создание экземпляра Keycloak
const keycloak = new Keycloak(keycloakConfig);

// Настройки инициализации
const initOptions = {
  onLoad: 'login-required',
  silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
  checkLoginIframe: false,
  enableLogging: true,
  pkceMethod: 'S256',
};

// Функция инициализации Keycloak
export const initKeycloak = (): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    logger.authInfo('Начало инициализации Keycloak', {
      config: keycloakConfig,
      initOptions,
      sessionId: logger.getSessionId()
    });

    keycloak
      .init(initOptions)
      .then((authenticated) => {
        logger.authInfo('Keycloak инициализирован успешно', {
          authenticated,
          token: authenticated ? keycloak.token : null,
          refreshToken: authenticated ? keycloak.refreshToken : null,
          sessionId: logger.getSessionId()
        });
        
        if (authenticated) {
          const userInfo = keycloakUtils.getUserInfo();
          logger.authInfo('Информация о пользователе получена', {
            userInfo,
            roles: keycloakUtils.getUserInfo()?.roles || [],
            sessionId: logger.getSessionId()
          });
        }
        
        resolve(authenticated);
      })
      .catch((error) => {
        logger.authError('Ошибка инициализации Keycloak', {
          error: error.message || error,
          stack: error.stack,
          sessionId: logger.getSessionId()
        });
        reject(error);
      });
  });
};

// Обработчики событий Keycloak
export const keycloakEventHandler = (eventType: string, error?: any) => {
  const sessionId = logger.getSessionId();
  const userInfo = keycloakUtils.getUserInfo();
  
  logger.authDebug('Keycloak событие получено', {
    eventType,
    error: error?.message || error,
    authenticated: keycloak.authenticated,
    userId: userInfo?.id,
    sessionId
  });
  
  switch (eventType) {
    case 'onReady':
      logger.authInfo('Keycloak готов к работе', {
        authenticated: keycloak.authenticated,
        sessionId
      });
      break;
    case 'onInitError':
      logger.authError('Ошибка инициализации Keycloak', {
        error: error?.message || error,
        stack: error?.stack,
        sessionId
      });
      break;
    case 'onAuthSuccess':
      logger.authInfo('Успешная авторизация пользователя', {
        userInfo,
        roles: userInfo?.roles || [],
        sessionId
      });
      break;
    case 'onAuthError':
      logger.authError('Ошибка авторизации', {
        error: error?.message || error,
        errorType: error?.error,
        errorDescription: error?.error_description,
        sessionId
      });
      break;
    case 'onAuthRefreshSuccess':
      logger.authInfo('Токен обновлен успешно', {
        userId: userInfo?.id,
        sessionId
      });
      break;
    case 'onAuthRefreshError':
      logger.authError('Ошибка обновления токена', {
        error: error?.message || error,
        userId: userInfo?.id,
        sessionId
      });
      break;
    case 'onAuthLogout':
      logger.authInfo('Пользователь вышел из системы', {
        userId: userInfo?.id,
        sessionId
      });
      break;
    case 'onTokenExpired':
      logger.authWarn('Токен истек, начинаем обновление', {
        userId: userInfo?.id,
        sessionId
      });
      keycloak.updateToken(30).then(() => {
        logger.authInfo('Токен обновлен после истечения', {
          userId: userInfo?.id,
          sessionId
        });
      }).catch((error) => {
        logger.authError('Ошибка обновления токена после истечения', {
          error: error?.message || error,
          userId: userInfo?.id,
          sessionId
        });
        keycloak.logout();
      });
      break;
    default:
      logger.authDebug('Неизвестное событие Keycloak', {
        eventType,
        error: error?.message || error,
        sessionId
      });
  }
};

// Экспорт экземпляра Keycloak
export default keycloak;

// Утилиты для работы с Keycloak
export const keycloakUtils = {
  // Получение токена
  getToken: (): string | undefined => {
    return keycloak.token;
  },

  // Получение информации о пользователе
  getUserInfo: () => {
    if (!keycloak.authenticated || !keycloak.tokenParsed) {
      return null;
    }

    const tokenParsed = keycloak.tokenParsed;
    return {
      id: tokenParsed.sub || '',
      username: tokenParsed.preferred_username || '',
      email: tokenParsed.email || '',
      firstName: tokenParsed.given_name || '',
      lastName: tokenParsed.family_name || '',
      roles: tokenParsed.realm_access?.roles || [],
      clientRoles: tokenParsed.resource_access?.['ai-frontend']?.roles || [],
      emailVerified: tokenParsed.email_verified || false,
    };
  },

  // Проверка роли
  hasRole: (role: string): boolean => {
    if (!keycloak.authenticated) return false;
    return keycloak.hasRealmRole(role) || keycloak.hasResourceRole(role, 'ai-frontend');
  },

  // Проверка любой из ролей
  hasAnyRole: (roles: string[]): boolean => {
    if (!keycloak.authenticated) return false;
    return roles.some(role => 
      keycloak.hasRealmRole(role) || keycloak.hasResourceRole(role, 'ai-frontend')
    );
  },

  // Проверка всех ролей
  hasAllRoles: (roles: string[]): boolean => {
    if (!keycloak.authenticated) return false;
    return roles.every(role => 
      keycloak.hasRealmRole(role) || keycloak.hasResourceRole(role, 'ai-frontend')
    );
  },

  // Вход в систему
  login: (options?: any) => {
    logger.authInfo('Попытка входа в систему', {
      options,
      sessionId: logger.getSessionId()
    });
    keycloak.login(options);
  },

  // Выход из системы
  logout: (options?: any) => {
    const userInfo = keycloakUtils.getUserInfo();
    logger.authInfo('Попытка выхода из системы', {
      userId: userInfo?.id,
      options,
      sessionId: logger.getSessionId()
    });
    keycloak.logout(options);
  },

  // Обновление токена
  updateToken: (minValidity: number = 30): Promise<boolean> => {
    return keycloak.updateToken(minValidity);
  },

  // Проверка аутентификации
  isAuthenticated: (): boolean => {
    return keycloak.authenticated || false;
  },

  // Получение URL для входа
  createLoginUrl: (options?: any): string => {
    return keycloak.createLoginUrl(options);
  },

  // Получение URL для выхода
  createLogoutUrl: (options?: any): string => {
    return keycloak.createLogoutUrl(options);
  },

  // Получение URL для регистрации
  createRegisterUrl: (options?: any): string => {
    return keycloak.createRegisterUrl(options);
  },

  // Получение URL для смены пароля
  createAccountUrl: (options?: any): string => {
    return keycloak.createAccountUrl(options);
  },
};