// Utility to load vault-themes.json and provide a theme context for the app
import React, { createContext, useContext, useState, useEffect } from 'react';
import themes from '../assets/vault-themes.json';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  // Default to first theme, or use localStorage, or system preference
  const [themeIndex, setThemeIndex] = useState(() => {
    const stored = localStorage.getItem('vault-theme-index');
    return stored ? parseInt(stored, 10) : 0;
  });
  const theme = themes[themeIndex] || themes[0];

  useEffect(() => {
    localStorage.setItem('vault-theme-index', themeIndex);
    // Set CSS variables for primary/accent
    document.documentElement.style.setProperty('--vault-primary', theme.primary);
    document.documentElement.style.setProperty('--vault-accent', theme.accent);
    document.documentElement.setAttribute('data-theme-mode', theme.mode);
  }, [theme, themeIndex]);

  return React.createElement(
    ThemeContext.Provider,
    { value: { theme, themeIndex, setThemeIndex, themes } },
    children
  );
}

export function useVaultTheme() {
  return useContext(ThemeContext);
}
