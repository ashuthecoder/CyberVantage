import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Mail } from 'lucide-react';
import apiClient from '../api/client';

export default function RequestPasswordResetPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await apiClient.post('/request_password_reset_otp', { email });
      
      if (response.data.success) {
        setSuccess('OTP sent! Check your email.');
        // Navigate to OTP verification page after 2 seconds
        setTimeout(() => {
          navigate('/verify-otp', { state: { email } });
        }, 2000);
      } else {
        setError(response.data.error || 'Failed to send OTP');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0e27',
      fontFamily: '"JetBrains Mono", monospace',
      color: '#00ff41',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');
        .terminal-text { text-shadow: 0 0 10px currentColor; animation: flicker 3s infinite; }
        @keyframes flicker { 0%, 100% { opacity: 1; } 50% { opacity: 0.95; } }
        input { font-family: "JetBrains Mono", monospace !important; }
      `}</style>

      {/* Grid background */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'linear-gradient(rgba(0, 217, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 217, 255, 0.03) 1px, transparent 1px)',
        backgroundSize: '50px 50px',
        pointerEvents: 'none',
        opacity: 0.3
      }} />

      <div style={{
        maxWidth: '450px',
        width: '100%',
        padding: '2rem',
        background: 'rgba(0, 0, 0, 0.7)',
        border: '1px solid #00d9ff40',
        position: 'relative',
        zIndex: 1,
        margin: '2rem'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <Shield size={48} color="#00d9ff" strokeWidth={2} />
          </div>
          <h1 className="terminal-text" style={{ 
            fontSize: '1.6rem', 
            fontWeight: 800, 
            color: '#00d9ff', 
            letterSpacing: '0.1em',
            marginBottom: '0.5rem'
          }}>
            PASSWORD_RESET
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#00ff4180' }}>
            ENTER_EMAIL_FOR_OTP
          </p>
        </div>

        {error && (
          <div style={{
            padding: '1rem',
            marginBottom: '1.5rem',
            background: 'rgba(255, 0, 85, 0.1)',
            border: '1px solid #ff0055',
            color: '#ff0055',
            fontSize: '0.875rem'
          }}>
            {error}
          </div>
        )}

        {success && (
          <div style={{
            padding: '1rem',
            marginBottom: '1.5rem',
            background: 'rgba(0, 255, 65, 0.1)',
            border: '1px solid #00ff41',
            color: '#00ff41',
            fontSize: '0.875rem'
          }}>
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem',
              color: '#00ff41',
              letterSpacing: '0.05em'
            }}>
              EMAIL_ADDRESS
            </label>
            <div style={{ position: 'relative' }}>
              <Mail 
                size={18} 
                color="#00d9ff40" 
                style={{ 
                  position: 'absolute', 
                  left: '0.75rem', 
                  top: '50%', 
                  transform: 'translateY(-50%)' 
                }} 
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="user@example.com"
                style={{
                  width: '100%',
                  padding: '0.75rem 0.75rem 0.75rem 2.75rem',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid #00d9ff40',
                  color: '#00ff41',
                  fontSize: '0.875rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => e.target.style.borderColor = '#00d9ff'}
                onBlur={(e) => e.target.style.borderColor = '#00d9ff40'}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '0.875rem',
              background: loading ? 'rgba(0, 217, 255, 0.3)' : 'rgba(0, 217, 255, 0.1)',
              border: '1px solid #00d9ff',
              color: '#00d9ff',
              fontSize: '0.875rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: '0 0 20px rgba(0, 217, 255, 0.3)',
              transition: 'all 0.3s ease'
            }}
            onMouseOver={(e) => !loading && (e.target.style.background = 'rgba(0, 217, 255, 0.2)')}
            onMouseOut={(e) => !loading && (e.target.style.background = 'rgba(0, 217, 255, 0.1)')}
          >
            {loading ? '[SENDING_OTP...]' : '[SEND_OTP]'}
          </button>
        </form>

        <div style={{ 
          marginTop: '2rem', 
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#00ff4180'
        }}>
          <p>
            REMEMBER_PASSWORD?{' '}
            <Link 
              to="/login" 
              style={{ 
                color: '#00d9ff', 
                textDecoration: 'none',
                borderBottom: '1px solid transparent'
              }}
              onMouseOver={(e) => e.target.style.borderBottomColor = '#00d9ff'}
              onMouseOut={(e) => e.target.style.borderBottomColor = 'transparent'}
            >
              [BACK_TO_LOGIN]
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
