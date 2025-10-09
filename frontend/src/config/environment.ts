// Конфигурация окружения для frontend
const environment = {
  // Keycloak Configuration
  keycloak: {
    url: process.env.REACT_APP_KEYCLOAK_URL || 'https://localhost:9080',
    realm: process.env.REACT_APP_KEYCLOAK_REALM || 'ai-engineering',
    clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'ai-frontend',
  },
  
  // API Configuration
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'https://localhost/api',
  },
  
  // Development Mode
  isDevelopment: process.env.REACT_APP_DEV_MODE === 'true' || process.env.NODE_ENV === 'development',
  
  // Feature Flags
  features: {
    enableKeycloak: process.env.REACT_APP_ENABLE_KEYCLOAK !== 'false',
    enableAnalytics: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
    enableDebugMode: process.env.REACT_APP_DEBUG_MODE === 'true',
  },
};

export default environment;
