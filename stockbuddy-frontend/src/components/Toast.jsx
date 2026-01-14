/**
 * Toast.jsx - Toast 通知系統
 * V10.29 新增
 *
 * 功能：
 * - 操作回饋通知
 * - 多種通知類型（成功/錯誤/警告/資訊）
 * - 自動消失與手動關閉
 * - 堆疊顯示多則通知
 */

import React, { createContext, useContext, useState, useCallback, memo } from 'react';

// Toast Context
const ToastContext = createContext(null);

// Toast 類型配置
const TOAST_TYPES = {
  success: {
    icon: '✓',
    bgClass: 'bg-emerald-600',
    borderClass: 'border-emerald-500',
  },
  error: {
    icon: '✕',
    bgClass: 'bg-red-600',
    borderClass: 'border-red-500',
  },
  warning: {
    icon: '⚠',
    bgClass: 'bg-yellow-600',
    borderClass: 'border-yellow-500',
  },
  info: {
    icon: 'ℹ',
    bgClass: 'bg-blue-600',
    borderClass: 'border-blue-500',
  },
};

// 單個 Toast 組件
const ToastItem = memo(({ toast, onClose }) => {
  const config = TOAST_TYPES[toast.type] || TOAST_TYPES.info;

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${config.bgClass} ${config.borderClass} text-white animate-slide-in-right`}
      role="alert"
    >
      {/* 圖示 */}
      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">
        {config.icon}
      </div>

      {/* 內容 */}
      <div className="flex-1 min-w-0">
        {toast.title && (
          <div className="font-medium text-sm">{toast.title}</div>
        )}
        <div className={`text-sm ${toast.title ? 'opacity-90' : ''}`}>
          {toast.message}
        </div>
      </div>

      {/* 關閉按鈕 */}
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 p-1 hover:bg-white/20 rounded transition-colors"
        aria-label="關閉通知"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
});

// Toast 容器組件
const ToastContainer = ({ toasts, onClose }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} onClose={onClose} />
        </div>
      ))}

      {/* 動畫樣式 */}
      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

// Toast Provider
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  // 新增 Toast
  const addToast = useCallback((options) => {
    const id = Date.now() + Math.random();
    const toast = {
      id,
      type: 'info',
      duration: 4000,
      ...options,
    };

    setToasts((prev) => [...prev, toast]);

    // 自動移除
    if (toast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, toast.duration);
    }

    return id;
  }, []);

  // 移除 Toast
  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // 快捷方法
  const success = useCallback(
    (message, options = {}) => addToast({ ...options, message, type: 'success' }),
    [addToast]
  );

  const error = useCallback(
    (message, options = {}) => addToast({ ...options, message, type: 'error', duration: 6000 }),
    [addToast]
  );

  const warning = useCallback(
    (message, options = {}) => addToast({ ...options, message, type: 'warning' }),
    [addToast]
  );

  const info = useCallback(
    (message, options = {}) => addToast({ ...options, message, type: 'info' }),
    [addToast]
  );

  // 清除所有
  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  const value = {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
    clearAll,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
};

// Hook
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export default ToastContext;
