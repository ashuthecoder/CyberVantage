import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield, Search, Globe, AlertTriangle, CheckCircle2, Activity,
  Server, FileText, Link as LinkIcon, ArrowLeft, Wifi, WifiOff
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import apiClient, { threats } from '../api/client';

const IP_PATTERN = /^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$/;
const HASH_PATTERN = /^([a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})$/;

function detectScanType(value) {
  const v = value.trim();
  if (IP_PATTERN.test(v)) return 'ip';
  if (HASH_PATTERN.test(v)) return 'file';
  return 'url';
}

function getStatusInfo(result) {
  const score = result.threat_score ?? 0;
  if (score === 0 && !result.is_malicious) return { cls: 'clean', label: 'Clean' };
  if (score <= 30 && !result.is_malicious) return { cls: 'clean', label: 'Clean' };
  if (score <= 60) return { cls: 'warning', label: 'Suspicious' };
  return { cls: 'danger', label: 'Malicious' };
}

export default function ThreatAnalysisPage() {
  const { theme, themeName } = useTheme();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [scanType, setScanType] = useState('url');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [serviceOnline, setServiceOnline] = useState(null);

  const t = theme;
  const isSoc = themeName === 'soc';
  const radius = isSoc ? '0' : '12px';

  // Service status check on mount
  useEffect(() => {
    let cancelled = false;
    apiClient.get('/health')
      .then(() => { if (!cancelled) setServiceOnline(true); })
      .catch(() => { if (!cancelled) setServiceOnline(false); });
    return () => { cancelled = true; };
  }, []);

  // Auto-detect scan type as user types
  const handleInputChange = useCallback((e) => {
    const val = e.target.value;
    setInput(val);
    if (val.trim()) setScanType(detectScanType(val));
  }, []);

  const placeholders = {
    url: isSoc ? 'https://target.example.com' : 'https://example.com or domain.com',
    ip: isSoc ? '192.168.1.1' : 'e.g. 192.168.1.1',
    file: isSoc ? 'MD5/SHA1/SHA256_HASH' : 'MD5, SHA-1, or SHA-256 hash',
  };

  const handleScan = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (!isAuthenticated) {
      setError('Please login to run VirusTotal checks.');
      return;
    }

    const trimmed = input.trim();
    if (!trimmed) return;

    setLoading(true);
    try {
      const response = await threats.checkUrl(trimmed);
      const scanResult = {
        ...response.data,
        _input: trimmed,
        _type: scanType,
        _time: new Date().toISOString(),
        scanId: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
      };
      setResult(scanResult);
      setHistory((prev) => [scanResult, ...prev].slice(0, 10));
    } catch (scanError) {
      setError(scanError.response?.data?.detail || 'Unable to scan this target right now.');
    } finally {
      setLoading(false);
    }
  };

  const removeHistoryItem = (id) => {
    setHistory((prev) => prev.filter((h) => h.scanId !== id));
  };

  // --- Shared styles ---
  const panelStyle = {
    border: `1px solid ${t.border}`,
    background: t.bgSecondary,
    borderRadius: radius,
    overflow: 'hidden',
  };
  const panelHeaderStyle = (bg) => ({
    padding: '1rem 1.25rem',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    background: bg,
    color: '#fff',
    fontSize: '0.95rem',
  });
  const panelBodyStyle = { padding: '1.5rem' };
  const badgeStyle = (color) => ({
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: isSoc ? '0' : '50px',
    fontSize: '0.78rem',
    fontWeight: 600,
    background: `${color}20`,
    color,
    border: isSoc ? `1px solid ${color}` : 'none',
  });
  const scanTypeColors = {
    url: t.primary,
    ip: t.warning || '#f59e0b',
    file: t.textSecondary,
  };

  // Status dot for service indicator
  const statusDot = (online) => ({
    width: 10,
    height: 10,
    borderRadius: '50%',
    background: online ? (isSoc ? '#00ff41' : '#22c55e') : (t.danger || '#ef4444'),
    display: 'inline-block',
    boxShadow: online ? `0 0 6px ${isSoc ? '#00ff41' : '#22c55e'}` : 'none',
    animation: online ? 'pulse-dot 2s infinite' : 'none',
  });

  const resultStatus = result ? getStatusInfo(result) : null;
  const statusColorMap = { clean: t.success, warning: t.warning || '#f59e0b', danger: t.danger };

  return (
    <div style={{ minHeight: '100vh', background: t.bg, fontFamily: t.fontFamily, color: t.text, padding: '2rem' }}>
      {/* Pulse animation for service dot */}
      <style>{`@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }`}</style>

      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

        {/* ── Back link ──────────────────────────────── */}
        <Link
          to="/dashboard"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
            color: t.primary, textDecoration: 'none', fontWeight: 600,
            fontSize: '0.9rem', marginBottom: '1rem',
            fontFamily: t.fontFamily,
          }}
        >
          <ArrowLeft size={16} />
          {isSoc ? '[BACK_TO_DASHBOARD]' : 'Back to Dashboard'}
        </Link>

        {/* ── Hero Section ───────────────────────────── */}
        <div style={{
          background: isSoc
            ? `linear-gradient(135deg, #0a1628, #0d2137)`
            : 'linear-gradient(135deg, #1e40af, #3b82f6)',
          borderRadius: radius,
          padding: '2.5rem 2rem',
          textAlign: 'center',
          marginBottom: '1.5rem',
          border: isSoc ? `1px solid ${t.border}` : 'none',
        }}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <Shield size={32} color="#fff" />
            <h1 style={{
              margin: 0, color: '#fff',
              fontSize: isSoc ? '1.5rem' : '1.8rem',
              letterSpacing: isSoc ? '0.1em' : 'normal',
              fontFamily: t.fontFamily,
            }}>
              {isSoc ? 'THREAT_INTELLIGENCE_CENTER' : 'Threat Intelligence Center'}
            </h1>
          </div>
          <p style={{ color: 'rgba(255,255,255,0.85)', margin: '0.5rem 0 0', fontSize: '0.95rem' }}>
            {isSoc
              ? '> Comprehensive threat analysis via VirusTotal global intelligence network'
              : 'Comprehensive threat analysis powered by VirusTotal\'s global security intelligence network'}
          </p>
          <span style={{
            display: 'inline-block', marginTop: '1rem',
            padding: '5px 16px',
            background: 'rgba(255,255,255,0.15)',
            borderRadius: isSoc ? '0' : '50px',
            fontSize: '0.82rem', color: '#fff',
            border: isSoc ? '1px solid rgba(255,255,255,0.25)' : 'none',
          }}>
            {isSoc ? '[BETA]' : 'Beta'}
          </span>
        </div>

        {/* ── Service Status ─────────────────────────── */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          marginBottom: '1.5rem', fontSize: '0.85rem',
          color: t.textSecondary,
        }}>
          {serviceOnline === null ? (
            <>
              <Activity size={14} style={{ opacity: 0.5 }} />
              {isSoc ? 'CHECKING_SERVICE...' : 'Checking service status…'}
            </>
          ) : serviceOnline ? (
            <>
              <span style={statusDot(true)} />
              <Wifi size={14} color={isSoc ? '#00ff41' : '#22c55e'} />
              <span style={{ color: isSoc ? '#00ff41' : '#22c55e', fontWeight: 600 }}>
                {isSoc ? 'VIRUSTOTAL_SERVICE_ONLINE' : 'VirusTotal Service Online'}
              </span>
            </>
          ) : (
            <>
              <span style={statusDot(false)} />
              <WifiOff size={14} color={t.danger} />
              <span style={{ color: t.danger, fontWeight: 600 }}>
                {isSoc ? 'VIRUSTOTAL_SERVICE_OFFLINE' : 'VirusTotal Service Offline'}
              </span>
            </>
          )}
        </div>

        {/* ── Two-column grid ────────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>

          {/* ── Quick Threat Scan panel ───────────────── */}
          <div style={panelStyle}>
            <div style={panelHeaderStyle(
              isSoc ? 'linear-gradient(135deg, #0e2a47, #0a3d62)' : 'linear-gradient(135deg, #1e40af, #3b82f6)'
            )}>
              <Search size={18} />
              <span>{isSoc ? 'QUICK_THREAT_SCAN' : 'Quick Threat Scan'}</span>
              <span style={{
                marginLeft: 'auto', padding: '3px 10px',
                background: 'rgba(255,255,255,0.15)',
                borderRadius: isSoc ? '0' : '50px',
                fontSize: '0.72rem',
              }}>
                {isSoc ? 'VT_POWERED' : 'VirusTotal Powered'}
              </span>
            </div>
            <div style={panelBodyStyle}>
              <form onSubmit={handleScan}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: t.textSecondary, fontSize: '0.9rem' }}>
                  <Globe size={14} style={{ verticalAlign: '-2px', marginRight: '4px' }} />
                  {isSoc ? 'TARGET_INPUT' : 'Enter URL, IP, or File Hash'}
                </label>
                <input
                  type="text"
                  value={input}
                  onChange={handleInputChange}
                  placeholder={placeholders[scanType]}
                  required
                  style={{
                    width: '100%', boxSizing: 'border-box',
                    padding: '0.8rem 1rem',
                    background: t.bg,
                    border: `1px solid ${t.border}`,
                    borderRadius: radius,
                    color: t.text,
                    fontSize: '0.95rem',
                    fontFamily: t.fontFamily,
                    outline: 'none',
                    marginBottom: '0.5rem',
                  }}
                />

                {/* ── Scan type toggle ──────────────── */}
                <label style={{ display: 'block', marginTop: '0.75rem', marginBottom: '6px', fontWeight: 600, color: t.textSecondary, fontSize: '0.9rem' }}>
                  {isSoc ? 'SCAN_TYPE' : 'Scan Type'}
                </label>
                <div style={{
                  display: 'flex', gap: 0,
                  borderRadius: radius, overflow: 'hidden',
                  border: `1px solid ${t.border}`,
                  marginBottom: '1.25rem',
                }}>
                  {[
                    { value: 'url', label: isSoc ? 'URL/DOMAIN' : 'URL / Domain', icon: <LinkIcon size={14} /> },
                    { value: 'ip', label: isSoc ? 'IP_ADDR' : 'IP Address', icon: <Server size={14} /> },
                    { value: 'file', label: isSoc ? 'FILE_HASH' : 'File Hash', icon: <FileText size={14} /> },
                  ].map((opt, i) => {
                    const selected = scanType === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setScanType(opt.value)}
                        style={{
                          flex: 1,
                          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                          padding: '10px 8px',
                          cursor: 'pointer',
                          fontSize: '0.85rem', fontWeight: 600,
                          fontFamily: t.fontFamily,
                          border: 'none',
                          borderRight: i < 2 ? `1px solid ${t.border}` : 'none',
                          background: selected
                            ? (isSoc ? `${t.primary}30` : t.primary)
                            : (isSoc ? 'transparent' : t.bg),
                          color: selected
                            ? (isSoc ? t.primary : '#fff')
                            : t.textSecondary,
                          transition: 'all 0.2s',
                        }}
                      >
                        {opt.icon} {opt.label}
                      </button>
                    );
                  })}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: '100%', padding: '0.85rem',
                    border: isSoc ? `1px solid ${t.primary}` : 'none',
                    borderRadius: isSoc ? '0' : '50px',
                    background: isSoc ? `${t.primary}20` : 'linear-gradient(135deg, #1e40af, #3b82f6)',
                    color: isSoc ? t.primary : '#fff',
                    fontWeight: 700, fontSize: '0.95rem',
                    fontFamily: t.fontFamily,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                    transition: 'all 0.2s',
                  }}
                >
                  <Search size={16} style={{ verticalAlign: '-3px', marginRight: '6px' }} />
                  {loading
                    ? (isSoc ? '[SCANNING...]' : 'Scanning…')
                    : (isSoc ? '[START_SCAN]' : 'Start Scan')}
                </button>
              </form>

              {/* ── Error display ─────────────────── */}
              {error && (
                <div style={{
                  marginTop: '1rem', padding: '0.85rem',
                  borderRadius: radius,
                  border: `1px solid ${t.danger}`,
                  background: `${t.danger}15`,
                  color: t.danger,
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  fontSize: '0.9rem',
                }}>
                  <AlertTriangle size={16} /> {error}
                </div>
              )}
            </div>
          </div>

          {/* ── Advanced Analysis panel ───────────────── */}
          <div style={panelStyle}>
            <div style={panelHeaderStyle(
              isSoc ? 'linear-gradient(135deg, #0b3d2e, #0d4f3c)' : 'linear-gradient(135deg, #059669, #10b981)'
            )}>
              <Activity size={18} />
              <span>{isSoc ? 'ADVANCED_ANALYSIS' : 'Advanced Analysis'}</span>
              <span style={{
                marginLeft: 'auto', padding: '3px 10px',
                background: 'rgba(255,255,255,0.15)',
                borderRadius: isSoc ? '0' : '50px',
                fontSize: '0.72rem',
              }}>
                {isSoc ? 'DEEP_SCAN' : 'Deep Scan'}
              </span>
            </div>
            <div style={panelBodyStyle}>
              <p style={{ color: t.textSecondary, marginTop: 0, marginBottom: '1.25rem', fontSize: '0.9rem' }}>
                <Shield size={14} color={t.success} style={{ verticalAlign: '-2px', marginRight: '4px' }} />
                {isSoc
                  ? '> Multi-hop redirect tracking, JS analysis, behavioral detection'
                  : 'Advanced multi-hop redirect tracking, JavaScript analysis, and behavioral detection.'}
              </p>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1.5rem' }}>
                {[
                  { icon: <Globe size={16} color={t.success} />, text: isSoc ? 'Multi-hop redirect chain analysis' : 'Multi-hop redirect chain analysis' },
                  { icon: <FileText size={16} color={t.success} />, text: isSoc ? 'JavaScript deobfuscation & analysis' : 'JavaScript deobfuscation & analysis' },
                  { icon: <AlertTriangle size={16} color={t.success} />, text: isSoc ? 'Behavioral pattern detection' : 'Behavioral pattern detection' },
                  { icon: <Activity size={16} color={t.success} />, text: isSoc ? 'Network traffic analysis' : 'Network traffic analysis' },
                ].map((feat, i) => (
                  <li key={i} style={{
                    padding: '8px 0', color: t.text,
                    display: 'flex', alignItems: 'center', gap: '10px',
                    fontSize: '0.9rem',
                    borderBottom: i < 3 ? `1px solid ${t.border}22` : 'none',
                  }}>
                    {feat.icon} {feat.text}
                  </li>
                ))}
              </ul>
              <Link
                to="/deep-search"
                style={{
                  display: 'block', textAlign: 'center', textDecoration: 'none',
                  padding: '0.85rem',
                  borderRadius: isSoc ? '0' : '50px',
                  background: isSoc ? `${t.success}20` : 'linear-gradient(135deg, #059669, #10b981)',
                  color: isSoc ? t.success : '#fff',
                  border: isSoc ? `1px solid ${t.success}` : 'none',
                  fontWeight: 700, fontSize: '0.95rem',
                  fontFamily: t.fontFamily,
                }}
              >
                <Activity size={16} style={{ verticalAlign: '-3px', marginRight: '6px' }} />
                {isSoc ? '[LAUNCH_DEEP_ANALYSIS]' : 'Launch Deep Analysis'}
              </Link>
            </div>
          </div>
        </div>

        {/* ── Scan Results ────────────────────────────── */}
        {result && (
          <div style={{ ...panelStyle, marginBottom: '1.5rem' }}>
            <div style={{
              ...panelHeaderStyle('transparent'),
              color: t.text,
              background: t.bgSecondary,
              borderBottom: `1px solid ${t.border}`,
              justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={18} color={t.primary} />
                <span>{isSoc ? 'SCAN_RESULTS' : 'Scan Results'}</span>
              </div>
              <span style={badgeStyle(statusColorMap[resultStatus.cls])}>
                {resultStatus.label}
              </span>
            </div>
            <div style={panelBodyStyle}>
              {/* Status banner */}
              <div style={{
                borderRadius: radius, padding: '1.25rem',
                marginBottom: '1.25rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: `${statusColorMap[resultStatus.cls]}12`,
                border: `1px solid ${statusColorMap[resultStatus.cls]}40`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {resultStatus.cls === 'clean'
                    ? <CheckCircle2 size={28} color={t.success} />
                    : resultStatus.cls === 'warning'
                      ? <AlertTriangle size={28} color={t.warning || '#f59e0b'} />
                      : <AlertTriangle size={28} color={t.danger} />}
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '1.05rem', color: statusColorMap[resultStatus.cls] }}>
                      {resultStatus.cls === 'clean'
                        ? (isSoc ? 'NO_THREATS_DETECTED' : 'No Threats Detected')
                        : resultStatus.cls === 'warning'
                          ? (isSoc ? 'POTENTIALLY_SUSPICIOUS' : 'Potentially Suspicious')
                          : (isSoc ? 'THREAT_DETECTED' : 'Threat Detected')}
                    </div>
                    <div style={{ color: t.textSecondary, fontSize: '0.85rem', marginTop: '2px' }}>
                      {result.details?.message || 'Scan completed.'}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.8rem', fontWeight: 700, color: statusColorMap[resultStatus.cls] }}>
                    {result.threat_score ?? 0}<span style={{ fontSize: '0.9rem', fontWeight: 400 }}>/100</span>
                  </div>
                  <div style={{ color: t.textSecondary, fontSize: '0.78rem' }}>
                    {isSoc ? 'THREAT_SCORE' : 'threat score'}
                  </div>
                </div>
              </div>

              {/* Detail grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ background: `${t.border}20`, border: `1px solid ${t.border}`, borderRadius: radius, overflow: 'hidden' }}>
                  <div style={{ padding: '0.7rem 1rem', background: `${t.border}30`, fontWeight: 600, fontSize: '0.85rem', color: t.textSecondary }}>
                    {isSoc ? 'RESOURCE_INFO' : 'Resource Information'}
                  </div>
                  <div style={{ padding: '0.8rem 1rem', fontSize: '0.88rem' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <tbody>
                        <tr><td style={{ padding: '6px 0', color: t.textSecondary, fontWeight: 600, width: '35%' }}>Target</td><td style={{ padding: '6px 0', wordBreak: 'break-all' }}>{result._input || result.url}</td></tr>
                        <tr><td style={{ padding: '6px 0', color: t.textSecondary, fontWeight: 600 }}>Type</td><td style={{ padding: '6px 0' }}><span style={badgeStyle(scanTypeColors[result._type] || t.primary)}>{result._type?.toUpperCase()}</span></td></tr>
                        <tr><td style={{ padding: '6px 0', color: t.textSecondary, fontWeight: 600 }}>Score</td><td style={{ padding: '6px 0' }}>{result.threat_score ?? 0}/100</td></tr>
                        <tr><td style={{ padding: '6px 0', color: t.textSecondary, fontWeight: 600 }}>Status</td><td style={{ padding: '6px 0' }}><span style={badgeStyle(statusColorMap[resultStatus.cls])}>{resultStatus.label}</span></td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                <div style={{ background: `${t.border}20`, border: `1px solid ${t.border}`, borderRadius: radius, overflow: 'hidden' }}>
                  <div style={{ padding: '0.7rem 1rem', background: `${t.border}30`, fontWeight: 600, fontSize: '0.85rem', color: t.textSecondary }}>
                    {isSoc ? 'THREAT_LEVEL' : 'Threat Level Indicator'}
                  </div>
                  <div style={{ padding: '0.8rem 1rem' }}>
                    {/* Detection bar */}
                    <div style={{ marginBottom: '0.5rem', fontSize: '0.82rem', color: t.textSecondary, display: 'flex', justifyContent: 'space-between' }}>
                      <span>{isSoc ? 'THREAT_LEVEL' : 'Threat Level'}</span>
                      <span>{result.threat_score ?? 0}%</span>
                    </div>
                    <div style={{ height: 8, background: `${t.border}40`, borderRadius: 4, overflow: 'hidden', marginBottom: '1rem' }}>
                      <div style={{
                        height: '100%', borderRadius: 4,
                        width: `${Math.min(result.threat_score ?? 0, 100)}%`,
                        background: statusColorMap[resultStatus.cls],
                        transition: 'width 0.5s',
                      }} />
                    </div>
                    {result.is_malicious !== undefined && (
                      <div style={{ fontSize: '0.85rem', color: t.textSecondary }}>
                        <strong style={{ color: t.text }}>{isSoc ? 'VERDICT:' : 'Verdict:'}</strong>{' '}
                        <span style={{ color: result.is_malicious ? t.danger : t.success }}>
                          {result.is_malicious
                            ? (isSoc ? 'MALICIOUS' : 'Potentially Malicious')
                            : (isSoc ? 'CLEAN' : 'No Known Threats')}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Scan History Table ──────────────────────── */}
        <div style={panelStyle}>
          <div style={{
            ...panelHeaderStyle(
              isSoc ? 'linear-gradient(135deg, #0a2e4a, #0e3d5e)' : 'linear-gradient(135deg, #0891b2, #06b6d4)'
            ),
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Search size={18} />
              <span>{isSoc ? 'RECENT_SCAN_HISTORY' : 'Recent Scan History'}</span>
            </div>
            {history.length > 0 && (
              <button
                onClick={() => setHistory([])}
                style={{
                  padding: '4px 12px',
                  borderRadius: isSoc ? '0' : '50px',
                  border: '1px solid rgba(255,255,255,0.25)',
                  background: 'transparent',
                  color: 'rgba(255,255,255,0.75)',
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                  fontFamily: t.fontFamily,
                }}
              >
                {isSoc ? '[CLEAR]' : 'Clear'}
              </button>
            )}
          </div>
          <div style={{ padding: 0, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {[
                    isSoc ? 'DATE/TIME' : 'Date/Time',
                    isSoc ? 'TARGET' : 'Target',
                    isSoc ? 'TYPE' : 'Type',
                    isSoc ? 'STATUS' : 'Status',
                    isSoc ? 'SCORE' : 'Score',
                    isSoc ? 'ACTIONS' : 'Actions',
                  ].map((col) => (
                    <th key={col} style={{
                      padding: '12px 16px', textAlign: col === 'Actions' || col === 'ACTIONS' ? 'center' : 'left',
                      fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.5px',
                      color: t.primary, background: `${t.border}20`,
                      borderBottom: `1px solid ${t.border}`,
                      fontFamily: t.fontFamily,
                    }}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '3rem 2rem', color: t.textSecondary }}>
                      <Search size={28} style={{ opacity: 0.3, marginBottom: '0.75rem', display: 'block', margin: '0 auto 0.75rem' }} />
                      <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '4px' }}>
                        {isSoc ? 'NO_SCAN_HISTORY' : 'No scan history available'}
                      </div>
                      <div style={{ fontSize: '0.85rem', opacity: 0.6 }}>
                        {isSoc ? '> Your recent scans will appear here' : 'Your recent scans will appear here'}
                      </div>
                    </td>
                  </tr>
                ) : (
                  history.map((item) => {
                    const st = getStatusInfo(item);
                    return (
                      <tr key={item.scanId} style={{ borderBottom: `1px solid ${t.border}30` }}>
                        <td style={{ padding: '10px 16px', fontSize: '0.85rem', color: t.textSecondary, whiteSpace: 'nowrap' }}>
                          {new Date(item._time).toLocaleString()}
                        </td>
                        <td style={{ padding: '10px 16px', fontSize: '0.85rem', wordBreak: 'break-all', maxWidth: '240px' }}>
                          {item._input || item.url}
                        </td>
                        <td style={{ padding: '10px 16px' }}>
                          <span style={badgeStyle(scanTypeColors[item._type] || t.primary)}>
                            {(item._type || 'url').toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '10px 16px' }}>
                          <span style={badgeStyle(statusColorMap[st.cls])}>
                            {st.label}
                          </span>
                        </td>
                        <td style={{ padding: '10px 16px', fontSize: '0.85rem', fontWeight: 600 }}>
                          {item.threat_score ?? 0}/100
                        </td>
                        <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                          <button
                            onClick={() => { setResult(item); window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }}
                            title="View"
                            style={{
                              padding: '4px 10px', marginRight: '4px',
                              borderRadius: isSoc ? '0' : '50px',
                              border: `1px solid ${t.primary}50`,
                              background: 'transparent', color: t.primary,
                              cursor: 'pointer', fontSize: '0.8rem',
                              fontFamily: t.fontFamily,
                            }}
                          >
                            {isSoc ? '[VIEW]' : 'View'}
                          </button>
                          <button
                            onClick={() => removeHistoryItem(item.scanId)}
                            title="Remove"
                            style={{
                              padding: '4px 10px',
                              borderRadius: isSoc ? '0' : '50px',
                              border: `1px solid ${t.danger}50`,
                              background: 'transparent', color: t.danger,
                              cursor: 'pointer', fontSize: '0.8rem',
                              fontFamily: t.fontFamily,
                            }}
                          >
                            {isSoc ? '[DEL]' : 'Remove'}
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
