import React from 'react';
import { CheckResult as CheckResultType, Issue, SpellCheckResult, StyleAnalysisResult, EthicsCheckResult, TerminologyCheckResult } from '../types';
import { 
  CheckCircle, 
  Error, 
  Warning, 
  Info,
  Schedule,
  PlayArrow,
  CheckCircleOutline
} from '@mui/icons-material';
import { 
  Box, 
  Typography, 
  Chip, 
  Accordion, 
  AccordionSummary, 
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

interface CheckResultProps {
  title: string;
  result: CheckResultType;
  onRunCheck?: () => void;
}

const CheckResult: React.FC<CheckResultProps> = ({ title, result, onRunCheck }) => {
  const getStatusIcon = () => {
    switch (result.status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'running':
        return <PlayArrow color="primary" />;
      case 'pending':
        return <Schedule color="disabled" />;
      default:
        return <Info color="info" />;
    }
  };

  const getStatusColor = () => {
    switch (result.status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'primary';
      case 'pending':
        return 'default';
      default:
        return 'info';
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const renderIssues = (issues: Issue[]) => {
    if (!issues || issues.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary">
          Проблем не найдено
        </Typography>
      );
    }

    return (
      <List dense>
        {issues.map((issue, index) => (
          <ListItem key={index}>
            <ListItemIcon>
              {issue.type === 'error' && <Error color="error" fontSize="small" />}
              {issue.type === 'warning' && <Warning color="warning" fontSize="small" />}
              {issue.type === 'suggestion' && <Info color="info" fontSize="small" />}
            </ListItemIcon>
            <ListItemText
              primary={issue.message}
              secondary={
                <Box>
                  <Chip 
                    label={issue.severity} 
                    size="small" 
                    color={issue.severity === 'high' ? 'error' : issue.severity === 'medium' ? 'warning' : 'default'}
                    sx={{ mr: 1 }}
                  />
                  {issue.position && (
                    <Typography variant="caption" color="text.secondary">
                      Позиция: {issue.position.start}-{issue.position.end}
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    );
  };

  const renderSpellCheckDetails = (details: SpellCheckResult) => {
    return (
      <Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Статистика проверки:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <Chip label={`Всего слов: ${details.total_words}`} size="small" />
            <Chip label={`Ошибок найдено: ${details.errors_found}`} size="small" color={details.errors_found > 0 ? 'error' : 'success'} />
            <Chip label={`Уверенность: ${(details.confidence_score * 100).toFixed(1)}%`} size="small" />
          </Box>
        </Box>
        
        {details.suggestions && details.suggestions.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Найденные ошибки и предложения:
            </Typography>
            <List dense>
              {details.suggestions.map((suggestion, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Error color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`"${suggestion.word}"`}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          Предложения: {suggestion.suggestions.join(', ')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Позиция: {suggestion.position}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
        
        {details.corrected_text && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Исправленный текст:
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, border: '1px solid', borderColor: 'grey.300' }}>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {details.corrected_text}
              </Typography>
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const renderStyleAnalysisDetails = (details: StyleAnalysisResult) => {
    return (
      <Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Оценки стиля:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <Chip label={`Читаемость: ${details.readability_score.toFixed(1)}`} size="small" />
            <Chip label={`Формальность: ${details.formality_score.toFixed(1)}`} size="small" />
            <Chip label={`Деловой стиль: ${details.business_style_score.toFixed(1)}`} size="small" />
          </Box>
        </Box>
        
        {details.tone_analysis && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Анализ тона:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip label={`Тон: ${details.tone_analysis.tone}`} size="small" />
              <Chip label={`Уверенность: ${(details.tone_analysis.confidence * 100).toFixed(1)}%`} size="small" />
            </Box>
          </Box>
        )}
        
        {details.recommendations && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Рекомендации:
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.300' }}>
              <Typography variant="body2">
                {details.recommendations}
              </Typography>
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const renderEthicsCheckDetails = (details: EthicsCheckResult) => {
    return (
      <Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Результат проверки этики:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <Chip 
              label={`Оценка этики: ${details.ethics_score.toFixed(1)}`} 
              size="small" 
              color={details.ethics_score >= 80 ? 'success' : details.ethics_score >= 60 ? 'warning' : 'error'}
            />
            <Chip 
              label={details.is_approved ? 'Одобрено' : 'Требует доработки'} 
              size="small" 
              color={details.is_approved ? 'success' : 'error'}
            />
          </Box>
        </Box>
        
        {details.violations_found && details.violations_found.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Найденные нарушения:
            </Typography>
            <List dense>
              {details.violations_found.map((violation, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Error color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={violation.type}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          {violation.description}
                        </Typography>
                        <Chip 
                          label={violation.severity} 
                          size="small" 
                          color={violation.severity === 'high' ? 'error' : violation.severity === 'medium' ? 'warning' : 'default'}
                        />
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
        
        {details.recommendations && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Рекомендации:
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'warning.50', borderRadius: 1, border: '1px solid', borderColor: 'warning.300' }}>
              <Typography variant="body2">
                {details.recommendations}
              </Typography>
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const renderTerminologyCheckDetails = (details: TerminologyCheckResult) => {
    return (
      <Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Результат проверки терминологии:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <Chip label={`Точность: ${(details.accuracy_score * 100).toFixed(1)}%`} size="small" />
            <Chip label={`Терминов найдено: ${details.terms_used.length}`} size="small" />
          </Box>
        </Box>
        
        {details.incorrect_terms && details.incorrect_terms.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Неправильные термины:
            </Typography>
            <List dense>
              {details.incorrect_terms.map((term, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Error color="error" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`"${term.term}"`}
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          Проблема: {term.issue}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Позиция: {term.position}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
        
        {details.suggestions && details.suggestions.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Предложения по улучшению:
            </Typography>
            <List dense>
              {details.suggestions.map((suggestion, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Info color="info" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`"${suggestion.term}" → "${suggestion.suggestion}"`}
                    secondary={`Уверенность: ${(suggestion.confidence * 100).toFixed(1)}%`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {getStatusIcon()}
          <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
            {title}
          </Typography>
          <Chip 
            label={result.status} 
            color={getStatusColor() as any}
            size="small"
            sx={{ mr: 1 }}
          />
          {result.score !== undefined && (
            <Chip 
              label={`${result.score}%`} 
              color={getScoreColor(result.score) as any}
              size="small"
              sx={{ mr: 1 }}
            />
          )}
          {onRunCheck && result.status === 'pending' && (
            <Chip 
              label="Запустить" 
              color="primary"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onRunCheck();
              }}
              icon={<PlayArrow />}
            />
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        {result.status === 'running' && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Выполняется проверка...
            </Typography>
            <LinearProgress />
          </Box>
        )}
        
        {result.status === 'completed' && (
          <Box>
            {/* Отображаем детальную информацию в зависимости от типа проверки */}
            {result.details && (
              <>
                {title.includes('орфографи') && renderSpellCheckDetails(result.details as SpellCheckResult)}
                {title.includes('стил') && renderStyleAnalysisDetails(result.details as StyleAnalysisResult)}
                {title.includes('этик') && renderEthicsCheckDetails(result.details as EthicsCheckResult)}
                {title.includes('терминолог') && renderTerminologyCheckDetails(result.details as TerminologyCheckResult)}
              </>
            )}
            
            {/* Fallback для старых данных */}
            {!result.details && result.issues && result.issues.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Найденные проблемы:
                </Typography>
                {renderIssues(result.issues)}
              </Box>
            )}
            
            {!result.details && result.suggestions && result.suggestions.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Рекомендации:
                </Typography>
                <List dense>
                  {result.suggestions.map((suggestion, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircleOutline color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={suggestion} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
            
            {result.completed_at && (
              <Typography variant="caption" color="text.secondary">
                Завершено: {new Date(result.completed_at).toLocaleString()}
              </Typography>
            )}
          </Box>
        )}
        
        {result.status === 'failed' && (
          <Typography variant="body2" color="error">
            Ошибка при выполнении проверки
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
};

export default CheckResult;
