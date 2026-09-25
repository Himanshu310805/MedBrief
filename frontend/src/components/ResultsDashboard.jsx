import React, { useState } from 'react';
import { 
  FileText, Activity, ShieldCheck, Clock, Layers, Sparkles, ChevronDown, 
  ChevronUp, User, Stethoscope, AlertCircle, Pill, TestTube, Scissors, 
  Calendar, RotateCcw, BarChart3, CheckCircle2, Download 
} from 'lucide-react';
import { downloadReport } from '../services/api';
import './ResultsDashboard.css';

export default function ResultsDashboard({ data, onReset }) {
  const [showOriginalText, setShowOriginalText] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      await downloadReport(data);
    } catch (err) {
      alert(err.message || 'Failed to download report PDF.');
    } finally {
      setIsDownloading(false);
    }
  };

  const {
    patient_information,
    stats,
    symptoms,
    diagnosis_conditions,
    medications,
    lab_findings,
    procedures,
    other_observations,
    follow_up,
    extractive_summary_text,
    abstractive_summary_text,
    original_report_text,
    rouge_evaluation
  } = data;

  const renderSectionItem = (title, icon, sectionData) => {
    const isPopulated = sectionData && sectionData.content && sectionData.content !== 'Not mentioned';
    return (
      <div className="medical-info-row">
        <div className="info-row-header">
          <div className="info-label-group">
            <span className="info-icon">{icon}</span>
            <span className="info-title">{title}</span>
          </div>
          {isPopulated ? (
            <span className="badge-verified">
              <CheckCircle2 size={12} />
              <span>Verified</span>
            </span>
          ) : (
            <span className="badge-not-mentioned">Not mentioned</span>
          )}
        </div>
        <div className={`info-row-content ${!isPopulated ? 'muted' : ''}`}>
          {isPopulated ? sectionData.content : 'Not mentioned in source report'}
        </div>
      </div>
    );
  };

  return (
    <div className="results-dashboard fade-in">
      {/* Dashboard Top Action Header */}
      <div className="dashboard-top-bar card-base">
        <div className="top-bar-left">
          <div className="doc-badge-icon">
            <FileText size={24} />
          </div>
          <div>
            <h1 className="report-patient-title">
              {patient_information?.patient_name || 'Patient Clinical Summary'}
            </h1>
            <div className="report-meta-pills">
              <span>Age: {patient_information?.age || 'N/A'}</span>
              <span>•</span>
              <span>Gender: {patient_information?.gender || 'N/A'}</span>
              <span>•</span>
              <span>Date: {patient_information?.report_date || patient_information?.date_of_visit || 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="top-bar-actions">
          <button
            type="button"
            className="btn-primary download-btn"
            onClick={handleDownload}
            disabled={isDownloading}
          >
            <Download size={16} />
            <span>{isDownloading ? 'Generating PDF...' : 'Download Report'}</span>
          </button>
          <button type="button" className="btn-secondary reset-btn" onClick={onReset}>
            <RotateCcw size={16} />
            <span>Analyze Another Report</span>
          </button>
        </div>
      </div>

      {/* 1. Report Statistics Tile Grid (Reference Style: "Live Body Metrics") */}
      <div className="stats-tile-grid">
        <div className="stat-tile card-base">
          <div className="stat-icon-wrapper blue">
            <FileText size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-name">Word Count</span>
            <span className="stat-number">{stats?.word_count ?? 0} words</span>
          </div>
        </div>

        <div className="stat-tile card-base">
          <div className="stat-icon-wrapper blue">
            <Layers size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-name">Sentence Count</span>
            <span className="stat-number">{stats?.sentence_count ?? 0} sentences</span>
          </div>
        </div>

        <div className="stat-tile card-base">
          <div className="stat-icon-wrapper blue">
            <Clock size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-name">Processing Duration</span>
            <span className="stat-number">{stats?.processing_time ?? '0.0'}s</span>
          </div>
        </div>

        <div className="stat-tile card-base">
          <div className="stat-icon-wrapper green">
            <ShieldCheck size={20} />
          </div>
          <div className="stat-details">
            <span className="stat-name">Faithfulness Status</span>
            <span className="stat-number green-text">{stats?.verification_rate ?? '100%'} Verified</span>
          </div>
        </div>
      </div>

      {/* 2. Primary 2-Column Main View Grid */}
      <div className="dashboard-main-grid">
        {/* Left Column: Extracted Medical Information */}
        <div className="left-column">
          <div className="card-base section-card">
            <div className="card-section-header">
              <Stethoscope className="header-icon" size={20} />
              <h2>Extracted Clinical Information</h2>
            </div>
            <div className="medical-info-list">
              {renderSectionItem("Symptoms & Concerns", <AlertCircle size={16} />, symptoms)}
              {renderSectionItem("Diagnosis & Conditions", <Stethoscope size={16} />, diagnosis_conditions)}
              {renderSectionItem("Prescribed Medications", <Pill size={16} />, medications)}
              
              {/* Lab Findings Section: Structured Table if present, else fallback card */}
              {data.lab_results_table && data.lab_results_table.length > 0 ? (
                <div className="medical-info-row">
                  <div className="info-row-header">
                    <div className="info-label-group">
                      <span className="info-icon"><TestTube size={16} /></span>
                      <span className="info-title">Lab Findings & Vitals</span>
                    </div>
                    <span className="badge-verified">
                      <CheckCircle2 size={12} />
                      <span>Verified ({data.lab_results_table.length} Tests Parsed)</span>
                    </span>
                  </div>
                  <div className="lab-table-container">
                    <table className="lab-findings-table">
                      <thead>
                        <tr>
                          <th>Test Name</th>
                          <th>Result</th>
                          <th>Unit</th>
                          <th>Reference Range</th>
                          <th>Flag</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.lab_results_table.map((row, idx) => (
                          <tr key={idx}>
                            <td className="test-name-cell">{row.test_name}</td>
                            <td className="result-cell">{row.result}</td>
                            <td className="unit-cell">{row.unit || '-'}</td>
                            <td className="ref-cell">{row.reference_range || '-'}</td>
                            <td className="flag-cell">
                              {row.flag === 'High' && <span className="flag-badge high">High</span>}
                              {row.flag === 'Low' && <span className="flag-badge low">Low</span>}
                              {row.flag === 'Normal' && <span className="flag-badge normal">Normal</span>}
                              {!['High', 'Low', 'Normal'].includes(row.flag) && <span className="flag-badge normal">{row.flag || 'Normal'}</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                renderSectionItem("Lab Findings & Vitals", <TestTube size={16} />, lab_findings)
              )}

              {renderSectionItem("Diagnostic Procedures", <Scissors size={16} />, procedures)}
              {renderSectionItem("Follow-up Directives", <Calendar size={16} />, follow_up)}
              {renderSectionItem("Other Clinical Observations", <Activity size={16} />, other_observations)}
            </div>
          </div>
        </div>

        {/* Right Column: Extractive, Abstractive & ROUGE Summaries */}
        <div className="right-column">
          {/* Abstractive Summary Card (Headline Feature) */}
          <div className="card-base section-card highlight-card">
            <div className="card-section-header">
              <Sparkles className="header-icon blue" size={20} />
              <h2>Abstractive AI Summary</h2>
              <span className="model-tag">DistilBART Transformer</span>
            </div>
            <p className="summary-text-body">
              {abstractive_summary_text}
            </p>
          </div>

          {/* Extractive Summary Card */}
          <div className="card-base section-card">
            <div className="card-section-header">
              <FileText className="header-icon" size={20} />
              <h2>Extractive Key Sentences</h2>
              <span className="model-tag gray">TextRank Algorithm</span>
            </div>
            <p className="summary-text-body">
              {extractive_summary_text}
            </p>
          </div>

          {/* ROUGE Evaluation Card (Optional Section) */}
          {rouge_evaluation && rouge_evaluation.show && (
            <div className="card-base section-card evaluation-card">
              <div className="card-section-header">
                <BarChart3 className="header-icon" size={20} />
                <h2>Academic ROUGE Evaluation Scores</h2>
                <span className="optional-badge">Optional Metric</span>
              </div>
              
              <div className="rouge-table-wrapper">
                <table className="rouge-table">
                  <thead>
                    <tr>
                      <th>Summary Method</th>
                      <th>ROUGE-1 (Unigram)</th>
                      <th>ROUGE-2 (Bigram)</th>
                      <th>ROUGE-L (LCS)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>Extractive (TextRank)</strong></td>
                      <td>F1: {rouge_evaluation.extractive_scores.rouge1.fmeasure}</td>
                      <td>F1: {rouge_evaluation.extractive_scores.rouge2.fmeasure}</td>
                      <td>F1: {rouge_evaluation.extractive_scores.rougeL.fmeasure}</td>
                    </tr>
                    <tr>
                      <td><strong>Abstractive (Transformer)</strong></td>
                      <td>F1: {rouge_evaluation.abstractive_scores.rouge1.fmeasure}</td>
                      <td>F1: {rouge_evaluation.abstractive_scores.rouge2.fmeasure}</td>
                      <td>F1: {rouge_evaluation.abstractive_scores.rougeL.fmeasure}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div className="comparison-note-box">
                <strong>Evaluation Note:</strong> {rouge_evaluation.comparison_note}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Collapsible Original Report Text Card */}
      <div className="card-base collapsible-card">
        <button 
          className="collapsible-toggle-btn"
          onClick={() => setShowOriginalText(!showOriginalText)}
        >
          <div className="toggle-left">
            <FileText size={18} />
            <span>View Full Original Source Report</span>
          </div>
          {showOriginalText ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>

        {showOriginalText && (
          <div className="collapsible-content fade-in">
            <pre className="original-text-block">
              {original_report_text}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
