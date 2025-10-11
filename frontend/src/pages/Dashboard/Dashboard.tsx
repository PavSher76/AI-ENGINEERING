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
      url: 'https://localhost:9300',
      port: 9300,
      description: 'Веб-интерфейс системы'
    },
    {
      name: 'Nginx',
      url: 'http://localhost:9081',
      port: 9081,
      description: 'Reverse proxy и статический сервер'
    },
    {
      name: 'Keycloak',
      url: 'https://localhost:9080',
      port: 9080,
      description: 'Система авторизации'
    },
    {
      name: 'PostgreSQL',
      url: 'https://localhost:9543',
      port: 9543,
      description: 'Основная база данных'
    },
    {
      name: 'Redis',
      url: 'https://localhost:9637',
      port: 9637,
      description: 'Кэширование и сессии'
    },
    {
      name: 'Qdrant',
      url: 'https://localhost:9633',
      port: 9633,
      description: 'Векторная база данных'
    },
    {
      name: 'MinIO',
      url: 'https://localhost:9900',
      port: 9900,
      description: 'Файловое хранилище'
    },
    {
      name: 'RabbitMQ',
      url: 'https://localhost:9568',
      port: 9568,
      description: 'Очереди сообщений'
    },
    {
      name: 'Ollama Service',
      url: 'http://localhost:9012',
      port: 9012,
      description: 'AI модели сервис'
    },
    {
      name: 'RAG Service',
      url: 'http://localhost:9001',
      port: 9001,
      description: 'Сервис векторного поиска'
    },
    {
      name: 'Chat Service',
      url: 'http://localhost:9003',
      port: 9003,
      description: 'Сервис чата с ИИ'
    },
    {
      name: 'Consultation Service',
      url: 'http://localhost:9004',
      port: 9004,
      description: 'Консультации по НТД'
    },
    {
      name: 'Archive Service',
      url: 'http://localhost:9005',
      port: 9005,
      description: 'Архив и объекты аналоги'
    },
    {
      name: 'Calculation Service',
      url: 'http://localhost:9006',
      port: 9006,
      description: 'Инженерные расчеты'
    },
    {
      name: 'Validation Service',
      url: 'http://localhost:9007',
      port: 9007,
      description: 'Валидация данных'
    },
    {
      name: 'Document Service',
      url: 'http://localhost:9008',
      port: 9008,
      description: 'Управление документами'
    },
    {
      name: 'Analytics Service',
      url: 'http://localhost:9009',
      port: 9009,
      description: 'Аналитика проектов'
    },
    {
      name: 'Integration Service',
      url: 'http://localhost:9010',
      port: 9010,
      description: 'Интеграции с PLM'
    },
    {
      name: 'Outgoing Control Service',
      url: 'http://localhost:9011',
      port: 9011,
      description: 'Выходной контроль документов'
    },
    {
      name: 'QR Validation Service',
      url: 'http://localhost:9013',
      port: 9013,
      description: 'Валидация QR кодов'
    },
    {
      name: 'TechExpert Connector',
      url: 'http://localhost:9014',
      port: 9014,
      description: 'Коннектор TechExpert'
    }
  ];

  const checkServiceStatus = async (service: Omit<ServiceStatus, 'status' | 'lastCheck'>): Promise<ServiceStatus> => {
    try {
      // Для некоторых сервисов используем специальные endpoints
      let healthUrl = `${service.url}/health`;
      
      // Специальные случаи для сервисов, которые не имеют /health endpoint
      if (service.name === 'Frontend') {
        healthUrl = service.url;
      } else if (service.name === 'Keycloak') {
        // Keycloak имеет проблемы с SSL, помечаем как warning
        return {
          ...service,
          status: 'warning',
          lastCheck: new Date().toLocaleTimeString()
        };
      } else if (service.name === 'PostgreSQL' || service.name === 'Redis' || service.name === 'Qdrant' || service.name === 'MinIO' || service.name === 'RabbitMQ' || service.name === 'Nginx' || service.name === 'TechExpert Connector') {
        // Эти сервисы не имеют HTTP endpoints или имеют CORS проблемы, помечаем как unknown
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
      
      // Для сервисов с CORS проблемами или недоступных помечаем как warning
      if (service.name === 'MinIO' || service.name === 'RabbitMQ' || service.name === 'Qdrant' || 
          service.name === 'PostgreSQL' || service.name === 'Redis' || service.name === 'Keycloak' ||
          service.name === 'TechExpert Connector') {
        return {
          ...service,
          status: 'warning',
          lastCheck: new Date().toLocaleTimeString()
        };
      }
      
      // Для основных сервисов помечаем как error
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