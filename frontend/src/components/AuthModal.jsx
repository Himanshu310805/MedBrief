import React, { useState, useEffect } from 'react';
import { X, LogIn, UserPlus, Lock, Mail, User, AlertCircle, ShieldCheck } from 'lucide-react';
import { loginUser, signupUser } from '../services/api';
import './AuthModal.css';

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode); // 'login' | 'signup'
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const resetForm = () => {
    setFullName('');
    setEmail('');
    setPassword('');
    setErrorMsg(null);
  };

  useEffect(() => {
    if (isOpen) {
      setMode(initialMode);
      resetForm();
    }
  }, [isOpen, initialMode]);

  if (!isOpen) return null;

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!email.trim() || !password.trim()) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    if (mode === 'signup' && !fullName.trim()) {
      setErrorMsg('Please enter your full name.');
      return;
    }

    try {
      setIsLoading(true);
      let res;
      if (mode === 'signup') {
        res = await signupUser(email.trim(), password, fullName.trim());
      } else {
        res = await loginUser(email.trim(), password);
      }

      if (res && res.user) {
        resetForm();
        onAuthSuccess(res.user);
        onClose();
      }
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleClose}>
      <div className="auth-modal-card card-base fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Close Button */}
        <button className="modal-close-btn" onClick={handleClose} title="Close">
          <X size={20} />
        </button>

        {/* Modal Header Icon */}
        <div className="auth-modal-header">
          <div className="auth-icon-circle">
            <ShieldCheck size={28} />
          </div>
          <h2>{mode === 'signup' ? 'Create a MedBrief Account' : 'Welcome Back to MedBrief'}</h2>
          <p className="auth-subtitle">
            {mode === 'signup' 
              ? 'Sign up to analyze clinical reports and access your saved report history.' 
              : 'Log in to access clinical report summarization and your saved reports.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setErrorMsg(null); }}
          >
            <LogIn size={16} />
            <span>Log In</span>
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => { setMode('signup'); setErrorMsg(null); }}
          >
            <UserPlus size={16} />
            <span>Sign Up</span>
          </button>
        </div>

        {/* Error Alert Box */}
        {errorMsg && (
          <div className="auth-error-banner">
            <AlertCircle size={18} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'signup' && (
            <div className="input-group">
              <label className="input-label">Full Name</label>
              <div className="input-field-wrapper">
                <User className="field-icon" size={18} />
                <input
                  type="text"
                  className="auth-input"
                  placeholder="Dr. Alex Morgan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required={mode === 'signup'}
                />
              </div>
            </div>
          )}

          <div className="input-group">
            <label className="input-label">Email Address</label>
            <div className="input-field-wrapper">
              <Mail className="field-icon" size={18} />
              <input
                type="email"
                className="auth-input"
                placeholder="doctor@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Password</label>
            <div className="input-field-wrapper">
              <Lock className="field-icon" size={18} />
              <input
                type="password"
                className="auth-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span>Processing...</span>
            ) : mode === 'signup' ? (
              <>
                <UserPlus size={18} />
                <span>Create Account</span>
              </>
            ) : (
              <>
                <LogIn size={18} />
                <span>Log In to MedBrief</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
