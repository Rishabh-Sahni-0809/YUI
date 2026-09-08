import React from 'react';
import ActionPill from './ActionPill';
import './MessageBubble.css';

const MessageBubble = ({ msg }) => {
  const isUser = msg.role === 'user';
  
  return (
    <div className={`message-bubble-wrapper ${isUser ? 'user' : 'yui'}`}>
      <div className={`message-bubble ${!msg.text ? 'actions-only' : ''}`}>
        {msg.text && <div className="message-text">{msg.text}</div>}
        
        {/* Render inline action pills if available */}
        {msg.actions && msg.actions.length > 0 && (
          <div className="action-pill-container">
            {msg.actions.map((action, i) => (
              <ActionPill 
                key={i} 
                tool={action.tool} 
                label={action.label} 
                url={action.url} 
                status={action.status} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
