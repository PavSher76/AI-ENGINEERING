import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import {
  QrCode,
  Description,
  Engineering,
  Assessment,
  QrCodeScanner,
  Upload,
  CheckCircle,
  Error,
  Warning,
  Info,
  Refresh,
  Download,
  Visibility,
  VisibilityOff,
  Add,
  Search,
  FileDownload
} from '@mui/icons-material';
import { useErrorHandler } from '../../hooks/useErrorHandler.ts';
import ErrorDisplay from '../../components/Common/ErrorDisplay';

interface QRDocument {
  document_id: string;
  document_type: string;
  project_id: string;
  version: string;
  status: string;
  title?: string;
  description?: string;
  author?: string;
  created_at: string;
  updated_at: string;
  metadata?: any;
  enovia_id?: string;
  mdr_id?: string;
  revision?: string;
  page_num?: number;
}

interface ValidationResult {
  is_valid: boolean;
  status: string;
  message: string;
  document_info?: QRDocument;
}

interface DocumentReleaseData {
  enovia_id: string;
  mdr_id: string;
  revision: string;
  document_type: string;
  project_id: string;
}

interface FieldEngineeringData {
  enovia_id: string;
  mdr_id: string;
  revision: string;
  page_num: number;
  project_id: string;
}

interface StatusReport {
  total_documents: number;
  pending_release: number;
  released: number;
  needs_revision: number;
  documents: QRDocument[];
}

