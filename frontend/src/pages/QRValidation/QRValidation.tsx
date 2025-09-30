import React, { useState, useRef } from 'react';
import './QRValidation.css';

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
}

interface ValidationResult {
  is_valid: boolean;
  status: string;
  message: string;
  document_info?: QRDocument;
}

const QRValidation: React.FC = () => {
  const [qrData, setQrData] = useState<string>('');
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleQRDataChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQrData(e.target.value);
    setError('');
    setValidationResult(null);
  };

  const validateQRCode = async () => {
    if (!qrData.trim()) {
      setError('Введите данные QR-кода');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/qr-validation/qr/validate', {
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

      const response = await fetch('/api/qr-validation/qr/validate-image', {
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
      setError('Ошибка загрузки файла');
    } finally {
      setLoading(false);
    }
  };

  const generateQRCode = async () => {
    const documentId = prompt('Введите ID документа:');
    if (!documentId) return;

    const documentType = prompt('Введите тип документа (drawing, specification, statement, etc.):');
    if (!documentType) return;

    const projectId = prompt('Введите ID проекта:');
    if (!projectId) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/qr-validation/qr/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          document_type: documentType,
          project_id: projectId,
          version: '1.0',
          title: `Документ ${documentId}`,
          description: 'Автоматически сгенерированный документ',
          author: 'System'
        }),
      });

      const result = await response.json();

      if (response.ok) {
        alert(`QR-код успешно сгенерирован!\nПуть: ${result.qr_code_path}`);
        // Можно добавить скачивание QR-кода
        window.open(`/api/qr-validation/qr/download/${documentId}`, '_blank');
      } else {
        setError(result.detail || 'Ошибка генерации QR-кода');
      }
    } catch (err) {
      setError('Ошибка подключения к сервису');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return '#4CAF50';
      case 'invalid': return '#F44336';
      case 'obsolete': return '#FF9800';
      case 'rejected': return '#F44336';
      case 'archived': return '#9E9E9E';
      default: return '#2196F3';
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

  return (
    <div className="qr-validation">
      <div className="qr-validation-header">
        <h1>QR валидация РД</h1>
        <p>Генерация и валидация QR-кодов для рабочей документации</p>
      </div>

      <div className="qr-validation-content">
        <div className="qr-validation-section">
          <h2>Валидация QR-кода</h2>
          
          <div className="qr-input-section">
            <div className="qr-text-input">
              <label htmlFor="qr-data">Данные QR-кода:</label>
              <textarea
                id="qr-data"
                value={qrData}
                onChange={handleQRDataChange}
                placeholder="Вставьте данные QR-кода или отсканируйте код..."
                rows={4}
              />
            </div>

            <div className="qr-file-input">
              <label htmlFor="qr-file">Или загрузите изображение с QR-кодом:</label>
              <input
                ref={fileInputRef}
                type="file"
                id="qr-file"
                accept="image/*"
                onChange={handleFileUpload}
              />
            </div>

            <div className="qr-actions">
              <button 
                onClick={validateQRCode}
                disabled={loading || !qrData.trim()}
                className="btn-primary"
              >
                {loading ? 'Валидация...' : 'Валидировать QR-код'}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {validationResult && (
            <div className="validation-result">
              <h3>Результат валидации</h3>
              <div className="validation-status">
                <span 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(validationResult.status) }}
                >
                  {getStatusText(validationResult.status)}
                </span>
                <span className="validation-message">{validationResult.message}</span>
              </div>

              {validationResult.document_info && (
                <div className="document-info">
                  <h4>Информация о документе</h4>
                  <div className="document-details">
                    <div className="detail-row">
                      <span className="label">ID документа:</span>
                      <span className="value">{validationResult.document_info.document_id}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Тип документа:</span>
                      <span className="value">{validationResult.document_info.document_type}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">ID проекта:</span>
                      <span className="value">{validationResult.document_info.project_id}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Версия:</span>
                      <span className="value">{validationResult.document_info.version}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Статус:</span>
                      <span className="value">{validationResult.document_info.status}</span>
                    </div>
                    {validationResult.document_info.title && (
                      <div className="detail-row">
                        <span className="label">Название:</span>
                        <span className="value">{validationResult.document_info.title}</span>
                      </div>
                    )}
                    {validationResult.document_info.author && (
                      <div className="detail-row">
                        <span className="label">Автор:</span>
                        <span className="value">{validationResult.document_info.author}</span>
                      </div>
                    )}
                    <div className="detail-row">
                      <span className="label">Создан:</span>
                      <span className="value">
                        {new Date(validationResult.document_info.created_at).toLocaleString('ru-RU')}
                      </span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Обновлен:</span>
                      <span className="value">
                        {new Date(validationResult.document_info.updated_at).toLocaleString('ru-RU')}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="qr-validation-section">
          <h2>Генерация QR-кода</h2>
          <p>Создайте новый QR-код для документа РД</p>
          
          <button 
            onClick={generateQRCode}
            disabled={loading}
            className="btn-secondary"
          >
            {loading ? 'Генерация...' : 'Сгенерировать QR-код'}
          </button>
        </div>

        <div className="qr-validation-section">
          <h2>Статистика</h2>
          <p>Информация о QR-кодах и документах в системе</p>
          
          <button 
            onClick={async () => {
              try {
                const response = await fetch('/api/qr-validation/qr/stats');
                const stats = await response.json();
                alert(`Статистика:\nВсего документов: ${stats.total_documents}\nПо статусам: ${JSON.stringify(stats.documents_by_status, null, 2)}`);
              } catch (err) {
                setError('Ошибка получения статистики');
              }
            }}
            className="btn-secondary"
          >
            Получить статистику
          </button>
        </div>
      </div>
    </div>
  );
};

export default QRValidation;
