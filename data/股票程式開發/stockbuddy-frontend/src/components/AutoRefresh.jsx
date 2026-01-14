/**
 * AutoRefresh.jsx - 自動刷新設定組件
 * V10.23 新增
 *
 * 功能：
 * - 設定自動刷新間隔（30秒/1分鐘/5分鐘/關閉）
 * - 顯示上次更新時間
 * - 手動刷新按鈕
 * - 盤中/盤後狀態顯示
 */

import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../config';

const AutoRefresh = ({ onRefresh, className = '' }) => {
  const [interval, setInterval_] = useState(0); // 0 = 關閉
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [marketStatus, setMarketStatus] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  // 刷新間隔選項
  const intervalOptions = [
    { value: 0, label: '關閉' },
    { value: 30, label: '30秒' },
    { value: 60, label: '1分鐘' },
    { value: 300, label: '5分鐘' },
  ];

  // 取得市場狀態
  const fetchMarketStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/scheduler/status`);
      const data = await res.json();
      setMarketStatus(data);
    } catch (err) {
      console.error('Failed to fetch market status:', err);
    }
  }, []);

  // 執行刷新
  const doRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      if (onRefresh) {
        await onRefresh();
      }
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Refresh failed:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh]);

  // 設定自動刷新
  useEffect(() => {
    fetchMarketStatus();

    if (interval === 0) return;

    const timer = window.setInterval(() => {
      doRefresh();
    }, interval * 1000);

    return () => window.clearInterval(timer);
  }, [interval, doRefresh, fetchMarketStatus]);

  // 格式化時間
  const formatTime = (date) => {
    if (!date) return '--:--:--';
    return date.toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // 計算距離上次更新時間
  const getTimeAgo = () => {
    if (!lastUpdate) return '';
    const seconds = Math.floor((Date.now() - lastUpdate.getTime()) / 1000);
    if (seconds < 60) return `${seconds}秒前`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分鐘前`;
    return formatTime(lastUpdate);
  };

  return (
    <div className={`relative ${className}`}>
      {/* 主按鈕 */}
      <button
        onClick={() => setShowSettings(!showSettings)}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
          transition-all duration-200
          ${interval > 0
            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            : 'bg-slate-700/50 text-slate-400 border border-slate-600/50 hover:bg-slate-700'
          }
        `}
      >
        {isRefreshing ? (
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          <span className="text-base">{interval > 0 ? '🔄' : '⏸️'}</span>
        )}
        <span>
          {interval > 0 ? `${intervalOptions.find(o => o.value === interval)?.label}` : '自動刷新'}
        </span>
        {lastUpdate && (
          <span className="text-xs text-slate-500">({getTimeAgo()})</span>
        )}
      </button>

      {/* 設定面板 */}
      {showSettings && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
          {/* 標題 */}
          <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
            <span className="text-white font-medium">自動刷新設定</span>
            <button
              onClick={() => setShowSettings(false)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          {/* 市場狀態 */}
          {marketStatus && (
            <div className={`
              px-4 py-2 text-sm flex items-center gap-2
              ${marketStatus.is_trading_hours
                ? 'bg-red-500/10 text-red-400'
                : 'bg-slate-700/50 text-slate-400'
              }
            `}>
              <span className="text-lg">
                {marketStatus.is_trading_hours ? '📈' : '🌙'}
              </span>
              <span>
                {marketStatus.market_status}
                {marketStatus.is_trading_hours && ' - 建議開啟自動刷新'}
              </span>
            </div>
          )}

          {/* 刷新間隔選項 */}
          <div className="p-4 space-y-2">
            <div className="text-xs text-slate-500 mb-2">刷新間隔</div>
            {intervalOptions.map(option => (
              <button
                key={option.value}
                onClick={() => {
                  setInterval_(option.value);
                  if (option.value > 0) doRefresh();
                }}
                className={`
                  w-full px-3 py-2 rounded-lg text-sm text-left transition-colors
                  ${interval === option.value
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'bg-slate-700/30 text-slate-300 hover:bg-slate-700/50'
                  }
                `}
              >
                {option.label}
                {option.value === 0 && ' (手動)'}
                {option.value === 30 && marketStatus?.is_trading_hours && ' (推薦)'}
              </button>
            ))}
          </div>

          {/* 手動刷新按鈕 */}
          <div className="px-4 pb-4">
            <button
              onClick={() => {
                doRefresh();
                setShowSettings(false);
              }}
              disabled={isRefreshing}
              className="w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 transition-all"
            >
              {isRefreshing ? '刷新中...' : '立即刷新'}
            </button>
          </div>

          {/* 上次更新時間 */}
          {lastUpdate && (
            <div className="px-4 pb-3 text-xs text-slate-500 text-center">
              上次更新：{formatTime(lastUpdate)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AutoRefresh;
