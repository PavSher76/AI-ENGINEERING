import React from 'react';
import './Header.css';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <button className="menu-button" onClick={onMenuClick}>
            <svg className="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="header-title">
            <h1>AI Engineering Platform</h1>
            <span className="header-subtitle">Инженерная платформа с поддержкой ИИ</span>
          </div>
        </div>
        <div className="header-right">
          <div className="header-status">
            <div className="status-indicator">
              <span className="status-dot success"></span>
              <span>Система работает</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;