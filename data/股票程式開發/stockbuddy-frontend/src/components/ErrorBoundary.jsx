/**
 * ErrorBoundary.jsx - 錯誤邊界組件
 * V10.35 新增
 *
 * 功能：
 * - 捕獲子組件的 JavaScript 錯誤
 * - 顯示友善的錯誤訊息
 * - 提供重試功能
 * - 記錄錯誤資訊
 */

import React, { Component } from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // 更新 state 使下一次渲染能夠顯示降級 UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // 記錄錯誤資訊
    this.setState({ errorInfo });

    // 可以在這裡將錯誤發送到錯誤監控服務
    // 例如：Sentry, LogRocket, etc.
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback, level = 'page' } = this.props;

    if (hasError) {
      // 如果提供了自定義 fallback，使用它
      if (fallback) {
        return typeof fallback === 'function'
          ? fallback({ error, errorInfo, retry: this.handleRetry })
          : fallback;
      }

      // 根據 level 顯示不同的錯誤 UI
      if (level === 'component') {
        return (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
            <span className="text-red-400 text-2xl">⚠️</span>
            <p className="text-red-300 text-sm mt-2">組件載入失敗</p>
            <button
              onClick={this.handleRetry}
              className="mt-2 px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-xs rounded transition-colors"
            >
              重試
            </button>
          </div>
        );
      }

      // 頁面級別錯誤
      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-800 rounded-xl border border-slate-700 p-8 text-center">
            {/* 錯誤圖示 */}
            <div className="text-6xl mb-4">🚨</div>

            {/* 錯誤標題 */}
            <h1 className="text-xl font-bold text-white mb-2">
              糟糕，出了點問題
            </h1>

            {/* 錯誤描述 */}
            <p className="text-slate-400 mb-6">
              應用程式遇到了一個錯誤，我們正在努力修復中。
            </p>

            {/* 錯誤詳情（開發模式下顯示） */}
            {process.env.NODE_ENV === 'development' && error && (
              <div className="mb-6 p-4 bg-slate-900/50 rounded-lg text-left">
                <p className="text-red-400 text-sm font-mono mb-2">
                  {error.toString()}
                </p>
                {errorInfo && (
                  <pre className="text-slate-500 text-xs overflow-auto max-h-40">
                    {errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            {/* 操作按鈕 */}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
              >
                重試
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
              >
                重新整理頁面
              </button>
            </div>

            {/* 額外提示 */}
            <p className="text-slate-500 text-xs mt-6">
              如果問題持續發生，請嘗試清除瀏覽器快取或聯繫技術支援。
            </p>
          </div>
        </div>
      );
    }

    return children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.oneOfType([PropTypes.node, PropTypes.func]),
  level: PropTypes.oneOf(['page', 'component']),
};

ErrorBoundary.defaultProps = {
  fallback: null,
  level: 'page',
};

// HOC 用於函數組件
export const withErrorBoundary = (WrappedComponent, options = {}) => {
  const { level = 'component', fallback } = options;

  return function WithErrorBoundary(props) {
    return (
      <ErrorBoundary level={level} fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
};

// 專門用於 Suspense 的錯誤邊界
export class SuspenseErrorBoundary extends ErrorBoundary {
  render() {
    const { hasError } = this.state;
    const { children, fallback, loadingFallback } = this.props;

    if (hasError) {
      return fallback || (
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <span className="text-4xl mb-2 block">⚠️</span>
            <p className="text-slate-400">載入失敗</p>
            <button
              onClick={this.handleRetry}
              className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors"
            >
              重試
            </button>
          </div>
        </div>
      );
    }

    return (
      <React.Suspense fallback={loadingFallback || <div className="animate-pulse p-4">載入中...</div>}>
        {children}
      </React.Suspense>
    );
  }
}

SuspenseErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node,
  loadingFallback: PropTypes.node,
};

SuspenseErrorBoundary.defaultProps = {
  fallback: null,
  loadingFallback: null,
};

export default ErrorBoundary;
