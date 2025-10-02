import React, { useState, useEffect } from 'react';
import './Dashboard.css';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  url: string;
  port: number;
  description: string;
  lastCheck: string;
}

const Dashboard: React.FC = () => {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const serviceList: Omit<ServiceStatus, 'status' | 'lastCheck'>[] = [
    {
      name: 'Frontend',
      url: 'https://localhost',
      port: 443,
      description: 'Веб-интерфейс системы'
    },
    {
      name: 'Nginx',
      url: 'https://localhost',
      port: 443,
      description: 'Reverse proxy и статический сервер'
    },
    {
      name: 'Keycloak',
      url: 'https://localhost:8080',
      port: 8080,
      description: 'Система авторизации'
    },
    {
      name: 'PostgreSQL',
      url: 'https://localhost',
      port: 5432,
      description: 'Основная база данных'
    },
    {
      name: 'Redis',
      url: 'https://localhost',
      port: 6379,
      description: 'Кэширование и сессии'
    },
    {
      name: 'Qdrant',
      url: 'https://localhost:6333',
      port: 6333,
      description: 'Векторная база данных'
    },
    {
      name: 'MinIO',
      url: 'https://localhost:9001',
      port: 9001,
      description: 'Файловое хранилище'
    },
    {
      name: 'RabbitMQ',
      url: 'https://localhost:15672',
      port: 15672,
      description: 'Очереди сообщений'
    },
    {
      name: 'Ollama',
      url: 'https://localhost:11434',
      port: 11434,
      description: 'AI модели (локально)'
    },
    {
      name: 'vLLM',
      url: 'https://localhost:8002',
      port: 8002,
      description: 'Высокопроизводительный LLM сервер'
    },
    {
      name: 'RAG Service',
      url: 'https://localhost/api/rag',
      port: 443,
      description: 'Сервис векторного поиска'
    },
    {
      name: 'Chat Service',
      url: 'https://localhost/api/chat',
      port: 443,
      description: 'Сервис чата с ИИ'
    },
    {
      name: 'Consultation Service',
      url: 'https://localhost/api/consultation',
      port: 443,
      description: 'Консультации по НТД'
    },
    {
      name: 'Archive Service',
      url: 'https://localhost/api/archive',
      port: 443,
      description: 'Архив и объекты аналоги'
    },
    {
      name: 'Calculation Service',
      url: 'https://localhost/api/calculation',
      port: 443,
      description: 'Инженерные расчеты'
    },
    {
      name: 'Validation Service',
      url: 'https://localhost/api/validation',
      port: 443,
      description: 'Валидация данных'
    },
    {
      name: 'Document Service',
      url: 'https://localhost/api/document',
      port: 443,
      description: 'Управление документами'
    },
    {
      name: 'Analytics Service',
      url: 'https://localhost/api/analytics',
      port: 443,
      description: 'Аналитика проектов'
    },
    {
      name: 'Integration Service',
      url: 'https://localhost/api/integration',
      port: 443,
      description: 'Интеграции с PLM'
    },
    {
      name: 'Outgoing Control Service',
      url: 'https://localhost/api/outgoing-control',
      port: 443,
      description: 'Выходной контроль документов'
    },
    {
      name: 'QR Validation Service',
      url: 'https://localhost/api/qr-validation',
      port: 443,
      description: 'Валидация QR кодов'
    }
  ];

  const checkServiceStatus = async (service: Omit<ServiceStatus, 'status' | 'lastCheck'>): Promise<ServiceStatus> => {
    try {
      // Для некоторых сервисов используем специальные endpoints
      let healthUrl = `${service.url}/health`;
      
      // Специальные случаи для сервисов, которые не имеют /health endpoint
      if (service.name === 'Frontend' || service.name === 'Nginx') {
        healthUrl = service.url;
      } else if (service.name === 'Keycloak') {
        healthUrl = `${service.url}/realms/ai-engineering/.well-known/openid-configuration`;
      } else if (service.name === 'PostgreSQL' || service.name === 'Redis') {
        // Эти сервисы не имеют HTTP endpoints, помечаем как unknown
        return {
          ...service,
          status: 'unknown',
          lastCheck: new Date().toLocaleTimeString()
        };
      } else if (service.name === 'vLLM' || service.name === 'Ollama') {
        // Эти сервисы могут быть не запущены, помечаем как unknown
        return {
          ...service,
          status: 'unknown',
          lastCheck: new Date().toLocaleTimeString()
        };
      }

      const response = await fetch(healthUrl, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (response.ok) {
        return {
          ...service,
          status: 'healthy',
          lastCheck: new Date().toLocaleTimeString()
        };
      } else {
        return {
          ...service,
          status: 'warning',
          lastCheck: new Date().toLocaleTimeString()
        };
      }
    } catch (error) {
      console.warn(`Failed to check ${service.name}:`, error);
      
      // Для сервисов с CORS проблемами помечаем как warning вместо error
      if (service.name === 'MinIO' || service.name === 'RabbitMQ' || service.name === 'Qdrant') {
        return {
          ...service,
          status: 'warning',
          lastCheck: new Date().toLocaleTimeString()
        };
      }
      
      return {
        ...service,
        status: 'error',
        lastCheck: new Date().toLocaleTimeString()
      };
    }
  };

  const checkAllServices = async () => {
    setLoading(true);
    const promises = serviceList.map(service => checkServiceStatus(service));
    const results = await Promise.all(promises);
    setServices(results);
    setLastUpdate(new Date());
    setLoading(false);
  };

  useEffect(() => {
    checkAllServices();
    const interval = setInterval(checkAllServices, 30000); // Проверка каждые 30 секунд
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return '❓';
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'status-success';
      case 'warning':
        return 'status-warning';
      case 'error':
        return 'status-error';
      default:
        return 'status-info';
    }
  };

  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const warningCount = services.filter(s => s.status === 'warning').length;
  const errorCount = services.filter(s => s.status === 'error').length;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Дашборд системы</h1>
        <p>Мониторинг состояния всех сервисов и модулей</p>
        <div className="dashboard-actions">
          <button className="btn btn-primary" onClick={checkAllServices} disabled={loading}>
            {loading ? 'Проверка...' : 'Обновить'}
          </button>
          <span className="last-update">
            Последнее обновление: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-number">{healthyCount}</div>
            <div className="stat-label">Работают</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <div className="stat-number">{warningCount}</div>
            <div className="stat-label">Предупреждения</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">❌</div>
          <div className="stat-content">
            <div className="stat-number">{errorCount}</div>
            <div className="stat-label">Ошибки</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-number">{services.length}</div>
            <div className="stat-label">Всего сервисов</div>
          </div>
        </div>
      </div>

      <div className="services-grid">
        {services.map((service, index) => (
          <div key={index} className="service-card card">
            <div className="card-header">
              <div className="service-header">
                <h3 className="card-title">{service.name}</h3>
                <span className={`status ${getStatusClass(service.status)}`}>
                  <span className="status-icon">
                    {getStatusIcon(service.status)}
                  </span>
                  {service.status === 'healthy' ? 'Работает' : 
                   service.status === 'warning' ? 'Предупреждение' : 
                   service.status === 'error' ? 'Ошибка' : 'Неизвестно'}
                </span>
              </div>
            </div>
            <div className="card-body">
              <p className="service-description">{service.description}</p>
              <div className="service-details">
                <div className="detail-item">
                  <span className="detail-label">URL:</span>
                  <a href={service.url} target="_blank" rel="noopener noreferrer" className="detail-value">
                    {service.url}
                  </a>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Порт:</span>
                  <span className="detail-value">{service.port}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Последняя проверка:</span>
                  <span className="detail-value">{service.lastCheck}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;