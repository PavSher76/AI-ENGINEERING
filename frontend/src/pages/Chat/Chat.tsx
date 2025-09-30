import React from 'react';
import './Chat.css';

const Chat: React.FC = () => {
  return (
    <div className="chat-page">
      <div className="page-header">
        <h1>💬 Чат с ИИ</h1>
        <p>Интерфейс для общения с искусственным интеллектом</p>
      </div>
      
      <div className="chat-container">
        <div className="chat-placeholder">
          <div className="placeholder-icon">🤖</div>
          <h2>Чат с ИИ</h2>
          <p>Модуль находится в разработке</p>
          <p>Здесь будет интерфейс для общения с ИИ через vLLM</p>
        </div>
      </div>
    </div>
  );
};

export default Chat;