import React from 'react';
import './RightDrawer.css';

const RightDrawer = ({ isOpen, onClose }) => {
  return (
    <div className={`right-drawer ${isOpen ? 'open' : ''}`}>
      <div className="drawer-header">
        <span className="drawer-title">Data Output</span>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>
      <div className="drawer-content">
        {/* Placeholder for Data output like Charts/Tables */}
        <div className="placeholder-chart">
          <span>Chart Data Will Appear Here</span>
        </div>
      </div>
    </div>
  );
};

export default RightDrawer;
