import React from 'react';
import './Consultation.css';

const Consultation: React.FC = () => {
  return (
    <div className="consultation-page">
      <div className="page-header">
        <h1>📚 Консультации НТД</h1>
        <p>Консультации по нормативно-технической документации</p>
      </div>
      
      <div className="consultation-container">
        <div className="consultation-placeholder">
          <div className="placeholder-icon">📖</div>
          <h2>Консультации НТД</h2>
          <p>Модуль находится в разработке</p>
          <p>Здесь будет система консультаций по нормативно-технической документации</p>
        </div>
      </div>
    </div>
  );
};

export default Consultation;
