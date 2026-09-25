import React from 'react';
import { FileText, Sparkles, ShieldCheck, Activity, ArrowRight } from 'lucide-react';
import './Hero.css';

export default function Hero({ onGetStarted }) {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-pill-badge">
          <Sparkles size={14} className="sparkle-icon" />
          <span>Hybrid NLP & Clinical Summarization</span>
        </div>
        <h1 className="hero-title">
          Understand your medical reports <span className="highlight-text">faster & clearer.</span>
        </h1>
        <p className="hero-subtitle">
          Instantly transform long clinical records, lab findings, and discharge summaries 
          into structured, verified insights using state-of-the-art NLP models.
        </p>
        <div className="hero-cta-group">
          <button className="btn-primary hero-btn" onClick={onGetStarted}>
            <span>Analyze Report Now</span>
            <ArrowRight size={18} />
          </button>
          <div className="hero-trust-tag">
            <ShieldCheck size={16} className="shield-icon" />
            <span>100% Deterministic Verification & Privacy Assured</span>
          </div>
        </div>
      </div>

      <div className="hero-visual">
        <div className="hero-card-stack">
          {/* Card 1: Live Analytics Tile */}
          <div className="mini-stat-card card-top">
            <div className="stat-icon-bg green">
              <ShieldCheck size={18} />
            </div>
            <div>
              <div className="stat-label">Zero Hallucination</div>
              <div className="stat-val">100% Verifiable</div>
            </div>
          </div>

          {/* Center Document Graphic Card */}
          <div className="main-doc-illustration">
            <div className="doc-header">
              <FileText className="doc-icon" size={24} />
              <div className="doc-title-placeholder">
                <span className="doc-line-lg"></span>
                <span className="doc-line-sm"></span>
              </div>
              <span className="status-badge-verified">Verified</span>
            </div>
            <div className="doc-body-lines">
              <div className="doc-section-block">
                <span className="section-label-blue">SYMPTOMS</span>
                <span className="doc-line-full"></span>
                <span className="doc-line-75"></span>
              </div>
              <div className="doc-section-block">
                <section className="section-label-green">MEDICATIONS & PLAN</section>
                <span className="doc-line-full"></span>
                <span className="doc-line-50"></span>
              </div>
            </div>
          </div>

          {/* Card 3: Model Performance Tile */}
          <div className="mini-stat-card card-bottom">
            <div className="stat-icon-bg blue">
              <Activity size={18} />
            </div>
            <div>
              <div className="stat-label">AI Processing Speed</div>
              <div className="stat-val">&lt; 8.0 Seconds</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
