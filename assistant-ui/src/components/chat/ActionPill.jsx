import React from 'react';
import './ActionPill.css';

const ToolIcons = {
  navigate: '🌐',
  click: '🖱',
  type: '🖊',
  hotkey: '⌨️',
  vision: '👁',
  wait: '⏱',
  app: '🚀',
  result: '✓',
  default: '⚡'
};

const ActionPill = ({ tool = 'default', label, url, status = 'success' }) => {
  // Try to extract value if the label has a structure like "Wait: 0.5s" or "Hotkey: win"
  let displayLabel = label;
  let displayValue = '';

  const colonIdx = label.indexOf(':');
  if (colonIdx > -1) {
    displayLabel = label.substring(0, colonIdx).trim();
    displayValue = label.substring(colonIdx + 1).trim();
  }

  return (
    <div className={`action-pill status-${status}`}>
      <span className="pill-icon">{ToolIcons[tool] || ToolIcons.default}</span>
      <div className="pill-content">
        <div className="pill-text-row">
          <span className="pill-label">{displayLabel}</span>
          {displayValue && <span className="pill-value">{displayValue}</span>}
        </div>
        {url && <span className="pill-url">{url}</span>}
      </div>
      <div className="pill-status-box">
        {status === 'pending' && <span className="spinner animate-spin">◷</span>}
        {status === 'success' && <span className="icon-success">[✓]</span>}
        {status === 'failed' && <span className="icon-failed">[✗]</span>}
        {status === 'retry' && <span className="icon-retry">[↻]</span>}
      </div>
    </div>
  );
};

export default ActionPill;
