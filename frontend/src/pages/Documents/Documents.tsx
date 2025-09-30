import React from 'react';

const Documents: React.FC = () => {
  return (
    <div className="documents-page">
      <div className="page-header">
        <h1>📄 Управление документами</h1>
        <p>Система управления проектной и рабочей документацией</p>
      </div>
      
      <div className="documents-container">
        <div className="documents-placeholder">
          <div className="placeholder-icon">📋</div>
          <h2>Управление документами</h2>
          <p>Модуль находится в разработке</p>
          <p>Здесь будет система управления документами и их версиями</p>
        </div>
      </div>
    </div>
  );
};

export default Documents;