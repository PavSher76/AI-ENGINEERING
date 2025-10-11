import React from 'react';
import { 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import { 
  Description, 
  CheckCircle, 
  Cancel, 
  Schedule,
  TextFields,
  Style,
  Security,
  Translate
} from '@mui/icons-material';
import { ServiceStats } from '../types';

interface StatsPanelProps {
  stats: ServiceStats;
  isLoading?: boolean;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ stats, isLoading = false }) => {
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}с`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}м ${remainingSeconds.toFixed(0)}с`;
  };

  const getApprovalRate = () => {
    if (stats.total_documents_processed === 0) return 0;
    return (stats.documents_approved / stats.total_documents_processed) * 100;
  };

  const getRejectionRate = () => {
    if (stats.total_documents_processed === 0) return 0;
    return (stats.documents_rejected / stats.total_documents_processed) * 100;
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Статистика
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Статистика системы
      </Typography>
      
      <Grid container spacing={2}>
        {/* Общая статистика */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Description color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  {stats.total_documents_processed}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Всего обработано
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Schedule color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  {stats.documents_needing_revision}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Требуют доработки
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  {stats.documents_approved}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Одобрено
              </Typography>
              <Chip 
                label={`${getApprovalRate().toFixed(1)}%`} 
                size="small" 
                color="success"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Cancel color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  {stats.documents_rejected}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Отклонено
              </Typography>
              <Chip 
                label={`${getRejectionRate().toFixed(1)}%`} 
                size="small" 
                color="error"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Время обработки */}
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Среднее время обработки
              </Typography>
              <Typography variant="h4" color="primary">
                {formatTime(stats.average_processing_time)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Частые проблемы */}
        <Grid item xs={12} sm={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Частые проблемы
              </Typography>
              {stats.most_common_issues && stats.most_common_issues.length > 0 ? (
                <List dense>
                  {stats.most_common_issues.map((issue, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={issue} />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Проблем не обнаружено
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StatsPanel;
