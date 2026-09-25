import React from 'react';
import { BrainCircuit, ShieldCheck, FileSearch, Sparkles, Award } from 'lucide-react';
import './InfoPages.css';

export function HowItWorksPage({ onBack }) {
  return (
    <div className="info-page-container card-base fade-in">
      <div className="info-page-header">
        <div className="info-icon-circle blue">
          <BrainCircuit size={28} />
        </div>
        <h1>How MedBrief Works</h1>
        <p>A 5-Stage Zero-Hallucination Medical Summarization Pipeline</p>
      </div>

      <div className="pipeline-steps-flow">
        <div className="flow-card">
          <div className="step-badge">Stage 1</div>
          <h3>Medical Text Normalization</h3>
          <p>Expands clinical abbreviations (e.g., "exertional dyspnea (DOE)", "Lisinopril") and normalizes punctuation.</p>
        </div>

        <div className="flow-card">
          <div className="step-badge">Stage 2</div>
          <h3>Clinical Entity & Demographic Extraction</h3>
          <p>Uses spaCy NER and hybrid regex rules to extract patient age, gender, symptoms, diagnoses, medications, and lab findings.</p>
        </div>

        <div className="flow-card">
          <div className="step-badge">Stage 3</div>
          <h3>Extractive Summarization</h3>
          <p>Ranks verbatim source sentences using TextRank graph algorithms and PageRank sentence scoring.</p>
        </div>

        <div className="flow-card">
          <div className="step-badge">Stage 4</div>
          <h3>Abstractive AI Summarization</h3>
          <p>Generates fluent, natural clinical narrative summaries using pretrained transformer models (DistilBART-CNN).</p>
        </div>

        <div className="flow-card highlight">
          <div className="step-badge green">Stage 5</div>
          <h3>Faithfulness Verification</h3>
          <p>Cross-verifies all extracted sections against source document text to guarantee zero-hallucination outputs.</p>
        </div>
      </div>

      <div className="info-action-row">
        <button className="btn-primary" onClick={onBack}>Try MedBrief Summarizer</button>
      </div>
    </div>
  );
}

export function AboutPage({ onBack }) {
  return (
    <div className="info-page-container card-base fade-in">
      <div className="info-page-header">
        <div className="info-icon-circle green">
          <Award size={28} />
        </div>
        <h1>About MedBrief Project</h1>
        <p>NLP Mini Project — Structured Clinical Summarization System</p>
      </div>

      <div className="about-content-body">
        <p>
          MedBrief is a specialized Natural Language Processing application designed to process complex electronic health records (EHR), physician notes, and laboratory findings.
        </p>
        <div className="feature-bullets">
          <div className="bullet-item">
            <ShieldCheck size={20} className="green" />
            <div>
              <strong>Zero-Hallucination Assembly:</strong> Deterministic section mapping ensures clinical data is never invented.
            </div>
          </div>
          <div className="bullet-item">
            <Sparkles size={20} className="blue" />
            <div>
              <strong>Dual Summarization:</strong> Combines verbatim Extractive TextRank with fluent Abstractive DistilBART summaries.
            </div>
          </div>
          <div className="bullet-item">
            <FileSearch size={20} className="blue" />
            <div>
              <strong>Academic Metric ROUGE Evaluation:</strong> Supports ROUGE-1, ROUGE-2, and ROUGE-L scoring against reference summaries.
            </div>
          </div>
        </div>
      </div>

      <div className="info-action-row">
        <button className="btn-primary" onClick={onBack}>Return to Summarizer</button>
      </div>
    </div>
  );
}
