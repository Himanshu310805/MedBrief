import React, { useEffect, useState } from 'react';
import { Activity, CheckCircle, BrainCircuit } from 'lucide-react';
import './ProcessingState.css';

const DEFAULT_STEPS = [
  "Extracting text from report document...",
  "Normalizing clinical abbreviations & RxNorm terms...",
  "Extracting medical entities (NER & Demographics)...",
  "Generating extractive & abstractive summaries...",
  "Assembling verified structured report..."
];

export default function ProcessingState({ stepIndex = 0, statusText = null }) {
  const [progressPercent, setProgressPercent] = useState(15);

  useEffect(() => {
    // Target percent based on step index (0 -> 20%, 1 -> 40%, 2 -> 60%, 3 -> 80%, 4 -> 95%)
    const targetPercent = Math.min(95, (stepIndex + 1) * 20);

    const timer = setInterval(() => {
      setProgressPercent((prev) => {
        if (prev < targetPercent) {
          return prev + 2;
        }
        return prev;
      });
    }, 50);

    return () => clearInterval(timer);
  }, [stepIndex]);

  const displayStatus = statusText || DEFAULT_STEPS[stepIndex] || "Processing medical report...";

  return (
    <div className="processing-container card-base fade-in">
      <div className="processing-header">
        <div className="processing-icon-circle">
          <BrainCircuit size={32} className="pulse-icon" />
        </div>
        <h2 className="processing-title">Analyzing Medical Report</h2>
        <p className="processing-subtitle">Our hybrid NLP pipeline is processing your clinical report in real-time</p>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar-wrapper">
        <div className="progress-bar-track">
          <div
            className="progress-bar-fill"
            style={{ width: `${Math.min(100, progressPercent)}%` }}
          ></div>
        </div>
        <div className="progress-label-row">
          <span className="current-status-text">{displayStatus}</span>
          <span className="progress-percentage">{Math.min(100, progressPercent)}%</span>
        </div>
      </div>

      {/* Step List Breakdown */}
      <div className="pipeline-steps-grid">
        {DEFAULT_STEPS.map((step, idx) => {
          const isDone = idx < stepIndex;
          const isCurrent = idx === stepIndex;
          return (
            <div
              key={idx}
              className={`step-item ${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}`}
            >
              <div className="step-icon">
                {isDone ? (
                  <CheckCircle size={16} className="green-check" />
                ) : isCurrent ? (
                  <Activity size={16} className="blue-spinner" />
                ) : (
                  <span className="step-num">{idx + 1}</span>
                )}
              </div>
              <span className="step-name">{step.replace('...', '')}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
