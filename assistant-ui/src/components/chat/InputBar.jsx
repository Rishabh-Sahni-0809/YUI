import React, { useState } from 'react';
import './InputBar.css';

const InputBar = ({ onSend, isRunning }) => {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (text.trim() && !isRunning) {
      onSend(text);
      setText('');
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-bar-container">
      <button className="mic-btn">🎤</button>
      <textarea
        className="input-textarea"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Type a command..."
        rows={1}
        disabled={isRunning}
      />
      <button 
        className={`send-btn ${isRunning ? 'running' : ''}`} 
        onClick={handleSend}
        disabled={isRunning}
      >
        {isRunning ? <span className="spinner animate-spin">◷</span> : '→'}
      </button>
    </div>
  );
};

export default InputBar;
