import React from 'react';
import { ShieldAlert } from 'lucide-react';
import './Disclaimer.css';

export default function Disclaimer() {
  return (
    <footer className="disclaimer-footer">
      <div className="disclaimer-container">
        <ShieldAlert className="disclaimer-icon" size={18} />
        <p className="disclaimer-text">
          MedBrief is an educational NLP-based summarization tool. It does not provide medical diagnosis or treatment recommendations. Always consult a qualified healthcare professional for medical decisions.
        </p>
      </div>
    </footer>
  );
}
