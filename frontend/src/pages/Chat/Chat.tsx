import React, { useState, useRef, useEffect } from 'react';
import './Chat.css';
import api from '../../services/api.ts';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  files?: FileInfo[];
}

interface FileInfo {
  filename: string;
  file_type: string;
  file_size: number;
  content?: any;
}

interface LLMSettings {
  model: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  top_k: number;
  repeat_penalty: number;
  system_prompt: string;
  timeout: number;
}

interface ChatSettings {
  auto_save: boolean;
  show_timestamps: boolean;
  enable_file_upload: boolean;
  max_file_size_mb: number;
  allowed_file_types: string[];
  enable_ocr: boolean;
  ocr_language: string;
  export_format: string;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}`);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [llmSettings, setLlmSettings] = useState<LLMSettings>({
    model: 'llama3.1:8b',
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 0.9,
    top_k: 40,
    repeat_penalty: 1.1,
    system_prompt: '',
    timeout: 300
  });
  const [chatSettings, setChatSettings] = useState<ChatSettings>({
    auto_save: true,
    show_timestamps: true,
    enable_file_upload: true,
    max_file_size_mb: 100,
    allowed_file_types: ['pdf', 'docx', 'xls', 'xlsx', 'txt', 'md'],
    enable_ocr: true,
    ocr_language: 'rus+eng',
    export_format: 'docx'
  });
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('llama3.1:8b');
  const [error, setError] = useState<string>('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Загрузка настроек при инициализации
  useEffect(() => {
    loadSettings();
    loadAvailableOptions();
  }, []);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSettings = async () => {
    try {
      const [llmResponse, chatResponse] = await Promise.all([
        api.get('/chat/settings/llm'),
        api.get('/chat/settings/chat')
      ]);

      setLlmSettings(llmResponse.data);
      setChatSettings(chatResponse.data);
    } catch (err) {
      console.error('Ошибка загрузки настроек:', err);
    }
  };

  const loadAvailableOptions = async () => {
    try {
      const response = await api.get('/chat/settings/available');
      setAvailableModels(response.data.models || []);
      setAvailableLanguages(response.data.languages || []);
    } catch (err) {
      console.error('Ошибка загрузки опций:', err);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    // Проверяем размер файлов
    const maxSize = chatSettings.max_file_size_mb * 1024 * 1024;
    const oversizedFiles = files.filter(file => file.size > maxSize);
    
    if (oversizedFiles.length > 0) {
      setError(`Файлы превышают максимальный размер ${chatSettings.max_file_size_mb}MB: ${oversizedFiles.map(f => f.name).join(', ')}`);
      return;
    }

    // Проверяем типы файлов
    const allowedTypes = chatSettings.allowed_file_types;
    const invalidFiles = files.filter(file => {
      const extension = file.name.split('.').pop()?.toLowerCase();
      return !extension || !allowedTypes.includes(extension);
    });

    if (invalidFiles.length > 0) {
      setError(`Неподдерживаемые типы файлов: ${invalidFiles.map(f => f.name).join(', ')}`);
      return;
    }

    setUploadedFiles(prev => [...prev, ...files]);
    setError('');
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() && uploadedFiles.length === 0) return;

    setIsLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('message', inputMessage);
      formData.append('session_id', sessionId);

      // Добавляем файлы
      uploadedFiles.forEach(file => {
        formData.append('files', file);
      });

      const response = await api.post('/chat/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status === 200) {
        const data = response.data;
        
        // Добавляем сообщение пользователя
        const userMessage: Message = {
          role: 'user',
          content: inputMessage,
          timestamp: new Date().toISOString(),
          files: uploadedFiles.map(file => ({
            filename: file.name,
            file_type: file.type,
            file_size: file.size
          }))
        };

        // Добавляем ответ ИИ
        const aiMessage: Message = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage, aiMessage]);
        setInputMessage('');
        setUploadedFiles([]);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Ошибка отправки сообщения');
      }
    } catch (err) {
      setError('Ошибка подключения к сервису');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const updateLlmSettings = async () => {
    try {
      await api.put('/chat/settings/llm', llmSettings);
      setError('');
      alert('Настройки LLM обновлены');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка подключения к сервису');
    }
  };

  const updateChatSettings = async () => {
    try {
      await api.put('/chat/settings/chat', chatSettings);
      setError('');
      alert('Настройки чата обновлены');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка подключения к сервису');
    }
  };

  const exportChat = async (format: 'docx' | 'pdf') => {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('filename', `chat_${sessionId}.${format}`);

      const response = await api.post(`/chat/export/${format}`, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status === 200) {
        const blob = response.data;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_${sessionId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Ошибка экспорта чата');
      }
    } catch (err) {
      setError('Ошибка экспорта чата');
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ru-RU');
  };

  return (
    <div className="chat-page">
      <div className="page-header">
        <h1>💬 Чат с ИИ</h1>
        <p>Расширенный интерфейс для общения с искусственным интеллектом</p>
        <div className="header-actions">
          <button 
            className="btn-settings"
            onClick={() => setShowSettings(!showSettings)}
          >
            ⚙️ Настройки
          </button>
          <button 
            className="btn-export"
            onClick={() => exportChat(chatSettings.export_format as 'docx' | 'pdf')}
            disabled={messages.length === 0}
          >
            📄 Экспорт
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="chat-container">
        {/* Настройки */}
        {showSettings && (
          <div className="settings-panel">
            <div className="settings-section">
              <h3>Настройки LLM</h3>
              <div className="settings-grid">
                <div className="setting-item">
                  <label>Модель:</label>
                  <select 
                    value={llmSettings.model}
                    onChange={(e) => setLlmSettings(prev => ({ ...prev, model: e.target.value }))}
                  >
                    {availableModels.map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                </div>
                <div className="setting-item">
                  <label>Температура:</label>
                  <input 
                    type="range" 
                    min="0" 
                    max="2" 
                    step="0.1"
                    value={llmSettings.temperature}
                    onChange={(e) => setLlmSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  />
                  <span>{llmSettings.temperature}</span>
                </div>
                <div className="setting-item">
                  <label>Макс. токенов:</label>
                  <input 
                    type="number" 
                    min="1" 
                    max="8192"
                    value={llmSettings.max_tokens}
                    onChange={(e) => setLlmSettings(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                  />
                </div>
                <div className="setting-item">
                  <label>Таймаут (сек):</label>
                  <input 
                    type="number" 
                    min="30" 
                    max="1800"
                    value={llmSettings.timeout}
                    onChange={(e) => setLlmSettings(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                  />
                </div>
                <div className="setting-item">
                  <label>Системный промпт:</label>
                  <textarea 
                    value={llmSettings.system_prompt}
                    onChange={(e) => setLlmSettings(prev => ({ ...prev, system_prompt: e.target.value }))}
                    rows={3}
                  />
                </div>
              </div>
              <button onClick={updateLlmSettings} className="btn-save">
                Сохранить настройки LLM
              </button>
            </div>

            <div className="settings-section">
              <h3>Настройки чата</h3>
              <div className="settings-grid">
                <div className="setting-item">
                  <label>
                    <input 
                      type="checkbox"
                      checked={chatSettings.enable_file_upload}
                      onChange={(e) => setChatSettings(prev => ({ ...prev, enable_file_upload: e.target.checked }))}
                    />
                    Разрешить загрузку файлов
                  </label>
                </div>
                <div className="setting-item">
                  <label>
                    <input 
                      type="checkbox"
                      checked={chatSettings.enable_ocr}
                      onChange={(e) => setChatSettings(prev => ({ ...prev, enable_ocr: e.target.checked }))}
                    />
                    Включить OCR для PDF
                  </label>
                </div>
                <div className="setting-item">
                  <label>Язык OCR:</label>
                  <select 
                    value={chatSettings.ocr_language}
                    onChange={(e) => setChatSettings(prev => ({ ...prev, ocr_language: e.target.value }))}
                  >
                    {availableLanguages.map(lang => (
                      <option key={lang} value={lang}>{lang}</option>
                    ))}
                  </select>
                </div>
                <div className="setting-item">
                  <label>Формат экспорта:</label>
                  <select 
                    value={chatSettings.export_format}
                    onChange={(e) => setChatSettings(prev => ({ ...prev, export_format: e.target.value }))}
                  >
                    <option value="docx">DOCX</option>
                    <option value="pdf">PDF</option>
                  </select>
                </div>
              </div>
              <button onClick={updateChatSettings} className="btn-save">
                Сохранить настройки чата
              </button>
            </div>
          </div>
        )}

        {/* Сообщения */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon">🤖</div>
              <h2>Добро пожаловать в чат с ИИ!</h2>
              <p>Загружайте файлы, настраивайте параметры и общайтесь с искусственным интеллектом</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-header">
                  <span className="message-role">
                    {message.role === 'user' ? '👤 Вы' : '🤖 ИИ'}
                  </span>
                  {chatSettings.show_timestamps && (
                    <span className="message-time">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  )}
                </div>
                <div className="message-content">
                  {message.content}
                </div>
                {message.files && message.files.length > 0 && (
                  <div className="message-files">
                    <strong>Прикрепленные файлы:</strong>
                    {message.files.map((file, fileIndex) => (
                      <div key={fileIndex} className="file-info">
                        📎 {file.filename} ({(file.file_size / 1024).toFixed(1)} KB)
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Загруженные файлы */}
        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h4>Загруженные файлы:</h4>
            {uploadedFiles.map((file, index) => (
              <div key={index} className="file-item">
                <span>📎 {file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                <button onClick={() => removeFile(index)} className="btn-remove">
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Ввод сообщения */}
        <div className="input-container">
          <div className="input-actions">
            {chatSettings.enable_file_upload && (
              <button 
                className="btn-upload"
                onClick={() => fileInputRef.current?.click()}
              >
                📎 Загрузить файл
              </button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.xls,.xlsx,.txt,.md"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </div>
          
          {/* Быстрый выбор модели */}
          <div className="model-selector">
            <label>Модель:</label>
            <select 
              value={llmSettings.model}
              onChange={(e) => setLlmSettings(prev => ({ ...prev, model: e.target.value }))}
              disabled={isLoading}
            >
              {availableModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
            <span className="timeout-info">Таймаут: {llmSettings.timeout}с</span>
          </div>
          
          <div className="input-area">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите ваше сообщение..."
              rows={3}
              disabled={isLoading}
            />
            <button 
              onClick={sendMessage}
              disabled={isLoading || (!inputMessage.trim() && uploadedFiles.length === 0)}
              className="btn-send"
            >
              {isLoading ? '⏳' : '📤'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;