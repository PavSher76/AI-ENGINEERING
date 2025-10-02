import React, { useEffect, useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { 
  Box, 
  Typography, 
  CircularProgress, 
  Button, 
  Card, 
  CardContent,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import { 
  Login as LoginIcon, 
  PersonAdd as PersonAddIcon,
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.tsx';

const Login: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isRedirecting, setIsRedirecting] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (initialized && keycloak.authenticated) {
      navigate(from, { replace: true });
    }
  }, [initialized, keycloak, navigate, from]);

  const handleLogin = () => {
    setIsRedirecting(true);
    login();
  };

  const handleRegister = () => {
    if (keycloak.authenticated) {
      return;
    }
    keycloak.register();
  };

  if (isRedirecting) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Typography variant="h4" gutterBottom>
          AI Engineering Platform
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Перенаправление на страницу входа...
        </Typography>
        <CircularProgress sx={{ mt: 2 }} />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: 'background.default',
      }}
    >
      {/* Левая панель с информацией */}
      <Box
        sx={{
          flex: 1,
          display: { xs: 'none', md: 'flex' },
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: 'primary.main',
          color: 'primary.contrastText',
          p: 4,
        }}
      >
        <Typography variant="h3" gutterBottom fontWeight="bold">
          AI Engineering Platform
        </Typography>
        <Typography variant="h6" sx={{ mb: 4, textAlign: 'center', opacity: 0.9 }}>
          Интеллектуальная платформа для инженерных расчетов и анализа
        </Typography>
        
        <List sx={{ maxWidth: 400 }}>
          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon color="inherit" />
            </ListItemIcon>
            <ListItemText 
              primary="ИИ-ассистент для расчетов" 
              secondary="Автоматизация сложных инженерных вычислений"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon color="inherit" />
            </ListItemIcon>
            <ListItemText 
              primary="Анализ документов" 
              secondary="Интеллектуальная обработка технической документации"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon color="inherit" />
            </ListItemIcon>
            <ListItemText 
              primary="Генерация отчетов" 
              secondary="Автоматическое создание технических отчетов"
            />
          </ListItem>
        </List>
      </Box>

      {/* Правая панель с формой входа */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          p: 4,
        }}
      >
        <Card sx={{ maxWidth: 400, width: '100%' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <SecurityIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Вход в систему
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Войдите в AI Engineering Platform для доступа ко всем функциям
              </Typography>
            </Box>

            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Режим разработки:</strong> Система работает без обязательной авторизации.
                Для production использования настройте Keycloak.
              </Typography>
            </Alert>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<LoginIcon />}
                onClick={handleLogin}
                disabled={isRedirecting}
                fullWidth
              >
                Войти через Keycloak
              </Button>

              <Divider>
                <Typography variant="body2" color="text.secondary">
                  или
                </Typography>
              </Divider>

              <Button
                variant="outlined"
                size="large"
                startIcon={<PersonAddIcon />}
                onClick={handleRegister}
                disabled={isRedirecting}
                fullWidth
              >
                Регистрация
              </Button>
            </Box>

            <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                <strong>Тестовые пользователи:</strong>
              </Typography>
              <Typography variant="caption" display="block">
                • admin/admin - Администратор
              </Typography>
              <Typography variant="caption" display="block">
                • developer/developer - Разработчик
              </Typography>
              <Typography variant="caption" display="block">
                • analyst/analyst - Аналитик
              </Typography>
              <Typography variant="caption" display="block">
                • viewer/viewer - Наблюдатель
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default Login;
