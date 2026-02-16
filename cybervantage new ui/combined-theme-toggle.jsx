import React, { useState, useEffect } from 'react';
import { Shield, Terminal, Database, Activity, Zap, BookOpen, BarChart2, Award, CheckCircle, Target, Clock } from 'lucide-react';

export default function CyberVantageThemeable() {
  const [theme, setTheme] = useState('soc'); // 'soc' or 'modern'
  const [activePhase, setActivePhase] = useState('learn');
  const [scanLines, setScanLines] = useState(0);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    if (theme === 'soc') {
      const scanInterval = setInterval(() => setScanLines(prev => (prev + 1) % 100), 50);
      const timeInterval = setInterval(() => setTime(new Date()), 1000);
      return () => {
        clearInterval(scanInterval);
        clearInterval(timeInterval);
      };
    }
  }, [theme]);

  const themes = {
    soc: {
      bg: '#0a0e27',
      bgSecondary: 'rgba(0, 0, 0, 0.5)',
      bgTertiary: 'rgba(0, 0, 0, 0.3)',
      text: '#00ff41',
      textSecondary: '#00ff4180',
      textTertiary: '#00ff4160',
      border: '#00d9ff40',
      primary: '#00d9ff',
      success: '#00ff41',
      warning: '#ffb800',
      danger: '#ff0055',
      fontFamily: '"JetBrains Mono", monospace'
    },
    modern: {
      bg: '#ffffff',
      bgSecondary: '#f8fafc',
      bgTertiary: '#f1f5f9',
      text: '#0f172a',
      textSecondary: '#64748b',
      textTertiary: '#94a3b8',
      border: '#e2e8f0',
      primary: '#3b82f6',
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444',
      fontFamily: '"Inter", sans-serif'
    }
  };

  const t = themes[theme];

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
      {theme === 'soc' && (
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
        borderBottom: theme === 'soc' ? `2px solid ${t.border}` : `1px solid ${t.border}`,
        background: theme === 'soc' ? t.bgSecondary : t.bg,
        backdropFilter: theme === 'soc' ? 'blur(10px)' : 'none',
        position: 'relative',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <Shield size={32} color={t.primary} strokeWidth={2} />
            <div>
              <div className={theme === 'soc' ? 'terminal-text' : ''} style={{ 
                fontSize: '1.5rem', 
                fontWeight: 800, 
                color: t.primary, 
                letterSpacing: theme === 'soc' ? '0.1em' : '-0.02em' 
              }}>
                {theme === 'soc' ? 'CYBERVANTAGE_SOC' : 'CyberVantage'}
              </div>
              <div style={{ fontSize: '0.75rem', color: t.textSecondary }}>
                {theme === 'soc' ? 'SECURITY OPERATIONS v2.4.1' : 'Security Training Platform'}
              </div>
            </div>
            {theme === 'soc' && (
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
            <button
              onClick={() => setTheme(theme === 'soc' ? 'modern' : 'soc')}
              style={{
                padding: '0.625rem 1.25rem',
                borderRadius: theme === 'soc' ? '0' : '8px',
                border: theme === 'soc' ? `1px solid ${t.primary}` : `1px solid ${t.border}`,
                background: theme === 'soc' ? 'rgba(0, 217, 255, 0.1)' : t.bgSecondary,
                color: theme === 'soc' ? t.primary : t.text,
                fontSize: '0.8rem',
                fontWeight: theme === 'soc' ? 700 : 600,
                letterSpacing: theme === 'soc' ? '0.05em' : 'normal',
                cursor: 'pointer',
                fontFamily: t.fontFamily,
                boxShadow: theme === 'soc' ? '0 0 20px rgba(0, 217, 255, 0.3)' : 'none',
                transition: 'all 0.3s ease'
              }}
            >
              {theme === 'soc' ? '[SWITCH_TO_MODERN]' : '🖥️ SOC Mode'}
            </button>

            <div style={{
              padding: '0.75rem 1.25rem',
              borderRadius: theme === 'soc' ? '0' : '8px',
              background: theme === 'soc' ? 'rgba(0, 255, 65, 0.05)' : `${t.warning}20`,
              border: theme === 'soc' ? `1px solid ${t.success}` : `1px solid ${t.warning}40`,
              boxShadow: theme === 'soc' ? `0 0 20px ${t.success}50` : 'none'
            }}>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary }}>
                {theme === 'soc' ? 'THREAT_POINTS' : 'Total Points'}
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: theme === 'soc' ? t.success : t.warning }}>
                2,840
              </div>
            </div>
          </div>
        </div>
      </header>

      <div style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
        {/* Sidebar */}
        <aside style={{
          width: '280px',
          borderRight: theme === 'soc' ? `2px solid ${t.border}` : `1px solid ${t.border}`,
          background: theme === 'soc' ? t.bgTertiary : t.bgSecondary,
          padding: '2rem 0',
          overflowY: 'auto'
        }}>
          <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
            <div style={{ 
              fontSize: '0.7rem', 
              color: t.textTertiary, 
              letterSpacing: theme === 'soc' ? '0.1em' : '0.05em', 
              marginBottom: '1rem',
              fontWeight: 700,
              textTransform: 'uppercase'
            }}>
              {theme === 'soc' ? 'SYSTEM_MODULES' : 'Learning Paths'}
            </div>
            
            {[
              { id: 'learn', label: theme === 'soc' ? 'LEARN' : 'Learn', icon: theme === 'soc' ? Database : BookOpen },
              { id: 'simulate', label: theme === 'soc' ? 'SIMULATE' : 'Simulate', icon: Terminal },
              { id: 'analyze', label: theme === 'soc' ? 'ANALYZE' : 'Analyze', icon: Activity },
              { id: 'demonstrate', label: theme === 'soc' ? 'DEMONSTRATE' : 'Demonstrate', icon: Zap }
            ].map((phase) => {
              const Icon = phase.icon;
              const isActive = activePhase === phase.id;
              return (
                <div
                  key={phase.id}
                  onClick={() => setActivePhase(phase.id)}
                  style={{
                    padding: theme === 'soc' ? '1rem' : '0.75rem 1rem',
                    marginBottom: '0.5rem',
                    background: isActive ? (theme === 'soc' ? 'rgba(0, 217, 255, 0.1)' : t.primary) : 'transparent',
                    border: isActive ? (theme === 'soc' ? `1px solid ${t.primary}` : 'none') : (theme === 'soc' ? '1px solid transparent' : 'none'),
                    borderRadius: theme === 'soc' ? '0' : '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: isActive ? (theme === 'soc' ? t.primary : '#fff') : t.textSecondary,
                    fontWeight: theme === 'soc' ? 700 : (isActive ? 600 : 500),
                    fontSize: theme === 'soc' ? '0.9rem' : '0.875rem',
                    letterSpacing: theme === 'soc' ? '0.05em' : 'normal',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  <span style={{ flex: 1 }}>{phase.label}</span>
                  {isActive && theme === 'soc' && (
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
              { label: theme === 'soc' ? 'DETECTION_RATE' : 'Detection Rate', value: '85.5%', color: t.success },
              { label: theme === 'soc' ? 'ACTIVE_STREAK' : 'Current Streak', value: '12 DAYS', color: t.warning },
              { label: theme === 'soc' ? 'THREATS_FOUND' : 'Threats Found', value: '47', color: t.primary },
              { label: theme === 'soc' ? 'AVG_RESPONSE' : 'Avg Response', value: '2.3s', color: '#8b5cf6' }
            ].map((stat, i) => (
              <div key={i} className="card" style={{
                padding: '1.5rem',
                background: theme === 'soc' ? t.bgTertiary : t.bgSecondary,
                border: theme === 'soc' ? `1px solid ${stat.color}40` : `1px solid ${t.border}`,
                borderRadius: theme === 'soc' ? '0' : '12px'
              }}>
                {theme === 'soc' && (
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: stat.color
                  }} />
                )}
                <div style={{ fontSize: theme === 'soc' ? '0.65rem' : '0.875rem', color: t.textSecondary, marginBottom: '0.75rem', fontWeight: 600 }}>
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
            background: theme === 'soc' ? t.bgTertiary : t.bgSecondary,
            border: theme === 'soc' ? `1px solid ${t.border}` : `1px solid ${t.border}`,
            borderRadius: theme === 'soc' ? '0' : '12px'
          }}>
            <h2 style={{
              margin: '0 0 1rem 0',
              fontSize: theme === 'soc' ? '1rem' : '1.5rem',
              fontWeight: theme === 'soc' ? 700 : 700,
              color: theme === 'soc' ? t.primary : t.text,
              letterSpacing: theme === 'soc' ? '0.05em' : 'normal'
            }}>
              {activePhase === 'learn' && (theme === 'soc' ? 'TRAINING_MODULES' : 'Learning Modules')}
              {activePhase === 'simulate' && (theme === 'soc' ? 'THREAT_SIMULATION' : 'Threat Simulation')}
              {activePhase === 'analyze' && (theme === 'soc' ? 'PERFORMANCE_ANALYTICS' : 'Performance Analytics')}
              {activePhase === 'demonstrate' && (theme === 'soc' ? 'RED_TEAM_EXERCISE' : 'Demonstrate Skills')}
            </h2>
            <p style={{ margin: 0, color: t.textSecondary, fontSize: '0.95rem' }}>
              Content for {activePhase} phase...
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
