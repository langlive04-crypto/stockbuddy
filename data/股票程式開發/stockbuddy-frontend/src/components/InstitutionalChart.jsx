/**
 * 三大法人持股追蹤圖表 V10.15
 * 視覺化法人買賣超趨勢
 */

import React, { useEffect, useRef, useState } from 'react';
import { API_BASE } from '../config';

const InstitutionalChart = ({ stockId, stockName, days = 20 }) => {
  const canvasRef = useRef(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 獲取資料
  useEffect(() => {
    const fetchData = async () => {
      if (!stockId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE}/api/stocks/institutional-tracking/${stockId}?days=${days}`
        );

        if (response.ok) {
          const result = await response.json();
          if (result.success) {
            setData(result.tracking_data);
          } else {
            setError(result.error || '無法取得資料');
          }
        } else {
          setError('API 請求失敗');
        }
      } catch (err) {
        console.error('法人追蹤資料載入失敗:', err);
        setError('載入失敗');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [stockId, days]);

  // 繪製圖表
  useEffect(() => {
    if (!data || data.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    const width = 600;
    const height = 300;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    // 清除畫布
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);

    // 計算數據範圍
    const foreignNets = data.map(d => d.foreign_net || 0);
    const trustNets = data.map(d => d.trust_net || 0);
    const dealerNets = data.map(d => d.dealer_net || 0);
    const totalNets = data.map(d => (d.foreign_net || 0) + (d.trust_net || 0) + (d.dealer_net || 0));

    const allValues = [...foreignNets, ...trustNets, ...dealerNets, ...totalNets];
    const maxValue = Math.max(...allValues.map(Math.abs)) * 1.2;

    if (maxValue === 0) {
      ctx.fillStyle = '#94a3b8';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('無法人買賣資料', width / 2, height / 2);
      return;
    }

    // 版面配置
    const padding = { top: 40, right: 80, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const barWidth = chartWidth / data.length * 0.6;
    const barSpacing = chartWidth / data.length;
    const midY = padding.top + chartHeight / 2;

    // 數值轉 Y 座標
    const valueToY = (value) => {
      return midY - (value / maxValue) * (chartHeight / 2);
    };

    // 繪製背景網格
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 0.5;

    // 中線（零軸）
    ctx.beginPath();
    ctx.moveTo(padding.left, midY);
    ctx.lineTo(width - padding.right, midY);
    ctx.stroke();

    // 水平網格
    const gridLines = 4;
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';

    for (let i = -gridLines / 2; i <= gridLines / 2; i++) {
      const y = midY - (i / (gridLines / 2)) * (chartHeight / 2);
      const value = (i / (gridLines / 2)) * maxValue;

      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // 標籤
      const label = Math.abs(value) >= 1000
        ? `${(value / 1000).toFixed(0)}K`
        : value.toFixed(0);
      ctx.fillText(label, padding.left - 5, y + 4);
    }

    // 繪製累積面積圖
    const drawAreaChart = (values, color, alpha = 0.3) => {
      ctx.beginPath();
      ctx.moveTo(padding.left, midY);

      values.forEach((val, i) => {
        const x = padding.left + i * barSpacing + barSpacing / 2;
        const y = valueToY(val);
        if (i === 0) {
          ctx.lineTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      // 閉合到零軸
      const lastX = padding.left + (values.length - 1) * barSpacing + barSpacing / 2;
      ctx.lineTo(lastX, midY);
      ctx.closePath();

      ctx.fillStyle = color.replace('1)', `${alpha})`);
      ctx.fill();

      // 繪製線條
      ctx.beginPath();
      values.forEach((val, i) => {
        const x = padding.left + i * barSpacing + barSpacing / 2;
        const y = valueToY(val);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    };

    // 繪製各法人線條
    drawAreaChart(foreignNets, 'rgba(59, 130, 246, 1)', 0.15);  // 藍色 - 外資
    drawAreaChart(trustNets, 'rgba(168, 85, 247, 1)', 0.15);   // 紫色 - 投信
    drawAreaChart(dealerNets, 'rgba(34, 197, 94, 1)', 0.15);   // 綠色 - 自營商

    // 繪製合計柱狀圖
    data.forEach((item, i) => {
      const x = padding.left + i * barSpacing + barSpacing / 2;
      const total = (item.foreign_net || 0) + (item.trust_net || 0) + (item.dealer_net || 0);
      const y = valueToY(total);
      const barHeight = Math.abs(y - midY);

      ctx.fillStyle = total >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)';
      ctx.fillRect(
        x - barWidth / 4,
        total >= 0 ? y : midY,
        barWidth / 2,
        barHeight
      );
    });

    // 繪製日期標籤
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';

    data.forEach((item, i) => {
      if (i % Math.ceil(data.length / 5) === 0 || i === data.length - 1) {
        const x = padding.left + i * barSpacing + barSpacing / 2;
        const date = item.date?.slice(-5) || '';  // MM-DD
        ctx.fillText(date, x, height - padding.bottom + 15);
      }
    });

    // 圖例
    const legends = [
      { label: '外資', color: 'rgba(59, 130, 246, 1)' },
      { label: '投信', color: 'rgba(168, 85, 247, 1)' },
      { label: '自營商', color: 'rgba(34, 197, 94, 1)' },
      { label: '合計', color: 'rgba(239, 68, 68, 1)' },
    ];

    legends.forEach((legend, i) => {
      const x = width - padding.right + 10;
      const y = padding.top + i * 25;

      ctx.fillStyle = legend.color;
      ctx.fillRect(x, y, 12, 12);

      ctx.fillStyle = '#e2e8f0';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(legend.label, x + 16, y + 10);
    });

    // 標題
    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${stockName || stockId} 三大法人買賣超追蹤`, padding.left, 25);

  }, [data, stockId, stockName]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-800 rounded-xl">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-slate-400">載入法人資料...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-800 rounded-xl">
        <p className="text-slate-400">{error}</p>
      </div>
    );
  }

  // 計算統計摘要
  const summary = data ? {
    foreignTotal: data.reduce((sum, d) => sum + (d.foreign_net || 0), 0),
    trustTotal: data.reduce((sum, d) => sum + (d.trust_net || 0), 0),
    dealerTotal: data.reduce((sum, d) => sum + (d.dealer_net || 0), 0),
  } : null;

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <canvas ref={canvasRef} className="rounded-lg" />

      {/* 統計摘要 */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-700">
          <div className="text-center">
            <div className="text-slate-400 text-xs">外資 {days}日</div>
            <div className={`font-bold ${summary.foreignTotal >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {summary.foreignTotal >= 0 ? '+' : ''}{(summary.foreignTotal / 1000).toFixed(1)}K
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-400 text-xs">投信 {days}日</div>
            <div className={`font-bold ${summary.trustTotal >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {summary.trustTotal >= 0 ? '+' : ''}{(summary.trustTotal / 1000).toFixed(1)}K
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-400 text-xs">自營商 {days}日</div>
            <div className={`font-bold ${summary.dealerTotal >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {summary.dealerTotal >= 0 ? '+' : ''}{(summary.dealerTotal / 1000).toFixed(1)}K
            </div>
          </div>
          <div className="text-center">
            <div className="text-slate-400 text-xs">合計</div>
            <div className={`font-bold text-lg ${
              (summary.foreignTotal + summary.trustTotal + summary.dealerTotal) >= 0
                ? 'text-red-400'
                : 'text-emerald-400'
            }`}>
              {(summary.foreignTotal + summary.trustTotal + summary.dealerTotal) >= 0 ? '+' : ''}
              {((summary.foreignTotal + summary.trustTotal + summary.dealerTotal) / 1000).toFixed(1)}K
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstitutionalChart;
