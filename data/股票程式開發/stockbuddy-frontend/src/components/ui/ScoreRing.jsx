/**
 * ScoreRing.jsx - 分數環組件
 * V10.37 從 App.jsx 拆分出來
 * V10.35.5: 加入評分類型標示
 */

import React from 'react';

const ScoreRing = ({ score, size = 60, type = 'momentum', showLabel = false }) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = ((score || 0) / 100) * circumference;

  const getColor = (s) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#eab308';
    if (s >= 40) return '#f97316';
    return '#ef4444';
  };

  // V10.35.5: 評分類型配置
  const typeConfig = {
    momentum: { label: '動能', color: 'text-amber-400', desc: '適合短線' },
    value: { label: '價值', color: 'text-blue-400', desc: '適合中長線' },
  };
  const config = typeConfig[type] || typeConfig.momentum;

  return (
    <div className="relative group" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none" stroke="#334155" strokeWidth="4"
        />
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none" stroke={getColor(score)} strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-white font-bold" style={{ fontSize: size * 0.28 }}>
          {score || '-'}
        </span>
      </div>
      {/* V10.35.5: 評分說明提示 (方案 F) */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
        <div className={`font-bold ${config.color}`}>{config.label}評分</div>
        <div className="text-slate-400 mt-1">
          {type === 'momentum' ? '技術面 40% | 籌碼面 35% | 基本面 25%' : '技術面 30% | 籌碼面 30% | 基本面 25% | 產業 15%'}
        </div>
        <div className="text-slate-500 text-[10px] mt-1">{config.desc}</div>
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-700"></div>
      </div>
      {/* V10.35.5: 顯示標籤 (方案 E) */}
      {showLabel && (
        <div className={`absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] ${config.color} whitespace-nowrap`}>
          {config.label}
        </div>
      )}
    </div>
  );
};

export default ScoreRing;
