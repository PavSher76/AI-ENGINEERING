import React from 'react';
import { Link } from 'react-router-dom';
import './Sidebar.css';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentPath: string;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, currentPath }) => {
  const menuItems = [
    {
      path: '/',
      icon: '📊',
      title: 'Дашборд',
      description: 'Обзор системы'
    },
    {
      path: '/chat',
      icon: '💬',
      title: 'Чат с ИИ',
      description: 'Общение с ИИ'
    },
    {
      path: '/consultation',
      icon: '📚',
      title: 'Консультации НТД',
      description: 'Нормативно-техническая документация'
    },
    {
      path: '/archive',
      icon: '📁',
      title: 'Объекты аналоги',
      description: 'Архив и база данных'
    },
    {
      path: '/calculations',
      icon: '🧮',
      title: 'Инженерные расчеты',
      description: 'Вычисления и анализ'
    },
    {
      path: '/validation',
      icon: '✅',
      title: 'Проверка данных',
      description: 'Валидация входных данных'
    },
    {
      path: '/documents',
      icon: '📄',
      title: 'Документы',
      description: 'Управление документами'
    },
    {
      path: '/analytics',
      icon: '📈',
      title: 'Аналитика',
      description: 'Глубокая аналитика проектов'
    },
    {
      path: '/integration',
      icon: '🔗',
      title: 'Интеграции',
      description: 'PLM и внешние системы'
    },
    {
      path: '/outgoing-control',
      icon: '📤',
      title: 'Выходной контроль',
      description: 'Проверка исходящих документов'
    },
    {
      path: '/qr-validation',
      icon: '📱',
      title: 'QR валидация РД',
      description: 'Генерация и валидация QR-кодов'
    },
    {
      path: '/settings',
      icon: '⚙️',
      title: 'Настройки',
      description: 'Конфигурация системы'
    }
  ];

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onClose} />}
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <h2>Модули системы</h2>
          <button className="sidebar-close" onClick={onClose}>
            <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <nav className="sidebar-nav">
          <ul className="nav-list">
            {menuItems.map((item) => (
              <li key={item.path} className="nav-item">
                <Link
                  to={item.path}
                  className={`nav-link ${currentPath === item.path ? 'active' : ''}`}
                  onClick={onClose}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <div className="nav-content">
                    <span className="nav-title">{item.title}</span>
                    <span className="nav-description">{item.description}</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sidebar-footer">
          <div className="system-info">
            <div className="info-item">
              <span className="info-label">Версия:</span>
              <span className="info-value">1.0.0</span>
            </div>
            <div className="info-item">
              <span className="info-label">Статус:</span>
              <span className="status status-success">Активна</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;