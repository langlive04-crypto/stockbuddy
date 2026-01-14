/**
 * RealtimeManager.jsx - 即時數據管理器
 * V10.32 新增
 *
 * 功能：
 * - 自動刷新頻率設定
 * - 數據更新時間戳顯示
 * - 連線狀態指示
 * - 刷新控制面板
 */

import React, { useState, useEffect, useCallback } from 'react';

// 刷新頻率選項 (毫秒)
const REFRESH_OPTIONS = [
  { value: 0, label: '手動刷新', desc: '不自動更新' },
  { value: 10000, label: '10 秒', desc: '即時追蹤' },
  { value: 30000, label: '30 秒', desc: '積極更新' },
  { value: 60000, label: '1 分鐘', desc: '標準更新' },
  { value: 300000, label: '5 分鐘', desc: '省電模式' },
];

// 連線狀態
const CONNECTION_STATUS = {
  connected: { label: '已連線', color: 'text-emerald-400', bg: 'bg-emerald-500', icon: '🟢' },
  connecting: { label: '連線中', color: 'text-yellow-400', bg: 'bg-yellow-500', icon: '🟡' },
  disconnected: { label: '已離線', color: 'text-slate-400', bg: 'bg-slate-500', icon: '⚫' },
  error: { label: '連線錯誤', color: 'text-red-400', bg: 'bg-red-500', icon: '🔴' },
};

const RealtimeManager = ({
  onRefresh,
  lastUpdate = null,
  isLoading = false,
  connectionStatus = 'connected',
}) => {
  const [refreshInterval, setRefreshInterval] = useState(() => {
    const saved = localStorage.getItem('stockbuddy_refresh_interval');
    return saved ? parseInt(saved) : 60000;
  });
  const [countdown, setCountdown] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // 保存刷新設定
  useEffect(() => {
    localStorage.setItem('stockbuddy_refresh_interval', refreshInterval.toString());
  }, [refreshInterval]);

  // 自動刷新邏輯
  useEffect(() => {
    if (refreshInterval === 0 || !autoRefreshEnabled) {
      setCountdown(0);
      return;
    }

    const startTime = Date.now();
    setCountdown(refreshInterval);

    const countdownTimer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, refreshInterval - elapsed);
      setCountdown(remaining);

      if (remaining === 0) {
        onRefresh?.();
      }
    }, 1000);

    const refreshTimer = setInterval(() => {
      onRefresh?.();
    }, refreshInterval);

    return () => {
      clearInterval(countdownTimer);
      clearInterval(refreshTimer);
    };
  }, [refreshInterval, autoRefreshEnabled, onRefresh]);

  // 格式化倒數計時
  const formatCountdown = (ms) => {
    const seconds = Math.ceil(ms / 1000);
    if (seconds >= 60) {
      const minutes = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${minutes}:${String(secs).padStart(2, '0')}`;
    }
    return `${seconds}s`;
  };

  // 格式化最後更新時間
  const formatLastUpdate = (date) => {
    if (!date) return '尚未更新';
    const d = new Date(date);
    return d.toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // 計算距離上次更新的時間
  const getTimeSinceUpdate = () => {
    if (!lastUpdate) return null;
    const diff = Date.now() - new Date(lastUpdate).getTime();
    if (diff < 60000) return `${Math.floor(diff / 1000)} 秒前`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分鐘前`;
    return `${Math.floor(diff / 3600000)} 小時前`;
  };

  const status = CONNECTION_STATUS[connectionStatus] || CONNECTION_STATUS.disconnected;
  const currentOption = REFRESH_OPTIONS.find(o => o.value === refreshInterval);

  return (
    <div className="relative">
      {/* 簡潔狀態列 */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors border border-slate-700"
      >
        {/* 連線狀態 */}
        <span className="text-sm">{status.icon}</span>

        {/* 最後更新 */}
        <span className="text-slate-400 text-xs">
          {lastUpdate ? formatLastUpdate(lastUpdate) : '--:--:--'}
        </span>

        {/* 倒數計時 */}
        {refreshInterval > 0 && autoRefreshEnabled && (
          <span className="text-blue-400 text-xs font-mono">
            ({formatCountdown(countdown)})
          </span>
        )}

        {/* 載入指示 */}
        {isLoading && (
          <span className="w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></span>
        )}

        {/* 展開/收合圖示 */}
        <span className="text-slate-500 text-xs">{isExpanded ? '▲' : '▼'}</span>
      </button>

      {/* 展開的控制面板 */}
      {isExpanded && (
        <div className="absolute top-full right-0 mt-2 w-72 bg-slate-800 rounded-xl border border-slate-700 shadow-xl z-50">
          <div className="p-4">
            <h4 className="text-white font-medium mb-3 flex items-center gap-2">
              <span>⚡</span>
              <span>即時數據設定</span>
            </h4>

            {/* 連線狀態 */}
            <div className="flex items-center justify-between mb-4 p-2 bg-slate-700/50 rounded-lg">
              <span className="text-slate-400 text-sm">連線狀態</span>
              <span className={`text-sm font-medium ${status.color}`}>
                {status.icon} {status.label}
              </span>
            </div>

            {/* 自動刷新開關 */}
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400 text-sm">自動刷新</span>
              <button
                onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  autoRefreshEnabled ? 'bg-blue-600' : 'bg-slate-600'
                }`}
              >
                <span
                  className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                    autoRefreshEnabled ? 'right-1' : 'left-1'
                  }`}
                />
              </button>
            </div>

            {/* 刷新頻率選擇 */}
            <div className="mb-4">
              <label className="text-slate-400 text-sm mb-2 block">刷新頻率</label>
              <div className="space-y-1">
                {REFRESH_OPTIONS.map(option => (
                  <button
                    key={option.value}
                    onClick={() => setRefreshInterval(option.value)}
                    disabled={!autoRefreshEnabled && option.value !== 0}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors ${
                      refreshInterval === option.value
                        ? 'bg-blue-600/20 border border-blue-500/50 text-blue-400'
                        : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                    } ${!autoRefreshEnabled && option.value !== 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <span className="font-medium">{option.label}</span>
                    <span className="text-xs text-slate-500">{option.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 上次更新資訊 */}
            <div className="p-2 bg-slate-700/30 rounded-lg mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">上次更新</span>
                <span className="text-white">{formatLastUpdate(lastUpdate)}</span>
              </div>
              {lastUpdate && (
                <div className="text-xs text-slate-500 text-right mt-1">
                  {getTimeSinceUpdate()}
                </div>
              )}
            </div>

            {/* 手動刷新按鈕 */}
            <button
              onClick={() => {
                onRefresh?.();
                setIsExpanded(false);
              }}
              disabled={isLoading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>更新中...</span>
                </>
              ) : (
                <>
                  <span>🔄</span>
                  <span>立即刷新</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* 點擊外部關閉 */}
      {isExpanded && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </div>
  );
};

// 簡化版狀態指示器（用於標題列）
export const DataStatusBadge = ({
  lastUpdate,
  isLoading = false,
  connectionStatus = 'connected',
}) => {
  const status = CONNECTION_STATUS[connectionStatus] || CONNECTION_STATUS.disconnected;

  const formatTime = (date) => {
    if (!date) return '--:--';
    return new Date(date).toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className={`w-2 h-2 rounded-full ${status.bg} ${isLoading ? 'animate-pulse' : ''}`}></span>
      <span className="text-slate-400">{formatTime(lastUpdate)}</span>
    </div>
  );
};

export default RealtimeManager;
