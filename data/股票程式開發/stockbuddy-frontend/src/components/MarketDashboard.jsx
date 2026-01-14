/**
 * MarketDashboard.jsx - 市場總覽儀表板
 * V10.27 新增
 *
 * 功能：
 * - 台股/美股市場狀態
 * - 主要指數即時報價
 * - 市場情緒指標
 * - 漲跌幅排行
 * - 產業表現熱力圖
 * - 成交量分析
 */

import React, { useState, useEffect, useCallback } from 'react';
import { API_STOCKS_BASE } from '../config';

const API_BASE = API_STOCKS_BASE;

// 台股產業分類
const TW_SECTORS = {
  semiconductor: { name: '半導體', stocks: ['2330', '2454', '2303', '3711'] },
  finance: { name: '金融', stocks: ['2881', '2882', '2891', '2886'] },
  electronics: { name: '電子', stocks: ['2317', '2382', '2357', '3231'] },
  traditional: { name: '傳產', stocks: ['1301', '1303', '2002', '1216'] },
  telecom: { name: '電信', stocks: ['2412', '3045', '4904'] },
};

const MarketDashboard = ({ onSelectStock }) => {
  // 狀態
  const [twMarketStatus, setTwMarketStatus] = useState(null);
  const [usMarketStatus, setUsMarketStatus] = useState(null);
  const [twIndex, setTwIndex] = useState(null);
  const [usIndices, setUsIndices] = useState({});
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [volumeHot, setVolumeHot] = useState([]);
  const [sectorPerformance, setSectorPerformance] = useState({});
  const [marketSentiment, setMarketSentiment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  // 計算台股市場狀態
  const getTwMarketStatus = useCallback(() => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const day = now.getDay();
    const time = hours * 100 + minutes;

    // 週末
    if (day === 0 || day === 6) {
      return { isOpen: false, status: 'weekend', message: '週末休市' };
    }

    // 交易時間 9:00 - 13:30
    if (time >= 900 && time <= 1330) {
      return { isOpen: true, status: 'open', message: '盤中' };
    } else if (time < 900) {
      return { isOpen: false, status: 'pre', message: '盤前' };
    } else {
      return { isOpen: false, status: 'closed', message: '已收盤' };
    }
  }, []);

  // 取得美股市場狀態
  const fetchUsMarketStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/us/market-status`);
      const data = await res.json();
      setUsMarketStatus(data);
    } catch (e) {
      console.error('Error fetching US market status:', e);
    }
  }, []);

  // 取得台股指數
  const fetchTwIndex = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/market-index`);
      if (res.ok) {
        const data = await res.json();
        setTwIndex(data);
      }
    } catch (e) {
      console.error('Error fetching TW index:', e);
    }
  }, []);

  // 取得美股指數
  const fetchUsIndices = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/us/indices`);
      const data = await res.json();
      if (data.success) {
        setUsIndices(data.data);
      }
    } catch (e) {
      console.error('Error fetching US indices:', e);
    }
  }, []);

  // 取得漲跌排行
  const fetchTopMovers = useCallback(async () => {
    try {
      const [gainersRes, losersRes, volumeRes] = await Promise.all([
        fetch(`${API_BASE}/top-gainers?limit=5`),
        fetch(`${API_BASE}/top-losers?limit=5`),
        fetch(`${API_BASE}/volume-hot?limit=5`),
      ]);

      if (gainersRes.ok) {
        const data = await gainersRes.json();
        setTopGainers(Array.isArray(data) ? data : []);
      }

      if (losersRes.ok) {
        const data = await losersRes.json();
        setTopLosers(Array.isArray(data) ? data : []);
      }

      if (volumeRes.ok) {
        const data = await volumeRes.json();
        setVolumeHot(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      console.error('Error fetching top movers:', e);
    }
  }, []);

  // 計算市場情緒
  const calculateSentiment = useCallback(() => {
    const gainersCount = topGainers.length;
    const losersCount = topLosers.length;

    // 計算平均漲跌幅
    const avgGain = topGainers.reduce((sum, s) => sum + (s.change_percent || 0), 0) / (gainersCount || 1);
    const avgLoss = topLosers.reduce((sum, s) => sum + Math.abs(s.change_percent || 0), 0) / (losersCount || 1);

    // 情緒分數 0-100
    let score = 50;
    if (avgGain > avgLoss) {
      score = Math.min(80, 50 + avgGain * 5);
    } else {
      score = Math.max(20, 50 - avgLoss * 5);
    }

    let label, color;
    if (score >= 70) {
      label = '極度樂觀';
      color = 'text-emerald-400';
    } else if (score >= 55) {
      label = '偏多';
      color = 'text-green-400';
    } else if (score >= 45) {
      label = '中性';
      color = 'text-yellow-400';
    } else if (score >= 30) {
      label = '偏空';
      color = 'text-orange-400';
    } else {
      label = '極度悲觀';
      color = 'text-red-400';
    }

    setMarketSentiment({ score: Math.round(score), label, color });
  }, [topGainers, topLosers]);

  // 初始載入
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setTwMarketStatus(getTwMarketStatus());
      await Promise.all([
        fetchUsMarketStatus(),
        fetchTwIndex(),
        fetchUsIndices(),
        fetchTopMovers(),
      ]);
      setLastUpdate(new Date());
      setLoading(false);
    };

    loadData();

    // 定時更新
    const interval = setInterval(loadData, 60000); // 1分鐘更新
    return () => clearInterval(interval);
  }, [getTwMarketStatus, fetchUsMarketStatus, fetchTwIndex, fetchUsIndices, fetchTopMovers]);

  // 計算情緒
  useEffect(() => {
    calculateSentiment();
  }, [calculateSentiment]);

  // 格式化數字
  const formatNumber = (num) => {
    if (!num) return '-';
    return num.toLocaleString();
  };

  // 渲染市場狀態卡片
  const renderMarketStatus = (market, status, label) => (
    <div className="bg-slate-700/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-sm">{label}</span>
        <span className={`w-2 h-2 rounded-full ${status?.isOpen ? 'bg-emerald-400' : 'bg-slate-500'}`} />
      </div>
      <div className={`text-lg font-medium ${status?.isOpen ? 'text-emerald-400' : 'text-slate-400'}`}>
        {status?.message || '載入中...'}
      </div>
    </div>
  );

  // 渲染指數卡片
  const renderIndexCard = (name, value, change, changePercent) => {
    const isUp = (change || 0) >= 0;
    const hasData = value !== null && value !== undefined;

    return (
      <div className="bg-slate-700/50 rounded-lg p-3">
        <div className="text-slate-400 text-xs mb-1">{name}</div>
        {hasData ? (
          <>
            <div className="text-white font-bold text-lg">{formatNumber(value)}</div>
            <div className={`text-sm ${isUp ? 'text-red-400' : 'text-emerald-400'}`}>
              {isUp ? '▲' : '▼'} {changePercent?.toFixed(2) || 0}%
            </div>
          </>
        ) : (
          <div className="text-slate-500 text-sm">載入中...</div>
        )}
      </div>
    );
  };

  // 渲染股票行
  const renderStockRow = (stock, showVolume = false) => {
    const isUp = (stock.change_percent || 0) >= 0;
    return (
      <div
        key={stock.stock_id}
        onClick={() => onSelectStock?.(stock.stock_id)}
        className="flex items-center justify-between py-2 px-3 hover:bg-slate-700/50 rounded cursor-pointer transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-white font-medium w-16">{stock.stock_id}</span>
          <span className="text-slate-400 text-sm truncate w-20">{stock.name}</span>
        </div>
        <div className="flex items-center gap-4">
          {showVolume && (
            <span className="text-slate-500 text-xs">
              {(stock.volume / 1000).toFixed(0)}K
            </span>
          )}
          <span className="text-white w-16 text-right">${stock.close?.toFixed(2)}</span>
          <span className={`w-20 text-right font-medium ${isUp ? 'text-red-400' : 'text-emerald-400'}`}>
            {isUp ? '+' : ''}{stock.change_percent?.toFixed(2)}%
          </span>
        </div>
      </div>
    );
  };

  // 渲染情緒指標
  const renderSentimentGauge = () => {
    if (!marketSentiment) return null;

    return (
      <div className="bg-slate-700/50 rounded-lg p-4">
        <div className="text-slate-400 text-sm mb-3">市場情緒指標</div>
        <div className="flex items-center gap-4">
          {/* 儀表盤 */}
          <div className="relative w-20 h-20">
            <svg viewBox="0 0 100 50" className="w-full">
              {/* 背景弧 */}
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke="#334155"
                strokeWidth="8"
              />
              {/* 前景弧 */}
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke={marketSentiment.score >= 50 ? '#22c55e' : '#ef4444'}
                strokeWidth="8"
                strokeDasharray={`${(marketSentiment.score / 100) * 125.6} 125.6`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center pt-4">
              <span className="text-white font-bold text-xl">{marketSentiment.score}</span>
            </div>
          </div>
          <div>
            <div className={`text-lg font-bold ${marketSentiment.color}`}>
              {marketSentiment.label}
            </div>
            <div className="text-slate-500 text-xs mt-1">
              基於市場漲跌分布計算
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading && !twIndex) {
    return (
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <div className="flex items-center justify-center py-12">
          <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="ml-4 text-slate-400">載入市場資料中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 標題列 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📊</span> 市場總覽
        </h2>
        {lastUpdate && (
          <span className="text-slate-500 text-sm">
            更新於 {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* 市場狀態 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {renderMarketStatus('tw', twMarketStatus, '🇹🇼 台股')}
        {renderMarketStatus('us', usMarketStatus, '🇺🇸 美股')}
        {renderSentimentGauge()}
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-2">今日重點</div>
          <div className="space-y-1 text-sm">
            <div className="text-emerald-400">漲幅前5 平均 +{
              (topGainers.reduce((s, g) => s + (g.change_percent || 0), 0) / (topGainers.length || 1)).toFixed(1)
            }%</div>
            <div className="text-red-400">跌幅前5 平均 {
              (topLosers.reduce((s, g) => s + (g.change_percent || 0), 0) / (topLosers.length || 1)).toFixed(1)
            }%</div>
          </div>
        </div>
      </div>

      {/* 指數一覽 */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>📈</span> 主要指數
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {/* 台股指數 */}
          {renderIndexCard(
            '🇹🇼 加權指數',
            twIndex?.value,
            twIndex?.change,
            twIndex?.change_percent
          )}
          {/* 美股指數 */}
          {Object.entries(usIndices).slice(0, 5).map(([symbol, data]) => (
            <div key={symbol}>
              {renderIndexCard(
                data.name,
                data.value,
                data.change,
                data.change_percent
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 漲跌排行 */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* 漲幅排行 */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>🚀</span> 漲幅排行
          </h3>
          <div className="space-y-1">
            {topGainers.slice(0, 5).map((stock) => renderStockRow(stock))}
            {topGainers.length === 0 && (
              <div className="text-slate-500 text-center py-4">暫無資料</div>
            )}
          </div>
        </div>

        {/* 跌幅排行 */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>📉</span> 跌幅排行
          </h3>
          <div className="space-y-1">
            {topLosers.slice(0, 5).map((stock) => renderStockRow(stock))}
            {topLosers.length === 0 && (
              <div className="text-slate-500 text-center py-4">暫無資料</div>
            )}
          </div>
        </div>

        {/* 成交量排行 */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>📊</span> 成交熱門
          </h3>
          <div className="space-y-1">
            {volumeHot.slice(0, 5).map((stock) => renderStockRow(stock, true))}
            {volumeHot.length === 0 && (
              <div className="text-slate-500 text-center py-4">暫無資料</div>
            )}
          </div>
        </div>
      </div>

      {/* 快速操作 */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <div className="text-white font-medium">今日市場摘要</div>
              <div className="text-slate-400 text-sm">
                {marketSentiment?.label === '極度樂觀' || marketSentiment?.label === '偏多'
                  ? '市場氣氛偏多，可留意強勢股突破機會'
                  : marketSentiment?.label === '中性'
                  ? '市場處於觀望階段，建議等待明確訊號'
                  : '市場氣氛偏弱，注意風險控管'}
              </div>
            </div>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
          >
            刷新資料
          </button>
        </div>
      </div>
    </div>
  );
};

export default MarketDashboard;
