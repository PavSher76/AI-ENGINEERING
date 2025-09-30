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
      url: 'http://localhost',
      port: 80,
      description: 'Веб-интерфейс системы'
    },
    {
      name: 'Nginx',
      url: 'http://localhost',
      port: 80,
      description: 'Reverse proxy и статический сервер'
    },
    {
      name: 'PostgreSQL',
      url: 'http://localhost',
      port: 5432,
      description: 'Основная база данных'
    },
    {
      name: 'Redis',
      url: 'http://localhost',
      port: 6379,
      description: 'Кэширование и сессии'
    },
    {
      name: 'Qdrant',
      url: 'http://localhost:6333',
      port: 6333,
      description: 'Векторная база данных'
    },
    {
      name: 'MinIO',
      url: 'http://localhost:9001',
      port: 9001,
      description: 'Файловое хранилище'
    },
    {
      name: 'RabbitMQ',
      url: 'http://localhost:15672',
      port: 15672,
      description: 'Очереди сообщений'
    },
    {
      name: 'Ollama',
      url: 'http://localhost:11434',
      port: 11434,
      description: 'AI модели (локально)'
    },
    {
      name: 'vLLM',
      url: 'http://localhost:8002',
      port: 8002,
      description: 'Высокопроизводительный LLM сервер'
    },
    {
      name: 'RAG Service',
      url: 'http://localhost:8001',
      port: 8001,
      description: 'Сервис векторного поиска'
    },
    {
      name: 'Chat Service',
      url: 'http://localhost:8003',
      port: 8003,
      description: 'Сервис чата с ИИ'
    },
    {
      name: 'Consultation Service',
      url: 'http://localhost:8004',
      port: 8004,
      description: 'Консультации по НТД'
    },
    {
      name: 'Archive Service',
      url: 'http://localhost:8005',
      port: 8005,
      description: 'Архив и объекты аналоги'
    },
    {
      name: 'Calculation Service',
      url: 'http://localhost:8006',
      port: 8006,
      description: 'Инженерные расчеты'
    },
    {
      name: 'Validation Service',
      url: 'http://localhost:8007',
      port: 8007,
      description: 'Валидация данных'
    },
    {
      name: 'Document Service',
      url: 'http://localhost:8008',
      port: 8008,
      description: 'Управление документами'
    },
    {
      name: 'Analytics Service',
      url: 'http://localhost:8009',
      port: 8009,
      description: 'Аналитика проектов'
    },
    {
      name: 'Integration Service',
      url: 'http://localhost:8010',
      port: 8010,
      description: 'Интеграции с PLM'
    },
    {
      name: 'Outgoing Control Service',
      url: 'http://localhost:8011',
      port: 8011,
      description: 'Выходной контроль документов'
    },
    {
      name: 'Ollama Management Service',
      url: 'http://localhost:8012',
      port: 8012,
      description: 'Управление моделями Ollama'
    }
  ];

  const checkServiceStatus = async (service: Omit<ServiceStatus, 'status' | 'lastCheck'>): Promise<ServiceStatus> => {
    try {
      const response = await fetch(`${service.url}/health`, {
        method: 'GET',
        timeout: 5000,
      } as any);
      
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