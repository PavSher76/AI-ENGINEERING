import Keycloak from 'keycloak-js';

const keycloakConfig = {
  url: process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:8080',
  realm: process.env.REACT_APP_KEYCLOAK_REALM || 'ai-engineering',
  clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'ai-frontend',
};

const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
