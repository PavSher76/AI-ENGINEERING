import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Menu,
  MenuItem,
  Avatar,
  Chip,
  Divider,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Logout,
  Settings,
  Person,
  Security,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Header.css';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
  };

  const handleSettings = () => {
    handleMenuClose();
    navigate('/settings');
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'error';
      case 'developer': return 'primary';
      case 'analyst': return 'success';
      case 'viewer': return 'default';
      default: return 'default';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin': return 'Администратор';
      case 'developer': return 'Разработчик';
      case 'analyst': return 'Аналитик';
      case 'viewer': return 'Наблюдатель';
      default: return role;
    }
  };

  return (
    <AppBar position="static" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          onClick={onMenuClick}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
            AI Engineering Platform
          </Typography>
          <Typography variant="caption" sx={{ opacity: 0.8 }}>
            Инженерная платформа с поддержкой ИИ
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Статус системы */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: 'success.main',
              }}
            />
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              Система работает
            </Typography>
          </Box>

          {/* Информация о пользователе */}
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* Роли пользователя */}
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {user.roles.slice(0, 2).map((role) => (
                  <Chip
                    key={role}
                    label={getRoleLabel(role)}
                    size="small"
                    color={getRoleColor(role) as any}
                    variant="outlined"
                    sx={{ 
                      fontSize: '0.7rem',
                      height: 20,
                      '& .MuiChip-label': { px: 1 }
                    }}
                  />
                ))}
                {user.roles.length > 2 && (
                  <Chip
                    label={`+${user.roles.length - 2}`}
                    size="small"
                    variant="outlined"
                    sx={{ 
                      fontSize: '0.7rem',
                      height: 20,
                      '& .MuiChip-label': { px: 1 }
                    }}
                  />
                )}
              </Box>

              {/* Меню пользователя */}
              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="user-menu"
                aria-haspopup="true"
                onClick={handleMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                  {user.firstName?.[0] || user.username?.[0] || 'U'}
                </Avatar>
              </IconButton>

              <Menu
                id="user-menu"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem disabled>
                  <ListItemIcon>
                    <Person fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={user.firstName && user.lastName 
                      ? `${user.firstName} ${user.lastName}`
                      : user.username
                    }
                    secondary={user.email}
                  />
                </MenuItem>

                <Divider />

                {hasRole('admin') || hasRole('developer') ? (
                  <MenuItem onClick={handleSettings}>
                    <ListItemIcon>
                      <Settings fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary="Настройки" />
                  </MenuItem>
                ) : null}

                <MenuItem onClick={handleLogout}>
                  <ListItemIcon>
                    <Logout fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Выйти" />
                </MenuItem>
              </Menu>
            </Box>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;