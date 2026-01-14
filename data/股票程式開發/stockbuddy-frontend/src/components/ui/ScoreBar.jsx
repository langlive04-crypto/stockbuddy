/**
 * ScoreBar.jsx - 評分進度條組件
 * V10.37 從 App.jsx 拆分出來
 * V10.17: 評分進度條功能
 */

import React from 'react';
import TermTooltip from './TermTooltip';

const ScoreBar = ({ label, score, maxScore = 100, color = 'blue' }) => {
  const percentage = Math.min((score / maxScore) * 100, 100);
  const colorMap = {
    red: 'bg-red-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    green: 'bg-emerald-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    amber: 'bg-amber-500',
  };

  const getColor = () => {
    if (score >= 70) return 'bg-red-500';
    if (score >= 55) return 'bg-yellow-500';
    return 'bg-slate-500';
  };

  return (
    <TermTooltip term={label}>
      <div className="flex items-center gap-2">
        <span className="text-slate-400 text-xs w-12">{label}</span>
        <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full ${colorMap[color] || getColor()} rounded-full transition-all`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-white text-xs w-8 text-right">{score}</span>
      </div>
    </TermTooltip>
  );
};

export default ScoreBar;
