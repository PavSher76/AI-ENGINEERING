// Конфигурация окружения для frontend
const environment = {
  // Keycloak Configuration
  keycloak: {
    url: 'http://localhost:9082', // process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:9082',
    realm: 'ai-engineering', // process.env.REACT_APP_KEYCLOAK_REALM || 'ai-engineering',
    clientId: 'ai-frontend', // process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'ai-frontend',
  },
  
  // API Configuration
  api: {
    baseUrl: 'http://localhost:9003', // process.env.REACT_APP_API_URL || 'http://localhost:9003',
  },
  
  // Development Mode
  isDevelopment: false, // process.env.REACT_APP_DEV_MODE === 'true' || process.env.NODE_ENV === 'development',
  
  // Feature Flags
  features: {
    enableKeycloak: false, // process.env.REACT_APP_ENABLE_KEYCLOAK !== 'false',
    enableAnalytics: false, // process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
    enableDebugMode: true, // process.env.REACT_APP_DEBUG_MODE === 'true',
  },
};

export default environment;
