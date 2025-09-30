import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const Reports: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Отчеты
      </Typography>
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          Модуль генерации отчетов находится в разработке
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Здесь будет интерфейс для создания пояснительных записок
        </Typography>
      </Paper>
    </Box>
  );
};

export default Reports;
