import React, { useState } from 'react';
import { ErrorInfo } from '../../utils/errorHandler';
import './ErrorDisplay.css';

interface ErrorDisplayProps {
  error: ErrorInfo | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  showDetails = false
}) => {
  const [showFullDetails, setShowFullDetails] = useState(false);

  if (!error) return null;

  const getErrorIcon = (type: string) => {
    switch (type) {
      case 'network':
        return '🌐';
      case 'server':
        return '🖥️';
      case 'validation':
        return '⚠️';
      case 'file':
        return '📁';
      case 'auth':
        return '🔐';
      case 'timeout':
        return '⏱️';
      default:
        return '❌';
    }
  };

  const getErrorColor = (type: string) => {
    switch (type) {
      case 'network':
        return '#ff6b6b';
      case 'server':
        return '#ffa726';
      case 'validation':
        return '#ff9800';
      case 'file':
        return '#9c27b0';
      case 'auth':
        return '#f44336';
      case 'timeout':
        return '#607d8b';
      default:
        return '#f44336';
    }
  };

  return (
    <div className="error-display" style={{ borderColor: getErrorColor(error.type) }}>
      <div className="error-header">
        <div className="error-icon">
          {getErrorIcon(error.type)}
        </div>
        <div className="error-content">
          <div className="error-title">
            {error.userMessage}
          </div>
          <div className="error-suggestion">
            {error.suggestion}
          </div>
        </div>
        <div className="error-actions">
          {onDismiss && (
            <button
              className="error-dismiss-btn"
              onClick={onDismiss}
              title="Закрыть"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {showDetails && (
        <div className="error-details">
          <button
            className="error-details-toggle"
            onClick={() => setShowFullDetails(!showFullDetails)}
          >
            {showFullDetails ? 'Скрыть детали' : 'Показать детали'}
          </button>
          
          {showFullDetails && (
            <div className="error-details-content">
              <div className="error-detail-item">
                <strong>Тип ошибки:</strong> {error.type}
              </div>
              {error.code && (
                <div className="error-detail-item">
                  <strong>Код:</strong> {error.code}
                </div>
              )}
              <div className="error-detail-item">
                <strong>Сообщение:</strong> {error.message}
              </div>
              {error.details && (
                <div className="error-detail-item">
                  <strong>Детали:</strong>
                  <pre className="error-details-json">
                    {JSON.stringify(error.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {error.canRetry && onRetry && (
        <div className="error-retry">
          <button
            className="error-retry-btn"
            onClick={onRetry}
          >
            🔄 Попробовать снова
          </button>
          {error.retryDelay && (
            <span className="error-retry-delay">
              (автоматически через {error.retryDelay / 1000}с)
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default ErrorDisplay;
