import React from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Chip, 
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  ButtonGroup,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';
import { 
  ExpandMore, 
  Description, 
  CheckCircle, 
  Warning, 
  Error,
  Info,
  Refresh,
  Delete,
  PlayArrow
} from '@mui/icons-material';
import { Document } from '../types';

interface DocumentDetailsProps {
  document: Document;
  onRerunChecks?: (documentId: string) => void;
  onDelete?: (documentId: string) => void;
  isProcessing?: boolean;
}

const DocumentDetails: React.FC<DocumentDetailsProps> = ({ 
  document, 
  onRerunChecks, 
  onDelete, 
  isProcessing = false 
}) => {
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);

  const handleRerunChecks = () => {
    if (onRerunChecks) {
      onRerunChecks(document.id);
    }
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (onDelete) {
      onDelete(document.id);
    }
    setDeleteDialogOpen(false);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'success';
      case 'rejected': return 'error';
      case 'processing': return 'warning';
      case 'reviewed': return 'info';
      case 'needs_revision': return 'warning';
      case 'pending': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft': return 'Черновик';
      case 'uploaded': return 'Загружен';
      case 'pending': return 'Ожидает';
      case 'processing': return 'Обрабатывается';
      case 'reviewed': return 'Проверен';
      case 'needs_revision': return 'Требует доработки';
      case 'approved': return 'Одобрен';
      case 'rejected': return 'Отклонен';
      default: return status;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Детали документа
        </Typography>
        
        <ButtonGroup variant="outlined" size="small">
          <Button
            startIcon={<Refresh />}
            onClick={handleRerunChecks}
            disabled={isProcessing || document.status === 'processing'}
            color="primary"
          >
            Повторная проверка
          </Button>
          <Button
            startIcon={<Delete />}
            onClick={handleDeleteClick}
            disabled={isProcessing}
            color="error"
          >
            Удалить
          </Button>
        </ButtonGroup>
      </Box>
      
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {document.title}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            <Chip 
              label={getStatusLabel(document.status)} 
              color={getStatusColor(document.status) as any}
              size="small"
            />
            <Chip 
              label={document.document_type || 'Неизвестно'} 
              color="primary"
              size="small"
            />
            {document.file_size && (
              <Chip 
                label={formatFileSize(document.file_size)} 
                color="default"
                size="small"
              />
            )}
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Дата создания
              </Typography>
              <Typography variant="body2">
                {new Date(document.created_at).toLocaleString()}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Последнее обновление
              </Typography>
              <Typography variant="body2">
                {new Date(document.updated_at).toLocaleString()}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Результаты проверок */}
      {document.checks && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Результаты проверок
            </Typography>
            
            {Object.entries(document.checks).map(([checkType, result]) => (
              <Accordion key={checkType}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    {result?.status === 'completed' && <CheckCircle color="success" sx={{ mr: 1 }} />}
                    {result?.status === 'failed' && <Error color="error" sx={{ mr: 1 }} />}
                    {result?.status === 'running' && <Warning color="warning" sx={{ mr: 1 }} />}
                    {result?.status === 'pending' && <Info color="info" sx={{ mr: 1 }} />}
                    
                    <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                      {checkType === 'spell_check' && 'Проверка орфографии'}
                      {checkType === 'style_analysis' && 'Анализ стиля'}
                      {checkType === 'ethics_check' && 'Проверка этики'}
                      {checkType === 'terminology_check' && 'Проверка терминологии'}
                    </Typography>
                    
                    {result?.score && (
                      <Chip 
                        label={`${result.score}%`} 
                        color={result.score >= 80 ? 'success' : result.score >= 60 ? 'warning' : 'error'}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                    )}
                    
                    <Chip 
                      label={result?.status || 'pending'} 
                      color={getStatusColor(result?.status || 'pending') as any}
                      size="small"
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {result?.issues && result.issues.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Найденные проблемы:
                      </Typography>
                      <List dense>
                        {result.issues.map((issue: any, index: number) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              {issue.type === 'error' && <Error color="error" fontSize="small" />}
                              {issue.type === 'warning' && <Warning color="warning" fontSize="small" />}
                              {issue.type === 'suggestion' && <Info color="info" fontSize="small" />}
                            </ListItemIcon>
                            <ListItemText
                              primary={issue.message}
                              secondary={issue.severity}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                  
                  {result?.suggestions && result.suggestions.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Рекомендации:
                      </Typography>
                      <List dense>
                        {result.suggestions.map((suggestion: string, index: number) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <CheckCircle color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={suggestion} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Извлеченный текст */}
      {document.extracted_text && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Извлеченный текст
            </Typography>
            <Box 
              sx={{ 
                maxHeight: 300, 
                overflow: 'auto', 
                p: 2, 
                backgroundColor: 'grey.50', 
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap'
              }}
            >
              {document.extracted_text}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Диалог подтверждения удаления */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Подтверждение удаления
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Вы уверены, что хотите удалить документ "{document.title}"? 
            Это действие нельзя отменить.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Отмена
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Удалить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentDetails;

