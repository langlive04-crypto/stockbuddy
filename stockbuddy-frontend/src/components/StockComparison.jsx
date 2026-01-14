/**
 * 股票比較組件 V10.18
 * V10.35.1 更新：比較表添加中文名稱
 *
 * 功能：
 * - 選擇多檔股票進行並排比較
 * - 比較表格展示各項指標（含中文名稱）
 * - 雷達圖視覺化
 * - 最佳股票標記
 */

import React, { useState, useEffect, useRef } from 'react';
import { getStockName } from '../services/stockNames';
import { API_BASE } from '../config';

// 比較類型配置
const METRICS_TYPES = {
  fundamental: { label: '基本面', icon: '📊' },
  valuation: { label: '估值', icon: '💰' },
  growth: { label: '成長性', icon: '📈' },
  dividend: { label: '股利', icon: '💵' },
};

// 簡易雷達圖組件
const RadarChart = ({ data, dimensions, size = 200 }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = (size / 2) - 30;

    // 清除畫布
    ctx.clearRect(0, 0, size, size);

    // 繪製背景網格
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;

    for (let level = 1; level <= 5; level++) {
      ctx.beginPath();
      const r = (radius * level) / 5;
      for (let i = 0; i <= dimensions.length; i++) {
        const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // 繪製軸線
    dimensions.forEach((_, i) => {
      const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + radius * Math.cos(angle),
        centerY + radius * Math.sin(angle)
      );
      ctx.stroke();
    });

    // 繪製標籤
    ctx.fillStyle = '#9CA3AF';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    dimensions.forEach((dim, i) => {
      const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2;
      const labelRadius = radius + 18;
      const x = centerX + labelRadius * Math.cos(angle);
      const y = centerY + labelRadius * Math.sin(angle) + 4;
      ctx.fillText(dim.label, x, y);
    });

    // 繪製數據
    const colors = [
      { fill: 'rgba(59, 130, 246, 0.2)', stroke: '#3B82F6' },
      { fill: 'rgba(249, 115, 22, 0.2)', stroke: '#F97316' },
      { fill: 'rgba(34, 197, 94, 0.2)', stroke: '#22C55E' },
      { fill: 'rgba(168, 85, 247, 0.2)', stroke: '#A855F7' },
      { fill: 'rgba(236, 72, 153, 0.2)', stroke: '#EC4899' },
    ];

    data.forEach((stock, stockIdx) => {
      const color = colors[stockIdx % colors.length];

      ctx.beginPath();
      ctx.fillStyle = color.fill;
      ctx.strokeStyle = color.stroke;
      ctx.lineWidth = 2;

      dimensions.forEach((dim, i) => {
        const value = stock[dim.key] || 0;
        const normalizedValue = value / (dim.max || 100);
        const r = radius * normalizedValue;
        const angle = (Math.PI * 2 * i) / dimensions.length - Math.PI / 2;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);

        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  }, [data, dimensions, size]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      className="mx-auto"
    />
  );
};

// 比較表格組件
const ComparisonTable = ({ table, stocks }) => {
  if (!table || table.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700">
            <th className="text-left py-3 px-4 text-slate-400 font-medium">指標</th>
            {stocks.map((stock) => (
              <th
                key={stock.stock_id}
                className="text-center py-3 px-4 font-medium"
              >
                <div className="text-white">{getStockName(stock.stock_id)}</div>
                <div className="text-slate-400 text-xs">{stock.stock_id}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.map((row) => (
            <tr key={row.metric_key} className="border-b border-slate-800 hover:bg-slate-800/50">
              <td className="py-3 px-4 text-slate-300">{row.metric_label}</td>
              {row.values.map((v) => (
                <td
                  key={v.stock_id}
                  className={`text-center py-3 px-4 ${
                    v.is_best
                      ? 'text-emerald-400 font-semibold bg-emerald-500/10'
                      : 'text-white'
                  }`}
                >
                  {v.display}
                  {v.is_best && <span className="ml-1 text-xs">★</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// 股票選擇器
const StockSelector = ({ selectedStocks, onAdd, onRemove }) => {
  const [input, setInput] = useState('');

  const handleAdd = () => {
    const stockId = input.trim().toUpperCase();
    if (stockId && !selectedStocks.includes(stockId) && selectedStocks.length < 5) {
      onAdd(stockId);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleAdd();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="輸入股票代號 (如: 2330)"
          className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 outline-none"
          disabled={selectedStocks.length >= 5}
        />
        <button
          onClick={handleAdd}
          disabled={selectedStocks.length >= 5 || !input.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
        >
          加入
        </button>
      </div>

      {/* 已選股票標籤 */}
      <div className="flex flex-wrap gap-2">
        {selectedStocks.map((stockId, i) => (
          <span
            key={stockId}
            className="inline-flex items-center gap-1 px-3 py-1 bg-slate-700 rounded-full text-white text-sm"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                ['bg-blue-500', 'bg-orange-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500'][i]
              }`}
            />
            {stockId}
            <button
              onClick={() => onRemove(stockId)}
              className="ml-1 text-slate-400 hover:text-red-400"
            >
              ×
            </button>
          </span>
        ))}
        {selectedStocks.length < 2 && (
          <span className="text-slate-500 text-sm">
            至少選擇 2 檔股票進行比較
          </span>
        )}
      </div>

      {/* 快速選擇熱門股票 */}
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="text-slate-500">快速加入:</span>
        {['2330', '2317', '2454', '2881', '2303'].map((stockId) => (
          <button
            key={stockId}
            onClick={() => {
              if (!selectedStocks.includes(stockId) && selectedStocks.length < 5) {
                onAdd(stockId);
              }
            }}
            disabled={selectedStocks.includes(stockId) || selectedStocks.length >= 5}
            className="px-2 py-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 rounded transition-colors"
          >
            {stockId}
          </button>
        ))}
      </div>
    </div>
  );
};

// 圖例
const Legend = ({ stocks }) => {
  const colors = ['bg-blue-500', 'bg-orange-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500'];

  return (
    <div className="flex flex-wrap gap-4 justify-center">
      {stocks.map((stock, i) => (
        <div key={stock.stock_id} className="flex items-center gap-2">
          <span className={`w-3 h-3 rounded ${colors[i]}`} />
          <span className="text-white text-sm">{stock.stock_id}</span>
        </div>
      ))}
    </div>
  );
};

// 主組件
const StockComparison = ({ onSelectStock }) => {
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [metricsType, setMetricsType] = useState('fundamental');
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAddStock = (stockId) => {
    setSelectedStocks([...selectedStocks, stockId]);
  };

  const handleRemoveStock = (stockId) => {
    setSelectedStocks(selectedStocks.filter((s) => s !== stockId));
  };

  const handleCompare = async () => {
    if (selectedStocks.length < 2) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `${API_BASE}/api/stocks/compare?stocks=${selectedStocks.join(',')}&metrics_type=${metricsType}`
      );
      const data = await res.json();

      if (data.success) {
        setComparisonData(data);
      } else {
        throw new Error(data.detail || '比較失敗');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>⚖️</span> 股票比較
        </h2>
      </div>

      {/* 股票選擇器 */}
      <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50">
        <h3 className="text-white font-semibold mb-3">選擇要比較的股票</h3>
        <StockSelector
          selectedStocks={selectedStocks}
          onAdd={handleAddStock}
          onRemove={handleRemoveStock}
        />
      </div>

      {/* 比較類型選擇 */}
      <div className="flex gap-2 flex-wrap">
        {Object.entries(METRICS_TYPES).map(([key, config]) => (
          <button
            key={key}
            onClick={() => setMetricsType(key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              metricsType === key
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {config.icon} {config.label}
          </button>
        ))}
      </div>

      {/* 比較按鈕 */}
      <button
        onClick={handleCompare}
        disabled={selectedStocks.length < 2 || loading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
      >
        {loading ? '比較中...' : '開始比較'}
      </button>

      {/* 錯誤訊息 */}
      {error && (
        <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* 比較結果 */}
      {comparisonData && (
        <div className="space-y-6">
          {/* 圖例 */}
          <Legend stocks={comparisonData.stocks} />

          {/* 雷達圖 */}
          {comparisonData.radar_data && comparisonData.radar_dimensions && (
            <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
              <h3 className="text-white font-semibold mb-4 text-center">五維度分析</h3>
              <RadarChart
                data={comparisonData.radar_data}
                dimensions={comparisonData.radar_dimensions}
                size={280}
              />
            </div>
          )}

          {/* 比較表格 */}
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white font-semibold mb-4">
              {METRICS_TYPES[comparisonData.metrics_type]?.label || '指標'} 比較
            </h3>
            <ComparisonTable
              table={comparisonData.comparison_table}
              stocks={comparisonData.stocks}
            />
            <div className="mt-3 text-xs text-slate-500">
              ★ 標記為該指標最佳股票
            </div>
          </div>

          {/* 最佳股票摘要 */}
          {comparisonData.best_picks && Object.keys(comparisonData.best_picks).length > 0 && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
              <h3 className="text-emerald-400 font-semibold mb-3">各指標優勝者</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                {Object.entries(comparisonData.best_picks).map(([metric, stockId]) => {
                  const metricLabel = comparisonData.metrics.find(m => m.key === metric)?.label || metric;
                  return (
                    <div key={metric} className="flex justify-between">
                      <span className="text-slate-400">{metricLabel}</span>
                      <span className="text-emerald-400 font-medium">{stockId}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 空狀態 */}
      {!comparisonData && !loading && (
        <div className="text-center py-12 text-slate-500">
          <div className="text-4xl mb-4">⚖️</div>
          <p>選擇股票並點擊「開始比較」</p>
        </div>
      )}

      {/* 說明 */}
      <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50 text-sm text-slate-400">
        <h4 className="text-white font-medium mb-2">💡 使用說明</h4>
        <ul className="list-disc list-inside space-y-1">
          <li>最多可同時比較 5 檔股票</li>
          <li>★ 標記表示該指標的最佳表現者</li>
          <li>雷達圖顯示五個維度的綜合評分</li>
          <li>點擊股票代號可查看詳細資訊</li>
        </ul>
      </div>
    </div>
  );
};

export default StockComparison;
