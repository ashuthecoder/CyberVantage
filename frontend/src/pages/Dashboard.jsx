import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Terminal, Database, Activity, Zap, BookOpen, BarChart2, Award, CheckCircle, Target, Clock, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, themeName, toggleTheme } = useTheme();
  const [activePhase, setActivePhase] = useState('learn');
  const [scanLines, setScanLines] = useState(0);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    if (themeName === 'soc') {
      const scanInterval = setInterval(() => setScanLines(prev => (prev + 1) % 100), 50);
      const timeInterval = setInterval(() => setTime(new Date()), 1000);
      return () => {
        clearInterval(scanInterval);
        clearInterval(timeInterval);
      };
    }
  }, [themeName]);

  const t = theme;
  const phaseContent = {
    learn: {
      overview: 'Strengthen core phishing detection skills through interactive micro-lessons.',
      modules: ['Phishing anatomy and spoof indicators', 'Link and sender verification drills', 'Safe reporting workflow and escalation basics']
    },
    simulate: {
      overview: 'Practice handling realistic inbox scenarios in a safe sandbox.',
      modules: ['Inbox triage simulation with mixed emails', 'Timed incident response challenge', 'Feedback on missed warning signs']
    },
    analyze: {
      overview: 'Track your performance and prioritize the skills that need reinforcement.',
      modules: ['Weekly threat-detection trend', 'False-positive vs false-negative breakdown', 'Recommended follow-up lesson plan']
    },
    demonstrate: {
      overview: 'Apply everything end-to-end and prove readiness in guided exercises.',
      modules: ['Capstone phishing investigation task', 'Team playbook walkthrough', 'Readiness score with improvement actions']
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: t.bg,
      fontFamily: t.fontFamily,
      color: t.text,
      position: 'relative',
      overflow: 'hidden',
      transition: 'all 0.5s ease'
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Inter:wght@400;600;700;800&display=swap');
        .terminal-text { text-shadow: 0 0 10px currentColor; animation: flicker 3s infinite; }
        @keyframes flicker { 0%, 100% { opacity: 1; } 50% { opacity: 0.95; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        .card { transition: all 0.2s ease; }
        .card:hover { transform: translateY(-2px); }
      `}</style>

      {/* SOC Effects */}
      {themeName === 'soc' && (
        <>
          <div style={{
            position: 'absolute',
            top: `${scanLines}%`,
            left: 0,
            right: 0,
            height: '2px',
            background: 'linear-gradient(to bottom, transparent, #00d9ff80, transparent)',
            pointerEvents: 'none',
            zIndex: 100
          }} />
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
        </>
      )}

      {/* Header */}
      <header style={{
        padding: '1rem 2rem',
        borderBottom: themeName === 'soc' ? `2px solid ${t.border}` : `1px solid ${t.border}`,
        background: themeName === 'soc' ? t.bgSecondary : t.bg,
        backdropFilter: themeName === 'soc' ? 'blur(10px)' : 'none',
        position: 'relative',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <Shield size={32} color={t.primary} strokeWidth={2} />
            <div>
              <div className={themeName === 'soc' ? 'terminal-text' : ''} style={{ 
                fontSize: '1.5rem', 
                fontWeight: 800, 
                color: t.primary, 
                letterSpacing: themeName === 'soc' ? '0.1em' : '-0.02em' 
              }}>
                {themeName === 'soc' ? 'CYBERVANTAGE_SOC' : 'CyberVantage'}
              </div>
              <div style={{ fontSize: '0.75rem', color: t.textSecondary }}>
                {themeName === 'soc' ? 'SECURITY OPERATIONS v2.4.1' : 'Security Training Platform'}
              </div>
            </div>
            {themeName === 'soc' && (
              <div style={{
                padding: '0.5rem 1rem',
                background: 'rgba(0, 217, 255, 0.1)',
                border: '1px solid #00d9ff40',
                fontSize: '0.8rem',
                color: '#00d9ff',
                letterSpacing: '0.05em'
              }}>
                {time.toLocaleTimeString('en-US', { hour12: false })} UTC
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <div style={{ fontSize: '0.875rem', color: t.textSecondary }}>
              {themeName === 'soc' ? `AGENT: ${user?.name || 'OPERATOR'}` : `Welcome, ${user?.name || 'Learner'}`}
            </div>
            <button
              onClick={toggleTheme}
              style={{
                padding: '0.625rem 1.25rem',
                borderRadius: themeName === 'soc' ? '0' : '8px',
                border: themeName === 'soc' ? `1px solid ${t.primary}` : `1px solid ${t.border}`,
                background: themeName === 'soc' ? 'rgba(0, 217, 255, 0.1)' : t.bgSecondary,
                color: themeName === 'soc' ? t.primary : t.text,
                fontSize: '0.8rem',
                fontWeight: themeName === 'soc' ? 700 : 600,
                letterSpacing: themeName === 'soc' ? '0.05em' : 'normal',
                cursor: 'pointer',
                fontFamily: t.fontFamily,
                boxShadow: themeName === 'soc' ? '0 0 20px rgba(0, 217, 255, 0.3)' : 'none',
                transition: 'all 0.3s ease'
              }}
            >
              {themeName === 'soc' ? '[SWITCH_TO_MODERN]' : '🖥️ SOC Mode'}
            </button>

            <div style={{
              padding: '0.75rem 1.25rem',
              borderRadius: themeName === 'soc' ? '0' : '8px',
              background: themeName === 'soc' ? 'rgba(0, 255, 65, 0.05)' : `${t.warning}20`,
              border: themeName === 'soc' ? `1px solid ${t.success}` : `1px solid ${t.warning}40`,
              boxShadow: themeName === 'soc' ? `0 0 20px ${t.success}50` : 'none'
            }}>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary }}>
                {themeName === 'soc' ? 'THREAT_POINTS' : 'Total Points'}
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: themeName === 'soc' ? t.success : t.warning }}>
                2,840
              </div>
            </div>
            <button
              onClick={handleLogout}
              style={{
                padding: '0.625rem 1rem',
                borderRadius: themeName === 'soc' ? '0' : '8px',
                border: `1px solid ${themeName === 'soc' ? t.danger : t.border}`,
                background: 'transparent',
                color: themeName === 'soc' ? t.danger : t.text,
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: themeName === 'soc' ? '0.05em' : 'normal',
                cursor: 'pointer',
                fontFamily: t.fontFamily
              }}
            >
              {themeName === 'soc' ? '[LOGOUT]' : 'Logout'}
            </button>
          </div>
        </div>
      </header>

      <div style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
        {/* Sidebar */}
        <aside style={{
          width: '280px',
          borderRight: themeName === 'soc' ? `2px solid ${t.border}` : `1px solid ${t.border}`,
          background: themeName === 'soc' ? t.bgTertiary : t.bgSecondary,
          padding: '2rem 0',
          overflowY: 'auto'
        }}>
          <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
            <div style={{ 
              fontSize: '0.7rem', 
              color: t.textTertiary, 
              letterSpacing: themeName === 'soc' ? '0.1em' : '0.05em', 
              marginBottom: '1rem',
              fontWeight: 700,
              textTransform: 'uppercase'
            }}>
              {themeName === 'soc' ? 'SYSTEM_MODULES' : 'Learning Paths'}
            </div>
            
            {[
              { id: 'learn', label: themeName === 'soc' ? 'LEARN' : 'Learn', icon: themeName === 'soc' ? Database : BookOpen },
              { id: 'simulate', label: themeName === 'soc' ? 'SIMULATE' : 'Simulate', icon: Terminal },
              { id: 'analyze', label: themeName === 'soc' ? 'ANALYZE' : 'Analyze', icon: Activity },
              { id: 'demonstrate', label: themeName === 'soc' ? 'DEMONSTRATE' : 'Demonstrate', icon: Zap }
            ].map((phase) => {
              const Icon = phase.icon;
              const isActive = activePhase === phase.id;
              return (
                <div
                  key={phase.id}
                  onClick={() => setActivePhase(phase.id)}
                  style={{
                    padding: themeName === 'soc' ? '1rem' : '0.75rem 1rem',
                    marginBottom: '0.5rem',
                    background: isActive ? (themeName === 'soc' ? 'rgba(0, 217, 255, 0.1)' : t.primary) : 'transparent',
                    border: isActive ? (themeName === 'soc' ? `1px solid ${t.primary}` : 'none') : (themeName === 'soc' ? '1px solid transparent' : 'none'),
                    borderRadius: themeName === 'soc' ? '0' : '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: isActive ? (themeName === 'soc' ? t.primary : '#fff') : t.textSecondary,
                    fontWeight: themeName === 'soc' ? 700 : (isActive ? 600 : 500),
                    fontSize: themeName === 'soc' ? '0.9rem' : '0.875rem',
                    letterSpacing: themeName === 'soc' ? '0.05em' : 'normal',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  <span style={{ flex: 1 }}>{phase.label}</span>
                  {isActive && themeName === 'soc' && (
                    <div style={{
                      width: '8px',
                      height: '8px',
                      background: t.primary,
                      animation: 'pulse 2s infinite'
                    }} />
                  )}
                </div>
              );
            })}
          </div>
        </aside>

        {/* Main Content */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
            {[
              { label: themeName === 'soc' ? 'DETECTION_RATE' : 'Detection Rate', value: '85.5%', color: t.success },
              { label: themeName === 'soc' ? 'ACTIVE_STREAK' : 'Current Streak', value: '12 DAYS', color: t.warning },
              { label: themeName === 'soc' ? 'THREATS_FOUND' : 'Threats Found', value: '47', color: t.primary },
              { label: themeName === 'soc' ? 'AVG_RESPONSE' : 'Avg Response', value: '2.3s', color: '#8b5cf6' }
            ].map((stat, i) => (
              <div key={i} className="card" style={{
                padding: '1.5rem',
                background: themeName === 'soc' ? t.bgTertiary : t.bgSecondary,
                border: themeName === 'soc' ? `1px solid ${stat.color}40` : `1px solid ${t.border}`,
                borderRadius: themeName === 'soc' ? '0' : '12px'
              }}>
                {themeName === 'soc' && (
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: stat.color
                  }} />
                )}
                <div style={{ fontSize: themeName === 'soc' ? '0.65rem' : '0.875rem', color: t.textSecondary, marginBottom: '0.75rem', fontWeight: 600 }}>
                  {stat.label}
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: stat.color }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* Content */}
          <div style={{
            padding: '2rem',
            background: themeName === 'soc' ? t.bgTertiary : t.bgSecondary,
            border: themeName === 'soc' ? `1px solid ${t.border}` : `1px solid ${t.border}`,
            borderRadius: themeName === 'soc' ? '0' : '12px'
          }}>
            <h2 style={{
              margin: '0 0 1rem 0',
              fontSize: themeName === 'soc' ? '1rem' : '1.5rem',
              fontWeight: themeName === 'soc' ? 700 : 700,
              color: themeName === 'soc' ? t.primary : t.text,
              letterSpacing: themeName === 'soc' ? '0.05em' : 'normal'
            }}>
              {activePhase === 'learn' && (themeName === 'soc' ? 'TRAINING_MODULES' : 'Learning Modules')}
              {activePhase === 'simulate' && (themeName === 'soc' ? 'THREAT_SIMULATION' : 'Threat Simulation')}
              {activePhase === 'analyze' && (themeName === 'soc' ? 'PERFORMANCE_ANALYTICS' : 'Performance Analytics')}
              {activePhase === 'demonstrate' && (themeName === 'soc' ? 'RED_TEAM_EXERCISE' : 'Demonstrate Skills')}
            </h2>
            <p style={{ margin: 0, color: t.textSecondary, fontSize: '0.95rem' }}>
              {phaseContent[activePhase].overview}
            </p>
            <ul style={{ margin: '1rem 0 0 1rem', padding: 0, color: t.textSecondary, lineHeight: 1.9 }}>
              {phaseContent[activePhase].modules.map((item) => (
                <li key={item} style={{ marginBottom: '0.35rem' }}>{item}</li>
              ))}
            </ul>
          </div>
        </main>
      </div>
    </div>
  );
}
