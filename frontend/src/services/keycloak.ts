import Keycloak from 'keycloak-js';
import environment from '../config/environment.ts';

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
  onLoad: 'check-sso',
  silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
  pkceMethod: 'S256',
  checkLoginIframe: false,
  enableLogging: true,
};

// Функция инициализации Keycloak
export const initKeycloak = (): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    keycloak
      .init(initOptions)
      .then((authenticated) => {
        console.log('Keycloak инициализирован:', authenticated);
        resolve(authenticated);
      })
      .catch((error) => {
        console.error('Ошибка инициализации Keycloak:', error);
        reject(error);
      });
  });
};

// Обработчики событий Keycloak
export const keycloakEventHandler = (eventType: string, error?: any) => {
  console.log('Keycloak событие:', eventType, error);
  
  switch (eventType) {
    case 'onReady':
      console.log('Keycloak готов');
      break;
    case 'onInitError':
      console.error('Ошибка инициализации Keycloak:', error);
      break;
    case 'onAuthSuccess':
      console.log('Успешная авторизация');
      break;
    case 'onAuthError':
      console.error('Ошибка авторизации:', error);
      break;
    case 'onAuthRefreshSuccess':
      console.log('Токен обновлен успешно');
      break;
    case 'onAuthRefreshError':
      console.error('Ошибка обновления токена:', error);
      break;
    case 'onAuthLogout':
      console.log('Пользователь вышел из системы');
      break;
    case 'onTokenExpired':
      console.log('Токен истек, обновляем...');
      keycloak.updateToken(30).catch((error) => {
        console.error('Ошибка обновления токена:', error);
        keycloak.logout();
      });
      break;
    default:
      console.log('Неизвестное событие Keycloak:', eventType);
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
    keycloak.login(options);
  },

  // Выход из системы
  logout: (options?: any) => {
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