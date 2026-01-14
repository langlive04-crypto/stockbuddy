/**
 * ThemeContext.jsx - 主題上下文
 * V10.27 新增
 *
 * 功能：
 * - 深色/淺色主題切換
 * - 自動偵測系統偏好
 * - 本地儲存主題設定
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

const THEME_KEY = 'stockbuddy_theme';

// 主題定義
export const themes = {
  dark: {
    name: 'dark',
    label: '深色模式',
    colors: {
      bg: {
        primary: 'bg-slate-900',
        secondary: 'bg-slate-800',
        tertiary: 'bg-slate-700',
        card: 'bg-slate-800',
        hover: 'hover:bg-slate-700',
      },
      text: {
        primary: 'text-white',
        secondary: 'text-slate-300',
        muted: 'text-slate-400',
        disabled: 'text-slate-500',
      },
      border: {
        primary: 'border-slate-700',
        secondary: 'border-slate-600',
      },
      accent: {
        positive: 'text-emerald-400',
        negative: 'text-red-400',
        warning: 'text-yellow-400',
        info: 'text-blue-400',
      },
    },
  },
  light: {
    name: 'light',
    label: '淺色模式',
    colors: {
      bg: {
        primary: 'bg-gray-100',
        secondary: 'bg-white',
        tertiary: 'bg-gray-50',
        card: 'bg-white',
        hover: 'hover:bg-gray-100',
      },
      text: {
        primary: 'text-gray-900',
        secondary: 'text-gray-700',
        muted: 'text-gray-500',
        disabled: 'text-gray-400',
      },
      border: {
        primary: 'border-gray-200',
        secondary: 'border-gray-300',
      },
      accent: {
        positive: 'text-emerald-600',
        negative: 'text-red-600',
        warning: 'text-yellow-600',
        info: 'text-blue-600',
      },
    },
  },
};

// Context
const ThemeContext = createContext(null);

// Provider
export const ThemeProvider = ({ children }) => {
  const [themeName, setThemeName] = useState('dark');
  const [isLoaded, setIsLoaded] = useState(false);

  // 初始化時讀取設定或系統偏好
  useEffect(() => {
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme && (savedTheme === 'dark' || savedTheme === 'light')) {
      setThemeName(savedTheme);
    } else {
      // 檢測系統偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setThemeName(prefersDark ? 'dark' : 'light');
    }
    setIsLoaded(true);
  }, []);

  // 監聽系統主題變化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => {
      if (!localStorage.getItem(THEME_KEY)) {
        setThemeName(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // 更新 document class
  useEffect(() => {
    if (isLoaded) {
      document.documentElement.classList.remove('dark', 'light');
      document.documentElement.classList.add(themeName);
    }
  }, [themeName, isLoaded]);

  // 切換主題
  const toggleTheme = () => {
    const newTheme = themeName === 'dark' ? 'light' : 'dark';
    setThemeName(newTheme);
    localStorage.setItem(THEME_KEY, newTheme);
  };

  // 設定特定主題
  const setTheme = (theme) => {
    if (theme === 'dark' || theme === 'light') {
      setThemeName(theme);
      localStorage.setItem(THEME_KEY, theme);
    }
  };

  const value = {
    theme: themes[themeName],
    themeName,
    isDark: themeName === 'dark',
    isLight: themeName === 'light',
    toggleTheme,
    setTheme,
  };

  if (!isLoaded) {
    return null; // 或顯示載入畫面
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;
