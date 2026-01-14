/**
 * UIComponents.jsx - 共用 UI 組件
 * V10.26 重構：從 App.jsx 提取
 * V10.35 更新：主題感知支援
 *
 * 包含：
 * - ScoreRing: 分數環形圖
 * - ScoreBar: 分數進度條
 * - MiniKLineChart: 迷你K線圖
 * - TermTooltip: 專有名詞解釋提示
 * - Loading: 載入動畫
 */

import React, { memo } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../contexts/ThemeContext';

// ===== 分數環形圖 =====
export const ScoreRing = memo(({ score, size = 60 }) => {
  const { isDark } = useTheme();
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = ((score || 0) / 100) * circumference;

  const getColor = (s) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#eab308';
    if (s >= 40) return '#f97316';
    return '#ef4444';
  };

  const trackColor = isDark ? '#334155' : '#e2e8f0';
  const textColor = isDark ? 'text-white' : 'text-gray-900';

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth="4"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`${textColor} font-bold`} style={{ fontSize: size * 0.28 }}>
          {score || '-'}
        </span>
      </div>
    </div>
  );
});

// ===== 迷你 K 線圖 =====
export const MiniKLineChart = memo(({ data, width = 100, height = 40 }) => {
  if (!data || data.length < 2) return null;

  const prices = data.map((d) => d.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice || 1;

  const points = prices
    .map((price, i) => {
      const x = (i / (prices.length - 1)) * width;
      const y = height - ((price - minPrice) / range) * height;
      return `${x},${y}`;
    })
    .join(' ');

  const isUp = prices[prices.length - 1] >= prices[0];

  return (
    <svg width={width} height={height} className="opacity-60">
      <polyline
        points={points}
        fill="none"
        stroke={isUp ? '#ef4444' : '#22c55e'}
        strokeWidth="1.5"
      />
    </svg>
  );
});

// ===== 專有名詞解釋 Tooltip =====
export const TermTooltip = ({ term, children }) => {
  const { isDark } = useTheme();
  const [showTooltip, setShowTooltip] = React.useState(false);

  const termExplanations = {
    '技術面': '根據股價走勢和成交量分析，判斷買賣時機',
    '基本面': '分析公司財務狀況，評估股票是否值得投資',
    '籌碼面': '觀察大戶和法人的買賣動向',
    '新聞面': '從近期新聞評估市場對股票的看法',
    'P/E': '本益比：股價除以每股盈餘，數字越低表示股票越便宜',
    '殖利率': '股息報酬率：每年能拿到的股息佔股價的比例',
    '止損': '設定一個價格，跌到這個價位就賣出，避免虧更多',
    '目標價': '預期股價可能漲到的價格',
    '產業熱度': '這個產業目前是否受到市場關注',
    // 技術指標解釋
    'RSI': '相對強弱指標：超過70為超買（可能下跌），低於30為超賣（可能上漲）',
    'MACD': '趨勢指標：金叉表示買進訊號，死叉表示賣出訊號',
    'KD': '隨機指標：K>80超買可能下跌，K<20超賣可能上漲，黃金交叉為買進訊號',
    '威廉指標': '動量指標：大於-20為超買，小於-80為超賣',
    '風險評估': '根據股價波動性評估投資風險，波動越大風險越高',
    '均線': '過去N天的平均價格，股價在均線上方表示趨勢偏多',
    '成交量': '股票交易的數量，放量上漲通常代表趨勢確立',
  };

  const explanation = termExplanations[term];
  if (!explanation) return children;

  const tooltipBg = isDark ? 'bg-slate-900 border-slate-600' : 'bg-white border-gray-200 shadow-lg';
  const tooltipText = isDark ? 'text-slate-300' : 'text-gray-600';
  const tooltipTitle = isDark ? 'text-white' : 'text-gray-900';
  const tooltipMuted = isDark ? 'text-slate-400' : 'text-gray-500';
  const arrowColor = isDark ? 'border-t-slate-900' : 'border-t-white';

  return (
    <span
      className="relative cursor-help"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className={`absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 ${tooltipBg} rounded-lg text-xs ${tooltipText} whitespace-nowrap z-50`}>
          <div className={`${tooltipTitle} font-medium mb-1`}>{term}</div>
          <div className={tooltipMuted}>{explanation}</div>
          <div className={`absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent ${arrowColor}`}></div>
        </div>
      )}
    </span>
  );
};

