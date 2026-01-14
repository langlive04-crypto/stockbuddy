/**
 * 資料狀態指示器 V10.15
 * 顯示資料更新時間與過期警告
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { formatDateDisplay } from '../utils/dateUtils';  // V10.35.4

const DataStatusIndicator = ({ onRefresh }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/stocks/data-status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('無法取得資料狀態:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // 每 5 分鐘檢查一次
    const interval = setInterval(fetchStatus, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const handleClearCache = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/stocks/clear-cache`, {
        method: 'POST'
      });
      if (response.ok) {
        fetchStatus();
        if (onRefresh) onRefresh();
      }
    } catch (err) {
      console.error('清除快取失敗:', err);
    }
  };

  if (loading) {
    return null;
  }

  if (!status) {
    return null;
  }

  // 資料過期警告
  if (status.is_stale) {
    return (
      <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">⚠️</span>
          <div>
            <div className="text-amber-400 font-medium">資料已過期</div>
            <div className="text-amber-200/70 text-sm">
              資料日期: {formatDateDisplay(status.data_date) || '未知'} | 今日: {formatDateDisplay(status.current_date)}
            </div>
          </div>
        </div>
        <button
          onClick={handleClearCache}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-medium transition-colors"
        >
          更新資料
        </button>
      </div>
    );
  }

  // 正常狀態（小型顯示）
  return (
    <div className="flex items-center gap-2 text-sm text-slate-400">
      <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
      <span>資料更新於 {status.data_date}</span>
      {status.is_trading_hours && (
        <span className="text-amber-400 text-xs">(交易時段)</span>
      )}
    </div>
  );
};

// 精簡版本（只顯示圖示）
export const DataStatusBadge = () => {
  const [isStale, setIsStale] = useState(false);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/stocks/data-status`);
        if (response.ok) {
          const data = await response.json();
          setIsStale(data.is_stale);
        }
      } catch (err) {
        // 忽略錯誤
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (!isStale) return null;

  return (
    <span className="relative">
      <span className="absolute -top-1 -right-1 w-3 h-3 bg-amber-500 rounded-full animate-pulse"></span>
      <span className="text-amber-400">⏰</span>
    </span>
  );
};

export default DataStatusIndicator;
