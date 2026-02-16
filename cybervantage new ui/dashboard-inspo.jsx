import React, { useState, useEffect } from 'react';
import { Terminal, Shield, Activity, Database, Zap, AlertTriangle, CheckCircle, XCircle, TrendingUp, Clock, Target, Eye } from 'lucide-react';

export default function SOCTemplate() {
  const [activePhase, setActivePhase] = useState('learn');
  const [scanLines, setScanLines] = useState(0);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const scanInterval = setInterval(() => {
      setScanLines(prev => (prev + 1) % 100);
    }, 50);
    
    const timeInterval = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => {
      clearInterval(scanInterval);
      clearInterval(timeInterval);
    };
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0e27',
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      color: '#00ff41',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Scan line effect */}
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

      {/* Grid overlay */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `
          linear-gradient(rgba(0, 217, 255, 0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0, 217, 255, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '50px 50px',
        pointerEvents: 'none',
        opacity: 0.3
      }} />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');
        
        @keyframes flicker {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.95; }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
        
        .terminal-text {
          text-shadow: 0 0 10px currentColor;
          animation: flicker 3s infinite;
        }
        
        .glow-cyan {
          box-shadow: 0 0 20px rgba(0, 217, 255, 0.5), inset 0 0 20px rgba(0, 217, 255, 0.1);
          border: 1px solid #00d9ff;
        }
        
        .glow-amber {
          box-shadow: 0 0 20px rgba(255, 184, 0, 0.5), inset 0 0 20px rgba(255, 184, 0, 0.1);
          border: 1px solid #ffb800;
        }
        
        .glow-green {
          box-shadow: 0 0 20px rgba(0, 255, 65, 0.5), inset 0 0 20px rgba(0, 255, 65, 0.1);
          border: 1px solid #00ff41;
        }
        
        .glow-red {
          box-shadow: 0 0 20px rgba(255, 0, 85, 0.5), inset 0 0 20px rgba(255, 0, 85, 0.1);
          border: 1px solid #ff0055;
        }
        
        .terminal-button {
          transition: all 0.2s ease;
          cursor: pointer;
        }
        
        .terminal-button:hover {
          transform: translateX(5px);
          text-shadow: 0 0 15px currentColor;
        }
        
        .stat-display {
          font-variant-numeric: tabular-nums;
        }
      `}</style>

      {/* Header */}
      <header style={{
        padding: '1rem 2rem',
        borderBottom: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(10px)',
        position: 'relative',
        zIndex: 10
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Shield size={32} color="#00d9ff" strokeWidth={2} />
              <div>
                <div className="terminal-text" style={{ fontSize: '1.5rem', fontWeight: 800, color: '#00d9ff', letterSpacing: '0.1em' }}>
                  CYBERVANTAGE_SOC
                </div>
                <div style={{ fontSize: '0.75rem', color: '#00ff4180', letterSpacing: '0.05em' }}>
                  SECURITY OPERATIONS CENTER v2.4.1
                </div>
              </div>
            </div>
            
            <div style={{
              padding: '0.5rem 1rem',
              background: 'rgba(0, 217, 255, 0.1)',
              border: '1px solid #00d9ff40',
              fontSize: '0.8rem',
              color: '#00d9ff',
              letterSpacing: '0.05em'
            }}>
              OPERATOR: {time.toLocaleTimeString('en-US', { hour12: false })} UTC
            </div>
          </div>

          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.25rem' }}>CLEARANCE_LEVEL</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#ffb800' }}>ADVANCED_ANALYST</div>
            </div>
            <div className="glow-green" style={{
              padding: '0.75rem 1.25rem',
              background: 'rgba(0, 255, 65, 0.05)'
            }}>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.25rem' }}>THREAT_POINTS</div>
              <div className="stat-display" style={{ fontSize: '1.5rem', fontWeight: 800, color: '#00ff41' }}>2,840</div>
            </div>
          </div>
        </div>
      </header>

      <div style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
        {/* Sidebar */}
        <aside style={{
          width: '280px',
          borderRight: '2px solid #00d9ff40',
          background: 'rgba(0, 0, 0, 0.3)',
          padding: '2rem 0',
          overflowY: 'auto'
        }}>
          <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
            <div style={{ fontSize: '0.7rem', color: '#00ff4180', letterSpacing: '0.1em', marginBottom: '1rem' }}>
              SYSTEM_MODULES
            </div>
            
            {[
              { id: 'learn', label: 'LEARN', icon: Database, status: 'ACTIVE' },
              { id: 'simulate', label: 'SIMULATE', icon: Terminal, status: 'ACTIVE' },
              { id: 'analyze', label: 'ANALYZE', icon: Activity, status: 'ACTIVE' },
              { id: 'demonstrate', label: 'DEMONSTRATE', icon: Zap, status: 'READY' }
            ].map((phase) => {
              const Icon = phase.icon;
              const isActive = activePhase === phase.id;
              return (
                <div
                  key={phase.id}
                  className="terminal-button"
                  onClick={() => setActivePhase(phase.id)}
                  style={{
                    padding: '1rem',
                    marginBottom: '0.5rem',
                    background: isActive ? 'rgba(0, 217, 255, 0.1)' : 'transparent',
                    border: isActive ? '1px solid #00d9ff' : '1px solid transparent',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    color: isActive ? '#00d9ff' : '#00ff4180'
                  }}
                >
                  <Icon size={20} strokeWidth={2} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, letterSpacing: '0.05em' }}>
                      {phase.label}
                    </div>
                    <div style={{ fontSize: '0.65rem', marginTop: '0.25rem' }}>
                      [{phase.status}]
                    </div>
                  </div>
                  {isActive && (
                    <div style={{
                      width: '8px',
                      height: '8px',
                      background: '#00d9ff',
                      animation: 'pulse 2s infinite'
                    }} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Threat Feed */}
          <div style={{ padding: '0 1.5rem', marginTop: '2rem' }}>
            <div style={{ fontSize: '0.7rem', color: '#ffb800', letterSpacing: '0.1em', marginBottom: '1rem' }}>
              LIVE_THREAT_FEED
            </div>
            <div style={{ fontSize: '0.75rem', color: '#00ff4160', lineHeight: 1.8 }}>
              {[
                '> NEW_THREAT_DETECTED: SPEAR_PHISHING',
                '> CLASSIFICATION: HIGH_PRIORITY',
                '> SCANNING_IP: 192.168.1.xxx',
                '> BEHAVIORAL_ANALYSIS: RUNNING',
                '> THREAT_DB_UPDATED: 2m_AGO'
              ].map((line, i) => (
                <div key={i} style={{ marginBottom: '0.5rem', animation: `slideUp 0.5s ease-out ${i * 0.1}s backwards` }}>
                  {line}
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
          {/* Stats Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
            <StatPanel label="DETECTION_RATE" value="85.5%" color="#00ff41" status="OPTIMAL" />
            <StatPanel label="ACTIVE_STREAK" value="12 DAYS" color="#ffb800" status="ONGOING" />
            <StatPanel label="THREATS_DETECTED" value="47" color="#00d9ff" status="TRACKING" />
            <StatPanel label="AVG_RESPONSE" value="2.3s" color="#ff0055" status="FAST" />
          </div>

          {/* Phase Content */}
          {activePhase === 'learn' && <LearnPhase />}
          {activePhase === 'simulate' && <SimulatePhase />}
          {activePhase === 'analyze' && <AnalyzePhase />}
          {activePhase === 'demonstrate' && <DemonstratePhase />}
        </main>
      </div>
    </div>
  );
}

function StatPanel({ label, value, color, status }) {
  return (
    <div style={{
      padding: '1.5rem',
      background: 'rgba(0, 0, 0, 0.3)',
      border: `1px solid ${color}40`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '2px',
        background: color,
        opacity: 0.5
      }} />
      
      <div style={{ fontSize: '0.65rem', color: `${color}80`, letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
        {label}
      </div>
      <div className="stat-display" style={{ fontSize: '2rem', fontWeight: 800, color: color, marginBottom: '0.5rem' }}>
        {value}
      </div>
      <div style={{ fontSize: '0.7rem', color: `${color}60` }}>
        [{status}]
      </div>
    </div>
  );
}

function LearnPhase() {
  const modules = [
    { id: 'MOD_001', name: 'PHISHING_FUNDAMENTALS', progress: 100, status: 'COMPLETED', threat: 'LOW' },
    { id: 'MOD_002', name: 'SOCIAL_ENGINEERING', progress: 70, status: 'IN_PROGRESS', threat: 'MEDIUM' },
    { id: 'MOD_003', name: 'EMAIL_SECURITY_PROTOCOL', progress: 45, status: 'IN_PROGRESS', threat: 'MEDIUM' },
    { id: 'MOD_004', name: 'COMPLIANCE_STANDARDS', progress: 0, status: 'LOCKED', threat: 'LOW' }
  ];

  return (
    <div>
      <div style={{ 
        fontSize: '0.8rem', 
        color: '#00d9ff', 
        letterSpacing: '0.1em', 
        marginBottom: '1.5rem',
        borderBottom: '1px solid #00d9ff40',
        paddingBottom: '0.5rem'
      }}>
        TRAINING_MODULES // SECURITY_EDUCATION_SYSTEM
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        {modules.map((module, index) => (
          <div key={module.id} style={{
            padding: '1.5rem',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid #00d9ff40',
            display: 'flex',
            alignItems: 'center',
            gap: '1.5rem',
            opacity: module.status === 'LOCKED' ? 0.4 : 1,
            cursor: module.status !== 'LOCKED' ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            animation: `slideUp 0.5s ease-out ${index * 0.1}s backwards`
          }}
          onMouseEnter={(e) => {
            if (module.status !== 'LOCKED') {
              e.currentTarget.style.borderColor = '#00d9ff';
              e.currentTarget.style.transform = 'translateX(10px)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#00d9ff40';
            e.currentTarget.style.transform = 'translateX(0)';
          }}>
            <div style={{
              width: '80px',
              padding: '1rem',
              background: 'rgba(0, 217, 255, 0.1)',
              border: '1px solid #00d9ff',
              textAlign: 'center',
              fontSize: '0.7rem',
              color: '#00d9ff',
              letterSpacing: '0.05em'
            }}>
              {module.id}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#00ff41', letterSpacing: '0.05em' }}>
                  {module.name}
                </div>
                <div style={{
                  padding: '0.25rem 0.75rem',
                  background: module.status === 'COMPLETED' ? 'rgba(0, 255, 65, 0.1)' :
                              module.status === 'IN_PROGRESS' ? 'rgba(255, 184, 0, 0.1)' :
                              'rgba(255, 255, 255, 0.1)',
                  border: module.status === 'COMPLETED' ? '1px solid #00ff41' :
                          module.status === 'IN_PROGRESS' ? '1px solid #ffb800' :
                          '1px solid #ffffff40',
                  color: module.status === 'COMPLETED' ? '#00ff41' :
                         module.status === 'IN_PROGRESS' ? '#ffb800' :
                         '#ffffff60',
                  fontSize: '0.7rem',
                  letterSpacing: '0.05em'
                }}>
                  [{module.status}]
                </div>
              </div>

              <div style={{ position: 'relative', height: '6px', background: 'rgba(0, 217, 255, 0.2)', marginBottom: '0.5rem' }}>
                <div style={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  height: '100%',
                  width: `${module.progress}%`,
                  background: '#00d9ff',
                  transition: 'width 1s ease-out'
                }} />
              </div>

              <div style={{ fontSize: '0.75rem', color: '#00d9ff80' }}>
                COMPLETION: {module.progress}% // THREAT_LEVEL: {module.threat}
              </div>
            </div>

            <div style={{
              fontSize: '1.5rem',
              color: module.status === 'COMPLETED' ? '#00ff41' : 
                     module.status === 'IN_PROGRESS' ? '#ffb800' : '#ffffff40'
            }}>
              {module.status === 'COMPLETED' ? '✓' : module.status === 'IN_PROGRESS' ? '◐' : '⊘'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SimulatePhase() {
  const [selectedEmail, setSelectedEmail] = useState(null);
  
  const threats = [
    { id: 'THREAT_001', from: 'security@paypa1-verify.com', subject: 'URGENT_ACCOUNT_VERIFICATION', risk: 'CRITICAL', indicators: 3 },
    { id: 'THREAT_002', from: 'hr@company.com', subject: 'BENEFITS_UPDATE_2024', risk: 'SAFE', indicators: 0 },
    { id: 'THREAT_003', from: 'no-reply@amaz0n-security.net', subject: 'ORDER_CANCELLED_#8472819', risk: 'HIGH', indicators: 4 },
    { id: 'THREAT_004', from: 'notifications@linkedin.com', subject: 'NEW_CONNECTION_REQUESTS', risk: 'SAFE', indicators: 0 }
  ];

  return (
    <div>
      <div style={{ 
        fontSize: '0.8rem', 
        color: '#00d9ff', 
        letterSpacing: '0.1em', 
        marginBottom: '1.5rem',
        borderBottom: '1px solid #00d9ff40',
        paddingBottom: '0.5rem'
      }}>
        THREAT_SIMULATION // INCIDENT_RESPONSE_TRAINING
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Threat Queue */}
        <div>
          <div style={{
            padding: '1rem',
            background: 'rgba(0, 217, 255, 0.1)',
            border: '1px solid #00d9ff',
            marginBottom: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span style={{ fontSize: '0.8rem', color: '#00d9ff', letterSpacing: '0.05em' }}>
              INCIDENT_QUEUE // SESSION_14
            </span>
            <span style={{ fontSize: '0.8rem', color: '#ffb800' }}>
              {threats.length} THREATS_PENDING
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {threats.map((threat, index) => (
              <div
                key={threat.id}
                onClick={() => setSelectedEmail(threat)}
                style={{
                  padding: '1rem',
                  background: selectedEmail?.id === threat.id ? 'rgba(0, 217, 255, 0.1)' : 'rgba(0, 0, 0, 0.3)',
                  border: selectedEmail?.id === threat.id ? '1px solid #00d9ff' : '1px solid #00d9ff40',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  animation: `slideUp 0.5s ease-out ${index * 0.1}s backwards`
                }}
                onMouseEnter={(e) => {
                  if (selectedEmail?.id !== threat.id) {
                    e.currentTarget.style.borderColor = '#00d9ff80';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedEmail?.id !== threat.id) {
                    e.currentTarget.style.borderColor = '#00d9ff40';
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: '#00d9ff80', letterSpacing: '0.05em' }}>
                    {threat.id}
                  </span>
                  <span className={threat.risk === 'CRITICAL' || threat.risk === 'HIGH' ? 'glow-red' : 'glow-green'} style={{
                    padding: '0.25rem 0.75rem',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    background: threat.risk === 'CRITICAL' ? 'rgba(255, 0, 85, 0.1)' :
                                threat.risk === 'HIGH' ? 'rgba(255, 184, 0, 0.1)' :
                                'rgba(0, 255, 65, 0.1)',
                    color: threat.risk === 'CRITICAL' ? '#ff0055' :
                           threat.risk === 'HIGH' ? '#ffb800' :
                           '#00ff41'
                  }}>
                    RISK: {threat.risk}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#ffffff80', marginBottom: '0.25rem' }}>
                  FROM: {threat.from}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#00ff41', fontWeight: 700 }}>
                  SUBJECT: {threat.subject}
                </div>
                {threat.indicators > 0 && (
                  <div style={{ fontSize: '0.7rem', color: '#ff0055', marginTop: '0.5rem' }}>
                    ⚠ {threat.indicators} THREAT_INDICATORS_DETECTED
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Analysis Terminal */}
        <div>
          {selectedEmail ? (
            <div style={{
              padding: '1.5rem',
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid #00d9ff',
              height: 'fit-content'
            }}>
              <div style={{ fontSize: '0.8rem', color: '#00d9ff', letterSpacing: '0.1em', marginBottom: '1.5rem' }}>
                THREAT_ANALYSIS_TERMINAL
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.75rem', letterSpacing: '0.05em' }}>
                  CLASSIFICATION_REQUIRED
                </div>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button className="glow-green" style={{
                    flex: 1,
                    padding: '1rem',
                    background: 'rgba(0, 255, 65, 0.05)',
                    color: '#00ff41',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    letterSpacing: '0.05em',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(0, 255, 65, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(0, 255, 65, 0.05)';
                  }}>
                    [LEGITIMATE]
                  </button>
                  <button className="glow-red" style={{
                    flex: 1,
                    padding: '1rem',
                    background: 'rgba(255, 0, 85, 0.05)',
                    color: '#ff0055',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    letterSpacing: '0.05em',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 0, 85, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 0, 85, 0.05)';
                  }}>
                    [PHISHING]
                  </button>
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.75rem', letterSpacing: '0.05em' }}>
                  INDICATORS_DETECTED
                </div>
                <div style={{ fontSize: '0.75rem', color: '#ff0055', lineHeight: 2 }}>
                  {['> SUSPICIOUS_DOMAIN_DETECTED', '> URGENCY_LANGUAGE_PRESENT', '> TYPOSQUATTING_IDENTIFIED'].map((line, i) => (
                    <div key={i}>{line}</div>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.75rem', letterSpacing: '0.05em' }}>
                  ANALYSIS_REASONING
                </div>
                <textarea
                  placeholder="// Enter detailed threat analysis..."
                  style={{
                    width: '100%',
                    minHeight: '120px',
                    padding: '1rem',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid #00d9ff40',
                    color: '#00ff41',
                    fontSize: '0.8rem',
                    fontFamily: 'inherit',
                    resize: 'vertical'
                  }}
                />
              </div>

              <button className="glow-cyan" style={{
                width: '100%',
                padding: '1rem',
                background: 'rgba(0, 217, 255, 0.1)',
                color: '#00d9ff',
                fontSize: '0.9rem',
                fontWeight: 700,
                cursor: 'pointer',
                letterSpacing: '0.05em',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(0, 217, 255, 0.2)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(0, 217, 255, 0.1)';
              }}>
                [SUBMIT_ANALYSIS]
              </button>
            </div>
          ) : (
            <div style={{
              padding: '3rem 2rem',
              background: 'rgba(0, 0, 0, 0.3)',
              border: '2px dashed #00d9ff40',
              textAlign: 'center',
              color: '#00d9ff60'
            }}>
              <Terminal size={48} style={{ margin: '0 auto 1rem' }} />
              <div style={{ fontSize: '0.9rem', letterSpacing: '0.05em' }}>
                SELECT_THREAT_TO_BEGIN_ANALYSIS
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnalyzePhase() {
  return (
    <div>
      <div style={{ 
        fontSize: '0.8rem', 
        color: '#00d9ff', 
        letterSpacing: '0.1em', 
        marginBottom: '1.5rem',
        borderBottom: '1px solid #00d9ff40',
        paddingBottom: '0.5rem'
      }}>
        PERFORMANCE_ANALYTICS // THREAT_DETECTION_METRICS
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
        <div style={{
          padding: '2rem',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid #00d9ff40'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#00d9ff', marginBottom: '2rem', letterSpacing: '0.05em' }}>
            ACCURACY_TREND_ANALYSIS
          </div>
          
          <svg width="100%" height="200" style={{ overflow: 'visible' }}>
            {/* Grid */}
            {[0, 25, 50, 75, 100].map((y, i) => (
              <g key={i}>
                <line
                  x1="40"
                  y1={180 - (y * 1.6)}
                  x2="100%"
                  y2={180 - (y * 1.6)}
                  stroke="#00d9ff20"
                  strokeWidth="1"
                />
                <text
                  x="0"
                  y={180 - (y * 1.6) + 5}
                  fill="#00d9ff60"
                  fontSize="10"
                  fontFamily="JetBrains Mono"
                >
                  {y}%
                </text>
              </g>
            ))}

            {/* Line */}
            <polyline
              points="60,115 140,90 220,75 300,65 380,45"
              fill="none"
              stroke="#00d9ff"
              strokeWidth="2"
            />

            {/* Points */}
            {[[60, 115], [140, 90], [220, 75], [300, 65], [380, 45]].map((point, i) => (
              <circle
                key={i}
                cx={point[0]}
                cy={point[1]}
                r="4"
                fill="#00d9ff"
                stroke="#0a0e27"
                strokeWidth="2"
              />
            ))}
          </svg>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="glow-green" style={{
            padding: '1.5rem',
            background: 'rgba(0, 255, 65, 0.05)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.65rem', color: '#00ff4180', marginBottom: '0.5rem' }}>BEST_ACCURACY</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#00ff41' }}>92%</div>
            <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginTop: '0.25rem' }}>SESSION_12</div>
          </div>
          
          <div className="glow-cyan" style={{
            padding: '1.5rem',
            background: 'rgba(0, 217, 255, 0.05)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.65rem', color: '#00d9ff80', marginBottom: '0.5rem' }}>IMPROVEMENT</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#00d9ff' }}>+27%</div>
            <div style={{ fontSize: '0.7rem', color: '#00d9ff80', marginTop: '0.25rem' }}>SINCE_START</div>
          </div>

          <div className="glow-amber" style={{
            padding: '1.5rem',
            background: 'rgba(255, 184, 0, 0.05)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.65rem', color: '#ffb80080', marginBottom: '0.5rem' }}>TOTAL_SESSIONS</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffb800' }}>14</div>
            <div style={{ fontSize: '0.7rem', color: '#ffb80080', marginTop: '0.25rem' }}>LAST_30_DAYS</div>
          </div>
        </div>
      </div>

      {/* Session Log */}
      <div style={{
        padding: '2rem',
        background: 'rgba(0, 0, 0, 0.3)',
        border: '1px solid #00d9ff40'
      }}>
        <div style={{ fontSize: '0.8rem', color: '#00d9ff', marginBottom: '1.5rem', letterSpacing: '0.05em' }}>
          SESSION_HISTORY_LOG
        </div>

        {[
          { id: 14, date: 'TODAY', accuracy: 88, threats: 15, time: '2.1s' },
          { id: 13, date: 'YESTERDAY', accuracy: 85, threats: 20, time: '2.3s' },
          { id: 12, date: '2_DAYS_AGO', accuracy: 92, threats: 18, time: '1.9s' },
          { id: 11, date: '3_DAYS_AGO', accuracy: 79, threats: 12, time: '2.8s' }
        ].map((session, index) => (
          <div key={session.id} style={{
            padding: '1rem',
            background: 'rgba(0, 217, 255, 0.05)',
            border: '1px solid #00d9ff20',
            marginBottom: '0.75rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            animation: `slideUp 0.5s ease-out ${index * 0.1}s backwards`
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <div style={{
                width: '60px',
                padding: '0.75rem',
                background: 'rgba(0, 217, 255, 0.1)',
                border: '1px solid #00d9ff',
                textAlign: 'center',
                fontSize: '0.9rem',
                fontWeight: 700,
                color: '#00d9ff'
              }}>
                {session.id}
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#00ff41', marginBottom: '0.25rem' }}>
                  SESSION_{session.id}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#00d9ff60' }}>
                  {session.date} // {session.threats}_THREATS_ANALYZED
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '2rem', textAlign: 'right' }}>
              <div>
                <div style={{ fontSize: '0.65rem', color: '#00ff4180', marginBottom: '0.25rem' }}>ACCURACY</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: session.accuracy >= 90 ? '#00ff41' : session.accuracy >= 80 ? '#00d9ff' : '#ffb800' }}>
                  {session.accuracy}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: '#00ff4180', marginBottom: '0.25rem' }}>AVG_TIME</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#00d9ff' }}>
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

function DemonstratePhase() {
  return (
    <div>
      <div style={{ 
        fontSize: '0.8rem', 
        color: '#00d9ff', 
        letterSpacing: '0.1em', 
        marginBottom: '1.5rem',
        borderBottom: '1px solid #00d9ff40',
        paddingBottom: '0.5rem'
      }}>
        RED_TEAM_EXERCISE // PHISHING_SIMULATION_CREATOR
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div style={{
          padding: '2rem',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid #00d9ff40'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#00d9ff', marginBottom: '1.5rem', letterSpacing: '0.05em' }}>
            THREAT_COMPOSER
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>
                TARGET_SCENARIO
              </div>
              <select style={{
                width: '100%',
                padding: '0.75rem',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid #00d9ff40',
                color: '#00d9ff',
                fontSize: '0.8rem',
                fontFamily: 'inherit'
              }}>
                <option>BANK_ACCOUNT_VERIFICATION</option>
                <option>PACKAGE_DELIVERY_ALERT</option>
                <option>IT_SECURITY_WARNING</option>
                <option>HR_BENEFITS_UPDATE</option>
              </select>
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>
                SENDER_ADDRESS
              </div>
              <input
                type="text"
                placeholder="security@paypa1-verify.com"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid #00d9ff40',
                  color: '#00ff41',
                  fontSize: '0.8rem',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>
                SUBJECT_LINE
              </div>
              <input
                type="text"
                placeholder="URGENT_VERIFICATION_REQUIRED"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid #00d9ff40',
                  color: '#00ff41',
                  fontSize: '0.8rem',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>
                MESSAGE_PAYLOAD
              </div>
              <textarea
                placeholder="// Construct phishing email content..."
                style={{
                  width: '100%',
                  minHeight: '150px',
                  padding: '1rem',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid #00d9ff40',
                  color: '#00ff41',
                  fontSize: '0.8rem',
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', marginBottom: '0.75rem', letterSpacing: '0.05em' }}>
                SOCIAL_ENGINEERING_TACTICS
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                {['URGENCY', 'AUTHORITY', 'FEAR', 'CURIOSITY', 'GREED'].map((tactic) => (
                  <button key={tactic} style={{
                    padding: '0.5rem 1rem',
                    background: 'rgba(255, 184, 0, 0.1)',
                    border: '1px solid #ffb800',
                    color: '#ffb800',
                    fontSize: '0.7rem',
                    cursor: 'pointer',
                    letterSpacing: '0.05em',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 184, 0, 0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 184, 0, 0.1)';
                  }}>
                    [{tactic}]
                  </button>
                ))}
              </div>
            </div>

            <button className="glow-amber" style={{
              width: '100%',
              padding: '1rem',
              background: 'rgba(255, 184, 0, 0.1)',
              color: '#ffb800',
              fontSize: '0.9rem',
              fontWeight: 700,
              cursor: 'pointer',
              letterSpacing: '0.05em',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(255, 184, 0, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 184, 0, 0.1)';
            }}>
              [EXECUTE_AI_EVALUATION]
            </button>
          </div>
        </div>

        <div style={{
          padding: '2rem',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid #00d9ff40'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#00d9ff', marginBottom: '1.5rem', letterSpacing: '0.05em' }}>
            AI_EVALUATION_RESULTS
          </div>

          <div style={{
            padding: '2rem',
            background: 'rgba(255, 184, 0, 0.1)',
            border: '2px solid #ffb800',
            marginBottom: '2rem',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.7rem', color: '#ffb80080', marginBottom: '0.5rem' }}>THREAT_SCORE</div>
            <div style={{ fontSize: '4rem', fontWeight: 800, color: '#ffb800', lineHeight: 1 }}>87</div>
            <div style={{ fontSize: '0.8rem', color: '#ffb80080', marginTop: '0.5rem' }}>/100</div>
          </div>

          <div style={{ fontSize: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.8rem', color: '#00d9ff', marginBottom: '1rem', letterSpacing: '0.05em' }}>
              BREAKDOWN_ANALYSIS
            </div>
            
            {[
              { metric: 'URGENCY_TACTICS', score: 92 },
              { metric: 'AUTHORITY_MIMICRY', score: 85 },
              { metric: 'TECHNICAL_SOPHISTICATION', score: 81 },
              { metric: 'SOCIAL_ENGINEERING', score: 90 }
            ].map((item, i) => (
              <div key={i} style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: '#00ff4180', fontSize: '0.75rem' }}>{item.metric}</span>
                  <span style={{ color: '#ffb800', fontWeight: 700 }}>{item.score}/100</span>
                </div>
                <div style={{ height: '4px', background: 'rgba(255, 184, 0, 0.2)' }}>
                  <div style={{
                    width: `${item.score}%`,
                    height: '100%',
                    background: '#ffb800',
                    transition: 'width 1s ease-out'
                  }} />
                </div>
              </div>
            ))}
          </div>

          <div style={{
            padding: '1rem',
            background: 'rgba(0, 217, 255, 0.1)',
            border: '1px solid #00d9ff40',
            fontSize: '0.75rem',
            color: '#00d9ff',
            lineHeight: 1.8
          }}>
            <div style={{ marginBottom: '0.5rem', fontWeight: 700 }}>RECOMMENDATIONS:</div>
            <div style={{ color: '#00d9ff80' }}>
              &gt; INCREASE_TECHNICAL_DETAILS<br/>
              &gt; ADD_DEADLINE_PRESSURE<br/>
              &gt; ENHANCE_CALL_TO_ACTION
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