const QRValidation: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const { handleError } = useErrorHandler();

  // Состояния для диалогов
  const [documentReleaseDialog, setDocumentReleaseDialog] = useState(false);
  const [fieldEngineeringDialog, setFieldEngineeringDialog] = useState(false);
  const [statusReportDialog, setStatusReportDialog] = useState(false);
  const [qrValidationDialog, setQrValidationDialog] = useState(false);

  // Состояния для форм
  const [documentReleaseData, setDocumentReleaseData] = useState<DocumentReleaseData>({
    enovia_id: '',
    mdr_id: '',
    revision: '',
    document_type: 'drawing',
    project_id: ''
  });

  const [fieldEngineeringData, setFieldEngineeringData] = useState<FieldEngineeringData>({
    enovia_id: '',
    mdr_id: '',
    revision: '',
    page_num: 1,
    project_id: ''
  });

  const [qrData, setQrData] = useState<string>('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [statusReport, setStatusReport] = useState<StatusReport | null>(null);

  const handleDocumentRelease = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:9013/qr/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentReleaseData.enovia_id,
          document_type: documentReleaseData.document_type,
          project_id: documentReleaseData.project_id,
          version: documentReleaseData.revision,
          title: `Документ РД ${documentReleaseData.mdr_id}`,
          description: `Актуальный документ РД: ${documentReleaseData.mdr_id}`,
          author: 'System',
          metadata: {
            enovia_id: documentReleaseData.enovia_id,
            mdr_id: documentReleaseData.mdr_id,
            revision: documentReleaseData.revision
          }
        }),
      });

      const result = await response.json();

      if (response.ok) {
        alert(`QR-код для документа РД ${documentReleaseData.mdr_id} успешно сгенерирован!`);
        setDocumentReleaseDialog(false);
        setDocumentReleaseData({
          enovia_id: '',
          mdr_id: '',
          revision: '',
          document_type: 'drawing',
          project_id: ''
        });
      } else {
        setError(result.detail || 'Ошибка генерации QR-кода');
      }
    } catch (err) {
      handleError(err);
      setError('Ошибка подключения к сервису');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldEngineeringRelease = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:9013/qr/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: `${fieldEngineeringData.enovia_id}_page_${fieldEngineeringData.page_num}`,
          document_type: 'field_engineering',
          project_id: fieldEngineeringData.project_id,
          version: fieldEngineeringData.revision,
          title: `Лист полевого инжиниринга ${fieldEngineeringData.mdr_id}`,
          description: `Лист полевого инжиниринга: ${fieldEngineeringData.mdr_id}, страница ${fieldEngineeringData.page_num}`,
          author: 'System',
          metadata: {
            enovia_id: fieldEngineeringData.enovia_id,
            mdr_id: fieldEngineeringData.mdr_id,
            revision: fieldEngineeringData.revision,
            page_num: fieldEngineeringData.page_num
          }
        }),
      });

      const result = await response.json();

      if (response.ok) {
        alert(`QR-код для листа полевого инжиниринга ${fieldEngineeringData.mdr_id} (стр. ${fieldEngineeringData.page_num}) успешно сгенерирован!`);
        setFieldEngineeringDialog(false);
        setFieldEngineeringData({
          enovia_id: '',
          mdr_id: '',
          revision: '',
          page_num: 1,
          project_id: ''
        });
      } else {
        setError(result.detail || 'Ошибка генерации QR-кода');
      }
    } catch (err) {
      handleError(err);
      setError('Ошибка подключения к сервису');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusReport = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:9013/qr/status-report', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();

      if (response.ok) {
        setStatusReport(result);
        setStatusReportDialog(true);
      } else {
        setError(result.detail || 'Ошибка получения отчета');
      }
    } catch (err) {
      handleError(err);
      setError('Ошибка подключения к сервису');
    } finally {
      setLoading(false);
    }
  };

  const handleQRValidation = async () => {
    if (!qrData.trim()) {
      setError('Введите данные QR-кода');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:9013/qr/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          qr_data: qrData,
          validate_signature: true
        }),
      });

      const result = await response.json();

      if (response.ok) {
        setValidationResult(result);
      } else {
        setError(result.detail || 'Ошибка валидации QR-кода');
      }
    } catch (err) {
      handleError(err);
      setError('Ошибка подключения к сервису');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:9013/qr/validate-image', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setValidationResult(result);
      } else {
        setError(result.detail || 'Ошибка обработки изображения');
      }
    } catch (err) {
      handleError(err);
      setError('Ошибка загрузки файла');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return 'success';
      case 'invalid': return 'error';
      case 'obsolete': return 'warning';
      case 'rejected': return 'error';
      case 'archived': return 'default';
      case 'version_mismatch': return 'warning';
      case 'invalid_signature': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid': return <CheckCircle />;
      case 'invalid': return <Error />;
      case 'obsolete': return <Warning />;
      case 'rejected': return <Error />;
      case 'archived': return <Info />;
      case 'version_mismatch': return <Warning />;
      case 'invalid_signature': return <Error />;
      default: return <Info />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'valid': return 'Валиден';
      case 'invalid': return 'Невалиден';
      case 'obsolete': return 'Устарел';
      case 'rejected': return 'Отклонен';
      case 'archived': return 'Архивирован';
      case 'version_mismatch': return 'Несоответствие версии';
      case 'invalid_signature': return 'Неверная подпись';
      default: return status;
    }
  };

  const tiles = [
    {
      id: 'document-release',
      title: 'Выпуск актуального документа РД',
      description: 'Генерация QR-кода для актуального документа рабочей документации',
      icon: <Description />,
      color: '#1976d2',
      onClick: () => setDocumentReleaseDialog(true)
    },
    {
      id: 'field-engineering',
      title: 'Выпуск листа полевого инжиниринга РД',
      description: 'Генерация QR-кода для листа полевого инжиниринга с указанием страницы',
      icon: <Engineering />,
      color: '#388e3c',
      onClick: () => setFieldEngineeringDialog(true)
    },
    {
      id: 'status-report',
      title: 'Отчет со статусом документов к перевыпуску',
      description: 'Просмотр статуса всех документов, требующих перевыпуска',
      icon: <Assessment />,
      color: '#f57c00',
      onClick: handleStatusReport
    },
    {
      id: 'qr-validation',
      title: 'Валидация QR-кода',
      description: 'Проверка валидности QR-кода документа',
      icon: <QrCodeScanner />,
      color: '#7b1fa2',
      onClick: () => setQrValidationDialog(true)
    }
  ];

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom color="primary">
          QR валидация РД
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Управление QR-кодами для рабочей документации
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {tiles.map((tile) => (
          <Grid item xs={12} sm={6} md={3} key={tile.id}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6
                }
              }}
              onClick={tile.onClick}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: 3 }}>
                <Box 
                  sx={{ 
                    display: 'inline-flex', 
                    p: 2, 
                    borderRadius: '50%', 
                    bgcolor: tile.color,
                    color: 'white',
                    mb: 2
                  }}
                >
                  {tile.icon}
                </Box>
                <Typography variant="h6" component="h2" gutterBottom>
                  {tile.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {tile.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button 
                  variant="contained" 
                  startIcon={tile.icon}
                  sx={{ 
                    bgcolor: tile.color,
                    '&:hover': {
                      bgcolor: tile.color,
                      opacity: 0.9
                    }
                  }}
                >
                  Открыть
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Диалог выпуска актуального документа РД */}
      <Dialog 
        open={documentReleaseDialog} 
        onClose={() => setDocumentReleaseDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Выпуск актуального документа РД</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Enovia ID"
                value={documentReleaseData.enovia_id}
                onChange={(e) => setDocumentReleaseData({...documentReleaseData, enovia_id: e.target.value})}
                placeholder="Введите Enovia ID"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="MDR ID / Шифр"
                value={documentReleaseData.mdr_id}
                onChange={(e) => setDocumentReleaseData({...documentReleaseData, mdr_id: e.target.value})}
                placeholder="Введите MDR ID или шифр документа"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Ревизия"
                value={documentReleaseData.revision}
                onChange={(e) => setDocumentReleaseData({...documentReleaseData, revision: e.target.value})}
                placeholder="A, B, C..."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Тип документа"
                select
                SelectProps={{ native: true }}
                value={documentReleaseData.document_type}
                onChange={(e) => setDocumentReleaseData({...documentReleaseData, document_type: e.target.value})}
              >
                <option value="drawing">Чертеж</option>
                <option value="specification">Спецификация</option>
                <option value="statement">Ведомость</option>
                <option value="schedule">График</option>
                <option value="report">Отчет</option>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="ID проекта"
                value={documentReleaseData.project_id}
                onChange={(e) => setDocumentReleaseData({...documentReleaseData, project_id: e.target.value})}
                placeholder="Введите ID проекта"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDocumentReleaseDialog(false)}>
            Отмена
          </Button>
          <Button 
            onClick={handleDocumentRelease}
            variant="contained"
            disabled={loading || !documentReleaseData.enovia_id || !documentReleaseData.mdr_id || !documentReleaseData.revision}
            startIcon={loading ? <CircularProgress size={20} /> : <QrCode />}
          >
            {loading ? 'Генерация...' : 'Сгенерировать QR-код'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог выпуска листа полевого инжиниринга РД */}
      <Dialog 
        open={fieldEngineeringDialog} 
        onClose={() => setFieldEngineeringDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Выпуск листа полевого инжиниринга РД</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Enovia ID"
                value={fieldEngineeringData.enovia_id}
                onChange={(e) => setFieldEngineeringData({...fieldEngineeringData, enovia_id: e.target.value})}
                placeholder="Введите Enovia ID"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="MDR ID / Шифр"
                value={fieldEngineeringData.mdr_id}
                onChange={(e) => setFieldEngineeringData({...fieldEngineeringData, mdr_id: e.target.value})}
                placeholder="Введите MDR ID или шифр документа"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Ревизия"
                value={fieldEngineeringData.revision}
                onChange={(e) => setFieldEngineeringData({...fieldEngineeringData, revision: e.target.value})}
                placeholder="A, B, C..."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Номер страницы"
                type="number"
                value={fieldEngineeringData.page_num}
                onChange={(e) => setFieldEngineeringData({...fieldEngineeringData, page_num: parseInt(e.target.value) || 1})}
                inputProps={{ min: 1 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="ID проекта"
                value={fieldEngineeringData.project_id}
                onChange={(e) => setFieldEngineeringData({...fieldEngineeringData, project_id: e.target.value})}
                placeholder="Введите ID проекта"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFieldEngineeringDialog(false)}>
            Отмена
          </Button>
          <Button 
            onClick={handleFieldEngineeringRelease}
            variant="contained"
            disabled={loading || !fieldEngineeringData.enovia_id || !fieldEngineeringData.mdr_id || !fieldEngineeringData.revision}
            startIcon={loading ? <CircularProgress size={20} /> : <Engineering />}
          >
            {loading ? 'Генерация...' : 'Сгенерировать QR-код'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог отчета со статусом документов */}
      <Dialog 
        open={statusReportDialog} 
        onClose={() => setStatusReportDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Отчет со статусом документов к перевыпуску</DialogTitle>
        <DialogContent>
          {statusReport ? (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                    <Typography variant="h4">{statusReport.total_documents}</Typography>
                    <Typography variant="body2">Всего документов</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                    <Typography variant="h4">{statusReport.pending_release}</Typography>
                    <Typography variant="body2">Ожидают выпуска</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                    <Typography variant="h4">{statusReport.released}</Typography>
                    <Typography variant="body2">Выпущены</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.light', color: 'error.contrastText' }}>
                    <Typography variant="h4">{statusReport.needs_revision}</Typography>
                    <Typography variant="body2">Требуют пересмотра</Typography>
                  </Paper>
                </Grid>
              </Grid>
              
              <Typography variant="h6" gutterBottom>
                Список документов
              </Typography>
              <List>
                {statusReport.documents.map((doc, index) => (
                  <ListItem key={index} divider>
                    <ListItemIcon>
                      {getStatusIcon(doc.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {doc.mdr_id || doc.document_id}
                          </Typography>
                          <Chip
                            label={getStatusText(doc.status)}
                            color={getStatusColor(doc.status) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Тип: {doc.document_type} | Версия: {doc.version} | Проект: {doc.project_id}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Обновлен: {new Date(doc.updated_at).toLocaleString('ru-RU')}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          ) : (
            <Typography>Загрузка отчета...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusReportDialog(false)}>
            Закрыть
          </Button>
          <Button 
            startIcon={<FileDownload />}
            variant="outlined"
            disabled={!statusReport}
          >
            Экспорт отчета
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог валидации QR-кода */}
      <Dialog 
        open={qrValidationDialog} 
        onClose={() => setQrValidationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Валидация QR-кода</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Данные QR-кода"
                value={qrData}
                onChange={(e) => setQrData(e.target.value)}
                placeholder="Введите данные QR-кода или загрузите файл..."
              />
            </Grid>
            <Grid item xs={12}>
              <input
                type="file"
                accept="image/*,.pdf,application/pdf"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                id="qr-file-upload"
              />
              <label htmlFor="qr-file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<Upload />}
                  fullWidth
                  disabled={loading}
                >
                  Загрузить файл с QR-кодом
                </Button>
              </label>
            </Grid>
            
            {validationResult && (
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Результат валидации
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Chip
                    icon={getStatusIcon(validationResult.status)}
                    label={getStatusText(validationResult.status)}
                    color={getStatusColor(validationResult.status) as any}
                    variant="filled"
                  />
                  <Typography variant="body1">
                    {validationResult.message}
                  </Typography>
                </Box>

                {validationResult.document_info && (
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="h6" gutterBottom>
                      Информация о документе
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText
                          primary="ID документа"
                          secondary={validationResult.document_info.document_id}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="MDR ID"
                          secondary={validationResult.document_info.mdr_id || 'Не указан'}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Enovia ID"
                          secondary={validationResult.document_info.enovia_id || 'Не указан'}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Тип документа"
                          secondary={validationResult.document_info.document_type}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Версия"
                          secondary={validationResult.document_info.version}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Статус"
                          secondary={validationResult.document_info.status}
                        />
                      </ListItem>
                    </List>
                  </Paper>
                )}
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQrValidationDialog(false)}>
            Закрыть
          </Button>
          <Button 
            onClick={handleQRValidation}
            variant="contained"
            disabled={loading || !qrData.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <QrCodeScanner />}
          >
            {loading ? 'Валидация...' : 'Валидировать'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QRValidation;