/**
 * useThemeClasses.js - 主題類別輔助 Hook
 * V10.35 新增
 *
 * 功能：
 * - 提供主題感知的 CSS 類別
 * - 簡化組件中的主題類別使用
 */

import { useTheme } from '../contexts/ThemeContext';

/**
 * 主題類別 Hook
 * 返回當前主題對應的 CSS 類別
 */
export const useThemeClasses = () => {
  const { isDark } = useTheme();

  return {
    // 背景
    bgPrimary: isDark ? 'bg-slate-900' : 'bg-gray-100',
    bgSecondary: isDark ? 'bg-slate-800' : 'bg-white',
    bgTertiary: isDark ? 'bg-slate-700' : 'bg-gray-50',
    bgCard: isDark ? 'bg-slate-800' : 'bg-white',
    bgHover: isDark ? 'hover:bg-slate-700' : 'hover:bg-gray-100',
    bgInput: isDark ? 'bg-slate-700' : 'bg-gray-50',

    // 文字
    textPrimary: isDark ? 'text-white' : 'text-gray-900',
    textSecondary: isDark ? 'text-slate-300' : 'text-gray-700',
    textMuted: isDark ? 'text-slate-400' : 'text-gray-500',
    textDisabled: isDark ? 'text-slate-500' : 'text-gray-400',

    // 邊框
    borderPrimary: isDark ? 'border-slate-700' : 'border-gray-200',
    borderSecondary: isDark ? 'border-slate-600' : 'border-gray-300',

    // 漸層
    gradient: isDark
      ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900'
      : 'bg-gradient-to-br from-gray-100 via-white to-gray-100',

    // 卡片組合類
    card: isDark
      ? 'bg-slate-800 border-slate-700 shadow-lg'
      : 'bg-white border-gray-200 shadow-md',

    // 輸入框組合類
    input: isDark
      ? 'bg-slate-700 border-slate-600 text-white placeholder-slate-500'
      : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400',

    // 其他常用組合
    divider: isDark ? 'border-slate-700' : 'border-gray-200',
    overlay: isDark ? 'bg-slate-900/80' : 'bg-white/80',
  };
};

/**
 * 條件類別工具
 * 根據主題返回對應的類別
 */
export const themeClass = (isDark, darkClass, lightClass) => {
  return isDark ? darkClass : lightClass;
};

export default useThemeClasses;
