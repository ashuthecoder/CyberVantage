import React, { useState, useEffect } from 'react';
import { Shield, Terminal, Zap, Target, TrendingUp, CheckCircle, ArrowRight, Play, Globe, Lock, Eye, Activity, Users, Award, ChevronDown } from 'lucide-react';

export default function CyberVantageLanding() {
  const [scanLines, setScanLines] = useState(0);
  const [time, setTime] = useState(new Date());
  const [typedText, setTypedText] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);

  const fullText = "NEXT_GENERATION_SECURITY_TRAINING";

  useEffect(() => {
    const scanInterval = setInterval(() => {
      setScanLines(prev => (prev + 1) % 100);
    }, 50);
    
    const timeInterval = setInterval(() => {
      setTime(new Date());
    }, 1000);

    // Typing effect
    let currentIndex = 0;
    const typingInterval = setInterval(() => {
      if (currentIndex <= fullText.length) {
        setTypedText(fullText.slice(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(typingInterval);
      }
    }, 100);

    // Cursor blink
    const cursorInterval = setInterval(() => {
      setCursorVisible(prev => !prev);
    }, 500);

    return () => {
      clearInterval(scanInterval);
      clearInterval(timeInterval);
      clearInterval(typingInterval);
      clearInterval(cursorInterval);
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
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slideInLeft {
          from {
            opacity: 0;
            transform: translateX(-50px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(50px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(0, 217, 255, 0.5); }
          50% { box-shadow: 0 0 40px rgba(0, 217, 255, 0.8); }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        
        .terminal-text {
          text-shadow: 0 0 10px currentColor;
          animation: flicker 3s infinite;
        }
        
        .glow-cyan {
          box-shadow: 0 0 20px rgba(0, 217, 255, 0.5), inset 0 0 20px rgba(0, 217, 255, 0.1);
          border: 1px solid #00d9ff;
        }
        
        .glow-green {
          box-shadow: 0 0 20px rgba(0, 255, 65, 0.5), inset 0 0 20px rgba(0, 255, 65, 0.1);
          border: 1px solid #00ff41;
        }
        
        .terminal-button {
          transition: all 0.3s ease;
          cursor: pointer;
          position: relative;
          overflow: hidden;
        }
        
        .terminal-button::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(0, 217, 255, 0.3), transparent);
          transition: left 0.5s ease;
        }
        
        .terminal-button:hover::before {
          left: 100%;
        }
        
        .terminal-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 30px rgba(0, 217, 255, 0.8);
        }
        
        .feature-card {
          transition: all 0.3s ease;
          cursor: pointer;
        }
        
        .feature-card:hover {
          transform: translateY(-10px);
          box-shadow: 0 0 30px rgba(0, 217, 255, 0.5);
        }
        
        .stat-counter {
          font-variant-numeric: tabular-nums;
        }
      `}</style>

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

      {/* Animated background elements */}
      <div style={{
        position: 'absolute',
        top: '10%',
        right: '10%',
        width: '400px',
        height: '400px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0, 217, 255, 0.2) 0%, transparent 70%)',
        animation: 'float 6s ease-in-out infinite',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '20%',
        left: '5%',
        width: '300px',
        height: '300px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0, 255, 65, 0.15) 0%, transparent 70%)',
        animation: 'float 8s ease-in-out infinite',
        animationDelay: '2s',
        pointerEvents: 'none'
      }} />

      {/* Navigation */}
      <nav style={{
        padding: '1.5rem 3rem',
        borderBottom: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 1000
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Shield size={36} color="#00d9ff" strokeWidth={2} style={{ animation: 'pulse 2s infinite' }} />
            <div>
              <div className="terminal-text" style={{ fontSize: '1.5rem', fontWeight: 800, color: '#00d9ff', letterSpacing: '0.1em' }}>
                CYBERVANTAGE
              </div>
              <div style={{ fontSize: '0.7rem', color: '#00ff4180', letterSpacing: '0.05em' }}>
                SECURITY_OPERATIONS_CENTER
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
            {['FEATURES', 'PLATFORM', 'PRICING', 'DOCS'].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                style={{
                  color: '#00d9ff80',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  textDecoration: 'none',
                  transition: 'all 0.3s ease',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = '#00d9ff';
                  e.currentTarget.style.textShadow = '0 0 10px #00d9ff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = '#00d9ff80';
                  e.currentTarget.style.textShadow = 'none';
                }}
              >
                [{item}]
              </a>
            ))}

            <div style={{
              padding: '0.5rem 1rem',
              background: 'rgba(0, 217, 255, 0.1)',
              border: '1px solid #00d9ff40',
              fontSize: '0.75rem',
              color: '#00d9ff',
              letterSpacing: '0.05em'
            }}>
              {time.toLocaleTimeString('en-US', { hour12: false })} UTC
            </div>

            <button className="terminal-button glow-cyan" style={{
              padding: '0.75rem 1.5rem',
              background: 'rgba(0, 217, 255, 0.1)',
              color: '#00d9ff',
              fontSize: '0.85rem',
              fontWeight: 700,
              letterSpacing: '0.05em',
              border: '1px solid #00d9ff'
            }}>
              [LOGIN]
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        padding: '8rem 3rem',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <div style={{
              display: 'inline-block',
              padding: '0.5rem 1.5rem',
              background: 'rgba(255, 184, 0, 0.1)',
              border: '1px solid #ffb800',
              marginBottom: '2rem',
              fontSize: '0.8rem',
              color: '#ffb800',
              letterSpacing: '0.1em',
              animation: 'slideUp 0.8s ease-out'
            }}>
              [STATUS: OPERATIONAL] • [UPTIME: 99.99%] • [ACTIVE_USERS: 50,000+]
            </div>

            <h1 style={{
              fontSize: '4.5rem',
              fontWeight: 800,
              margin: '0 0 1.5rem 0',
              letterSpacing: '0.05em',
              lineHeight: 1.2,
              animation: 'slideUp 0.8s ease-out 0.2s backwards'
            }}>
              <span className="terminal-text" style={{ color: '#00d9ff' }}>TRAIN.</span>{' '}
              <span className="terminal-text" style={{ color: '#00ff41' }}>DEFEND.</span>{' '}
              <span className="terminal-text" style={{ color: '#ffb800' }}>DOMINATE.</span>
            </h1>

            <div style={{
              fontSize: '1.2rem',
              color: '#00d9ff80',
              marginBottom: '1rem',
              letterSpacing: '0.05em',
              animation: 'slideUp 0.8s ease-out 0.4s backwards',
              minHeight: '40px'
            }}>
              &gt; {typedText}<span style={{ opacity: cursorVisible ? 1 : 0 }}>_</span>
            </div>

            <p style={{
              fontSize: '1.1rem',
              color: '#00ff4180',
              maxWidth: '800px',
              margin: '0 auto 3rem',
              lineHeight: 1.8,
              animation: 'slideUp 0.8s ease-out 0.6s backwards'
            }}>
              Enterprise-grade phishing simulation platform powered by AI.
              <br />
              Train your team to identify, analyze, and neutralize cyber threats in real-time.
            </p>

            <div style={{
              display: 'flex',
              gap: '1.5rem',
              justifyContent: 'center',
              animation: 'slideUp 0.8s ease-out 0.8s backwards'
            }}>
              <button className="terminal-button glow-green" style={{
                padding: '1.25rem 2.5rem',
                background: 'rgba(0, 255, 65, 0.1)',
                color: '#00ff41',
                fontSize: '1rem',
                fontWeight: 700,
                letterSpacing: '0.05em',
                border: '1px solid #00ff41',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                [START_TRAINING]
                <ArrowRight size={20} />
              </button>

              <button className="terminal-button" style={{
                padding: '1.25rem 2.5rem',
                background: 'rgba(0, 0, 0, 0.5)',
                color: '#00d9ff',
                fontSize: '1rem',
                fontWeight: 700,
                letterSpacing: '0.05em',
                border: '1px solid #00d9ff40',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <Play size={20} />
                [WATCH_DEMO]
              </button>
            </div>
          </div>

          {/* Terminal Preview */}
          <div style={{
            margin: '0 auto',
            maxWidth: '1100px',
            animation: 'slideUp 1s ease-out 1s backwards'
          }}>
            <div style={{
              background: 'rgba(0, 0, 0, 0.8)',
              border: '2px solid #00d9ff',
              boxShadow: '0 0 50px rgba(0, 217, 255, 0.5)',
              position: 'relative'
            }}>
              {/* Terminal Header */}
              <div style={{
                padding: '1rem 1.5rem',
                borderBottom: '1px solid #00d9ff40',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(0, 217, 255, 0.05)'
              }}>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff0055' }} />
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffb800' }} />
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#00ff41' }} />
                </div>
                <div style={{ fontSize: '0.8rem', color: '#00d9ff80', letterSpacing: '0.05em' }}>
                  CYBERVANTAGE_TERMINAL v2.4.1
                </div>
              </div>

              {/* Terminal Content */}
              <div style={{ padding: '2rem', fontSize: '0.9rem', lineHeight: 2 }}>
                <div style={{ color: '#00d9ff' }}>&gt; system.initialize()</div>
                <div style={{ color: '#00ff4180' }}>  [OK] Loading security modules...</div>
                <div style={{ color: '#00ff4180' }}>  [OK] AI threat detection: ONLINE</div>
                <div style={{ color: '#00ff4180' }}>  [OK] Phishing simulator: ACTIVE</div>
                <div style={{ color: '#00ff4180' }}>  [OK] Analytics engine: READY</div>
                <div style={{ color: '#ffb800', marginTop: '1rem' }}>&gt; stats.overview()</div>
                <div style={{ color: '#00ff41', marginTop: '0.5rem' }}>
                  ┌─────────────────────────────────────────┐<br />
                  │ ACTIVE_USERS:      50,000+             │<br />
                  │ THREATS_DETECTED:  2.4M                │<br />
                  │ ACCURACY_RATE:     94.7%               │<br />
                  │ TRAINING_HOURS:    180K+               │<br />
                  └─────────────────────────────────────────┘
                </div>
                <div style={{ color: '#00d9ff', marginTop: '1rem' }}>&gt; <span style={{ animation: 'pulse 1s infinite' }}>_</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section style={{
        padding: '3rem',
        borderTop: '2px solid #00d9ff40',
        borderBottom: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '3rem' }}>
            {[
              { label: 'ACTIVE_ORGANIZATIONS', value: '1,200+', icon: Users },
              { label: 'THREATS_NEUTRALIZED', value: '2.4M', icon: Shield },
              { label: 'ACCURACY_RATE', value: '94.7%', icon: Target },
              { label: 'UPTIME_SLA', value: '99.99%', icon: Activity }
            ].map((stat, i) => {
              const Icon = stat.icon;
              return (
                <div key={i} style={{
                  textAlign: 'center',
                  animation: `slideUp 0.8s ease-out ${i * 0.1}s backwards`
                }}>
                  <Icon size={32} color="#00d9ff" strokeWidth={2} style={{ marginBottom: '1rem' }} />
                  <div className="stat-counter" style={{
                    fontSize: '2.5rem',
                    fontWeight: 800,
                    color: '#00ff41',
                    marginBottom: '0.5rem',
                    textShadow: '0 0 20px currentColor'
                  }}>
                    {stat.value}
                  </div>
                  <div style={{
                    fontSize: '0.8rem',
                    color: '#00d9ff80',
                    letterSpacing: '0.05em'
                  }}>
                    {stat.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{
        padding: '8rem 3rem',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '5rem' }}>
            <div style={{
              fontSize: '0.8rem',
              color: '#ffb800',
              letterSpacing: '0.1em',
              marginBottom: '1rem'
            }}>
              [SYSTEM_CAPABILITIES]
            </div>
            <h2 style={{
              fontSize: '3rem',
              fontWeight: 800,
              margin: '0 0 1rem 0',
              letterSpacing: '0.05em'
            }}>
              <span className="terminal-text" style={{ color: '#00d9ff' }}>FOUR_PHASE</span>{' '}
              <span style={{ color: '#00ff41' }}>TRAINING_PROTOCOL</span>
            </h2>
            <p style={{
              fontSize: '1rem',
              color: '#00ff4180',
              maxWidth: '700px',
              margin: '0 auto'
            }}>
              Comprehensive security training designed by experts, powered by AI
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '2rem', marginBottom: '4rem' }}>
            {[
              {
                phase: 'PHASE_01',
                title: 'LEARN',
                description: 'Master cybersecurity fundamentals through interactive modules covering phishing tactics, social engineering, and compliance standards.',
                icon: Terminal,
                color: '#3b82f6',
                features: ['Interactive_Modules', 'Video_Training', 'Certification_Prep']
              },
              {
                phase: 'PHASE_02',
                title: 'SIMULATE',
                description: 'Practice threat detection with AI-generated phishing scenarios. Classify emails and explain your reasoning in realistic simulations.',
                icon: Eye,
                color: '#8b5cf6',
                features: ['AI_Generated_Threats', 'Real_Time_Feedback', 'Performance_Scoring']
              },
              {
                phase: 'PHASE_03',
                title: 'ANALYZE',
                description: 'Track your progress with advanced analytics. Monitor accuracy trends, session history, and identify improvement areas.',
                icon: TrendingUp,
                color: '#ec4899',
                features: ['Performance_Metrics', 'Trend_Analysis', 'Benchmark_Comparison']
              },
              {
                phase: 'PHASE_04',
                title: 'DEMONSTRATE',
                description: 'Prove mastery by creating your own phishing emails. Receive AI evaluation and detailed scoring on your techniques.',
                icon: Award,
                color: '#f59e0b',
                features: ['AI_Evaluation', 'Technique_Scoring', 'Expert_Feedback']
              }
            ].map((feature, i) => {
              const Icon = feature.icon;
              return (
                <div
                  key={i}
                  className="feature-card"
                  style={{
                    padding: '2.5rem',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: `1px solid ${feature.color}40`,
                    backdropFilter: 'blur(10px)',
                    position: 'relative',
                    overflow: 'hidden',
                    animation: i % 2 === 0 ? 'slideInLeft 0.8s ease-out' : 'slideInRight 0.8s ease-out'
                  }}
                >
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '3px',
                    background: feature.color
                  }} />

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    marginBottom: '1.5rem'
                  }}>
                    <div style={{
                      width: '60px',
                      height: '60px',
                      background: `${feature.color}20`,
                      border: `2px solid ${feature.color}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Icon size={32} color={feature.color} strokeWidth={2} />
                    </div>
                    <div>
                      <div style={{
                        fontSize: '0.75rem',
                        color: `${feature.color}80`,
                        letterSpacing: '0.1em',
                        marginBottom: '0.25rem'
                      }}>
                        {feature.phase}
                      </div>
                      <div style={{
                        fontSize: '1.8rem',
                        fontWeight: 800,
                        color: feature.color,
                        letterSpacing: '0.05em'
                      }}>
                        {feature.title}
                      </div>
                    </div>
                  </div>

                  <p style={{
                    fontSize: '0.95rem',
                    color: '#00ff4180',
                    lineHeight: 1.8,
                    marginBottom: '1.5rem'
                  }}>
                    {feature.description}
                  </p>

                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem'
                  }}>
                    {feature.features.map((f, idx) => (
                      <div key={idx} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        fontSize: '0.85rem',
                        color: '#00d9ff'
                      }}>
                        <CheckCircle size={16} color="#00ff41" />
                        <span style={{ letterSpacing: '0.03em' }}>{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Additional Features */}
          <div style={{
            padding: '3rem',
            background: 'rgba(0, 217, 255, 0.05)',
            border: '1px solid #00d9ff40'
          }}>
            <h3 style={{
              fontSize: '1.5rem',
              fontWeight: 800,
              color: '#00d9ff',
              marginBottom: '2rem',
              letterSpacing: '0.05em',
              textAlign: 'center'
            }}>
              [ENTERPRISE_FEATURES]
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
              {[
                { icon: Lock, title: 'SECURE_BY_DESIGN', desc: 'Enterprise-grade security with JWT auth, CSRF protection, and encryption' },
                { icon: Zap, title: 'AI_POWERED', desc: 'Azure OpenAI and Google Gemini integration for threat generation and analysis' },
                { icon: Globe, title: 'THREAT_INTELLIGENCE', desc: 'Real-time VirusTotal API integration for URL/IP/hash scanning' },
                { icon: Activity, title: 'ANALYTICS_ENGINE', desc: 'Advanced performance tracking with session grouping and trend analysis' },
                { icon: Users, title: 'TEAM_MANAGEMENT', desc: 'Multi-user support with role-based access control and admin dashboards' },
                { icon: Award, title: 'COMPLIANCE_READY', desc: 'Built-in compliance training for industry standards and regulations' }
              ].map((feature, i) => {
                const Icon = feature.icon;
                return (
                  <div key={i} style={{
                    padding: '1.5rem',
                    background: 'rgba(0, 0, 0, 0.5)',
                    border: '1px solid #00d9ff20'
                  }}>
                    <Icon size={28} color="#00d9ff" strokeWidth={2} style={{ marginBottom: '1rem' }} />
                    <div style={{
                      fontSize: '0.9rem',
                      fontWeight: 700,
                      color: '#00d9ff',
                      marginBottom: '0.5rem',
                      letterSpacing: '0.05em'
                    }}>
                      {feature.title}
                    </div>
                    <div style={{
                      fontSize: '0.85rem',
                      color: '#00ff4180',
                      lineHeight: 1.6
                    }}>
                      {feature.desc}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{
        padding: '6rem 3rem',
        background: 'rgba(0, 217, 255, 0.05)',
        borderTop: '2px solid #00d9ff40',
        borderBottom: '2px solid #00d9ff40',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{
            fontSize: '0.8rem',
            color: '#ffb800',
            letterSpacing: '0.1em',
            marginBottom: '1rem'
          }}>
            [READY_TO_BEGIN?]
          </div>

          <h2 style={{
            fontSize: '3rem',
            fontWeight: 800,
            margin: '0 0 1.5rem 0',
            letterSpacing: '0.05em'
          }}>
            <span className="terminal-text" style={{ color: '#00d9ff' }}>START_YOUR</span>{' '}
            <span style={{ color: '#00ff41' }}>SECURITY_JOURNEY</span>
          </h2>

          <p style={{
            fontSize: '1.1rem',
            color: '#00ff4180',
            marginBottom: '3rem',
            lineHeight: 1.8
          }}>
            Join 50,000+ security professionals already training on CyberVantage.
            <br />
            Get started with a free trial—no credit card required.
          </p>

          <div style={{
            display: 'flex',
            gap: '1.5rem',
            justifyContent: 'center',
            marginBottom: '2rem'
          }}>
            <button className="terminal-button glow-green" style={{
              padding: '1.5rem 3rem',
              background: 'rgba(0, 255, 65, 0.1)',
              color: '#00ff41',
              fontSize: '1.1rem',
              fontWeight: 700,
              letterSpacing: '0.05em',
              border: '2px solid #00ff41'
            }}>
              [START_FREE_TRIAL]
            </button>

            <button className="terminal-button glow-cyan" style={{
              padding: '1.5rem 3rem',
              background: 'rgba(0, 217, 255, 0.1)',
              color: '#00d9ff',
              fontSize: '1.1rem',
              fontWeight: 700,
              letterSpacing: '0.05em',
              border: '2px solid #00d9ff'
            }}>
              [SCHEDULE_DEMO]
            </button>
          </div>

          <div style={{
            fontSize: '0.85rem',
            color: '#00d9ff80',
            letterSpacing: '0.03em'
          }}>
            ✓ 14_DAY_FREE_TRIAL &nbsp;•&nbsp; ✓ NO_CREDIT_CARD &nbsp;•&nbsp; ✓ INSTANT_ACCESS
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '4rem 3rem 2rem',
        borderTop: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.8)'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '3rem', marginBottom: '3rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <Shield size={28} color="#00d9ff" strokeWidth={2} />
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#00d9ff', letterSpacing: '0.1em' }}>
                  CYBERVANTAGE
                </div>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#00ff4180', lineHeight: 1.8 }}>
                Enterprise-grade phishing simulation and security training platform.
              </p>
            </div>

            {[
              {
                title: 'PLATFORM',
                links: ['Features', 'Pricing', 'Security', 'Integrations']
              },
              {
                title: 'RESOURCES',
                links: ['Documentation', 'API Reference', 'Blog', 'Case Studies']
              },
              {
                title: 'COMPANY',
                links: ['About', 'Careers', 'Contact', 'Legal']
              }
            ].map((section, i) => (
              <div key={i}>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: '#00d9ff',
                  letterSpacing: '0.1em',
                  marginBottom: '1rem'
                }}>
                  [{section.title}]
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {section.links.map((link) => (
                    <a
                      key={link}
                      href="#"
                      style={{
                        color: '#00ff4180',
                        fontSize: '0.85rem',
                        textDecoration: 'none',
                        transition: 'color 0.3s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#00d9ff'}
                      onMouseLeave={(e) => e.currentTarget.style.color = '#00ff4180'}
                    >
                      &gt; {link}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div style={{
            paddingTop: '2rem',
            borderTop: '1px solid #00d9ff40',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.8rem',
            color: '#00d9ff80'
          }}>
            <div>
              © 2026 CYBERVANTAGE. ALL_RIGHTS_RESERVED.
            </div>
            <div style={{ display: 'flex', gap: '2rem' }}>
              <a href="#" style={{ color: '#00d9ff80', textDecoration: 'none' }}>PRIVACY</a>
              <a href="#" style={{ color: '#00d9ff80', textDecoration: 'none' }}>TERMS</a>
              <a href="#" style={{ color: '#00d9ff80', textDecoration: 'none' }}>STATUS</a>
            </div>
          </div>
        </div>
      </footer>

      {/* Scroll indicator */}
      <div style={{
        position: 'fixed',
        bottom: '2rem',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        animation: 'float 3s ease-in-out infinite'
      }}>
        <ChevronDown size={32} color="#00d9ff" strokeWidth={2} style={{ opacity: 0.6 }} />
      </div>
    </div>
  );
}
