import React, { useEffect } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { Box, Typography, CircularProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const navigate = useNavigate();

  useEffect(() => {
    if (initialized) {
      if (keycloak.authenticated) {
        navigate('/dashboard');
      } else {
        // Автоматический редирект на Keycloak для входа
        keycloak.login();
      }
    }
  }, [initialized, keycloak, navigate]);

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
};

export default Login;
