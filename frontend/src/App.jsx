import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import UploadSection from './components/UploadSection';
import ProcessingState from './components/ProcessingState';
import ResultsDashboard from './components/ResultsDashboard';
import ErrorCard from './components/ErrorCard';
import Disclaimer from './components/Disclaimer';
import AuthModal from './components/AuthModal';
import ReportHistory from './components/ReportHistory';
import { HowItWorksPage, AboutPage } from './pages/InfoPages';
import { 
  extractFromPdf, 
  extractFromImage, 
  extractFromText, 
  analyzeFull, 
  evaluateSummaries, 
  getMe, 
  logoutUser 
} from './services/api';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'history' | 'how-it-works' | 'about'
  const [viewState, setViewState] = useState('input'); // 'input' | 'processing' | 'results' | 'error'
  const [reportData, setReportData] = useState(null);
  const [processingStep, setProcessingStep] = useState(0);
  const [processingStatusText, setProcessingStatusText] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [lastFormData, setLastFormData] = useState(null);

  // Auth States
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login');

  // Check active session on initial page load
  useEffect(() => {
    getMe().then((usr) => {
      if (usr) {
        setCurrentUser(usr);
      }
    });
  }, []);

  const handleAnalyze = async (formData) => {
    // If not logged in, prompt Auth Modal
    if (!currentUser) {
      setAuthModalMode('login');
      setIsAuthModalOpen(true);
      return;
    }

    setLastFormData(formData);
    setErrorMessage(null);
    setViewState('processing');
    setProcessingStep(0);
    setProcessingStatusText('Extracting report text content...');

    const startTime = performance.now();

    try {
      let rawText = '';
      let textWarning = null;

      // 1. Text / PDF / Image Extraction Step
      if (formData.mode === 'pdf' && formData.file) {
        const fileName = formData.file.name.toLowerCase();
        const isImage = fileName.endsWith('.png') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg');
        
        if (isImage) {
          setProcessingStatusText(`Extracting text via OCR from image: ${formData.file.name}...`);
          const imgRes = await extractFromImage(formData.file);
          rawText = imgRes.extracted_text;
          textWarning = imgRes.warning;
        } else {
          setProcessingStatusText(`Extracting text from PDF file: ${formData.file.name}...`);
          const pdfRes = await extractFromPdf(formData.file);
          rawText = pdfRes.extracted_text;
          textWarning = pdfRes.warning;
        }
      } else {
        setProcessingStatusText('Cleaning plain text clinical report...');
        const textRes = await extractFromText(formData.text);
        rawText = textRes.extracted_text;
        textWarning = textRes.warning;
      }

      if (!rawText || !rawText.trim()) {
        throw new Error(
          textWarning || 'No extractable text found in report. If this is a PDF, it may be a scanned image-only file.'
        );
      }

      // 2. Full NLP Pipeline Analysis Step
      setProcessingStep(1);
      setProcessingStatusText('Extracting medical entities, demographics, and clinical history...');
      
      setProcessingStep(2);
      setProcessingStatusText('Running TextRank extractive and Transformer abstractive models...');

      setProcessingStep(3);
      setProcessingStatusText('Assembling verified structured report sections...');

      const structuredRes = await analyzeFull(rawText);

      // 3. Optional ROUGE Evaluation Step
      let rougeEval = null;
      if (formData.referenceSummary && formData.referenceSummary.trim()) {
        setProcessingStep(4);
        setProcessingStatusText('Evaluating summary quality against reference summary (ROUGE metrics)...');
        try {
          const evalRes = await evaluateSummaries(
            structuredRes.extractive_summary_text,
            structuredRes.abstractive_summary_text,
            formData.referenceSummary.trim()
          );
          rougeEval = {
            show: true,
            extractive_scores: evalRes.extractive_scores,
            abstractive_scores: evalRes.abstractive_scores,
            comparison_note: evalRes.comparison_note
          };
        } catch (evalErr) {
          console.warn('ROUGE evaluation warning:', evalErr);
          rougeEval = { show: false };
        }
      }

      const totalProcessingTime = ((performance.now() - startTime) / 1000).toFixed(2);
      const wordCount = rawText.split(/\s+/).filter(Boolean).length;
      const sentenceCount = rawText.split(/[.!?]+/).filter((s) => s.trim().length > 0).length;

      // Calculate Faithfulness Verification Rate
      const sections = [
        structuredRes.symptoms,
        structuredRes.diagnosis_conditions,
        structuredRes.medications,
        structuredRes.lab_findings,
        structuredRes.procedures,
        structuredRes.other_observations,
        structuredRes.follow_up
      ];
      const verifiedCount = sections.filter((s) => s && s.verified).length;
      const totalPopulated = sections.filter((s) => s && s.content && s.content !== 'Not mentioned').length;
      const verificationRate = totalPopulated > 0 ? `${Math.round((verifiedCount / totalPopulated) * 100)}%` : '100%';

      const finalData = {
        patient_information: structuredRes.patient_information || {},
        stats: {
          word_count: wordCount,
          sentence_count: sentenceCount,
          processing_time: totalProcessingTime,
          verification_rate: verificationRate
        },
        symptoms: structuredRes.symptoms,
        diagnosis_conditions: structuredRes.diagnosis_conditions,
        medications: structuredRes.medications,
        lab_findings: structuredRes.lab_findings,
        lab_results_table: structuredRes.lab_results_table || [],
        procedures: structuredRes.procedures,
        other_observations: structuredRes.other_observations,
        follow_up: structuredRes.follow_up,
        extractive_summary_text: structuredRes.extractive_summary_text,
        abstractive_summary_text: structuredRes.abstractive_summary_text,
        original_report_text: rawText,
        rouge_evaluation: rougeEval
      };

      setReportData(finalData);
      setViewState('results');
    } catch (err) {
      console.error('Error during medical report analysis:', err);
      let msg = err.message || 'An unexpected error occurred during processing.';
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('Load failed')) {
        msg = 'Unable to connect to backend server. Please check your network connection and verify FastAPI backend is running at http://localhost:8000.';
      }
      setErrorMessage(msg);
      setViewState('error');
    }
  };

  const handleRetry = () => {
    if (lastFormData) {
      handleAnalyze(lastFormData);
    } else {
      setViewState('input');
    }
  };

  const handleReset = () => {
    setViewState('input');
    setActiveTab('home');
    setReportData(null);
    setErrorMessage(null);
    setLastFormData(null);
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
    handleReset();
  };

  const handleViewHistoryReport = (historyReport) => {
    if (historyReport && historyReport.structured_summary) {
      const summary = historyReport.structured_summary;
      const finalData = {
        patient_information: summary.patient_information || { patient_name: historyReport.patient_name },
        stats: {
          word_count: historyReport.word_count || 0,
          sentence_count: historyReport.sentence_count || 0,
          processing_time: 'Cached',
          verification_rate: '100%'
        },
        symptoms: summary.symptoms,
        diagnosis_conditions: summary.diagnosis_conditions,
        medications: summary.medications,
        lab_findings: summary.lab_findings,
        lab_results_table: summary.lab_results_table || [],
        procedures: summary.procedures,
        other_observations: summary.other_observations,
        follow_up: summary.follow_up,
        extractive_summary_text: summary.extractive_summary_text || historyReport.extractive_summary,
        abstractive_summary_text: summary.abstractive_summary_text || historyReport.abstractive_summary,
        original_report_text: summary.original_text || historyReport.abstractive_summary || '',
        rouge_evaluation: summary.rouge_evaluation || { show: false }
      };
      setReportData(finalData);
      setActiveTab('home');
      setViewState('results');
    }
  };

  const scrollToUpload = () => {
    setActiveTab('home');
    setViewState('input');
    const uploadEl = document.getElementById('upload-card');
    if (uploadEl) {
      uploadEl.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="app-container">
      {/* 1. Header Navbar */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onLogoClick={handleReset} 
        currentUser={currentUser}
        onOpenAuthModal={() => { setAuthModalMode('login'); setIsAuthModalOpen(true); }}
        onLogout={handleLogout}
      />

      {/* 2. Main Page Content Routing */}
      <main className="main-content">
        {activeTab === 'how-it-works' && <HowItWorksPage onBack={handleReset} />}

        {activeTab === 'about' && <AboutPage onBack={handleReset} />}

        {activeTab === 'history' && (
          <ReportHistory 
            onViewReport={handleViewHistoryReport} 
            onAnalyzeNew={handleReset} 
          />
        )}

        {activeTab === 'home' && (
          <>
            {viewState === 'input' && (
              <>
                <Hero onGetStarted={scrollToUpload} />
                <UploadSection onAnalyze={handleAnalyze} />
              </>
            )}

            {viewState === 'processing' && (
              <ProcessingState stepIndex={processingStep} statusText={processingStatusText} />
            )}

            {viewState === 'error' && (
              <ErrorCard
                title="Analysis Error"
                message={errorMessage}
                onRetry={handleRetry}
                onReset={handleReset}
              />
            )}

            {viewState === 'results' && reportData && (
              <ResultsDashboard data={reportData} onReset={handleReset} />
            )}
          </>
        )}
      </main>

      {/* 3. Authentication Modal Dialog */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={(user) => setCurrentUser(user)}
        initialMode={authModalMode}
      />

      {/* 4. Mandatory Medical Disclaimer Footer */}
      <Disclaimer />
    </div>
  );
}
