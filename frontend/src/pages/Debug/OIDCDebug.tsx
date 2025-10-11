import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  Grid,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useAuth } from '../../contexts/AuthContext.tsx';
import environment from '../../config/environment.ts';

interface WellKnownConfig {
  issuer?: string;
  authorization_endpoint?: string;
  token_endpoint?: string;
  userinfo_endpoint?: string;
  end_session_endpoint?: string;
  jwks_uri?: string;
}

interface TokenInfo {
  sub?: string;
  iss?: string;
  aud?: string;
  exp?: number;
  iat?: number;
  preferred_username?: string;
  email?: string;
  realm_access?: {
    roles?: string[];
  };
  resource_access?: {
    [key: string]: {
      roles?: string[];
    };
  };
}

const OIDCDebug: React.FC = () => {
  const { user, isAuthenticated, updateToken } = useAuth();
  const [wellKnownConfig, setWellKnownConfig] = useState<WellKnownConfig | null>(null);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [envVars, setEnvVars] = useState<Record<string, any>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Получаем переменные окружения
    setEnvVars({
      KEYCLOAK_URL: environment.keycloak.url,
      KEYCLOAK_REALM: environment.keycloak.realm,
      KEYCLOAK_CLIENT_ID: environment.keycloak.clientId,
      ENABLE_KEYCLOAK: environment.features.enableKeycloak,
      API_URL: environment.api.baseUrl,
      IS_DEVELOPMENT: environment.isDevelopment,
    });
  }, []);

  const fetchWellKnownConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `${environment.keycloak.url}/realms/${environment.keycloak.realm}/.well-known/openid-configuration`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const config = await response.json();
      setWellKnownConfig(config);
    } catch (err) {
      setError(`Ошибка получения конфигурации: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const decodeToken = () => {
    try {
      // Получаем токен из localStorage или sessionStorage
      const token = localStorage.getItem('keycloak-token') || 
                   sessionStorage.getItem('keycloak-token') ||
                   localStorage.getItem('kc-token') ||
                   sessionStorage.getItem('kc-token');
      
      if (!token) {
        setError('Токен не найден в localStorage/sessionStorage');
        return;
      }

      // Декодируем JWT токен
      const parts = token.split('.');
      if (parts.length !== 3) {
        setError('Неверный формат JWT токена');
        return;
      }

      const payload = JSON.parse(atob(parts[1]));
      setTokenInfo(payload);
    } catch (err) {
      setError(`Ошибка декодирования токена: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const testTokenRefresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const success = await updateToken();
      if (success) {
        setError(null);
        // Обновляем информацию о токене
        decodeToken();
      } else {
        setError('Не удалось обновить токен');
      }
    } catch (err) {
      setError(`Ошибка обновления токена: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp?: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        OIDC Debug Panel
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Переменные окружения */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Переменные окружения
              </Typography>
              {Object.entries(envVars).map(([key, value]) => (
                <Box key={key} sx={{ mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    {key}:
                  </Typography>
                  <Chip 
                    label={String(value)} 
                    size="small" 
                    color={value ? 'primary' : 'default'}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Статус авторизации */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Статус авторизации
              </Typography>
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Аутентифицирован:
                </Typography>
                <Chip 
                  label={isAuthenticated ? 'Да' : 'Нет'} 
                  color={isAuthenticated ? 'success' : 'error'}
                  size="small"
                />
              </Box>
              {user && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Пользователь:
                  </Typography>
                  <Typography variant="body2">
                    {user.firstName} {user.lastName} ({user.username})
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Действия */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Действия
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button 
                  variant="contained" 
                  onClick={fetchWellKnownConfig}
                  disabled={loading}
                >
                  Получить .well-known конфигурацию
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={decodeToken}
                  disabled={loading}
                >
                  Декодировать токен
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={testTokenRefresh}
                  disabled={loading}
                >
                  Обновить токен
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Конфигурация OpenID Connect */}
        {wellKnownConfig && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Конфигурация OpenID Connect
                </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Endpoints</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {Object.entries(wellKnownConfig).map(([key, value]) => (
                      <Box key={key} sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {key}:
                        </Typography>
                        <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                          {String(value)}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                      </Box>
                    ))}
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Информация о токене */}
        {tokenInfo && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Информация о токене
                </Typography>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Данные токена</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Subject (sub):
                      </Typography>
                      <Typography variant="body2">{tokenInfo.sub || 'N/A'}</Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Issuer (iss):
                      </Typography>
                      <Typography variant="body2">{tokenInfo.iss || 'N/A'}</Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Audience (aud):
                      </Typography>
                      <Typography variant="body2">{tokenInfo.aud || 'N/A'}</Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Истекает (exp):
                      </Typography>
                      <Typography variant="body2">{formatTimestamp(tokenInfo.exp)}</Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Выдан (iat):
                      </Typography>
                      <Typography variant="body2">{formatTimestamp(tokenInfo.iat)}</Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Username:
                      </Typography>
                      <Typography variant="body2">{tokenInfo.preferred_username || 'N/A'}</Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Email:
                      </Typography>
                      <Typography variant="body2">{tokenInfo.email || 'N/A'}</Typography>
                    </Box>
                    {tokenInfo.realm_access?.roles && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Realm роли:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {tokenInfo.realm_access.roles.map((role) => (
                            <Chip key={role} label={role} size="small" />
                          ))}
                        </Box>
                      </Box>
                    )}
                    {tokenInfo.resource_access && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Client роли:
                        </Typography>
                        {Object.entries(tokenInfo.resource_access).map(([client, roles]) => (
                          <Box key={client} sx={{ mb: 1 }}>
                            <Typography variant="body2" color="text.secondary">
                              {client}:
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              {roles.roles?.map((role) => (
                                <Chip key={role} label={role} size="small" />
                              ))}
                            </Box>
                          </Box>
                        ))}
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default OIDCDebug;
