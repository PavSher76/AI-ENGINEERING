import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Switch,
  FormControlLabel,
  FormGroup,
  Button,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  InputAdornment,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore,
  Save,
  Refresh,
  Settings,
  Psychology,
  Description,
  Security,
  Notifications,
  Api,
  CheckCircle,
  Warning,
  Error
} from '@mui/icons-material';
import { OutgoingControlService } from '../../../services/api.ts';
import {
  OutgoingControlSettings,
  CheckType,
  ReportFormat,
  LLMProvider,
  SettingsResponse,
  SettingsValidationResponse
} from '../../../types/outgoingControlSettings.ts';

interface OutgoingControlSettingsProps {
  onSettingsChange?: (settings: OutgoingControlSettings) => void;
}

const OutgoingControlSettingsComponent: React.FC<OutgoingControlSettingsProps> = ({
  onSettingsChange
}) => {
  const [settings, setSettings] = useState<OutgoingControlSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [validation, setValidation] = useState<SettingsValidationResponse | null>(null);

  // Загрузка настроек
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await OutgoingControlService.getSettings();
      setSettings(response.settings);
      if (onSettingsChange) {
        onSettingsChange(response.settings);
      }
    } catch (err: any) {
      setError(`Ошибка загрузки настроек: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      // Валидируем настройки перед сохранением
      const validationResponse = await OutgoingControlService.validateSettings(settings);
      setValidation(validationResponse);

      if (!validationResponse.valid) {
        setError(`Ошибки валидации: ${validationResponse.errors.join(', ')}`);
        return;
      }

      const response: SettingsResponse = await OutgoingControlService.updateSettings(settings);
      
      if (response.success) {
        setSuccess('Настройки успешно сохранены');
        if (onSettingsChange) {
          onSettingsChange(response.settings);
        }
      } else {
        setError(response.message || 'Ошибка сохранения настроек');
      }
    } catch (err: any) {
      setError(`Ошибка сохранения: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const resetSettings = async () => {
    try {
      setSaving(true);
      setError(null);
      const response = await OutgoingControlService.resetSettings();
      if (response.success) {
        setSettings(response.settings);
        setSuccess('Настройки сброшены к значениям по умолчанию');
        if (onSettingsChange) {
          onSettingsChange(response.settings);
        }
      }
    } catch (err: any) {
      setError(`Ошибка сброса настроек: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSettingChange = (key: keyof OutgoingControlSettings, value: any) => {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
    setSuccess(null);
    setError(null);
  };

  const handleCheckTypeToggle = (checkType: CheckType) => {
    if (!settings) return;
    const enabledChecks = settings.enabled_checks.includes(checkType)
      ? settings.enabled_checks.filter(c => c !== checkType)
      : [...settings.enabled_checks, checkType];
    handleSettingChange('enabled_checks', enabledChecks);
  };

  const handleFileTypeToggle = (fileType: string) => {
    if (!settings) return;
    const allowedTypes = settings.allowed_file_types.includes(fileType)
      ? settings.allowed_file_types.filter(t => t !== fileType)
      : [...settings.allowed_file_types, fileType];
    handleSettingChange('allowed_file_types', allowedTypes);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Typography>Загрузка настроек...</Typography>
      </Box>
    );
  }

  if (!settings) {
    return (
      <Alert severity="error">
        Не удалось загрузить настройки модуля
      </Alert>
    );
  }

  return (
    <Box>
      {/* Заголовок и кнопки управления */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
          Настройки модуля "Выходной контроль исходящей переписки"
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadSettings}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Обновить
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={saveSettings}
            disabled={saving}
            color="primary"
          >
            {saving ? 'Сохранение...' : 'Сохранить'}
          </Button>
        </Box>
      </Box>

      {/* Сообщения об ошибках и успехе */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Валидация */}
      {validation && (
        <Box mb={2}>
          {validation.errors.length > 0 && (
            <Alert severity="error" sx={{ mb: 1 }}>
              <strong>Ошибки:</strong> {validation.errors.join(', ')}
            </Alert>
          )}
          {validation.warnings.length > 0 && (
            <Alert severity="warning" sx={{ mb: 1 }}>
              <strong>Предупреждения:</strong> {validation.warnings.join(', ')}
            </Alert>
          )}
        </Box>
      )}

      <Grid container spacing={3}>
        {/* Настройки LLM */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Psychology sx={{ mr: 1 }} />
              <Typography variant="h6">Настройки LLM</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Провайдер LLM</InputLabel>
                    <Select
                      value={settings.llm_provider}
                      onChange={(e) => handleSettingChange('llm_provider', e.target.value)}
                      label="Провайдер LLM"
                    >
                      <MenuItem value={LLMProvider.OLLAMA}>Ollama</MenuItem>
                      <MenuItem value={LLMProvider.OPENAI}>OpenAI</MenuItem>
                      <MenuItem value={LLMProvider.ANTHROPIC}>Anthropic</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Модель"
                    value={settings.llm_model}
                    onChange={(e) => handleSettingChange('llm_model', e.target.value)}
                    placeholder="llama3.1:8b"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography gutterBottom>Температура: {settings.llm_temperature}</Typography>
                  <Slider
                    value={settings.llm_temperature}
                    onChange={(_, value) => handleSettingChange('llm_temperature', value)}
                    min={0}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 1, label: '1' },
                      { value: 2, label: '2' }
                    ]}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Максимум токенов"
                    type="number"
                    value={settings.llm_max_tokens}
                    onChange={(e) => handleSettingChange('llm_max_tokens', parseInt(e.target.value))}
                    inputProps={{ min: 100, max: 4096 }}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Таймаут (сек)"
                    type="number"
                    value={settings.llm_timeout}
                    onChange={(e) => handleSettingChange('llm_timeout', parseInt(e.target.value))}
                    inputProps={{ min: 10, max: 300 }}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Промпты для проверок */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Description sx={{ mr: 1 }} />
              <Typography variant="h6">Промпты для проверок</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Промпт проверки орфографии"
                    value={settings.spell_check_prompt}
                    onChange={(e) => handleSettingChange('spell_check_prompt', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Промпт анализа стиля"
                    value={settings.style_analysis_prompt}
                    onChange={(e) => handleSettingChange('style_analysis_prompt', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Промпт проверки этики"
                    value={settings.ethics_check_prompt}
                    onChange={(e) => handleSettingChange('ethics_check_prompt', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Промпт проверки терминологии"
                    value={settings.terminology_check_prompt}
                    onChange={(e) => handleSettingChange('terminology_check_prompt', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Промпт финальной проверки"
                    value={settings.final_review_prompt}
                    onChange={(e) => handleSettingChange('final_review_prompt', e.target.value)}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Настройки отчетов */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Description sx={{ mr: 1 }} />
              <Typography variant="h6">Настройки отчетов</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Формат отчета по умолчанию</InputLabel>
                    <Select
                      value={settings.default_report_format}
                      onChange={(e) => handleSettingChange('default_report_format', e.target.value)}
                      label="Формат отчета по умолчанию"
                    >
                      <MenuItem value={ReportFormat.PDF}>PDF</MenuItem>
                      <MenuItem value={ReportFormat.DOCX}>DOCX</MenuItem>
                      <MenuItem value={ReportFormat.TXT}>TXT</MenuItem>
                      <MenuItem value={ReportFormat.HTML}>HTML</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormGroup>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.include_detailed_analysis}
                          onChange={(e) => handleSettingChange('include_detailed_analysis', e.target.checked)}
                        />
                      }
                      label="Включать детальный анализ"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.include_suggestions}
                          onChange={(e) => handleSettingChange('include_suggestions', e.target.checked)}
                        />
                      }
                      label="Включать предложения"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.include_statistics}
                          onChange={(e) => handleSettingChange('include_statistics', e.target.checked)}
                        />
                      }
                      label="Включать статистику"
                    />
                  </FormGroup>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Настройки проверок */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <CheckCircle sx={{ mr: 1 }} />
              <Typography variant="h6">Настройки проверок</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    Включенные типы проверок:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {Object.values(CheckType).map((checkType) => (
                      <Chip
                        key={checkType}
                        label={getCheckTypeLabel(checkType)}
                        color={settings.enabled_checks.includes(checkType) ? 'primary' : 'default'}
                        onClick={() => handleCheckTypeToggle(checkType)}
                        clickable
                      />
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormGroup>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.auto_process_on_upload}
                          onChange={(e) => handleSettingChange('auto_process_on_upload', e.target.checked)}
                        />
                      }
                      label="Автоматически обрабатывать при загрузке"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.require_manual_approval}
                          onChange={(e) => handleSettingChange('require_manual_approval', e.target.checked)}
                        />
                      }
                      label="Требовать ручного одобрения"
                    />
                  </FormGroup>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>
                    Минимальный порог уверенности: {settings.min_confidence_threshold}
                  </Typography>
                  <Slider
                    value={settings.min_confidence_threshold}
                    onChange={(_, value) => handleSettingChange('min_confidence_threshold', value)}
                    min={0}
                    max={1}
                    step={0.1}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 0.5, label: '0.5' },
                      { value: 1, label: '1' }
                    ]}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Настройки безопасности */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Security sx={{ mr: 1 }} />
              <Typography variant="h6">Настройки безопасности</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormGroup>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.require_authentication}
                          onChange={(e) => handleSettingChange('require_authentication', e.target.checked)}
                        />
                      }
                      label="Требовать аутентификацию"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.enable_api_access}
                          onChange={(e) => handleSettingChange('enable_api_access', e.target.checked)}
                        />
                      }
                      label="Включить API доступ"
                    />
                  </FormGroup>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Максимальный размер файла (МБ)"
                    type="number"
                    value={settings.max_file_size_mb}
                    onChange={(e) => handleSettingChange('max_file_size_mb', parseInt(e.target.value))}
                    inputProps={{ min: 1, max: 500 }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" gutterBottom>
                    Разрешенные типы файлов:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {['pdf', 'docx', 'txt', 'rtf', 'odt'].map((fileType) => (
                      <Chip
                        key={fileType}
                        label={fileType.toUpperCase()}
                        color={settings.allowed_file_types.includes(fileType) ? 'primary' : 'default'}
                        onClick={() => handleFileTypeToggle(fileType)}
                        clickable
                      />
                    ))}
                  </Box>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Кнопка сброса */}
        <Grid item xs={12}>
          <Divider sx={{ my: 2 }} />
          <Box display="flex" justifyContent="center">
            <Button
              variant="outlined"
              color="warning"
              onClick={resetSettings}
              disabled={saving}
              startIcon={<Refresh />}
            >
              Сбросить к значениям по умолчанию
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

// Вспомогательная функция для получения меток типов проверок
const getCheckTypeLabel = (checkType: CheckType): string => {
  const labels = {
    [CheckType.SPELL_CHECK]: 'Проверка орфографии',
    [CheckType.STYLE_ANALYSIS]: 'Анализ стиля',
    [CheckType.ETHICS_CHECK]: 'Проверка этики',
    [CheckType.TERMINOLOGY_CHECK]: 'Проверка терминологии',
    [CheckType.FINAL_REVIEW]: 'Финальная проверка'
  };
  return labels[checkType] || checkType;
};

export default OutgoingControlSettingsComponent;
