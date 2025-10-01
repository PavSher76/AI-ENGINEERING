import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Box, CircularProgress, Typography } from '@mui/material';

// Keycloak
import keycloak, { keycloakEventHandler } from './services/keycloak';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { ProjectProvider } from './contexts/ProjectContext';

// Components
import Layout from './components/Layout/Layout.tsx';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';

// Pages
import Login from './pages/Auth/Login.tsx';
import Dashboard from './pages/Dashboard/Dashboard.tsx';
import Chat from './pages/Chat/Chat.tsx';
import Consultation from './pages/Consultation/Consultation.tsx';
import Archive from './pages/Archive/Archive.tsx';
import Calculations from './pages/Calculations/Calculations.tsx';
import Validation from './pages/Validation/Validation.tsx';
import Documents from './pages/Documents/Documents.tsx';
import Analytics from './pages/Analytics/Analytics.tsx';
import Integration from './pages/Integration/Integration.tsx';
import OutgoingControl from './pages/OutgoingControl/OutgoingControl.tsx';
import QRValidation from './pages/QRValidation/QRValidation.tsx';
import Settings from './pages/Settings/Settings.tsx';

import './App.css';

// React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

// Loading component
const LoadingSpinner: React.FC<{ message?: string }> = ({ message = 'Загрузка...' }) => (
  <Box
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    minHeight="100vh"
    gap={2}
  >
    <CircularProgress size={40} />
    <Typography variant="body2" color="text.secondary">
      {message}
    </Typography>
  </Box>
);

function App() {
  return (
    <ReactKeycloakProvider
      authClient={keycloak}
      onEvent={keycloakEventHandler}
      LoadingComponent={<LoadingSpinner message="Инициализация системы авторизации..." />}
    >
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AuthProvider>
            <ProjectProvider>
              <Router>
                <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                  <Routes>
                    {/* Public routes */}
                    <Route path="/login" element={<Login />} />
                    
                    {/* Protected routes */}
                    <Route path="/" element={
                      <ProtectedRoute>
                        <Layout />
                      </ProtectedRoute>
                    }>
                      <Route index element={<Navigate to="/dashboard" replace />} />
                      <Route path="dashboard" element={<Dashboard />} />
                      <Route path="chat" element={<Chat />} />
                      <Route path="consultation" element={<Consultation />} />
                      <Route path="archive" element={<Archive />} />
                      <Route path="calculations" element={<Calculations />} />
                      <Route path="validation" element={<Validation />} />
                      <Route path="documents" element={<Documents />} />
                      <Route path="analytics" element={<Analytics />} />
                      <Route path="integration" element={<Integration />} />
                      <Route path="outgoing-control" element={<OutgoingControl />} />
                      <Route path="qr-validation" element={<QRValidation />} />
                      <Route path="settings" element={
                        <ProtectedRoute requiredRoles={['admin', 'developer']}>
                          <Settings />
                        </ProtectedRoute>
                      } />
                    </Route>
                    
                    {/* Catch all route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Box>
              </Router>
            </ProjectProvider>
          </AuthProvider>
        </ThemeProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ReactKeycloakProvider>
  );
}

export default App;