import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Box, CircularProgress, Typography } from '@mui/material';
import Header from './Header.tsx';
import Sidebar from './Sidebar.tsx';
import './Layout.css';

interface LayoutProps {
  children?: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { user, isAuthenticated, isLoading } = useAuth();

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Показываем загрузку пока проверяем авторизацию
  if (isLoading) {
    return (
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
          Загрузка приложения...
        </Typography>
      </Box>
    );
  }

  // Если пользователь не аутентифицирован, показываем сообщение
  if (!isAuthenticated || !user) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <Typography variant="h6" color="error">
          Требуется авторизация
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Пожалуйста, войдите в систему для доступа к приложению
        </Typography>
      </Box>
    );
  }

  return (
    <div className="layout">
      <Header onMenuClick={toggleSidebar} />
      <div className="layout-content">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} currentPath={location.pathname} />
        <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
          <div className="content-wrapper">
            {children || <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;