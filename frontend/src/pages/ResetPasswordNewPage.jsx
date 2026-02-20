import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Lock, CheckCircle } from 'lucide-react';
import apiClient from '../api/client';

export default function ResetPasswordNewPage() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, message: '' });
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const resetToken = location.state?.reset_token || '';

  useEffect(() => {
    // Redirect if no email or reset token
    if (!email || !resetToken) {
      navigate('/reset-password');
    }
  }, [email, resetToken, navigate]);

  const checkPasswordStrength = (pwd) => {
    let score = 0;
    let messages = [];

    if (pwd.length >= 8) score++;
    else messages.push('At least 8 characters');

    if (/[A-Z]/.test(pwd)) score++;
    else messages.push('One uppercase letter');

    if (/[a-z]/.test(pwd)) score++;
    else messages.push('One lowercase letter');

    if (/\d/.test(pwd)) score++;
    else messages.push('One number');

    if (/[^A-Za-z0-9]/.test(pwd)) score++;

    const strengthLevels = ['WEAK', 'FAIR', 'GOOD', 'STRONG', 'VERY_STRONG'];
    return {
      score,
      message: score < 4 ? `Need: ${messages.join(', ')}` : strengthLevels[score - 1]
    };
  };

  const handlePasswordChange = (e) => {
    const pwd = e.target.value;
    setPassword(pwd);
    if (pwd) {
      setPasswordStrength(checkPasswordStrength(pwd));
    } else {
      setPasswordStrength({ score: 0, message: '' });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (passwordStrength.score < 4) {
      setError('Password does not meet requirements');
      return;
    }

    setLoading(true);

    try {
      const response = await apiClient.post('/reset_password_with_otp', {
        email,
        reset_token: resetToken,
        new_password: password
      });

      if (response.data.success) {
        setSuccess(true);
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setError(response.data.error || 'Failed to reset password');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reset password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = (score) => {
    if (score < 2) return '#ff0055';
    if (score < 3) return '#ffb800';
    if (score < 4) return '#00d9ff';
    return '#00ff41';
  };

  if (success) {
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
          .terminal-text { text-shadow: 0 0 10px currentColor; }
          @keyframes checkmark { 0% { transform: scale(0) rotate(0deg); } 50% { transform: scale(1.2) rotate(180deg); } 100% { transform: scale(1) rotate(360deg); } }
        `}</style>

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
          padding: '3rem 2rem',
          background: 'rgba(0, 0, 0, 0.7)',
          border: '1px solid #00ff41',
          position: 'relative',
          zIndex: 1,
          textAlign: 'center',
          margin: '2rem'
        }}>
          <div style={{ 
            marginBottom: '1.5rem',
            animation: 'checkmark 0.6s ease-out'
          }}>
            <CheckCircle size={64} color="#00ff41" strokeWidth={2} />
          </div>
          <h1 className="terminal-text" style={{ 
            fontSize: '1.6rem', 
            fontWeight: 800, 
            color: '#00ff41', 
            letterSpacing: '0.1em',
            marginBottom: '1rem'
          }}>
            PASSWORD_RESET_SUCCESS
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#00ff4180', marginBottom: '1rem' }}>
            Your password has been reset successfully.
          </p>
          <p style={{ fontSize: '0.875rem', color: '#00d9ff' }}>
            Redirecting to login...
          </p>
        </div>
      </div>
    );
  }

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
            <Lock size={48} color="#00d9ff" strokeWidth={2} />
          </div>
          <h1 className="terminal-text" style={{ 
            fontSize: '1.6rem', 
            fontWeight: 800, 
            color: '#00d9ff', 
            letterSpacing: '0.1em',
            marginBottom: '0.5rem'
          }}>
            NEW_PASSWORD
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#00ff4180' }}>
            CREATE_SECURE_PASSWORD
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

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem',
              color: '#00ff41',
              letterSpacing: '0.05em'
            }}>
              NEW_PASSWORD
            </label>
            <input
              type="password"
              value={password}
              onChange={handlePasswordChange}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
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
            {password && (
              <div style={{ marginTop: '0.5rem' }}>
                <div style={{
                  height: '4px',
                  background: 'rgba(0, 0, 0, 0.5)',
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${(passwordStrength.score / 5) * 100}%`,
                    background: getStrengthColor(passwordStrength.score),
                    transition: 'all 0.3s ease'
                  }} />
                </div>
                <p style={{
                  fontSize: '0.75rem',
                  color: getStrengthColor(passwordStrength.score),
                  marginTop: '0.25rem'
                }}>
                  {passwordStrength.message}
                </p>
              </div>
            )}
          </div>

          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem',
              color: '#00ff41',
              letterSpacing: '0.05em'
            }}>
              CONFIRM_PASSWORD
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
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

          <button
            type="submit"
            disabled={loading || passwordStrength.score < 4}
            style={{
              padding: '0.875rem',
              background: (loading || passwordStrength.score < 4) ? 'rgba(0, 217, 255, 0.3)' : 'rgba(0, 217, 255, 0.1)',
              border: '1px solid #00d9ff',
              color: '#00d9ff',
              fontSize: '0.875rem',
              fontWeight: 700,
              letterSpacing: '0.1em',
              cursor: (loading || passwordStrength.score < 4) ? 'not-allowed' : 'pointer',
              boxShadow: '0 0 20px rgba(0, 217, 255, 0.3)',
              transition: 'all 0.3s ease'
            }}
            onMouseOver={(e) => {
              if (!loading && passwordStrength.score >= 4) {
                e.target.style.background = 'rgba(0, 217, 255, 0.2)';
              }
            }}
            onMouseOut={(e) => {
              if (!loading && passwordStrength.score >= 4) {
                e.target.style.background = 'rgba(0, 217, 255, 0.1)';
              }
            }}
          >
            {loading ? '[RESETTING...]' : '[RESET_PASSWORD]'}
          </button>
        </form>

        <div style={{ 
          marginTop: '2rem', 
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#00ff4180'
        }}>
          <p>
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
