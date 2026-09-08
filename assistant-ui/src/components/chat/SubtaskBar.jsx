import React from 'react';
import './SubtaskBar.css';

const SubtaskBar = ({ subtasks = [], isRunning }) => {
  if (subtasks.length === 0 || !isRunning) return null;

  return (
    <div className="subtask-bar">
      {subtasks.map((task, idx) => {
        // Simplified completion logic for visual display
        const isCompleted = false; // Could be wired to actual completion later
        
        return (
          <div key={idx} className={`subtask-pill ${isCompleted ? 'completed' : ''}`}>
            <span className="subtask-icon">{isCompleted ? '✓' : '🔹'}</span>
            <span>{task}</span>
          </div>
        );
      })}
    </div>
  );
};

export default SubtaskBar;
