import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Key } from 'lucide-react';
import apiClient from '../api/client';

export default function VerifyOTPPage() {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const inputRefs = useRef([]);

  useEffect(() => {
    // Redirect if no email provided
    if (!email) {
      navigate('/reset-password');
    }
    // Focus first input on mount
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, [email, navigate]);

  const handleChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    // Handle backspace
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    
    for (let i = 0; i < pastedData.length; i++) {
      newOtp[i] = pastedData[i];
    }
    setOtp(newOtp);
    
    // Focus the next empty input or last input
    const nextIndex = Math.min(pastedData.length, 5);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const otpCode = otp.join('');
    
    if (otpCode.length !== 6) {
      setError('Please enter all 6 digits');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post('/verify_otp', { 
        email, 
        otp: otpCode 
      });
      
      if (response.data.success) {
        // Navigate to new password page with reset token
        navigate('/reset-password-new', { 
          state: { 
            email, 
            reset_token: response.data.reset_token 
          } 
        });
      } else {
        setError(response.data.error || 'Invalid OTP');
        // Clear OTP on error
        setOtp(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to verify OTP');
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
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
        .otp-input::-webkit-outer-spin-button,
        .otp-input::-webkit-inner-spin-button {
          -webkit-appearance: none;
          margin: 0;
        }
        .otp-input[type=number] {
          -moz-appearance: textfield;
        }
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
        maxWidth: '500px',
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
            <Key size={48} color="#00d9ff" strokeWidth={2} />
          </div>
          <h1 className="terminal-text" style={{ 
            fontSize: '1.6rem', 
            fontWeight: 800, 
            color: '#00d9ff', 
            letterSpacing: '0.1em',
            marginBottom: '0.5rem'
          }}>
            VERIFY_OTP
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#00ff4180', marginBottom: '0.5rem' }}>
            ENTER_6_DIGIT_CODE
          </p>
          <p style={{ fontSize: '0.75rem', color: '#00d9ff80' }}>
            Sent to: {email}
          </p>
        </div>

        {error && (
          <div style={{
            padding: '1rem',
            marginBottom: '1.5rem',
            background: 'rgba(255, 0, 85, 0.1)',
            border: '1px solid #ff0055',
            color: '#ff0055',
            fontSize: '0.875rem',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div style={{ 
            display: 'flex', 
            gap: '0.75rem', 
            justifyContent: 'center',
            marginBottom: '1rem'
          }}>
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                className="otp-input"
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                style={{
                  width: '3rem',
                  height: '3.5rem',
                  textAlign: 'center',
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '2px solid #00d9ff40',
                  color: '#00ff41',
                  outline: 'none',
                  transition: 'all 0.2s ease'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#00d9ff';
                  e.target.style.boxShadow = '0 0 20px rgba(0, 217, 255, 0.3)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#00d9ff40';
                  e.target.style.boxShadow = 'none';
                }}
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={loading || otp.join('').length !== 6}
            style={{
              padding: '0.875rem',
              background: (loading || otp.join('').length !== 6) ? 'rgba(0, 217, 255, 0.3)' : 'rgba(0, 217, 255, 0.1)',
              border: '1px solid #00d9ff',
              color: '#00d9ff',
              fontSize: '0.875rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              cursor: (loading || otp.join('').length !== 6) ? 'not-allowed' : 'pointer',
              boxShadow: '0 0 20px rgba(0, 217, 255, 0.3)',
              transition: 'all 0.3s ease'
            }}
            onMouseOver={(e) => {
              if (!loading && otp.join('').length === 6) {
                e.target.style.background = 'rgba(0, 217, 255, 0.2)';
              }
            }}
            onMouseOut={(e) => {
              if (!loading && otp.join('').length === 6) {
                e.target.style.background = 'rgba(0, 217, 255, 0.1)';
              }
            }}
          >
            {loading ? '[VERIFYING...]' : '[VERIFY_OTP]'}
          </button>
        </form>

        <div style={{ 
          marginTop: '2rem', 
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#00ff4180'
        }}>
          <p>
            DIDN'T_RECEIVE_CODE?{' '}
            <Link 
              to="/reset-password" 
              style={{ 
                color: '#00d9ff', 
                textDecoration: 'none',
                borderBottom: '1px solid transparent'
              }}
              onMouseOver={(e) => e.target.style.borderBottomColor = '#00d9ff'}
              onMouseOut={(e) => e.target.style.borderBottomColor = 'transparent'}
            >
              [REQUEST_NEW_OTP]
            </Link>
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            <Link 
              to="/login" 
              style={{ 
                color: '#00d9ff80', 
                textDecoration: 'none',
                borderBottom: '1px solid transparent',
                fontSize: '0.8rem'
              }}
              onMouseOver={(e) => e.target.style.borderBottomColor = '#00d9ff80'}
              onMouseOut={(e) => e.target.style.borderBottomColor = 'transparent'}
            >
              [CANCEL]
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
