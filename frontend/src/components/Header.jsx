import React from 'react';
import { ShieldPlus, User, LogIn, LogOut } from 'lucide-react';
import './Header.css';

export default function Header({ activeTab, setActiveTab, onLogoClick, currentUser, onOpenAuthModal, onLogout }) {
  const handleLogoClick = () => {
    if (onLogoClick) {
      onLogoClick();
    } else {
      setActiveTab('home');
    }
  };

  return (
    <header className="site-header">
      <div className="header-container">
        {/* Brand Logo */}
        <div className="brand-logo" onClick={handleLogoClick}>
          <div className="logo-icon-wrapper">
            <ShieldPlus className="logo-icon" />
          </div>
          <div className="logo-text">
            <span className="brand-name">MedBrief</span>
            <span className="brand-tag">Clinical Summarizer</span>
          </div>
        </div>

        {/* Center Navigation Links */}
        <nav className="header-nav">
          <button 
            className={`nav-link ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => setActiveTab('home')}
          >
            Home
          </button>

          {currentUser && (
            <button 
              className={`nav-link ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              My History
            </button>
          )}

          <button 
            className={`nav-link ${activeTab === 'how-it-works' ? 'active' : ''}`}
            onClick={() => setActiveTab('how-it-works')}
          >
            How It Works
          </button>
          <button 
            className={`nav-link ${activeTab === 'about' ? 'active' : ''}`}
            onClick={() => setActiveTab('about')}
          >
            About
          </button>
        </nav>

        {/* Right Side Controls */}
        <div className="header-right">
          {currentUser ? (
            <div className="logged-in-group">
              <div className="user-profile-badge">
                <div className="avatar-circle">
                  <User size={16} />
                </div>
                <span className="user-name">{currentUser.full_name || currentUser.email}</span>
                {currentUser.is_admin && <span className="admin-badge">Admin</span>}
              </div>
              <button 
                type="button"
                className="logout-btn btn-secondary" 
                onClick={onLogout}
                title="Log Out"
              >
                <LogOut size={16} />
                <span>Log Out</span>
              </button>
            </div>
          ) : (
            <button 
              type="button"
              className="btn-primary auth-header-btn" 
              onClick={onOpenAuthModal}
            >
              <LogIn size={16} />
              <span>Log In / Sign Up</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
