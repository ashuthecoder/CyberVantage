import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield } from 'lucide-react';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    const result = await register(name, email, password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error || 'Registration failed');
    }
    
    setLoading(false);
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
      overflow: 'hidden',
      padding: '2rem'
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');
        .terminal-text { text-shadow: 0 0 10px currentColor; }
        input { font-family: "JetBrains Mono", monospace !important; }
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
        padding: '2rem',
        background: 'rgba(0, 0, 0, 0.7)',
        border: '1px solid #00d9ff40',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <Shield size={48} color="#00d9ff" strokeWidth={2} />
          </div>
          <h1 className="terminal-text" style={{ 
            fontSize: '1.8rem', 
            fontWeight: 800, 
            color: '#00d9ff', 
            letterSpacing: '0.1em',
            marginBottom: '0.5rem'
          }}>
            CYBERVANTAGE_REGISTER
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#00ff4180' }}>
            CREATE_NEW_ACCOUNT
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

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem',
              color: '#00ff41',
              letterSpacing: '0.05em'
            }}>
              FULL_NAME
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid #00d9ff40',
                color: '#00ff41',
                fontSize: '0.875rem',
                outline: 'none'
              }}
            />
          </div>

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
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid #00d9ff40',
                color: '#00ff41',
                fontSize: '0.875rem',
                outline: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem',
              color: '#00ff41',
              letterSpacing: '0.05em'
            }}>
              PASSWORD
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid #00d9ff40',
                color: '#00ff41',
                fontSize: '0.875rem',
                outline: 'none'
              }}
            />
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
                outline: 'none'
              }}
            />
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
          >
            {loading ? '[CREATING_ACCOUNT...]' : '[REGISTER]'}
          </button>
        </form>

        <div style={{ 
          marginTop: '2rem', 
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#00ff4180'
        }}>
          <p>
            ALREADY_HAVE_ACCOUNT?{' '}
            <Link 
              to="/login" 
              style={{ 
                color: '#00d9ff', 
                textDecoration: 'none',
                borderBottom: '1px solid transparent'
              }}
            >
              [LOGIN_HERE]
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
