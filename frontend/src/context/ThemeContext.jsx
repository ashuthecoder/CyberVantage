import React, { createContext, useState, useContext, useEffect } from 'react';

const ThemeContext = createContext(null);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

const themes = {
  soc: {
    name: 'soc',
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
    name: 'modern',
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

export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved || 'soc';
  });

  useEffect(() => {
    localStorage.setItem('theme', currentTheme);
  }, [currentTheme]);

  const toggleTheme = () => {
    setCurrentTheme(prev => prev === 'soc' ? 'modern' : 'soc');
  };

  const setTheme = (themeName) => {
    if (themes[themeName]) {
      setCurrentTheme(themeName);
    }
  };

  const value = {
    theme: themes[currentTheme],
    themeName: currentTheme,
    toggleTheme,
    setTheme,
    themes,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};
