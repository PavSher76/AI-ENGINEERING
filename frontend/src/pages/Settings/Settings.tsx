import React from 'react';

const Settings: React.FC = () => {
  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>⚙️ Настройки системы</h1>
        <p>Конфигурация и управление системой</p>
      </div>
      
      <div className="settings-container">
        <div className="settings-placeholder">
          <div className="placeholder-icon">🔧</div>
          <h2>Настройки</h2>
          <p>Модуль находится в разработке</p>
          <p>Здесь будет система настроек и конфигурации</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;