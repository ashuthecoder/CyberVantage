import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Terminal, Database, Activity, Zap, BookOpen, BarChart2, Award, CheckCircle, Target, Clock, Info, LogOut, AlertTriangle, Eye, TrendingUp } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { theme: t, themeName, toggleTheme } = useTheme();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [activePhase, setActivePhase] = useState('learn');
  const [scanLines, setScanLines] = useState(0);
  const [time, setTime] = useState(new Date());

  const isSoc = themeName === 'soc';

  useEffect(() => {
    if (isSoc) {
      const scanInterval = setInterval(() => setScanLines(prev => (prev + 1) % 100), 50);
      const timeInterval = setInterval(() => setTime(new Date()), 1000);
      return () => {
        clearInterval(scanInterval);
        clearInterval(timeInterval);
      };
    }
  }, [isSoc]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const sidebarPhases = [
    { id: 'learn', label: isSoc ? 'LEARN' : 'Learn', icon: isSoc ? Database : BookOpen },
    { id: 'simulate', label: isSoc ? 'SIMULATE' : 'Simulate', icon: Terminal },
    { id: 'demonstrate', label: isSoc ? 'DEMONSTRATE' : 'Demonstrate', icon: Zap },
    { id: 'analyze', label: isSoc ? 'ANALYZE' : 'Analyze', icon: Activity }
  ];

  const sidebarNav = [
    { id: 'check-threats', label: isSoc ? 'CHECK_THREATS' : 'Check Threats', icon: Shield, path: '/check-threats' },
    { id: 'about', label: isSoc ? 'ABOUT' : 'About', icon: Info, path: '/about' }
  ];

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
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .card { transition: all 0.2s ease; }
        .card:hover { transform: translateY(-2px); }
      `}</style>

      {isSoc && (
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
            top: 0, left: 0, right: 0, bottom: 0,
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
        borderBottom: isSoc ? `2px solid ${t.border}` : `1px solid ${t.border}`,
        background: isSoc ? t.bgSecondary : t.bg,
        backdropFilter: isSoc ? 'blur(10px)' : 'none',
        position: 'relative',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <Shield size={32} color={t.primary} strokeWidth={2} />
            <div>
              <div className={isSoc ? 'terminal-text' : ''} style={{
                fontSize: '1.5rem', fontWeight: 800, color: t.primary,
                letterSpacing: isSoc ? '0.1em' : '-0.02em'
              }}>
                {isSoc ? 'CYBERVANTAGE_SOC' : 'CyberVantage'}
              </div>
              <div style={{ fontSize: '0.75rem', color: t.textSecondary }}>
                {isSoc ? 'SECURITY OPERATIONS v2.4.1' : 'Security Training Platform'}
              </div>
            </div>
            {isSoc && (
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
              onClick={toggleTheme}
              style={{
                padding: '0.625rem 1.25rem',
                borderRadius: isSoc ? '0' : '8px',
                border: isSoc ? `1px solid ${t.primary}` : `1px solid ${t.border}`,
                background: isSoc ? 'rgba(0, 217, 255, 0.1)' : t.bgSecondary,
                color: isSoc ? t.primary : t.text,
                fontSize: '0.8rem',
                fontWeight: isSoc ? 700 : 600,
                letterSpacing: isSoc ? '0.05em' : 'normal',
                cursor: 'pointer',
                fontFamily: t.fontFamily,
                boxShadow: isSoc ? '0 0 20px rgba(0, 217, 255, 0.3)' : 'none',
                transition: 'all 0.3s ease'
              }}
            >
              {isSoc ? '[SWITCH_TO_MODERN]' : '🖥️ SOC Mode'}
            </button>

            <div style={{
              padding: '0.75rem 1.25rem',
              borderRadius: isSoc ? '0' : '8px',
              background: isSoc ? 'rgba(0, 255, 65, 0.05)' : `${t.warning}20`,
              border: isSoc ? `1px solid ${t.success}` : `1px solid ${t.warning}40`,
              boxShadow: isSoc ? `0 0 20px ${t.success}50` : 'none'
            }}>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary }}>
                {isSoc ? 'THREAT_POINTS' : 'Total Points'}
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isSoc ? t.success : t.warning }}>
                2,840
              </div>
            </div>

            <button
              onClick={handleLogout}
              style={{
                padding: '0.625rem 1.25rem',
                borderRadius: isSoc ? '0' : '8px',
                border: isSoc ? `1px solid ${t.danger}` : `1px solid ${t.border}`,
                background: isSoc ? 'rgba(255, 0, 85, 0.1)' : t.bgSecondary,
                color: isSoc ? t.danger : t.text,
                fontSize: '0.8rem',
                fontWeight: isSoc ? 700 : 600,
                letterSpacing: isSoc ? '0.05em' : 'normal',
                cursor: 'pointer',
                fontFamily: t.fontFamily,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.3s ease'
              }}
            >
              <LogOut size={16} />
              {isSoc ? '[LOGOUT]' : 'Logout'}
            </button>
          </div>
        </div>
      </header>

      <div style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
        {/* Sidebar */}
        <aside style={{
          width: '280px',
          borderRight: isSoc ? `2px solid ${t.border}` : `1px solid ${t.border}`,
          background: isSoc ? t.bgTertiary : t.bgSecondary,
          padding: '2rem 0',
          overflowY: 'auto'
        }}>
          <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
            <div style={{
              fontSize: '0.7rem', color: t.textTertiary,
              letterSpacing: isSoc ? '0.1em' : '0.05em',
              marginBottom: '1rem', fontWeight: 700, textTransform: 'uppercase'
            }}>
              {isSoc ? 'SYSTEM_MODULES' : 'Learning Paths'}
            </div>

            {sidebarPhases.map((phase) => {
              const Icon = phase.icon;
              const isActive = activePhase === phase.id;
              return (
                <div
                  key={phase.id}
                  onClick={() => setActivePhase(phase.id)}
                  style={{
                    padding: isSoc ? '1rem' : '0.75rem 1rem',
                    marginBottom: '0.5rem',
                    background: isActive ? (isSoc ? 'rgba(0, 217, 255, 0.1)' : t.primary) : 'transparent',
                    border: isActive ? (isSoc ? `1px solid ${t.primary}` : 'none') : (isSoc ? '1px solid transparent' : 'none'),
                    borderRadius: isSoc ? '0' : '8px',
                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                    color: isActive ? (isSoc ? t.primary : '#fff') : t.textSecondary,
                    fontWeight: isSoc ? 700 : (isActive ? 600 : 500),
                    fontSize: isSoc ? '0.9rem' : '0.875rem',
                    letterSpacing: isSoc ? '0.05em' : 'normal',
                    cursor: 'pointer', transition: 'all 0.2s ease'
                  }}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  <span style={{ flex: 1 }}>{phase.label}</span>
                  {isActive && isSoc && (
                    <div style={{ width: '8px', height: '8px', background: t.primary, animation: 'pulse 2s infinite' }} />
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ padding: '0 1.5rem' }}>
            <div style={{
              fontSize: '0.7rem', color: t.textTertiary,
              letterSpacing: isSoc ? '0.1em' : '0.05em',
              marginBottom: '1rem', fontWeight: 700, textTransform: 'uppercase'
            }}>
              {isSoc ? 'NAVIGATION' : 'Navigation'}
            </div>

            {sidebarNav.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  onClick={() => navigate(item.path)}
                  style={{
                    padding: isSoc ? '1rem' : '0.75rem 1rem',
                    marginBottom: '0.5rem',
                    background: 'transparent',
                    border: isSoc ? '1px solid transparent' : 'none',
                    borderRadius: isSoc ? '0' : '8px',
                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                    color: t.textSecondary,
                    fontWeight: isSoc ? 700 : 500,
                    fontSize: isSoc ? '0.9rem' : '0.875rem',
                    letterSpacing: isSoc ? '0.05em' : 'normal',
                    cursor: 'pointer', transition: 'all 0.2s ease'
                  }}
                >
                  <Icon size={20} strokeWidth={2} />
                  <span style={{ flex: 1 }}>{item.label}</span>
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
              { id: 'detection', label: isSoc ? 'DETECTION_RATE' : 'Detection Rate', value: '85.5%', color: t.success },
              { id: 'streak', label: isSoc ? 'ACTIVE_STREAK' : 'Current Streak', value: '12 DAYS', color: t.warning },
              { id: 'threats', label: isSoc ? 'THREATS_FOUND' : 'Threats Found', value: '47', color: t.primary },
              { id: 'response', label: isSoc ? 'AVG_RESPONSE' : 'Avg Response', value: '2.3s', color: '#8b5cf6' }
            ].map((stat) => (
              <div key={stat.id} className="card" style={{
                padding: '1.5rem',
                background: isSoc ? t.bgTertiary : t.bgSecondary,
                border: isSoc ? `1px solid ${stat.color}40` : `1px solid ${t.border}`,
                borderRadius: isSoc ? '0' : '12px',
                position: 'relative', overflow: 'hidden'
              }}>
                {isSoc && (
                  <div style={{
                    position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: stat.color
                  }} />
                )}
                <div style={{ fontSize: isSoc ? '0.65rem' : '0.875rem', color: t.textSecondary, marginBottom: '0.75rem', fontWeight: 600 }}>
                  {stat.label}
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: stat.color }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>

          {/* Phase Content */}
          {activePhase === 'learn' && <LearnPhase t={t} isSoc={isSoc} />}
          {activePhase === 'simulate' && <SimulatePhase t={t} isSoc={isSoc} />}
          {activePhase === 'demonstrate' && <DemonstratePhase t={t} isSoc={isSoc} />}
          {activePhase === 'analyze' && <AnalyzePhase t={t} isSoc={isSoc} />}
        </main>
      </div>
    </div>
  );
}

function LearnPhase({ t, isSoc }) {
  const modules = [
    { id: 'MOD_001', name: 'PHISHING_FUNDAMENTALS', displayName: 'Phishing Fundamentals', progress: 100, status: 'COMPLETED', displayStatus: 'Completed', threat: 'LOW' },
    { id: 'MOD_002', name: 'SOCIAL_ENGINEERING', displayName: 'Social Engineering', progress: 70, status: 'IN_PROGRESS', displayStatus: 'In Progress', threat: 'MEDIUM' },
    { id: 'MOD_003', name: 'EMAIL_SECURITY_PROTOCOL', displayName: 'Email Security Protocol', progress: 45, status: 'IN_PROGRESS', displayStatus: 'In Progress', threat: 'MEDIUM' },
    { id: 'MOD_004', name: 'COMPLIANCE_STANDARDS', displayName: 'Compliance Standards', progress: 0, status: 'LOCKED', displayStatus: 'Locked', threat: 'LOW' }
  ];

  const getStatusColor = (status) => {
    if (status === 'COMPLETED') return t.success;
    if (status === 'IN_PROGRESS') return t.warning;
    return t.textTertiary;
  };

  return (
    <div>
      <div style={{
        fontSize: '0.8rem', color: t.primary,
        letterSpacing: isSoc ? '0.1em' : '0.02em',
        marginBottom: '1.5rem',
        borderBottom: `1px solid ${t.border}`,
        paddingBottom: '0.5rem'
      }}>
        {isSoc ? 'TRAINING_MODULES // SECURITY_EDUCATION_SYSTEM' : 'Training Modules — Security Education System'}
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        {modules.map((module, index) => (
          <div key={module.id} style={{
            padding: '1.5rem',
            background: isSoc ? t.bgTertiary : t.bgSecondary,
            border: `1px solid ${t.border}`,
            borderRadius: isSoc ? '0' : '12px',
            display: 'flex', alignItems: 'center', gap: '1.5rem',
            opacity: module.status === 'LOCKED' ? 0.4 : 1,
            cursor: module.status !== 'LOCKED' ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            animation: `slideUp 0.5s ease-out ${index * 0.1}s backwards`
          }}
          onMouseEnter={(e) => {
            if (module.status !== 'LOCKED') {
              e.currentTarget.style.borderColor = t.primary;
              e.currentTarget.style.transform = 'translateX(10px)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = t.border;
            e.currentTarget.style.transform = 'translateX(0)';
          }}>
            <div style={{
              width: '80px', padding: '1rem',
              background: isSoc ? 'rgba(0, 217, 255, 0.1)' : `${t.primary}10`,
              border: `1px solid ${t.primary}`,
              borderRadius: isSoc ? '0' : '8px',
              textAlign: 'center', fontSize: '0.7rem',
              color: t.primary, letterSpacing: '0.05em'
            }}>
              {module.id}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: t.text, letterSpacing: isSoc ? '0.05em' : 'normal' }}>
                  {isSoc ? module.name : module.displayName}
                </div>
                <div style={{
                  padding: '0.25rem 0.75rem',
                  background: `${getStatusColor(module.status)}15`,
                  border: `1px solid ${getStatusColor(module.status)}`,
                  borderRadius: isSoc ? '0' : '12px',
                  color: getStatusColor(module.status),
                  fontSize: '0.7rem', letterSpacing: isSoc ? '0.05em' : 'normal'
                }}>
                  {isSoc ? `[${module.status}]` : module.displayStatus}
                </div>
              </div>

              <div style={{
                position: 'relative', height: '6px',
                background: `${t.primary}30`,
                borderRadius: isSoc ? '0' : '3px',
                marginBottom: '0.5rem'
              }}>
                <div style={{
                  position: 'absolute', left: 0, top: 0, height: '100%',
                  width: `${module.progress}%`,
                  background: t.primary,
                  borderRadius: isSoc ? '0' : '3px',
                  transition: 'width 1s ease-out'
                }} />
              </div>

              <div style={{ fontSize: '0.75rem', color: t.textSecondary }}>
                {isSoc
                  ? `COMPLETION: ${module.progress}% // THREAT_LEVEL: ${module.threat}`
                  : `${module.progress}% complete · Threat Level: ${module.threat}`}
              </div>
            </div>

            <div style={{
              fontSize: '1.5rem',
              color: getStatusColor(module.status)
            }}>
              {module.status === 'COMPLETED' ? '✓' : module.status === 'IN_PROGRESS' ? '◐' : '⊘'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SimulatePhase({ t, isSoc }) {
  const navigate = useNavigate();
  const [selectedEmail, setSelectedEmail] = useState(null);

  // Real emails from the predefined list - 5 emails that will be shown in Phase 1
  const predefinedEmails = [
    { 
      id: 1, 
      from: 'security@paypa1.com', 
      subject: isSoc ? 'YOUR_ACCOUNT_COMPROMISED' : 'Your account has been compromised',
      preview: 'We have detected unusual activity on your account...',
      risk: 'CRITICAL', 
      indicators: 3,
      isSpam: true
    },
    { 
      id: 2, 
      from: 'amazondelivery@amazon-shipment.net', 
      subject: isSoc ? 'PACKAGE_DELIVERY_FAILED' : 'Your Amazon package delivery failed',
      preview: 'We attempted to deliver your package today but were unable...',
      risk: 'CRITICAL', 
      indicators: 4,
      isSpam: true
    },
    { 
      id: 3, 
      from: 'notifications@linkedin.com', 
      subject: isSoc ? 'NEW_CONNECTION_REQUESTS' : 'You have 3 new connection requests',
      preview: 'You have 3 new connection requests waiting for your response...',
      risk: 'SAFE', 
      indicators: 0,
      isSpam: false
    },
    { 
      id: 4, 
      from: 'microsoft365@outlook.cn', 
      subject: isSoc ? 'PASSWORD_EXPIRATION_URGENT' : 'Your Microsoft password will expire today',
      preview: 'URGENT: Your Microsoft password will expire in 12 hours...',
      risk: 'HIGH', 
      indicators: 2,
      isSpam: true
    },
    { 
      id: 5, 
      from: 'newsletter@nytimes.com', 
      subject: isSoc ? 'WEEKLY_NEWS_DIGEST' : 'Your Weekly News Digest from The New York Times',
      preview: 'This Week\'s Top Stories: Global Climate Summit Concludes...',
      risk: 'SAFE', 
      indicators: 0,
      isSpam: false
    }
  ];

  const getRiskColor = (risk) => {
    if (risk === 'CRITICAL') return t.danger;
    if (risk === 'HIGH') return t.warning;
    return t.success;
  };

  const handleStartSimulation = () => {
    // Navigate to the Flask simulation route
    window.location.href = '/simulate';
  };

  return (
    <div>
      <div style={{
        fontSize: '0.8rem', color: t.primary,
        letterSpacing: isSoc ? '0.1em' : '0.02em',
        marginBottom: '1.5rem',
        borderBottom: `1px solid ${t.border}`,
        paddingBottom: '0.5rem'
      }}>
        {isSoc ? 'THREAT_SIMULATION // PHISHING_EMAIL_TRAINING' : 'Threat Simulation — Phishing Email Training'}
      </div>

      {/* Info Panel */}
      <div style={{
        padding: '1.5rem',
        background: isSoc ? 'rgba(0, 217, 255, 0.05)' : `${t.primary}05`,
        border: `1px solid ${t.primary}`,
        borderRadius: isSoc ? '0' : '12px',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'start', gap: '1rem', marginBottom: '1rem' }}>
          <Terminal size={24} color={t.primary} />
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: t.text, marginBottom: '0.5rem' }}>
              {isSoc ? 'SIMULATION_PROTOCOL' : 'Simulation Protocol'}
            </div>
            <div style={{ fontSize: '0.85rem', color: t.textSecondary, lineHeight: 1.6 }}>
              {isSoc 
                ? '> PHASE_1: 5 PREDEFINED_EMAILS // PHASE_2: 5 AI_GENERATED_EMAILS'
                : 'Phase 1: Analyze 5 predefined emails · Phase 2: Analyze 5 AI-generated emails based on your performance'}
            </div>
          </div>
        </div>
        <button
          onClick={handleStartSimulation}
          style={{
            width: '100%',
            padding: '1rem',
            background: `${t.primary}`,
            border: 'none',
            borderRadius: isSoc ? '0' : '8px',
            color: '#fff',
            fontSize: '0.9rem',
            fontWeight: 700,
            cursor: 'pointer',
            letterSpacing: isSoc ? '0.05em' : 'normal',
            fontFamily: t.fontFamily,
            transition: 'all 0.3s ease',
            boxShadow: isSoc ? '0 0 20px rgba(0, 217, 255, 0.3)' : '0 2px 8px rgba(0,0,0,0.1)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = isSoc ? '0 0 30px rgba(0, 217, 255, 0.5)' : '0 4px 12px rgba(0,0,0,0.15)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = isSoc ? '0 0 20px rgba(0, 217, 255, 0.3)' : '0 2px 8px rgba(0,0,0,0.1)';
          }}
        >
          {isSoc ? '[START_SIMULATION]' : '🚀 Start Simulation'}
        </button>
      </div>

      {/* Email Preview Grid */}
      <div style={{
        fontSize: '0.75rem', 
        color: t.textSecondary, 
        marginBottom: '1rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: isSoc ? '0.1em' : '0.05em'
      }}>
        {isSoc ? 'PHASE_1_EMAIL_PREVIEW' : 'Phase 1 Email Preview (5 Emails)'}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
        {predefinedEmails.map((email, index) => {
          const isSelected = selectedEmail?.id === email.id;
          return (
            <div
              key={email.id}
              onClick={() => setSelectedEmail(email)}
              style={{
                padding: '1rem',
                background: isSelected ? (isSoc ? 'rgba(0, 217, 255, 0.1)' : `${t.primary}10`) : (isSoc ? t.bgTertiary : t.bgSecondary),
                border: isSelected ? `2px solid ${t.primary}` : `1px solid ${t.border}`,
                borderRadius: isSoc ? '0' : '8px',
                cursor: 'pointer', 
                transition: 'all 0.2s ease',
                animation: `slideUp 0.5s ease-out ${index * 0.1}s backwards`
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.borderColor = t.primary;
                  e.currentTarget.style.transform = 'translateY(-4px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.borderColor = t.border;
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', alignItems: 'start' }}>
                <span style={{ 
                  fontSize: '0.7rem', 
                  color: t.textTertiary, 
                  letterSpacing: isSoc ? '0.05em' : 'normal',
                  fontWeight: 600
                }}>
                  {isSoc ? `EMAIL_${String(email.id).padStart(3, '0')}` : `Email #${email.id}`}
                </span>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  fontSize: '0.65rem', 
                  fontWeight: 700,
                  borderRadius: isSoc ? '0' : '12px',
                  background: `${getRiskColor(email.risk)}15`,
                  border: `1px solid ${getRiskColor(email.risk)}`,
                  color: getRiskColor(email.risk)
                }}>
                  {isSoc ? `RISK:${email.risk}` : email.risk}
                </span>
              </div>
              
              <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.5rem' }}>
                {isSoc ? 'FROM: ' : 'From: '}{email.from}
              </div>
              
              <div style={{ fontSize: '0.85rem', color: t.text, fontWeight: 700, marginBottom: '0.5rem' }}>
                {email.subject}
              </div>
              
              <div style={{ 
                fontSize: '0.75rem', 
                color: t.textSecondary, 
                marginBottom: '0.75rem',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {email.preview}
              </div>
              
              {email.indicators > 0 && (
                <div style={{ fontSize: '0.7rem', color: t.danger }}>
                  {isSoc
                    ? `⚠ ${email.indicators} THREAT_INDICATORS`
                    : `⚠ ${email.indicators} threat indicators detected`}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* AI Generation Info */}
      <div style={{
        padding: '1.5rem',
        background: isSoc ? 'rgba(138, 92, 246, 0.05)' : '#f3e8ff',
        border: `1px solid ${isSoc ? '#8b5cf6' : '#c084fc'}`,
        borderRadius: isSoc ? '0' : '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <Zap size={20} color="#8b5cf6" />
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: isSoc ? '#a78bfa' : '#7c3aed' }}>
            {isSoc ? 'PHASE_2_AI_GENERATION' : 'Phase 2: AI-Generated Emails'}
          </div>
        </div>
        <div style={{ fontSize: '0.8rem', color: t.textSecondary, lineHeight: 1.6 }}>
          {isSoc 
            ? '> After Phase 1 completion, AI will generate 5 custom phishing scenarios tailored to your performance metrics. Difficulty adapts based on detection accuracy.'
            : 'After completing Phase 1, our AI will generate 5 custom phishing scenarios tailored to your performance. The difficulty adapts based on your detection accuracy.'}
        </div>
      </div>
    </div>
  );
}

function AnalyzePhase({ t, isSoc }) {
  const sessions = [
    { id: 14, date: isSoc ? 'TODAY' : 'Today', accuracy: 88, threats: 15, time: '2.1s' },
    { id: 13, date: isSoc ? 'YESTERDAY' : 'Yesterday', accuracy: 85, threats: 20, time: '2.3s' },
    { id: 12, date: isSoc ? '2_DAYS_AGO' : '2 days ago', accuracy: 92, threats: 18, time: '1.9s' },
    { id: 11, date: isSoc ? '3_DAYS_AGO' : '3 days ago', accuracy: 79, threats: 12, time: '2.8s' }
  ];

  const getAccuracyColor = (acc) => {
    if (acc >= 90) return t.success;
    if (acc >= 80) return t.primary;
    return t.warning;
  };

  return (
    <div>
      <div style={{
        fontSize: '0.8rem', color: t.primary,
        letterSpacing: isSoc ? '0.1em' : '0.02em',
        marginBottom: '1.5rem',
        borderBottom: `1px solid ${t.border}`,
        paddingBottom: '0.5rem'
      }}>
        {isSoc ? 'PERFORMANCE_ANALYTICS // THREAT_DETECTION_METRICS' : 'Performance Analytics — Threat Detection Metrics'}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
        {/* Chart */}
        <div style={{
          padding: '2rem',
          background: isSoc ? t.bgTertiary : t.bgSecondary,
          border: `1px solid ${t.border}`,
          borderRadius: isSoc ? '0' : '12px'
        }}>
          <div style={{ fontSize: '0.8rem', color: t.primary, marginBottom: '2rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
            {isSoc ? 'ACCURACY_TREND_ANALYSIS' : 'Accuracy Trend Analysis'}
          </div>

          <svg width="100%" height="200" style={{ overflow: 'visible' }}>
            {[0, 25, 50, 75, 100].map((y) => (
              <g key={`grid-${y}`}>
                <line x1="40" y1={180 - (y * 1.6)} x2="100%" y2={180 - (y * 1.6)} stroke={`${t.primary}20`} strokeWidth="1" />
                <text x="0" y={180 - (y * 1.6) + 5} fill={t.textTertiary} fontSize="10" fontFamily={t.fontFamily}>
                  {y}%
                </text>
              </g>
            ))}
            <polyline points="60,115 140,90 220,75 300,65 380,45" fill="none" stroke={t.primary} strokeWidth="2" />
            {[[60, 115], [140, 90], [220, 75], [300, 65], [380, 45]].map((point, i) => (
              <circle key={`point-${i}`} cx={point[0]} cy={point[1]} r="4" fill={t.primary} stroke={t.bg} strokeWidth="2" />
            ))}
          </svg>
        </div>

        {/* Stats sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            { label: isSoc ? 'BEST_ACCURACY' : 'Best Accuracy', value: '92%', sub: isSoc ? 'SESSION_12' : 'Session 12', color: t.success },
            { label: isSoc ? 'IMPROVEMENT' : 'Improvement', value: '+27%', sub: isSoc ? 'SINCE_START' : 'Since start', color: t.primary },
            { label: isSoc ? 'TOTAL_SESSIONS' : 'Total Sessions', value: '14', sub: isSoc ? 'LAST_30_DAYS' : 'Last 30 days', color: t.warning }
          ].map((stat) => (
            <div key={stat.label} style={{
              padding: '1.5rem',
              background: `${stat.color}08`,
              border: `1px solid ${stat.color}`,
              borderRadius: isSoc ? '0' : '12px',
              textAlign: 'center',
              boxShadow: isSoc ? `0 0 20px ${stat.color}30` : 'none'
            }}>
              <div style={{ fontSize: '0.65rem', color: t.textSecondary, marginBottom: '0.5rem' }}>{stat.label}</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: stat.color }}>{stat.value}</div>
              <div style={{ fontSize: '0.7rem', color: t.textTertiary, marginTop: '0.25rem' }}>{stat.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Session Log */}
      <div style={{
        padding: '2rem',
        background: isSoc ? t.bgTertiary : t.bgSecondary,
        border: `1px solid ${t.border}`,
        borderRadius: isSoc ? '0' : '12px'
      }}>
        <div style={{ fontSize: '0.8rem', color: t.primary, marginBottom: '1.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
          {isSoc ? 'SESSION_HISTORY_LOG' : 'Session History'}
        </div>

        {sessions.map((session, index) => (
          <div key={`session-${session.id}`} style={{
            padding: '1rem',
            background: `${t.primary}08`,
            border: `1px solid ${t.border}`,
            borderRadius: isSoc ? '0' : '8px',
            marginBottom: '0.75rem',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            animation: `slideUp 0.5s ease-out ${index * 0.1}s backwards`
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <div style={{
                width: '60px', padding: '0.75rem',
                background: `${t.primary}15`,
                border: `1px solid ${t.primary}`,
                borderRadius: isSoc ? '0' : '8px',
                textAlign: 'center', fontSize: '0.9rem', fontWeight: 700, color: t.primary
              }}>
                {session.id}
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: t.text, marginBottom: '0.25rem' }}>
                  {isSoc ? `SESSION_${session.id}` : `Session ${session.id}`}
                </div>
                <div style={{ fontSize: '0.7rem', color: t.textSecondary }}>
                  {isSoc
                    ? `${session.date} // ${session.threats}_THREATS_ANALYZED`
                    : `${session.date} · ${session.threats} threats analyzed`}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '2rem', textAlign: 'right' }}>
              <div>
                <div style={{ fontSize: '0.65rem', color: t.textSecondary, marginBottom: '0.25rem' }}>
                  {isSoc ? 'ACCURACY' : 'Accuracy'}
                </div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: getAccuracyColor(session.accuracy) }}>
                  {session.accuracy}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: t.textSecondary, marginBottom: '0.25rem' }}>
                  {isSoc ? 'AVG_TIME' : 'Avg Time'}
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: t.primary }}>
                  {session.time}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DemonstratePhase({ t, isSoc }) {
  const breakdownItems = [
    { metric: isSoc ? 'URGENCY_TACTICS' : 'Urgency Tactics', score: 92 },
    { metric: isSoc ? 'AUTHORITY_MIMICRY' : 'Authority Mimicry', score: 85 },
    { metric: isSoc ? 'TECHNICAL_SOPHISTICATION' : 'Technical Sophistication', score: 81 },
    { metric: isSoc ? 'SOCIAL_ENGINEERING' : 'Social Engineering', score: 90 }
  ];

  const tactics = ['URGENCY', 'AUTHORITY', 'FEAR', 'CURIOSITY', 'GREED'];
  const tacticLabels = isSoc ? tactics : ['Urgency', 'Authority', 'Fear', 'Curiosity', 'Greed'];

  return (
    <div>
      <div style={{
        fontSize: '0.8rem', color: t.primary,
        letterSpacing: isSoc ? '0.1em' : '0.02em',
        marginBottom: '1.5rem',
        borderBottom: `1px solid ${t.border}`,
        paddingBottom: '0.5rem'
      }}>
        {isSoc ? 'RED_TEAM_EXERCISE // PHISHING_SIMULATION_CREATOR' : 'Red Team Exercise — Phishing Simulation Creator'}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Threat Composer */}
        <div style={{
          padding: '2rem',
          background: isSoc ? t.bgTertiary : t.bgSecondary,
          border: `1px solid ${t.border}`,
          borderRadius: isSoc ? '0' : '12px'
        }}>
          <div style={{ fontSize: '0.8rem', color: t.primary, marginBottom: '1.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
            {isSoc ? 'THREAT_COMPOSER' : 'Threat Composer'}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
                {isSoc ? 'TARGET_SCENARIO' : 'Target Scenario'}
              </div>
              <select style={{
                width: '100%', padding: '0.75rem',
                background: isSoc ? 'rgba(0, 0, 0, 0.5)' : t.bgTertiary,
                border: `1px solid ${t.border}`,
                borderRadius: isSoc ? '0' : '8px',
                color: t.primary, fontSize: '0.8rem',
                fontFamily: t.fontFamily
              }}>
                <option>{isSoc ? 'BANK_ACCOUNT_VERIFICATION' : 'Bank Account Verification'}</option>
                <option>{isSoc ? 'PACKAGE_DELIVERY_ALERT' : 'Package Delivery Alert'}</option>
                <option>{isSoc ? 'IT_SECURITY_WARNING' : 'IT Security Warning'}</option>
                <option>{isSoc ? 'HR_BENEFITS_UPDATE' : 'HR Benefits Update'}</option>
              </select>
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
                {isSoc ? 'SENDER_ADDRESS' : 'Sender Address'}
              </div>
              <input
                type="text"
                placeholder="security@paypa1-verify.com"
                style={{
                  width: '100%', padding: '0.75rem',
                  background: isSoc ? 'rgba(0, 0, 0, 0.5)' : t.bgTertiary,
                  border: `1px solid ${t.border}`,
                  borderRadius: isSoc ? '0' : '8px',
                  color: t.text, fontSize: '0.8rem',
                  fontFamily: t.fontFamily, boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
                {isSoc ? 'SUBJECT_LINE' : 'Subject Line'}
              </div>
              <input
                type="text"
                placeholder={isSoc ? 'URGENT_VERIFICATION_REQUIRED' : 'Urgent Verification Required'}
                style={{
                  width: '100%', padding: '0.75rem',
                  background: isSoc ? 'rgba(0, 0, 0, 0.5)' : t.bgTertiary,
                  border: `1px solid ${t.border}`,
                  borderRadius: isSoc ? '0' : '8px',
                  color: t.text, fontSize: '0.8rem',
                  fontFamily: t.fontFamily, boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
                {isSoc ? 'MESSAGE_PAYLOAD' : 'Email Body'}
              </div>
              <textarea
                placeholder={isSoc ? '// Construct phishing email content...' : 'Construct your phishing email content...'}
                style={{
                  width: '100%', minHeight: '150px', padding: '1rem',
                  background: isSoc ? 'rgba(0, 0, 0, 0.5)' : t.bgTertiary,
                  border: `1px solid ${t.border}`,
                  borderRadius: isSoc ? '0' : '8px',
                  color: t.text, fontSize: '0.8rem',
                  fontFamily: t.fontFamily, resize: 'vertical',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.75rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
                {isSoc ? 'SOCIAL_ENGINEERING_TACTICS' : 'Social Engineering Tactics'}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                {tacticLabels.map((tactic) => (
                  <button key={tactic} style={{
                    padding: '0.5rem 1rem',
                    background: `${t.warning}15`,
                    border: `1px solid ${t.warning}`,
                    borderRadius: isSoc ? '0' : '8px',
                    color: t.warning, fontSize: '0.7rem',
                    cursor: 'pointer', letterSpacing: isSoc ? '0.05em' : 'normal',
                    fontFamily: t.fontFamily, transition: 'all 0.2s ease'
                  }}>
                    {isSoc ? `[${tactic}]` : tactic}
                  </button>
                ))}
              </div>
            </div>

            <button style={{
              width: '100%', padding: '1rem',
              background: `${t.warning}15`,
              border: `1px solid ${t.warning}`,
              borderRadius: isSoc ? '0' : '8px',
              color: t.warning, fontSize: '0.9rem', fontWeight: 700,
              cursor: 'pointer', letterSpacing: isSoc ? '0.05em' : 'normal',
              fontFamily: t.fontFamily, transition: 'all 0.2s ease'
            }}>
              {isSoc ? '[EXECUTE_AI_EVALUATION]' : 'Run AI Evaluation'}
            </button>
          </div>
        </div>

        {/* Scoring Rubric / AI Results */}
        <div style={{
          padding: '2rem',
          background: isSoc ? t.bgTertiary : t.bgSecondary,
          border: `1px solid ${t.border}`,
          borderRadius: isSoc ? '0' : '12px'
        }}>
          <div style={{ fontSize: '0.8rem', color: t.primary, marginBottom: '1.5rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
            {isSoc ? 'AI_EVALUATION_RESULTS' : 'AI Evaluation Results'}
          </div>

          <div style={{
            padding: '2rem',
            background: `${t.warning}10`,
            border: `2px solid ${t.warning}`,
            borderRadius: isSoc ? '0' : '12px',
            marginBottom: '2rem', textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.7rem', color: t.textSecondary, marginBottom: '0.5rem' }}>
              {isSoc ? 'THREAT_SCORE' : 'Threat Score'}
            </div>
            <div style={{ fontSize: '4rem', fontWeight: 800, color: t.warning, lineHeight: 1 }}>87</div>
            <div style={{ fontSize: '0.8rem', color: t.textSecondary, marginTop: '0.5rem' }}>/100</div>
          </div>

          <div style={{ fontSize: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.8rem', color: t.primary, marginBottom: '1rem', letterSpacing: isSoc ? '0.05em' : 'normal' }}>
              {isSoc ? 'BREAKDOWN_ANALYSIS' : 'Breakdown Analysis'}
            </div>

            {breakdownItems.map((item) => (
              <div key={item.metric} style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: t.textSecondary, fontSize: '0.75rem' }}>{item.metric}</span>
                  <span style={{ color: t.warning, fontWeight: 700 }}>{item.score}/100</span>
                </div>
                <div style={{ height: '4px', background: `${t.warning}30`, borderRadius: isSoc ? '0' : '2px' }}>
                  <div style={{
                    width: `${item.score}%`, height: '100%',
                    background: t.warning,
                    borderRadius: isSoc ? '0' : '2px',
                    transition: 'width 1s ease-out'
                  }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{
            padding: '1rem',
            background: `${t.primary}10`,
            border: `1px solid ${t.border}`,
            borderRadius: isSoc ? '0' : '8px',
            fontSize: '0.75rem', color: t.primary, lineHeight: 1.8
          }}>
            <div style={{ marginBottom: '0.5rem', fontWeight: 700 }}>
              {isSoc ? 'RECOMMENDATIONS:' : 'Recommendations:'}
            </div>
            <div style={{ color: t.textSecondary }}>
              {isSoc ? (
                <>
                  {'> INCREASE_TECHNICAL_DETAILS'}<br />
                  {'> ADD_DEADLINE_PRESSURE'}<br />
                  {'> ENHANCE_CALL_TO_ACTION'}
                </>
              ) : (
                <>
                  {'• Increase technical details'}<br />
                  {'• Add deadline pressure'}<br />
                  {'• Enhance call to action'}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}