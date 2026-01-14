/**
 * 綜合投資策略儀表板 V10.16
 *
 * 功能：
 * - 投資建議等級顯示 (Strong Buy/Buy/Hold/Reduce/Sell)
 * - 完整交易策略 (進場/加碼/止損/獲利)
 * - 多維度分析雷達圖
 * - 風險評估視覺化
 * - 投資論點與關鍵因素
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

// 投資評級顏色和文字
const RATING_CONFIG = {
  strong_buy: {
    color: 'bg-red-500',
    textColor: 'text-red-400',
    label: '強力買進',
    icon: '🚀',
    description: '多項指標強勢，建議積極布局'
  },
  buy: {
    color: 'bg-orange-500',
    textColor: 'text-orange-400',
    label: '推薦買入',
    icon: '📈',
    description: '整體表現良好，可考慮進場'
  },
  hold: {
    color: 'bg-yellow-500',
    textColor: 'text-yellow-400',
    label: '持有觀望',
    icon: '⏸️',
    description: '指標中性，等待明確訊號'
  },
  reduce: {
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    label: '建議減碼',
    icon: '📉',
    description: '部分指標轉弱，建議降低持股'
  },
  sell: {
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    label: '建議賣出',
    icon: '🛑',
    description: '多項指標弱勢，建議出場觀望'
  },
};

// 風險等級配置
const RISK_CONFIG = {
  low: { color: 'text-emerald-400', bg: 'bg-emerald-500/20', label: '低風險' },
  medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: '中等風險' },
  high: { color: 'text-orange-400', bg: 'bg-orange-500/20', label: '高風險' },
  very_high: { color: 'text-red-400', bg: 'bg-red-500/20', label: '極高風險' },
};

// 評級徽章組件
const RatingBadge = ({ rating, score }) => {
  const config = RATING_CONFIG[rating] || RATING_CONFIG.hold;

  return (
    <div className="flex items-center gap-3">
      <div className={`${config.color} text-white px-4 py-2 rounded-lg font-bold text-lg flex items-center gap-2`}>
        <span>{config.icon}</span>
        <span>{config.label}</span>
      </div>
      <div className="text-3xl font-bold text-white">
        {score}
        <span className="text-lg text-slate-400">/100</span>
      </div>
    </div>
  );
};

// 分數圓環組件
const ScoreRing = ({ score, label, size = 80 }) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  const getColor = (s) => {
    if (s >= 70) return '#ef4444'; // red
    if (s >= 50) return '#f59e0b'; // amber
    return '#22c55e'; // green
  };

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#334155"
          strokeWidth="6"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-xl font-bold text-white">{score}</span>
      </div>
      <span className="text-xs text-slate-400 mt-1">{label}</span>
    </div>
  );
};

// 多維度分數卡片
const DimensionScores = ({ scores }) => {
  const dimensions = [
    { key: 'technical', label: '技術面', icon: '📊' },
    { key: 'fundamental', label: '基本面', icon: '💰' },
    { key: 'chip', label: '籌碼面', icon: '🏦' },
    { key: 'industry', label: '產業面', icon: '🏭' },
  ];

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span>📐</span> 多維度評分
      </h4>
      <div className="grid grid-cols-4 gap-4">
        {dimensions.map(dim => (
          <div key={dim.key} className="relative flex flex-col items-center">
            <ScoreRing
              score={scores[`${dim.key}_score`] || 50}
              label={dim.label}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// 交易策略卡片
const TradingStrategyCard = ({ strategy, currentPrice }) => {
  if (!strategy) return null;

  return (
    <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-xl p-4 border border-blue-500/30">
      <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span>🎯</span> 交易策略
      </h4>

      <div className="space-y-4">
        {/* 進場策略 */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-sm text-slate-400 mb-1">進場策略</div>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-white font-medium">建議進場價: </span>
              <span className="text-red-400 font-bold">${strategy.entry_price}</span>
            </div>
            <div className="text-xs text-slate-500">
              區間: ${strategy.entry_range?.[0]} - ${strategy.entry_range?.[1]}
            </div>
          </div>
          <div className="text-xs text-slate-400 mt-1">{strategy.entry_timing}</div>
        </div>

        {/* 止損策略 */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-sm text-slate-400 mb-1">止損策略</div>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-white font-medium">止損價: </span>
              <span className="text-emerald-400 font-bold">${strategy.stop_loss_price}</span>
            </div>
            <div className="text-xs text-orange-400">
              -{strategy.stop_loss_percent}%
            </div>
          </div>
          {strategy.trailing_stop && (
            <div className="text-xs text-slate-400 mt-1">
              移動止損: {strategy.trailing_stop_percent}%
            </div>
          )}
        </div>

        {/* 目標價 */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-sm text-slate-400 mb-2">獲利目標</div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-xs text-slate-500">目標1</div>
              <div className="text-red-400 font-bold">${strategy.target_price_1}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">目標2</div>
              <div className="text-red-400 font-bold">${strategy.target_price_2}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">目標3</div>
              <div className="text-red-400 font-bold">${strategy.target_price_3}</div>
            </div>
          </div>
        </div>

        {/* 資金配置 */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="text-sm text-slate-400 mb-1">資金配置建議</div>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-white font-medium">建議倉位: </span>
              <span className="text-amber-400 font-bold">{strategy.suggested_position_percent}%</span>
            </div>
            <div className="text-xs text-slate-500">
              最大: {strategy.max_position_percent}%
            </div>
          </div>
          <div className="text-xs text-slate-400 mt-1">{strategy.position_sizing_reason}</div>
        </div>
      </div>
    </div>
  );
};

// 風險評估卡片
const RiskAssessmentCard = ({ risk }) => {
  if (!risk) return null;

  const riskConfig = RISK_CONFIG[risk.overall_risk] || RISK_CONFIG.medium;

  return (
    <div className="bg-gradient-to-br from-orange-600/20 to-red-600/20 rounded-xl p-4 border border-orange-500/30">
      <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span>🛡️</span> 風險評估
      </h4>

      {/* 整體風險 */}
      <div className={`${riskConfig.bg} rounded-lg p-3 mb-4`}>
        <div className="flex items-center justify-between">
          <span className={`${riskConfig.color} font-bold text-lg`}>
            {riskConfig.label}
          </span>
          <span className="text-white font-bold">
            {risk.risk_score}/100
          </span>
        </div>
      </div>

      {/* 各類風險 */}
      <div className="space-y-2">
        {[
          { key: 'market_risk', label: '市場風險' },
          { key: 'liquidity_risk', label: '流動性風險' },
          { key: 'volatility_risk', label: '波動風險' },
          { key: 'fundamental_risk', label: '基本面風險' },
        ].map(item => (
          <div key={item.key} className="flex items-center justify-between">
            <span className="text-slate-400 text-sm">{item.label}</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    risk[item.key] > 60 ? 'bg-red-500' :
                    risk[item.key] > 40 ? 'bg-yellow-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${risk[item.key]}%` }}
                />
              </div>
              <span className="text-white text-sm w-8">{risk[item.key]}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 風險因素 */}
      {risk.risk_factors && risk.risk_factors.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="text-sm text-slate-400 mb-2">風險因素</div>
          <ul className="space-y-1">
            {risk.risk_factors.map((factor, i) => (
              <li key={i} className="text-xs text-orange-400 flex items-start gap-1">
                <span>⚠️</span>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 緩解策略 */}
      {risk.mitigation_strategies && risk.mitigation_strategies.length > 0 && (
        <div className="mt-3">
          <div className="text-sm text-slate-400 mb-2">風險緩解</div>
          <ul className="space-y-1">
            {risk.mitigation_strategies.map((strategy, i) => (
              <li key={i} className="text-xs text-emerald-400 flex items-start gap-1">
                <span>✅</span>
                <span>{strategy}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// 投資論點卡片
const InvestmentThesisCard = ({ thesis, catalysts, risks }) => {
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span>💡</span> 投資論點
      </h4>

      <div className="text-slate-300 mb-4">{thesis}</div>

      <div className="grid grid-cols-2 gap-4">
        {/* 催化劑 */}
        <div>
          <div className="text-sm text-emerald-400 font-medium mb-2">關鍵催化劑</div>
          <ul className="space-y-1">
            {catalysts?.map((item, i) => (
              <li key={i} className="text-xs text-slate-400 flex items-start gap-1">
                <span className="text-emerald-400">▲</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 風險 */}
        <div>
          <div className="text-sm text-red-400 font-medium mb-2">關鍵風險</div>
          <ul className="space-y-1">
            {risks?.map((item, i) => (
              <li key={i} className="text-xs text-slate-400 flex items-start gap-1">
                <span className="text-red-400">▼</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

// 主組件
const StrategyDashboard = ({ stockId, stockName }) => {
  const [strategy, setStrategy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStrategy = async () => {
      if (!stockId) return;

      setLoading(true);
      setError(null);

      try {
        const res = await fetch(`${API_BASE}/api/stocks/strategy/${stockId}`);
        if (!res.ok) throw new Error('取得策略失敗');

        const data = await res.json();
        if (data.success) {
          setStrategy(data.strategy);
        } else {
          throw new Error(data.error || '未知錯誤');
        }
      } catch (err) {
        console.error('策略分析失敗:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStrategy();
  }, [stockId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-slate-400">產生投資策略中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>無策略資料</p>
      </div>
    );
  }

  const ratingConfig = RATING_CONFIG[strategy.rating] || RATING_CONFIG.hold;

  return (
    <div className="space-y-4">
      {/* 標題與評級 */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            {strategy.stock_name || stockId} 綜合投資策略
          </h3>
          <div className="text-xs text-slate-500">
            {new Date(strategy.analysis_time).toLocaleString()}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <RatingBadge rating={strategy.rating} score={strategy.rating_score} />
          <div className="text-right">
            <div className="text-3xl font-bold text-white">
              ${strategy.current_price}
            </div>
            <div className="text-sm text-slate-400">
              {strategy.investment_horizon}
            </div>
          </div>
        </div>

        <div className="mt-3 text-slate-400 text-sm">
          {strategy.rating_summary}
        </div>

        {/* 評級理由 */}
        {strategy.rating_reasons && strategy.rating_reasons.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {strategy.rating_reasons.map((reason, i) => (
              <span
                key={i}
                className={`px-2 py-1 rounded text-xs ${ratingConfig.textColor} bg-slate-700/50`}
              >
                {reason}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 多維度分數 */}
      <DimensionScores scores={strategy} />

      {/* 交易策略與風險評估 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TradingStrategyCard
          strategy={strategy.trading_strategy}
          currentPrice={strategy.current_price}
        />
        <RiskAssessmentCard risk={strategy.risk_assessment} />
      </div>

      {/* 投資論點 */}
      <InvestmentThesisCard
        thesis={strategy.investment_thesis}
        catalysts={strategy.key_catalysts}
        risks={strategy.key_risks}
      />

      {/* 適合投資者 */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-sm">建議投資期限:</span>
            <span className="text-white font-medium">{strategy.investment_horizon}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-sm">適合投資者:</span>
            <span className="text-white font-medium">{strategy.suitable_investor}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyDashboard;
