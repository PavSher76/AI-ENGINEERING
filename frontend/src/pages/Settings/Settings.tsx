import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Container
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Psychology,
  Description,
  Security,
  Notifications
} from '@mui/icons-material';
import OutgoingControlSettings from './components/OutgoingControlSettings.tsx';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          <SettingsIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          Настройки системы
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Конфигурация и управление модулями системы
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="настройки модулей">
            <Tab 
              icon={<Description />} 
              label="Выходной контроль" 
              iconPosition="start"
              id="settings-tab-0"
              aria-controls="settings-tabpanel-0"
            />
            <Tab 
              icon={<Psychology />} 
              label="AI Chat" 
              iconPosition="start"
              id="settings-tab-1"
              aria-controls="settings-tabpanel-1"
            />
            <Tab 
              icon={<Security />} 
              label="Безопасность" 
              iconPosition="start"
              id="settings-tab-2"
              aria-controls="settings-tabpanel-2"
            />
            <Tab 
              icon={<Notifications />} 
              label="Уведомления" 
              iconPosition="start"
              id="settings-tab-3"
              aria-controls="settings-tabpanel-3"
            />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <OutgoingControlSettings />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <Box textAlign="center">
              <Psychology sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Настройки AI Chat
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Модуль находится в разработке
              </Typography>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <Box textAlign="center">
              <Security sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Настройки безопасности
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Модуль находится в разработке
              </Typography>
            </Box>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <Box textAlign="center">
              <Notifications sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Настройки уведомлений
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Модуль находится в разработке
              </Typography>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default Settings;