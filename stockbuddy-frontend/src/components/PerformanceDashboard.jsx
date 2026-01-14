/**
 * 績效分析儀表板 V10.15
 * 參考券商 APP 和 FinLab 交易練習生
 *
 * 功能：
 * - 獲利能力指標（年化報酬、Alpha、Beta）
 * - 風險報酬比（夏普、Sortino、Calmar）
 * - 抗風險能力（最大回撤、VaR、CVaR）
 * - 月報酬熱力圖
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

// 獲利能力卡片
const ProfitabilityCard = ({ data }) => {
  if (!data) return null;

  const summary = data.summary || {};
  const riskAdj = data.risk_adjusted || {};

  return (
    <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-xl p-4 border border-blue-500/30">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">💰</span> 獲利能力
      </h3>

      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-slate-400 text-xs mb-1">總報酬</div>
          <div className={`text-2xl font-bold ${summary.total_return_pct >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {summary.total_return_pct >= 0 ? '+' : ''}{summary.total_return_pct?.toFixed(1)}%
          </div>
        </div>

        <div className="text-center">
          <div className="text-slate-400 text-xs mb-1">年化報酬</div>
          <div className={`text-2xl font-bold ${summary.annualized_return_pct >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {summary.annualized_return_pct >= 0 ? '+' : ''}{summary.annualized_return_pct?.toFixed(1)}%
          </div>
        </div>

        <div className="text-center">
          <div className="text-slate-400 text-xs mb-1">交易日數</div>
          <div className="text-2xl font-bold text-white">
            {summary.trading_days}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-700/50">
        <div className="text-center">
          <div className="text-slate-400 text-xs mb-1">Alpha</div>
          <div className={`text-lg font-bold ${riskAdj.alpha >= 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            {riskAdj.alpha >= 0 ? '+' : ''}{riskAdj.alpha?.toFixed(2)}%
          </div>
          <div className="text-slate-500 text-xs">超額報酬</div>
        </div>

        <div className="text-center">
          <div className="text-slate-400 text-xs mb-1">Beta</div>
          <div className={`text-lg font-bold ${riskAdj.beta > 1 ? 'text-orange-400' : 'text-cyan-400'}`}>
            {riskAdj.beta?.toFixed(2)}
          </div>
          <div className="text-slate-500 text-xs">{riskAdj.beta > 1 ? '高波動' : '低波動'}</div>
        </div>
      </div>
    </div>
  );
};

// 風險報酬比卡片
const RiskRewardCard = ({ data }) => {
  if (!data) return null;

  const riskAdj = data.risk_adjusted || {};

  // 評級函數
  const getRating = (value, type) => {
    switch (type) {
      case 'sharpe':
        if (value >= 2) return { text: '優秀', color: 'text-emerald-400' };
        if (value >= 1) return { text: '良好', color: 'text-blue-400' };
        if (value >= 0) return { text: '一般', color: 'text-yellow-400' };
        return { text: '差', color: 'text-red-400' };
      case 'sortino':
        if (value >= 2) return { text: '優秀', color: 'text-emerald-400' };
        if (value >= 1) return { text: '良好', color: 'text-blue-400' };
        return { text: '一般', color: 'text-yellow-400' };
      case 'calmar':
        if (value >= 1) return { text: '優秀', color: 'text-emerald-400' };
        if (value >= 0.5) return { text: '良好', color: 'text-blue-400' };
        return { text: '待改善', color: 'text-yellow-400' };
      default:
        return { text: '', color: '' };
    }
  };

  const sharpeRating = getRating(riskAdj.sharpe_ratio, 'sharpe');
  const sortinoRating = getRating(riskAdj.sortino_ratio, 'sortino');
  const calmarRating = getRating(riskAdj.calmar_ratio, 'calmar');

  return (
    <div className="bg-gradient-to-br from-emerald-600/20 to-teal-600/20 rounded-xl p-4 border border-emerald-500/30">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">📊</span> 風險報酬比
      </h3>

      <div className="space-y-4">
        {/* 夏普比率 */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-medium">夏普比率</div>
            <div className="text-slate-500 text-xs">每單位風險報酬</div>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-white">{riskAdj.sharpe_ratio?.toFixed(2)}</div>
            <div className={`text-xs ${sharpeRating.color}`}>{sharpeRating.text}</div>
          </div>
        </div>

        {/* Sortino */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-medium">Sortino Ratio</div>
            <div className="text-slate-500 text-xs">下行風險調整報酬</div>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-white">{riskAdj.sortino_ratio?.toFixed(2)}</div>
            <div className={`text-xs ${sortinoRating.color}`}>{sortinoRating.text}</div>
          </div>
        </div>

        {/* Calmar */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-medium">Calmar Ratio</div>
            <div className="text-slate-500 text-xs">報酬/最大回撤</div>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-white">{riskAdj.calmar_ratio?.toFixed(2)}</div>
            <div className={`text-xs ${calmarRating.color}`}>{calmarRating.text}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 抗風險能力卡片
const RiskMetricsCard = ({ data }) => {
  if (!data) return null;

  const risk = data.risk_metrics || {};

  return (
    <div className="bg-gradient-to-br from-orange-600/20 to-red-600/20 rounded-xl p-4 border border-orange-500/30">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">🛡️</span> 抗風險能力
      </h3>

      <div className="space-y-4">
        {/* 最大回撤 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-white font-medium">最大回撤</span>
            <span className="text-red-400 font-bold">-{risk.max_drawdown_pct?.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full"
              style={{ width: `${Math.min(100, risk.max_drawdown_pct || 0)}%` }}
            />
          </div>
        </div>

        {/* VaR */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-medium">VaR (95%)</div>
            <div className="text-slate-500 text-xs">單日最大損失風險</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-orange-400">-{risk.var_95?.toFixed(2)}%</div>
          </div>
        </div>

        {/* CVaR */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-medium">CVaR (95%)</div>
            <div className="text-slate-500 text-xs">極端損失預期值</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-red-400">-{risk.cvar_95?.toFixed(2)}%</div>
          </div>
        </div>

        {/* 波動率 */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-white font-medium">年化波動率</div>
            <div className="text-slate-500 text-xs">價格變動幅度</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-white">{risk.volatility_annual?.toFixed(1)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 月報酬熱力圖
const MonthlyHeatmap = ({ data }) => {
  if (!data || !data.monthly_returns) return null;

  const monthlyReturns = data.monthly_returns;
  const years = Object.keys(monthlyReturns).sort().reverse();
  const months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
  const monthLabels = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];

  // 獲取熱力圖顏色
  const getHeatmapColor = (value) => {
    if (value === null || value === undefined) return 'bg-slate-800';
    if (value >= 10) return 'bg-red-500';
    if (value >= 5) return 'bg-red-400';
    if (value >= 2) return 'bg-red-300/70';
    if (value >= 0) return 'bg-red-200/50';
    if (value >= -2) return 'bg-emerald-200/50';
    if (value >= -5) return 'bg-emerald-300/70';
    if (value >= -10) return 'bg-emerald-400';
    return 'bg-emerald-500';
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">🗓️</span> 月報酬熱力圖
      </h3>

      {/* 月份標籤 */}
      <div className="flex mb-2">
        <div className="w-16"></div>
        {monthLabels.map((m, i) => (
          <div key={i} className="flex-1 text-center text-slate-400 text-xs">
            {m.slice(0, 2)}
          </div>
        ))}
      </div>

      {/* 熱力圖格子 */}
      <div className="space-y-1">
        {years.map(year => (
          <div key={year} className="flex items-center">
            <div className="w-16 text-slate-400 text-sm font-medium">{year}</div>
            <div className="flex-1 flex gap-1">
              {months.map(month => {
                const value = monthlyReturns[year]?.[month];
                return (
                  <div
                    key={month}
                    className={`flex-1 aspect-square rounded flex items-center justify-center text-xs font-medium ${getHeatmapColor(value)}`}
                    title={value !== undefined ? `${year}/${month}: ${value?.toFixed(1)}%` : '無資料'}
                  >
                    {value !== undefined ? (
                      <span className={value >= 0 ? 'text-red-900' : 'text-emerald-900'}>
                        {value.toFixed(0)}
                      </span>
                    ) : '-'}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* 圖例 */}
      <div className="flex justify-center gap-2 mt-4">
        <span className="text-slate-500 text-xs">虧損</span>
        <div className="flex gap-0.5">
          <div className="w-4 h-4 bg-emerald-500 rounded"></div>
          <div className="w-4 h-4 bg-emerald-400 rounded"></div>
          <div className="w-4 h-4 bg-emerald-300/70 rounded"></div>
          <div className="w-4 h-4 bg-emerald-200/50 rounded"></div>
          <div className="w-4 h-4 bg-red-200/50 rounded"></div>
          <div className="w-4 h-4 bg-red-300/70 rounded"></div>
          <div className="w-4 h-4 bg-red-400 rounded"></div>
          <div className="w-4 h-4 bg-red-500 rounded"></div>
        </div>
        <span className="text-slate-500 text-xs">獲利</span>
      </div>

      {/* 統計摘要 */}
      {data.summary && (
        <div className="flex justify-center gap-6 mt-4 pt-4 border-t border-slate-700">
          <div className="text-center">
            <div className="text-slate-400 text-xs">月平均報酬</div>
            <div className={`font-bold ${data.summary.avg_monthly_return >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {data.summary.avg_monthly_return >= 0 ? '+' : ''}{data.summary.avg_monthly_return?.toFixed(2)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-400 text-xs">月勝率</div>
            <div className="text-white font-bold">{data.summary.monthly_win_rate?.toFixed(1)}%</div>
          </div>
          <div className="text-center">
            <div className="text-slate-400 text-xs">統計月數</div>
            <div className="text-white font-bold">{data.summary.total_months}</div>
          </div>
        </div>
      )}
    </div>
  );
};

// 主組件
const PerformanceDashboard = ({ stockId, stockName }) => {
  const [performance, setPerformance] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState(12); // 分析期間（月）

  useEffect(() => {
    const fetchData = async () => {
      if (!stockId) return;

      setLoading(true);
      setError(null);

      try {
        // 並行請求
        const [perfRes, heatmapRes] = await Promise.all([
          fetch(`${API_BASE}/api/stocks/performance/${stockId}?months=${period}`),
          fetch(`${API_BASE}/api/stocks/performance/${stockId}/monthly-heatmap?years=3`),
        ]);

        if (perfRes.ok) {
          const perfData = await perfRes.json();
          setPerformance(perfData.performance);
        }

        if (heatmapRes.ok) {
          const hmData = await heatmapRes.json();
          setHeatmapData(hmData);
        }
      } catch (err) {
        console.error('績效分析載入失敗:', err);
        setError('無法載入績效分析資料');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [stockId, period]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-slate-400">載入績效分析中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>{error}</p>
        <button
          onClick={() => setPeriod(p => p)} // 重新觸發
          className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
        >
          重試
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 標題與期間選擇 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">
          {stockName || stockId} 績效分析
        </h2>
        <div className="flex gap-2">
          {[6, 12, 24, 36].map(m => (
            <button
              key={m}
              onClick={() => setPeriod(m)}
              className={`px-3 py-1 text-sm rounded ${
                period === m
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
              }`}
            >
              {m}月
            </button>
          ))}
        </div>
      </div>

      {/* 績效指標卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ProfitabilityCard data={performance} />
        <RiskRewardCard data={performance} />
        <RiskMetricsCard data={performance} />
      </div>

      {/* 月報酬熱力圖 */}
      <MonthlyHeatmap data={heatmapData} />
    </div>
  );
};

export default PerformanceDashboard;
