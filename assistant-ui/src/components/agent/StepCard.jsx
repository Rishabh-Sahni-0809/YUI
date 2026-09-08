import React, { useState } from 'react';
import './StepCard.css';

const TypeIcons = {
  thought: '👁',
  action: '⚡',
  navigate: '🌐',
  vision: '🔍',
  os: '🖥',
  result: '✓',
};

const StepCard = ({ type = 'thought', status = 'success', content, command, retryCount = 0 }) => {
  const [expanded, setExpanded] = useState(false);

  // Map types to base colors
  const colorClass = `type-${type}`;
  const statusClass = `status-${status}`;

  // Parse UI-TARS style mock command if it's an action
  let displayCommand = command;
  if (type === 'action' && command) {
    const rawMatch = command.match(/\[AGENT(?::[^\]]+)?\]\s*(.*)/i);
    if (rawMatch) {
       displayCommand = rawMatch[1];
    }
  }

  return (
    <div className={`step-card ${colorClass} ${statusClass} ${status === 'running' ? 'animate-pulse-border' : ''} animate-slide-in`}>
      {/* Top Header section */}
      <div className="step-header" onClick={() => setExpanded(!expanded)}>
        <span className="step-icon">{TypeIcons[type] || '⚡'}</span>
        <span className="step-title">
          {type === 'thought' ? 'Thought' : type === 'action' ? 'Action' : type === 'result' ? 'Result' : 'Operation'}
        </span>
        
        <div className="step-status-badges">
          {retryCount > 0 && <span className="badge badge-retry">Retry {retryCount}/3</span>}
          {status === 'running' && <span className="spinner animate-spin">◷</span>}
          {status === 'success' && <span className="badge badge-success">Success</span>}
          {status === 'failed' && <span className="badge badge-failed">Failed</span>}
        </div>
      </div>
      
      {/* Dynamic Content Section */}
      <div className={`step-content ${type === 'thought' ? 'italic' : ''}`}>
        {type === 'action' ? (
          <div className="step-command-inline">
            <span className="cmd-keyword">{displayCommand?.split(':')[0]?.toUpperCase()}</span>
            {displayCommand?.includes(':') && (
              <>
                <span className="cmd-sep">|</span>
                <span className="cmd-val">value="{displayCommand?.split(':')[1]?.trim()}"</span>
              </>
            )}
          </div>
        ) : (
          content
        )}
      </div>
    </div>
  );
};

export default StepCard;
