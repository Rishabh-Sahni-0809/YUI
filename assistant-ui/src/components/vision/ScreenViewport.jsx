import React from 'react';
import './ScreenViewport.css';

const ScreenViewport = ({ screenshotBase64, boundingBoxes = [], activeCursor, lastUpdated }) => {
  return (
    <div className="screen-viewport-container">
      <div className="viewport-header">
        <span className="header-title">📷 Screen Grounding</span>
        <span className="header-meta">{lastUpdated ? `last updated ${lastUpdated}` : 'waiting for feed...'}</span>
      </div>
      
      <div className="viewport-content">
        {screenshotBase64 ? (
          <div className="screenshot-wrapper">
            <img 
              key={screenshotBase64} 
              src={screenshotBase64} 
              alt="Live Screen" 
              className="screenshot-image animate-fade-in" 
            />
            
            {/* SVG overlay for bounding boxes */}
            <svg className="bounding-box-overlay" viewBox="0 0 1 1" preserveAspectRatio="none">
              {boundingBoxes.map((box, i) => {
                // Color mapping logic from spec
                let color = '#00D4AA'; // Default teal
                if (box.type === 'input') color = '#0EA5E9'; // Blue
                if (box.type === 'nav') color = '#A78BFA'; // Purple
                
                return (
                  <rect
                    key={i}
                    x={box.x}
                    y={box.y}
                    width={box.w}
                    height={box.h}
                    fill={`${color}99`} // 0.6 opacity
                    stroke={box.active ? '#FFFFFF' : color}
                    strokeWidth="0.002"
                    className={box.active ? 'box-active animate-pulse' : ''}
                  />
                );
              })}
              
              {/* Cursor indicator */}
              {activeCursor && (
                <circle 
                  cx={activeCursor.x} 
                  cy={activeCursor.y} 
                  r="0.005" 
                  fill="#FFFFFF" 
                  className="cursor-dot animate-pop-in"
                />
              )}
            </svg>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">🖥️</div>
            <p>No screen activity yet</p>
          </div>
        )}
      </div>
      
      <div className="viewport-controls">
        <button className="control-btn">[−]</button>
        <button className="control-btn">[+]</button>
        <button className="control-btn">[↔ fit]</button>
      </div>
    </div>
  );
};

export default ScreenViewport;