// ===== 評分進度條 =====
export const ScoreBar = memo(({ label, score, maxScore = 100, color = 'blue' }) => {
  const { isDark } = useTheme();
  const percentage = Math.min((score / maxScore) * 100, 100);
  const colorMap = {
    red: 'bg-red-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    green: 'bg-emerald-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  };

  const labelColor = isDark ? 'text-slate-400' : 'text-gray-500';
  const scoreColor = isDark ? 'text-white' : 'text-gray-900';
  const trackColor = isDark ? 'bg-slate-700' : 'bg-gray-200';

  return (
    <div className="mb-2">
      <div className="flex justify-between items-center mb-1">
        <span className={`${labelColor} text-sm`}>{label}</span>
        <span className={`${scoreColor} font-medium text-sm`}>{score}</span>
      </div>
      <div className={`h-2 ${trackColor} rounded-full overflow-hidden`}>
        <div
          className={`h-full ${colorMap[color] || colorMap.blue} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
});

// ===== 載入動畫 =====
export const Loading = memo(() => {
  const { isDark } = useTheme();
  const textColor = isDark ? 'text-slate-400' : 'text-gray-500';
  const mutedColor = isDark ? 'text-slate-500' : 'text-gray-400';

  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      <p className={`mt-4 ${textColor}`}>AI 正在分析全市場股票...</p>
      <p className={`${mutedColor} text-sm`}>約需 5-10 秒</p>
    </div>
  );
});

// ===== 價格變動顯示 =====
export const PriceChange = memo(({ change, changePercent }) => {
  const isPositive = change >= 0;
  const bgColor = isPositive ? 'bg-red-500/10' : 'bg-emerald-500/10';
  const textColor = isPositive ? 'text-red-400' : 'text-emerald-400';
  const arrow = isPositive ? '▲' : '▼';

  return (
    <span className={`${bgColor} ${textColor} px-2 py-0.5 rounded text-sm font-medium`}>
      {arrow} {isPositive ? '+' : ''}
      {changePercent?.toFixed(2)}%
    </span>
  );
});

// ===== 信號標籤 =====
export const SignalBadge = memo(({ signal }) => {
  const signalStyles = {
    '強力買進': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    '買進': 'bg-green-500/20 text-green-400 border-green-500/30',
    '持有': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    '觀望': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    '減碼': 'bg-red-500/20 text-red-400 border-red-500/30',
    '賣出': 'bg-red-600/20 text-red-500 border-red-600/30',
  };

  const style = signalStyles[signal] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';

  return (
    <span className={`${style} px-2 py-1 rounded-full text-xs font-medium border`}>
      {signal}
    </span>
  );
});

// ===== 空狀態提示 =====
export const EmptyState = memo(({ icon = '📭', title, description }) => {
  const { isDark } = useTheme();
  const titleColor = isDark ? 'text-white' : 'text-gray-900';
  const descColor = isDark ? 'text-slate-400' : 'text-gray-500';

  return (
    <div className="text-center py-12">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className={`${titleColor} font-medium mb-2`}>{title}</h3>
      {description && <p className={`${descColor} text-sm`}>{description}</p>}
    </div>
  );
});

// ===== 卡片容器 =====
export const Card = memo(({ children, className = '', ...props }) => {
  const { isDark } = useTheme();
  const cardClass = isDark
    ? 'bg-slate-800 border-slate-700'
    : 'bg-white border-gray-200 shadow-sm';

  return (
    <div
      className={`${cardClass} rounded-xl border ${className}`}
      {...props}
    >
      {children}
    </div>
  );
});

// ===== 卡片標題 =====
export const CardHeader = memo(({ icon, title, action }) => {
  const { isDark } = useTheme();
  const borderColor = isDark ? 'border-slate-700' : 'border-gray-200';
  const titleColor = isDark ? 'text-white' : 'text-gray-900';

  return (
    <div className={`flex items-center justify-between p-4 border-b ${borderColor}`}>
      <div className="flex items-center gap-2">
        {icon && <span className="text-xl">{icon}</span>}
        <h3 className={`${titleColor} font-medium`}>{title}</h3>
      </div>
      {action}
    </div>
  );
});

// PropTypes 定義
ScoreRing.propTypes = {
  score: PropTypes.number,
  size: PropTypes.number,
};

MiniKLineChart.propTypes = {
  data: PropTypes.arrayOf(PropTypes.shape({
    close: PropTypes.number.isRequired,
  })),
  width: PropTypes.number,
  height: PropTypes.number,
};

ScoreBar.propTypes = {
  label: PropTypes.string.isRequired,
  score: PropTypes.number.isRequired,
  maxScore: PropTypes.number,
  color: PropTypes.oneOf(['red', 'orange', 'yellow', 'green', 'blue', 'purple']),
};

PriceChange.propTypes = {
  change: PropTypes.number,
  changePercent: PropTypes.number,
};

SignalBadge.propTypes = {
  signal: PropTypes.string,
};

EmptyState.propTypes = {
  icon: PropTypes.string,
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};

CardHeader.propTypes = {
  icon: PropTypes.string,
  title: PropTypes.string.isRequired,
  action: PropTypes.node,
};

export default {
  ScoreRing,
  MiniKLineChart,
  TermTooltip,
  ScoreBar,
  Loading,
  PriceChange,
  SignalBadge,
  EmptyState,
  Card,
  CardHeader,
};
