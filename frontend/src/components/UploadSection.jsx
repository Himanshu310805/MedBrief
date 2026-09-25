import React, { useState } from 'react';
import { UploadCloud, FileText, AlignLeft, X, Sparkles, CheckCircle2 } from 'lucide-react';
import './UploadSection.css';

export default function UploadSection({ onAnalyze }) {
  const [activeMode, setActiveMode] = useState('pdf'); // 'pdf' | 'text'
  const [selectedFile, setSelectedFile] = useState(null);
  const [pastedText, setPastedText] = useState('');
  const [referenceSummary, setReferenceSummary] = useState('');
  const [showReferenceField, setShowReferenceField] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Sample report loader for quick testing
  const loadSampleText = () => {
    setActiveMode('text');
    setPastedText(`PATIENT INFORMATION:
Patient Name: John Doe (Synthetic)
Age: 54 | Gender: Male | DOB: 1970-05-15
MRN: SYN-987654 | Date of Visit: 2026-09-10
Attending Physician: Dr. Jane Smith, MD (Cardiology)

CHIEF COMPLAINT:
Patient reports shortness of breath on exertion and recurrent mild chest tightness over the past two weeks.

CLINICAL HISTORY & PRESENT ILLNESS:
The patient is a 54-year-old male with a history of essential hypertension and hyperlipidemia. He reports experiencing progressive exertional dyspnea when climbing stairs. Denies acute severe chest pain, radiation to jaw or arm, diaphoresis, nausea, or syncope.

PHYSICAL EXAMINATION:
- Vital Signs: BP 138/86 mmHg, HR 76 bpm, RR 18/min, Temp 98.4°F, SpO2 97% on room air.
- Cardiovascular: Regular rate and rhythm. S1 and S2 present. No S3, S4, or murmurs.
- Respiratory: Clear to auscultation bilaterally. No wheezes, rales, or rhonchi.
- Extremities: No peripheral edema. Pulses intact 2+ bilaterally.

DIAGNOSTIC WORKUP & LAB RESULTS:
- Electrocardiogram (ECG): Normal sinus rhythm at 74 bpm. No acute ST-T wave changes.
- Troponin I: < 0.01 ng/mL (Normal)
- BNP: 45 pg/mL (Normal)
- Lipid Panel: Total Cholesterol 215 mg/dL, LDL 135 mg/dL, HDL 42 mg/dL, Triglycerides 190 mg/dL.
- Echocardiogram: Left ventricular ejection fraction (LVEF) 60%. Mild left ventricular hypertrophy. No regional wall motion abnormalities.

IMPRESSION / DIAGNOSIS:
1. Exertional dyspnea secondary to mild hypertensive heart disease and hyperlipidemia.
2. Acute coronary syndrome ruled out based on serial cardiac biomarkers and ECG.

TREATMENT PLAN & RECOMMENDATIONS:
1. Continue Lisinopril 10 mg orally once daily for blood pressure management.
2. Initiate Atorvastatin 20 mg orally once daily for hyperlipidemia.
3. Schedule an outpatient treadmill stress test within 2 weeks.
4. Dietary modifications: Low-sodium, heart-healthy Mediterranean diet.
5. Follow-up clinic appointment in 4 weeks or sooner if symptoms worsen.`);
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      const validExts = ['.pdf', '.png', '.jpg', '.jpeg'];
      const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (validTypes.includes(file.type) || validExts.includes(ext)) {
        setSelectedFile(file);
      } else {
        alert('Please select a valid PDF or image file (.pdf, .png, .jpg, .jpeg).');
      }
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const isFormValid = activeMode === 'pdf' ? !!selectedFile : pastedText.trim().length > 20;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isFormValid) return;
    onAnalyze({
      mode: activeMode,
      file: selectedFile,
      text: pastedText,
      referenceSummary: referenceSummary.trim()
    });
  };

  return (
    <section className="upload-section-card card-base" id="upload-card">
      {/* Mode Switcher Tabs */}
      <div className="upload-tabs-header">
        <div className="tab-buttons">
          <button
            type="button"
            className={`upload-tab ${activeMode === 'pdf' ? 'active' : ''}`}
            onClick={() => setActiveMode('pdf')}
          >
            <FileText size={18} />
            <span>Upload PDF / Image Report</span>
          </button>
          <button
            type="button"
            className={`upload-tab ${activeMode === 'text' ? 'active' : ''}`}
            onClick={() => setActiveMode('text')}
          >
            <AlignLeft size={18} />
            <span>Paste Clinical Text</span>
          </button>
        </div>

        <button type="button" className="sample-loader-btn" onClick={loadSampleText}>
          <Sparkles size={14} />
          <span>Load Sample Clinical Report</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        {/* Mode 1: PDF or Image Drop Zone */}
        {activeMode === 'pdf' && (
          <div className="pdf-upload-container">
            {!selectedFile ? (
              <div
                className={`dropzone ${isDragging ? 'dragging' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleFileDrop}
              >
                <div className="dropzone-icon-circle">
                  <UploadCloud size={32} />
                </div>
                <h3 className="dropzone-heading">Drag & drop your medical PDF or image (PNG/JPG) here</h3>
                <p className="dropzone-subtext">Supports PDF reports, scanned document images, and photos (max 10MB)</p>
                
                <label className="btn-secondary select-file-btn">
                  <span>Browse Report File</span>
                  <input
                    type="file"
                    accept=".pdf,application/pdf,.png,image/png,.jpg,.jpeg,image/jpeg"
                    onChange={handleFileSelect}
                    hidden
                  />
                </label>
              </div>
            ) : (
              <div className="selected-file-card">
                <div className="file-info-left">
                  <div className="pdf-icon-bg">
                    <FileText size={24} />
                  </div>
                  <div className="file-details">
                    <div className="file-name">{selectedFile.name}</div>
                    <div className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB • Ready for Analysis</div>
                  </div>
                </div>
                <button
                  type="button"
                  className="remove-file-btn"
                  onClick={() => setSelectedFile(null)}
                  title="Remove File"
                >
                  <X size={18} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Mode 2: Paste Text Area */}
        {activeMode === 'text' && (
          <div className="text-input-container">
            <textarea
              className="clinical-textarea"
              rows={10}
              placeholder="Paste patient clinical notes, lab findings, or discharge summary here..."
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
            ></textarea>
            <div className="character-counter">
              {pastedText.length} characters • {pastedText.split(/\s+/).filter(Boolean).length} words
            </div>
          </div>
        )}

        {/* Optional Academic Reference Summary Input Toggle */}
        <div className="reference-summary-toggle">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showReferenceField}
              onChange={(e) => setShowReferenceField(e.target.checked)}
            />
            <span>Include Reference Summary (For ROUGE Academic Evaluation)</span>
          </label>
        </div>

        {showReferenceField && (
          <div className="reference-summary-input fade-in">
            <label className="field-label">Human Gold-Standard Reference Summary (Optional)</label>
            <textarea
              className="reference-textarea"
              rows={3}
              placeholder="Paste an optional doctor-written reference summary to evaluate ROUGE scores against..."
              value={referenceSummary}
              onChange={(e) => setReferenceSummary(e.target.value)}
            ></textarea>
          </div>
        )}

        {/* Submit CTA Button */}
        <div className="form-action-footer">
          <button
            type="submit"
            className="btn-primary analyze-submit-btn"
            disabled={!isFormValid}
          >
            <Sparkles size={18} />
            <span>Analyze Medical Report</span>
          </button>
        </div>
      </form>
    </section>
  );
}
