import React from 'react';
import './TitleBar.css';

const BACKEND_DISPLAY = {
  local_ollama: { label: 'Local · Ollama', className: 'provider-local' },
  local_openvino: { label: 'Local · OpenVINO', className: 'provider-local' },
  cloud_groq: { label: 'Cloud · Groq', className: 'provider-groq' },
  cloud_gemini: { label: 'Cloud · Gemini', className: 'provider-gemini' },
  unknown: { label: 'Waiting...', className: 'provider-unknown' },
};

const TitleBar = ({ activeTask, status = 'idle', routingStatus, cpuPercent, cpuState, activeView, onViewChange }) => {
  const backend = routingStatus?.backend || 'unknown';
  const display = BACKEND_DISPLAY[backend] || BACKEND_DISPLAY.unknown;
  const latency = routingStatus?.latency_ms ? `${Math.round(routingStatus.latency_ms)}ms` : '';

  return (
    <div className="titlebar">
      <div className="titlebar-left">
        <div className="brand">
          <span className="brand-logo">●</span>
          <span className="brand-name">Kira</span>
        </div>
        
        {/* View switcher */}
        <div className="view-tabs">
          <button 
            className={`view-tab ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => onViewChange('chat')}
          >
            💬 Chat
          </button>
          <button 
            className={`view-tab ${activeView === 'benchmark' ? 'active' : ''}`}
            onClick={() => onViewChange('benchmark')}
          >
            ⚡ Benchmark
          </button>
        </div>

        <div className="task-indicator">
          <span className={`status-dot ${status}`}>●</span>
          <span className="task-text">
            {status === 'running' ? `Running: ${activeTask}` : 'Idle'}
          </span>
        </div>
      </div>

      <div className="titlebar-right">
        {/* Dynamic backend badge */}
        <div className={`model-badge ${display.className}`}>
          <span className={`route-dot ${backend.startsWith('local') ? 'route-local' : 'route-cloud'}`}>●</span>
          {display.label}
          {latency && <span className="latency-tag">{latency}</span>}
        </div>
        
        <div className={`cpu-badge ${(cpuState === 'red') ? 'critical' : (cpuState === 'yellow') ? 'warning' : 'normal'}`}>
          CPU {Math.round(cpuPercent || 0)}%
        </div>
        
        <button className="settings-btn">⚙</button>
      </div>
    </div>
  );
};

export default TitleBar;
