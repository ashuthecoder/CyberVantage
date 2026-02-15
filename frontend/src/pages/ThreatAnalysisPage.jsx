import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Search, Globe, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { threats } from '../api/client';

export default function ThreatAnalysisPage() {
  const { theme, themeName } = useTheme();
  const { isAuthenticated } = useAuth();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  const t = theme;

  const handleScan = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (!isAuthenticated) {
      setError('Please login to run VirusTotal checks.');
      return;
    }

    setLoading(true);
    try {
      const response = await threats.checkUrl(url);
      setResult(response.data);
      setHistory((prev) => [response.data, ...prev].slice(0, 5));
    } catch (scanError) {
      setError(scanError.response?.data?.detail || 'Unable to scan this URL right now.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: t.bg, fontFamily: t.fontFamily, color: t.text, padding: '2rem' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
        <div style={{
          marginBottom: '1.5rem',
          padding: '1.5rem',
          border: `1px solid ${t.border}`,
          background: themeName === 'soc' ? t.bgSecondary : t.bgSecondary,
          borderRadius: themeName === 'soc' ? '0' : '12px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Shield size={30} color={t.primary} />
              <div>
                <h1 style={{ margin: 0, fontSize: '1.3rem', color: t.primary, letterSpacing: themeName === 'soc' ? '0.06em' : 'normal' }}>
                  {themeName === 'soc' ? 'VIRUSTOTAL_THREAT_CENTER' : 'VirusTotal Threat Analysis Center'}
                </h1>
                <p style={{ margin: '0.4rem 0 0', color: t.textSecondary, fontSize: '0.92rem' }}>
                  Scan suspicious URLs and review threat responses in real-time.
                </p>
              </div>
            </div>
            <Link to="/dashboard" style={{ color: t.primary, textDecoration: 'none', fontWeight: 700 }}>
              {themeName === 'soc' ? '[BACK_TO_DASHBOARD]' : 'Back to Dashboard'}
            </Link>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1rem' }}>
          <div style={{ border: `1px solid ${t.border}`, background: t.bgSecondary, borderRadius: themeName === 'soc' ? '0' : '12px', padding: '1.5rem' }}>
            <h2 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: t.primary }}>
              {themeName === 'soc' ? 'RUN_THREAT_SCAN' : 'Run Threat Scan'}
            </h2>
            <form onSubmit={handleScan}>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: t.textSecondary }}>URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  background: t.bg,
                  border: `1px solid ${t.border}`,
                  color: t.text,
                  marginBottom: '1rem',
                  outline: 'none'
                }}
              />
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: `1px solid ${t.primary}`,
                  background: themeName === 'soc' ? 'rgba(0, 217, 255, 0.1)' : t.primary,
                  color: themeName === 'soc' ? t.primary : '#fff',
                  fontWeight: 700,
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? '[SCANNING...]' : '[SCAN_URL]'}
              </button>
            </form>

            {error && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', border: `1px solid ${t.danger}`, color: t.danger }}>
                {error}
              </div>
            )}

            {result && (
              <div style={{ marginTop: '1rem', padding: '1rem', border: `1px solid ${result.is_malicious ? t.danger : t.success}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  {result.is_malicious ? <AlertTriangle size={18} color={t.danger} /> : <CheckCircle2 size={18} color={t.success} />}
                  <strong>{result.is_malicious ? 'Potential threat detected' : 'No known threat detected'}</strong>
                </div>
                <div style={{ color: t.textSecondary, fontSize: '0.9rem' }}>Threat score: {result.threat_score}/100</div>
                <div style={{ color: t.textSecondary, fontSize: '0.9rem', marginTop: '0.35rem' }}>
                  {result.details?.message || 'Scan completed.'}
                </div>
              </div>
            )}
          </div>

          <div style={{ border: `1px solid ${t.border}`, background: t.bgSecondary, borderRadius: themeName === 'soc' ? '0' : '12px', padding: '1.5rem' }}>
            <h2 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1rem', color: t.primary }}>
              {themeName === 'soc' ? 'SCAN_HISTORY' : 'Recent Scans'}
            </h2>
            {history.length === 0 ? (
              <div style={{ color: t.textSecondary, fontSize: '0.9rem' }}>No scans yet in this session.</div>
            ) : (
              history.map((item, idx) => (
                <div key={`${item.url}-${idx}`} style={{ borderTop: idx === 0 ? 'none' : `1px solid ${t.border}`, padding: idx === 0 ? '0' : '0.75rem 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <Globe size={14} color={t.primary} />
                    <span style={{ fontSize: '0.85rem', wordBreak: 'break-all' }}>{item.url}</span>
                  </div>
                  <div style={{ color: item.is_malicious ? t.danger : t.success, fontSize: '0.82rem' }}>
                    {item.is_malicious ? 'Malicious' : 'Clean'} • Score {item.threat_score}/100
                  </div>
                </div>
              ))
            )}
            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: `1px solid ${t.border}`, color: t.textSecondary, fontSize: '0.85rem', display: 'flex', gap: '0.5rem' }}>
              <Search size={14} />
              URL scanning uses the backend threat endpoint.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
