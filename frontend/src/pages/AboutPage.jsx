import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Terminal, Globe, Target, Zap, Database, Activity, BookOpen, Code, Users, Heart, ArrowLeft, Github } from 'lucide-react';

export default function AboutPage() {
  const navigate = useNavigate();
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

  const featureCards = [
    {
      icon: BookOpen,
      title: 'LEARN',
      description: 'Understand phishing fundamentals and core cybersecurity principles through structured, interactive lessons.'
    },
    {
      icon: Target,
      title: 'SIMULATE',
      description: 'Practice with AI-generated realistic phishing scenarios in a safe, controlled environment.'
    },
    {
      icon: Activity,
      title: 'ANALYZE',
      description: 'Review detailed performance analytics, track your progress, and identify areas for improvement.'
    },
    {
      icon: Terminal,
      title: 'DEMONSTRATE',
      description: 'Create your own phishing simulations to demonstrate understanding and test your skills.'
    }
  ];

  const techStack = [
    { category: 'FRONTEND', items: 'React, Vite, Lucide Icons', icon: Globe },
    { category: 'BACKEND', items: 'FastAPI, Python', icon: Code },
    { category: 'AI', items: 'Azure OpenAI, Google Gemini', icon: Zap },
    { category: 'DATABASE', items: 'PostgreSQL', icon: Database },
    { category: 'EMAIL', items: 'Resend', icon: Shield }
  ];

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
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(0, 217, 255, 0.5); }
          50% { box-shadow: 0 0 40px rgba(0, 217, 255, 0.8); }
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
          cursor: default;
        }

        .feature-card:hover {
          transform: translateY(-10px);
          box-shadow: 0 0 30px rgba(0, 217, 255, 0.5);
        }

        .nav-link {
          color: #00d9ff80;
          font-size: 0.85rem;
          font-weight: 700;
          letter-spacing: 0.05em;
          text-decoration: none;
          transition: all 0.3s ease;
          cursor: pointer;
          background: none;
          border: none;
          font-family: inherit;
        }

        .nav-link:hover {
          color: #00d9ff;
          text-shadow: 0 0 10px #00d9ff;
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

      {/* Floating gradient orbs */}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }} onClick={() => navigate('/')}>
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
            <button className="nav-link" onClick={() => navigate('/')}>[HOME]</button>
            <button className="nav-link" onClick={() => navigate('/dashboard')}>[DASHBOARD]</button>

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
              border: '1px solid #00d9ff',
              fontFamily: 'inherit',
              cursor: 'pointer'
            }}
            onClick={() => navigate('/login')}
            >
              [LOGIN]
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        padding: '6rem 3rem',
        position: 'relative',
        zIndex: 1,
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{
            display: 'inline-block',
            padding: '0.5rem 1.5rem',
            background: 'rgba(0, 217, 255, 0.1)',
            border: '1px solid #00d9ff40',
            marginBottom: '2rem',
            fontSize: '0.8rem',
            color: '#00d9ff',
            letterSpacing: '0.1em',
            animation: 'slideUp 0.8s ease-out'
          }}>
            [PAGE: ABOUT] • [STATUS: ACTIVE]
          </div>

          <h1 style={{
            fontSize: '3.5rem',
            fontWeight: 800,
            margin: '0 0 1.5rem 0',
            letterSpacing: '0.05em',
            lineHeight: 1.2,
            animation: 'slideUp 0.8s ease-out 0.2s backwards'
          }}>
            <span className="terminal-text" style={{ color: '#00d9ff' }}>ABOUT_</span>
            <span className="terminal-text" style={{ color: '#00ff41' }}>CYBERVANTAGE</span>
          </h1>

          <p style={{
            fontSize: '1.1rem',
            color: '#00ff4180',
            maxWidth: '800px',
            margin: '0 auto 2rem',
            lineHeight: 1.8,
            animation: 'slideUp 0.8s ease-out 0.4s backwards'
          }}>
            CyberVantage is an educational cybersecurity training platform that empowers students
            to learn, practice, and master the art of identifying and defending against phishing
            attacks through AI-powered simulations and interactive exercises.
          </p>

          <button className="terminal-button" style={{
            padding: '0.75rem 1.5rem',
            background: 'rgba(0, 0, 0, 0.5)',
            color: '#00d9ff',
            fontSize: '0.85rem',
            fontWeight: 700,
            letterSpacing: '0.05em',
            border: '1px solid #00d9ff40',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.75rem',
            fontFamily: 'inherit',
            cursor: 'pointer',
            animation: 'slideUp 0.8s ease-out 0.6s backwards'
          }}
          onClick={() => navigate('/')}
          >
            <ArrowLeft size={18} />
            [BACK_TO_HOME]
          </button>
        </div>
      </section>

      {/* Mission Section */}
      <section style={{
        padding: '5rem 3rem',
        borderTop: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.3)',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ marginBottom: '3rem', animation: 'slideUp 0.8s ease-out' }}>
            <div style={{ fontSize: '0.8rem', color: '#00d9ff80', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
              SECTION_01 // OUR_MISSION
            </div>
            <h2 className="terminal-text" style={{
              fontSize: '2.25rem',
              fontWeight: 800,
              color: '#00d9ff',
              margin: '0 0 1.5rem 0',
              letterSpacing: '0.05em'
            }}>
              Our Mission
            </h2>
            <p style={{
              fontSize: '1rem',
              color: '#00ff4180',
              lineHeight: 1.8,
              maxWidth: '800px'
            }}>
              CyberVantage is dedicated to teaching students about cybersecurity through interactive
              simulations. We believe that hands-on experience is the most effective way to understand
              and combat modern cyber threats, particularly phishing attacks.
            </p>
          </div>

          {/* Mission Goals */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
            {[
              {
                icon: BookOpen,
                title: 'ACCESSIBLE_EDUCATION',
                text: 'Make cybersecurity education accessible to all students, regardless of their technical background.'
              },
              {
                icon: Zap,
                title: 'AI_PERSONALIZED_TRAINING',
                text: 'Leverage AI to create personalized training experiences that adapt to each student\'s skill level.'
              },
              {
                icon: Shield,
                title: 'SAFE_HANDS_ON_EXPERIENCE',
                text: 'Provide a safe, controlled environment for students to practice identifying and responding to threats.'
              }
            ].map((goal, i) => {
              const Icon = goal.icon;
              return (
                <div key={i} className="feature-card" style={{
                  padding: '2rem',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid #00d9ff40',
                  animation: `slideUp 0.8s ease-out ${i * 0.15}s backwards`
                }}>
                  <Icon size={28} color="#00d9ff" strokeWidth={2} style={{ marginBottom: '1rem' }} />
                  <div style={{ fontSize: '0.8rem', color: '#00d9ff', letterSpacing: '0.05em', marginBottom: '1rem', fontWeight: 700 }}>
                    [{goal.title}]
                  </div>
                  <p style={{ fontSize: '0.9rem', color: '#00ff4180', lineHeight: 1.7, margin: 0 }}>
                    {goal.text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Platform Features Section */}
      <section style={{
        padding: '5rem 3rem',
        borderTop: '2px solid #00d9ff40',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ marginBottom: '3rem', animation: 'slideUp 0.8s ease-out' }}>
            <div style={{ fontSize: '0.8rem', color: '#00d9ff80', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
              SECTION_02 // PLATFORM_FEATURES
            </div>
            <h2 className="terminal-text" style={{
              fontSize: '2.25rem',
              fontWeight: 800,
              color: '#00d9ff',
              margin: 0,
              letterSpacing: '0.05em'
            }}>
              What You Can Do
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '2rem' }}>
            {featureCards.map((card, i) => {
              const Icon = card.icon;
              return (
                <div key={i} className="feature-card" style={{
                  padding: '2.5rem',
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid #00d9ff40',
                  animation: `slideUp 0.8s ease-out ${i * 0.15}s backwards`
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: 'rgba(0, 217, 255, 0.1)',
                      border: '1px solid #00d9ff40'
                    }}>
                      <Icon size={24} color="#00d9ff" strokeWidth={2} />
                    </div>
                    <h3 style={{
                      fontSize: '1.25rem',
                      fontWeight: 800,
                      color: '#00ff41',
                      margin: 0,
                      letterSpacing: '0.05em',
                      textShadow: '0 0 10px currentColor'
                    }}>
                      [{card.title}]
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: '#00ff4180', lineHeight: 1.7, margin: 0 }}>
                    {card.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Technology Stack Section */}
      <section style={{
        padding: '5rem 3rem',
        borderTop: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.3)',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ marginBottom: '3rem', animation: 'slideUp 0.8s ease-out' }}>
            <div style={{ fontSize: '0.8rem', color: '#00d9ff80', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
              SECTION_03 // TECHNOLOGY_STACK
            </div>
            <h2 className="terminal-text" style={{
              fontSize: '2.25rem',
              fontWeight: 800,
              color: '#00d9ff',
              margin: 0,
              letterSpacing: '0.05em'
            }}>
              Built With
            </h2>
          </div>

          {/* Terminal-style tech stack display */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.8)',
            border: '2px solid #00d9ff',
            boxShadow: '0 0 30px rgba(0, 217, 255, 0.3)',
            animation: 'slideUp 0.8s ease-out 0.2s backwards'
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
                TECH_STACK_OVERVIEW
              </div>
            </div>

            {/* Terminal Content */}
            <div style={{ padding: '2rem', fontSize: '0.9rem', lineHeight: 2.2 }}>
              <div style={{ color: '#00d9ff' }}>&gt; system.techStack()</div>
              <div style={{ color: '#00ff4180', marginTop: '0.5rem' }}>
                {techStack.map((tech, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ color: '#00ff41' }}>  [{tech.category}]</span>
                    <span style={{ color: '#00d9ff40' }}>→</span>
                    <span style={{ color: '#00ff4180' }}>{tech.items}</span>
                  </div>
                ))}
              </div>
              <div style={{ color: '#00d9ff', marginTop: '1rem' }}>&gt; <span style={{ animation: 'pulse 1s infinite' }}>_</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* Team / Creator Section */}
      <section style={{
        padding: '5rem 3rem',
        borderTop: '2px solid #00d9ff40',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto', textAlign: 'center' }}>
          <div style={{ marginBottom: '3rem', animation: 'slideUp 0.8s ease-out' }}>
            <div style={{ fontSize: '0.8rem', color: '#00d9ff80', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
              SECTION_04 // THE_PROJECT
            </div>
            <h2 className="terminal-text" style={{
              fontSize: '2.25rem',
              fontWeight: 800,
              color: '#00d9ff',
              margin: '0 0 1.5rem 0',
              letterSpacing: '0.05em'
            }}>
              Open Source & Educational
            </h2>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '2rem',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            <div className="feature-card" style={{
              padding: '2.5rem',
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid #00d9ff40',
              textAlign: 'center',
              animation: 'slideUp 0.8s ease-out 0.1s backwards'
            }}>
              <Users size={36} color="#00d9ff" strokeWidth={2} style={{ marginBottom: '1.25rem' }} />
              <div style={{ fontSize: '0.85rem', color: '#00d9ff', letterSpacing: '0.05em', marginBottom: '1rem', fontWeight: 700 }}>
                [EDUCATIONAL_PROJECT]
              </div>
              <p style={{ fontSize: '0.9rem', color: '#00ff4180', lineHeight: 1.7, margin: 0 }}>
                CyberVantage was built as an educational project to help students gain practical
                cybersecurity skills in a safe and engaging environment.
              </p>
            </div>

            <div className="feature-card" style={{
              padding: '2.5rem',
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid #00d9ff40',
              textAlign: 'center',
              animation: 'slideUp 0.8s ease-out 0.25s backwards'
            }}>
              <Heart size={36} color="#00ff41" strokeWidth={2} style={{ marginBottom: '1.25rem' }} />
              <div style={{ fontSize: '0.85rem', color: '#00ff41', letterSpacing: '0.05em', marginBottom: '1rem', fontWeight: 700 }}>
                [OPEN_SOURCE]
              </div>
              <p style={{ fontSize: '0.9rem', color: '#00ff4180', lineHeight: 1.7, margin: 0 }}>
                This platform is open source, welcoming contributions from the community to improve
                cybersecurity education for everyone.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '3rem',
        borderTop: '2px solid #00d9ff40',
        background: 'rgba(0, 0, 0, 0.5)',
        backdropFilter: 'blur(10px)',
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Shield size={24} color="#00d9ff" strokeWidth={2} />
              <span className="terminal-text" style={{ fontSize: '1rem', fontWeight: 800, color: '#00d9ff', letterSpacing: '0.1em' }}>
                CYBERVANTAGE
              </span>
            </div>

            <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
              <button className="nav-link" onClick={() => navigate('/')}>[HOME]</button>
              <button className="nav-link" onClick={() => navigate('/dashboard')}>[DASHBOARD]</button>
              <button className="nav-link" onClick={() => navigate('/login')}>[LOGIN]</button>
            </div>

            <div style={{
              fontSize: '0.75rem',
              color: '#00d9ff40',
              letterSpacing: '0.05em'
            }}>
              &copy; {new Date().getFullYear()} CyberVantage. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
