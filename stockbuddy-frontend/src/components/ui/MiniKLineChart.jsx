/**
 * MiniKLineChart.jsx - 迷你 K 線圖組件
 * V10.37 從 App.jsx 拆分出來
 */

import React from 'react';

const MiniKLineChart = ({ data, width = 100, height = 40 }) => {
  if (!data || data.length < 2) return null;

  const prices = data.map(d => d.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice || 1;

  const points = prices.map((price, i) => {
    const x = (i / (prices.length - 1)) * width;
    const y = height - ((price - minPrice) / range) * height;
    return `${x},${y}`;
  }).join(' ');

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
};

export default MiniKLineChart;
