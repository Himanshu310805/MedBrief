import React from 'react';
import { AlertTriangle, RotateCcw, ArrowLeft } from 'lucide-react';
import './ErrorCard.css';

export default function ErrorCard({ title = "Analysis Failed", message, onRetry, onReset }) {
  return (
    <div className="error-card-container card-base fade-in">
      <div className="error-card-header">
        <div className="error-icon-circle">
          <AlertTriangle size={28} />
        </div>
        <h3 className="error-card-title">{title}</h3>
      </div>
      
      <p className="error-card-message">{message || "An unexpected error occurred while processing the report."}</p>

      <div className="error-card-actions">
        {onRetry && (
          <button type="button" className="btn-primary retry-btn" onClick={onRetry}>
            <RotateCcw size={16} />
            <span>Try Again</span>
          </button>
        )}
        {onReset && (
          <button type="button" className="btn-secondary reset-error-btn" onClick={onReset}>
            <ArrowLeft size={16} />
            <span>Back to Upload</span>
          </button>
        )}
      </div>
    </div>
  );
}
