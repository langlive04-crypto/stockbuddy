/**
 * useResponsive.js - 響應式 Hook
 * V10.28 新增
 *
 * 功能：
 * - 偵測螢幕尺寸
 * - 響應式斷點判斷
 * - 觸控裝置偵測
 * - 螢幕方向偵測
 */

import { useState, useEffect, useCallback } from 'react';

// Tailwind CSS 斷點
const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

/**
 * 響應式設計 Hook
 */
const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [orientation, setOrientation] = useState('portrait');

  // 更新視窗尺寸
  const handleResize = useCallback(() => {
    setWindowSize({
      width: window.innerWidth,
      height: window.innerHeight,
    });
    setOrientation(window.innerWidth > window.innerHeight ? 'landscape' : 'portrait');
  }, []);

  // 初始化
  useEffect(() => {
    // 偵測觸控裝置
    const hasTouch =
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0;
    setIsTouchDevice(hasTouch);

    // 初始方向
    setOrientation(window.innerWidth > window.innerHeight ? 'landscape' : 'portrait');

    // 監聽視窗尺寸變化
    window.addEventListener('resize', handleResize);

    // 監聽方向變化
    window.addEventListener('orientationchange', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, [handleResize]);

  // 斷點判斷函數
  const isXs = windowSize.width < BREAKPOINTS.sm;
  const isSm = windowSize.width >= BREAKPOINTS.sm && windowSize.width < BREAKPOINTS.md;
  const isMd = windowSize.width >= BREAKPOINTS.md && windowSize.width < BREAKPOINTS.lg;
  const isLg = windowSize.width >= BREAKPOINTS.lg && windowSize.width < BREAKPOINTS.xl;
  const isXl = windowSize.width >= BREAKPOINTS.xl && windowSize.width < BREAKPOINTS['2xl'];
  const is2Xl = windowSize.width >= BREAKPOINTS['2xl'];

  // 便利判斷
  const isMobile = windowSize.width < BREAKPOINTS.md;
  const isTablet = windowSize.width >= BREAKPOINTS.md && windowSize.width < BREAKPOINTS.lg;
  const isDesktop = windowSize.width >= BREAKPOINTS.lg;

  // 斷點以上判斷
  const isSmUp = windowSize.width >= BREAKPOINTS.sm;
  const isMdUp = windowSize.width >= BREAKPOINTS.md;
  const isLgUp = windowSize.width >= BREAKPOINTS.lg;
  const isXlUp = windowSize.width >= BREAKPOINTS.xl;

  // 斷點以下判斷
  const isSmDown = windowSize.width < BREAKPOINTS.sm;
  const isMdDown = windowSize.width < BREAKPOINTS.md;
  const isLgDown = windowSize.width < BREAKPOINTS.lg;
  const isXlDown = windowSize.width < BREAKPOINTS.xl;

  // 取得當前斷點名稱
  const currentBreakpoint = is2Xl
    ? '2xl'
    : isXl
      ? 'xl'
      : isLg
        ? 'lg'
        : isMd
          ? 'md'
          : isSm
            ? 'sm'
            : 'xs';

  return {
    // 視窗尺寸
    windowSize,
    width: windowSize.width,
    height: windowSize.height,

    // 斷點判斷
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    is2Xl,

    // 便利判斷
    isMobile,
    isTablet,
    isDesktop,

    // 斷點以上
    isSmUp,
    isMdUp,
    isLgUp,
    isXlUp,

    // 斷點以下
    isSmDown,
    isMdDown,
    isLgDown,
    isXlDown,

    // 其他
    currentBreakpoint,
    isTouchDevice,
    orientation,
    isLandscape: orientation === 'landscape',
    isPortrait: orientation === 'portrait',
  };
};

export default useResponsive;

/**
 * 響應式條件組件
 * 根據斷點顯示/隱藏內容
 */
export const Responsive = ({
  children,
  show = null, // 'mobile' | 'tablet' | 'desktop' | 'sm' | 'md' | 'lg' | 'xl'
  hide = null,
}) => {
  const responsive = useResponsive();

  const shouldShow = () => {
    if (show) {
      switch (show) {
        case 'mobile':
          return responsive.isMobile;
        case 'tablet':
          return responsive.isTablet;
        case 'desktop':
          return responsive.isDesktop;
        case 'sm':
          return responsive.isSm;
        case 'md':
          return responsive.isMd;
        case 'lg':
          return responsive.isLg;
        case 'xl':
          return responsive.isXl;
        case 'smUp':
          return responsive.isSmUp;
        case 'mdUp':
          return responsive.isMdUp;
        case 'lgUp':
          return responsive.isLgUp;
        case 'xlUp':
          return responsive.isXlUp;
        default:
          return true;
      }
    }

    if (hide) {
      switch (hide) {
        case 'mobile':
          return !responsive.isMobile;
        case 'tablet':
          return !responsive.isTablet;
        case 'desktop':
          return !responsive.isDesktop;
        case 'sm':
          return !responsive.isSm;
        case 'md':
          return !responsive.isMd;
        case 'lg':
          return !responsive.isLg;
        case 'xl':
          return !responsive.isXl;
        default:
          return true;
      }
    }

    return true;
  };

  if (!shouldShow()) return null;
  return <>{children}</>;
};
