import React, { useState, useEffect } from 'react';
import { 
  History, FileText, Download, Eye, Calendar, Sparkles, 
  Search, AlertCircle, Clock, CheckCircle2, User 
} from 'lucide-react';
import { getUserReports, downloadReport } from '../services/api';
import './ReportHistory.css';

export default function ReportHistory({ onViewReport, onAnalyzeNew }) {
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await getUserReports();
      if (res && res.reports) {
        setReports(res.reports);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load report history.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadPdf = async (report) => {
    if (!report.structured_summary) {
      alert('Detailed structured data is not available for this report.');
      return;
    }
    try {
      await downloadReport(report.structured_summary);
    } catch (err) {
      alert(err.message || 'Failed to download report PDF.');
    }
  };

  const filteredReports = reports.filter((r) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    const patient = (r.patient_name || '').toLowerCase();
    const abstractive = (r.abstractive_summary || '').toLowerCase();
    return patient.includes(term) || abstractive.includes(term);
  });

  return (
    <div className="report-history-container card-base fade-in">
      {/* Header Bar */}
      <div className="history-header">
        <div className="history-header-left">
          <div className="history-icon-wrapper">
            <History size={24} />
          </div>
          <div>
            <h2>My Saved Report History</h2>
            <p className="history-subtext">View and re-download your previously analyzed medical reports.</p>
          </div>
        </div>

        <button className="btn-primary analyze-new-btn" onClick={onAnalyzeNew}>
          <Sparkles size={16} />
          <span>Analyze New Report</span>
        </button>
      </div>

      {/* Search Filter Bar */}
      <div className="history-filter-bar">
        <div className="search-input-wrapper">
          <Search className="search-icon" size={18} />
          <input
            type="text"
            className="search-input"
            placeholder="Search report by patient name or summary keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <span className="reports-count-pill">
          {filteredReports.length} {filteredReports.length === 1 ? 'Report' : 'Reports'} Found
        </span>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="history-loading-state">
          <Clock className="spin-icon" size={32} />
          <p>Loading your saved report history from database...</p>
        </div>
      )}

      {/* Error State */}
      {errorMsg && (
        <div className="history-error-banner">
          <AlertCircle size={20} />
          <span>{errorMsg}</span>
          <button className="retry-btn" onClick={fetchHistory}>Retry</button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !errorMsg && filteredReports.length === 0 && (
        <div className="history-empty-state">
          <FileText size={48} className="empty-icon" />
          <h3>No Saved Reports Found</h3>
          <p>
            {searchTerm 
              ? 'No reports matched your search criteria.' 
              : 'You have not analyzed any medical reports yet. Analyze a report to save it here.'}
          </p>
          {!searchTerm && (
            <button className="btn-primary start-first-btn" onClick={onAnalyzeNew}>
              <Sparkles size={16} />
              <span>Analyze Your First Report</span>
            </button>
          )}
        </div>
      )}

      {/* Report Cards Grid */}
      {!isLoading && !errorMsg && filteredReports.length > 0 && (
        <div className="history-cards-grid">
          {filteredReports.map((report) => (
            <div key={report.id} className="history-card card-base">
              <div className="card-top">
                <div className="patient-info-group">
                  <div className="patient-avatar">
                    <User size={18} />
                  </div>
                  <div>
                    <h3 className="patient-name">{report.patient_name || 'Patient Report'}</h3>
                    <div className="meta-row">
                      <span className="source-tag">{report.source_type.toUpperCase()}</span>
                      <span className="meta-date">
                        <Calendar size={13} />
                        {new Date(report.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="word-count-badge">
                  {report.word_count} words
                </div>
              </div>

              {/* Summary Snippet */}
              <div className="card-summary-snippet">
                <p>
                  {report.abstractive_summary || report.extractive_summary || 'No summary text available.'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="card-actions">
                <button
                  className="btn-secondary view-report-btn"
                  onClick={() => onViewReport(report)}
                >
                  <Eye size={15} />
                  <span>View Dashboard</span>
                </button>

                <button
                  className="btn-primary download-pdf-btn"
                  onClick={() => handleDownloadPdf(report)}
                  disabled={!report.structured_summary}
                >
                  <Download size={15} />
                  <span>Download PDF</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
