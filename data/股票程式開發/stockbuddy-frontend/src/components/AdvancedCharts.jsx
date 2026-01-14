/**
 * AdvancedCharts.jsx - 進階圖表
 * V10.31 新增
 * V10.35.1 更新：添加示範數據標示和 API 整合準備
 *
 * 功能：
 * - 技術指標疊加圖
 * - 籌碼變化圖
 * - 產業輪動圖
 * - 相關性熱力圖
 *
 * 數據來源：
 * - 目前使用示範數據
 * - 後續可接入 /api/stocks/technical、/api/stocks/chip 等 API
 */

import React, { useState, useEffect } from 'react';
import { API_STOCKS_BASE } from '../config';

const API_BASE = API_STOCKS_BASE;

// 數據狀態標籤
const DataSourceBadge = ({ isDemo = true }) => (
  <span className={`px-2 py-0.5 rounded text-xs ${
    isDemo
      ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
  }`}>
    {isDemo ? '示範數據' : '即時數據'}
  </span>
);

// 模擬技術指標數據 (作為 fallback)
const MOCK_TECHNICAL_DATA = Array.from({ length: 30 }, (_, i) => ({
  date: `01/${String(i + 1).padStart(2, '0')}`,
  price: 980 + Math.random() * 40,
  ma5: 985 + Math.random() * 20,
  ma10: 990 + Math.random() * 15,
  ma20: 995 + Math.random() * 10,
  rsi: 45 + Math.random() * 30,
  macd: -5 + Math.random() * 10,
  signal: -3 + Math.random() * 6,
  histogram: -2 + Math.random() * 4,
  volume: 10000 + Math.random() * 30000,
}));

// 模擬籌碼數據
const MOCK_CHIP_DATA = [
  { date: '01/06', foreign: 5200, investment: 1800, dealer: -500 },
  { date: '01/07', foreign: -3100, investment: 2200, dealer: 800 },
  { date: '01/08', foreign: 8500, investment: -1200, dealer: 300 },
  { date: '01/09', foreign: 2300, investment: 900, dealer: -200 },
  { date: '01/10', foreign: -1500, investment: 3100, dealer: 600 },
];

// 模擬產業輪動數據
const MOCK_SECTOR_DATA = [
  { sector: '半導體', momentum: 85, change: 2.5, status: 'leading' },
  { sector: '電子零組件', momentum: 72, change: 1.8, status: 'leading' },
  { sector: '金融業', momentum: 45, change: -0.5, status: 'lagging' },
  { sector: '傳產', momentum: 38, change: -1.2, status: 'lagging' },
  { sector: '生技醫療', momentum: 65, change: 0.8, status: 'improving' },
  { sector: '航運', momentum: 52, change: -0.3, status: 'weakening' },
  { sector: '鋼鐵', momentum: 35, change: -1.5, status: 'lagging' },
  { sector: '電信', momentum: 58, change: 0.2, status: 'improving' },
];

// 模擬相關性數據
const MOCK_CORRELATION_STOCKS = ['2330', '2454', '2317', '2412', '3008'];
const MOCK_CORRELATION_NAMES = ['台積電', '聯發科', '鴻海', '中華電', '大立光'];
const MOCK_CORRELATION_MATRIX = [
  [1.00, 0.85, 0.72, 0.25, 0.68],
  [0.85, 1.00, 0.65, 0.18, 0.75],
  [0.72, 0.65, 1.00, 0.32, 0.55],
  [0.25, 0.18, 0.32, 1.00, 0.15],
  [0.68, 0.75, 0.55, 0.15, 1.00],
];

// 標籤頁定義
const TABS = [
  { id: 'technical', label: '技術指標', icon: '📊' },
  { id: 'chip', label: '籌碼變化', icon: '💰' },
  { id: 'sector', label: '產業輪動', icon: '🔄' },
  { id: 'correlation', label: '相關性', icon: '🔗' },
];

const AdvancedCharts = ({ stock = null }) => {
  const [activeTab, setActiveTab] = useState('technical');
  const [selectedIndicators, setSelectedIndicators] = useState(['price', 'ma5', 'ma20']);

  // 技術指標圖表
  const TechnicalChart = () => {
    const maxPrice = Math.max(...MOCK_TECHNICAL_DATA.map(d => d.price));
    const minPrice = Math.min(...MOCK_TECHNICAL_DATA.map(d => d.price));
    const priceRange = maxPrice - minPrice || 1;

    return (
      <div className="space-y-4">
        {/* 指標選擇 */}
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'price', label: '股價', color: 'bg-white' },
            { id: 'ma5', label: 'MA5', color: 'bg-yellow-400' },
            { id: 'ma10', label: 'MA10', color: 'bg-blue-400' },
            { id: 'ma20', label: 'MA20', color: 'bg-purple-400' },
          ].map(ind => (
            <button
              key={ind.id}
              onClick={() => {
                setSelectedIndicators(prev =>
                  prev.includes(ind.id)
                    ? prev.filter(i => i !== ind.id)
                    : [...prev, ind.id]
                );
              }}
              className={`px-3 py-1 rounded-full text-xs flex items-center gap-1.5 transition-colors ${
                selectedIndicators.includes(ind.id)
                  ? 'bg-slate-600 text-white'
                  : 'bg-slate-700/50 text-slate-400'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${ind.color}`}></span>
              {ind.label}
            </button>
          ))}
        </div>

        {/* 價格線圖 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">股價與均線</h4>
          <div className="h-48 relative">
            <svg viewBox="0 0 600 200" className="w-full h-full">
              {/* 網格線 */}
              {[0, 1, 2, 3, 4].map(i => (
                <line
                  key={i}
                  x1="0"
                  y1={i * 50}
                  x2="600"
                  y2={i * 50}
                  stroke="#374151"
                  strokeWidth="1"
                />
              ))}

              {/* 股價線 */}
              {selectedIndicators.includes('price') && (
                <polyline
                  fill="none"
                  stroke="#fff"
                  strokeWidth="2"
                  points={MOCK_TECHNICAL_DATA.map((d, i) =>
                    `${i * 20},${200 - ((d.price - minPrice) / priceRange) * 180}`
                  ).join(' ')}
                />
              )}

              {/* MA5 */}
              {selectedIndicators.includes('ma5') && (
                <polyline
                  fill="none"
                  stroke="#facc15"
                  strokeWidth="1.5"
                  points={MOCK_TECHNICAL_DATA.map((d, i) =>
                    `${i * 20},${200 - ((d.ma5 - minPrice) / priceRange) * 180}`
                  ).join(' ')}
                />
              )}

              {/* MA10 */}
              {selectedIndicators.includes('ma10') && (
                <polyline
                  fill="none"
                  stroke="#60a5fa"
                  strokeWidth="1.5"
                  points={MOCK_TECHNICAL_DATA.map((d, i) =>
                    `${i * 20},${200 - ((d.ma10 - minPrice) / priceRange) * 180}`
                  ).join(' ')}
                />
              )}

              {/* MA20 */}
              {selectedIndicators.includes('ma20') && (
                <polyline
                  fill="none"
                  stroke="#a78bfa"
                  strokeWidth="1.5"
                  points={MOCK_TECHNICAL_DATA.map((d, i) =>
                    `${i * 20},${200 - ((d.ma20 - minPrice) / priceRange) * 180}`
                  ).join(' ')}
                />
              )}
            </svg>

            {/* Y軸標籤 */}
            <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-slate-500 -ml-10 w-9 text-right">
              <span>{maxPrice.toFixed(0)}</span>
              <span>{((maxPrice + minPrice) / 2).toFixed(0)}</span>
              <span>{minPrice.toFixed(0)}</span>
            </div>
          </div>
        </div>

        {/* RSI 圖表 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">RSI (14)</h4>
          <div className="h-24 relative">
            <svg viewBox="0 0 600 100" className="w-full h-full">
              {/* 超買超賣區域 */}
              <rect x="0" y="0" width="600" height="30" fill="#ef444420" />
              <rect x="0" y="70" width="600" height="30" fill="#22c55e20" />
              <line x1="0" y1="30" x2="600" y2="30" stroke="#ef4444" strokeDasharray="4" />
              <line x1="0" y1="70" x2="600" y2="70" stroke="#22c55e" strokeDasharray="4" />

              {/* RSI 線 */}
              <polyline
                fill="none"
                stroke="#f97316"
                strokeWidth="2"
                points={MOCK_TECHNICAL_DATA.map((d, i) =>
                  `${i * 20},${100 - d.rsi}`
                ).join(' ')}
              />
            </svg>
            <div className="absolute right-0 top-0 text-xs text-slate-500">超買 70</div>
            <div className="absolute right-0 bottom-0 text-xs text-slate-500">超賣 30</div>
          </div>
        </div>

        {/* MACD 圖表 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">MACD</h4>
          <div className="h-24 flex items-end gap-0.5">
            {MOCK_TECHNICAL_DATA.map((d, i) => (
              <div
                key={i}
                className={`flex-1 ${d.histogram >= 0 ? 'bg-red-500' : 'bg-emerald-500'}`}
                style={{ height: `${Math.abs(d.histogram) * 10 + 5}px` }}
                title={`${d.date}: ${d.histogram.toFixed(2)}`}
              />
            ))}
          </div>
        </div>
      </div>
    );
  };

  // 籌碼變化圖
  const ChipChart = () => {
    const maxVal = Math.max(...MOCK_CHIP_DATA.flatMap(d => [
      Math.abs(d.foreign),
      Math.abs(d.investment),
      Math.abs(d.dealer)
    ]));

    return (
      <div className="space-y-4">
        {/* 三大法人買賣超 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">三大法人買賣超 (張)</h4>
          <div className="space-y-4">
            {MOCK_CHIP_DATA.map((d, idx) => (
              <div key={idx} className="space-y-2">
                <div className="text-slate-400 text-xs">{d.date}</div>
                <div className="grid grid-cols-3 gap-2">
                  {/* 外資 */}
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">外資</div>
                    <div className="h-8 bg-slate-600 rounded relative overflow-hidden">
                      <div
                        className={`absolute inset-y-0 ${d.foreign >= 0 ? 'bg-red-500 left-1/2' : 'bg-emerald-500 right-1/2'}`}
                        style={{ width: `${Math.abs(d.foreign) / maxVal * 50}%` }}
                      />
                    </div>
                    <div className={`text-xs mt-1 ${d.foreign >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {d.foreign >= 0 ? '+' : ''}{d.foreign.toLocaleString()}
                    </div>
                  </div>

                  {/* 投信 */}
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">投信</div>
                    <div className="h-8 bg-slate-600 rounded relative overflow-hidden">
                      <div
                        className={`absolute inset-y-0 ${d.investment >= 0 ? 'bg-red-500 left-1/2' : 'bg-emerald-500 right-1/2'}`}
                        style={{ width: `${Math.abs(d.investment) / maxVal * 50}%` }}
                      />
                    </div>
                    <div className={`text-xs mt-1 ${d.investment >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {d.investment >= 0 ? '+' : ''}{d.investment.toLocaleString()}
                    </div>
                  </div>

                  {/* 自營商 */}
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">自營商</div>
                    <div className="h-8 bg-slate-600 rounded relative overflow-hidden">
                      <div
                        className={`absolute inset-y-0 ${d.dealer >= 0 ? 'bg-red-500 left-1/2' : 'bg-emerald-500 right-1/2'}`}
                        style={{ width: `${Math.abs(d.dealer) / maxVal * 50}%` }}
                      />
                    </div>
                    <div className={`text-xs mt-1 ${d.dealer >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {d.dealer >= 0 ? '+' : ''}{d.dealer.toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 累積統計 */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: '外資累計', value: MOCK_CHIP_DATA.reduce((s, d) => s + d.foreign, 0), color: 'blue' },
            { label: '投信累計', value: MOCK_CHIP_DATA.reduce((s, d) => s + d.investment, 0), color: 'purple' },
            { label: '自營商累計', value: MOCK_CHIP_DATA.reduce((s, d) => s + d.dealer, 0), color: 'orange' },
          ].map((stat, idx) => (
            <div key={idx} className="bg-slate-700/50 rounded-lg p-3 text-center">
              <div className="text-slate-400 text-xs mb-1">{stat.label}</div>
              <div className={`text-lg font-bold ${stat.value >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {stat.value >= 0 ? '+' : ''}{stat.value.toLocaleString()}
              </div>
              <div className="text-slate-500 text-xs">張</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // 產業輪動圖
  const SectorRotation = () => {
    const statusColors = {
      leading: 'bg-red-500/20 border-red-500/50 text-red-400',
      improving: 'bg-orange-500/20 border-orange-500/50 text-orange-400',
      weakening: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400',
      lagging: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400',
    };

    const statusLabels = {
      leading: '領漲',
      improving: '轉強',
      weakening: '轉弱',
      lagging: '落後',
    };

    return (
      <div className="space-y-4">
        {/* 四象限圖 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">產業輪動象限圖</h4>
          <div className="relative h-64 bg-slate-800 rounded-lg overflow-hidden">
            {/* 象限分隔線 */}
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600" />
            <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-600" />

            {/* 象限標籤 */}
            <div className="absolute top-2 right-2 text-red-400 text-xs">領漲</div>
            <div className="absolute top-2 left-2 text-orange-400 text-xs">轉強</div>
            <div className="absolute bottom-2 left-2 text-emerald-400 text-xs">落後</div>
            <div className="absolute bottom-2 right-2 text-yellow-400 text-xs">轉弱</div>

            {/* 產業點 */}
            {MOCK_SECTOR_DATA.map((sector, idx) => {
              // 根據動能和變化計算位置
              const x = 50 + sector.change * 15; // 變化決定左右
              const y = 100 - sector.momentum; // 動能決定上下

              return (
                <div
                  key={idx}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                  style={{ left: `${x}%`, top: `${y}%` }}
                  title={`${sector.sector}: 動能 ${sector.momentum}, 變化 ${sector.change}%`}
                >
                  <div className={`w-3 h-3 rounded-full ${
                    sector.status === 'leading' ? 'bg-red-500' :
                    sector.status === 'improving' ? 'bg-orange-500' :
                    sector.status === 'weakening' ? 'bg-yellow-500' :
                    'bg-emerald-500'
                  }`} />
                  <div className="absolute left-full ml-1 whitespace-nowrap text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 px-1 rounded">
                    {sector.sector}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 產業列表 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">產業動能排行</h4>
          <div className="space-y-2">
            {MOCK_SECTOR_DATA.sort((a, b) => b.momentum - a.momentum).map((sector, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="text-slate-400 text-sm w-4">{idx + 1}</span>
                <span className="text-white text-sm flex-1">{sector.sector}</span>
                <div className="w-24 h-2 bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      sector.momentum >= 70 ? 'bg-red-500' :
                      sector.momentum >= 50 ? 'bg-orange-500' :
                      'bg-emerald-500'
                    }`}
                    style={{ width: `${sector.momentum}%` }}
                  />
                </div>
                <span className={`text-xs w-12 text-right ${sector.change >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {sector.change >= 0 ? '+' : ''}{sector.change}%
                </span>
                <span className={`text-xs px-2 py-0.5 rounded border ${statusColors[sector.status]}`}>
                  {statusLabels[sector.status]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // 相關性熱力圖
  const CorrelationHeatmap = () => {
    const getCorrelationColor = (value) => {
      if (value >= 0.8) return 'bg-red-600';
      if (value >= 0.6) return 'bg-red-500';
      if (value >= 0.4) return 'bg-orange-500';
      if (value >= 0.2) return 'bg-yellow-500';
      if (value >= 0) return 'bg-slate-500';
      return 'bg-emerald-500';
    };

    return (
      <div className="space-y-4">
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white text-sm mb-3">股票相關性熱力圖</h4>

          {/* 熱力圖 */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="p-2"></th>
                  {MOCK_CORRELATION_NAMES.map((name, idx) => (
                    <th key={idx} className="p-2 text-slate-400 text-xs text-center">
                      <div>{name}</div>
                      <div className="text-slate-500">{MOCK_CORRELATION_STOCKS[idx]}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MOCK_CORRELATION_NAMES.map((name, rowIdx) => (
                  <tr key={rowIdx}>
                    <td className="p-2 text-slate-400 text-xs">
                      <div>{name}</div>
                      <div className="text-slate-500">{MOCK_CORRELATION_STOCKS[rowIdx]}</div>
                    </td>
                    {MOCK_CORRELATION_MATRIX[rowIdx].map((value, colIdx) => (
                      <td key={colIdx} className="p-1">
                        <div
                          className={`w-12 h-12 mx-auto rounded flex items-center justify-center text-xs text-white font-medium ${getCorrelationColor(value)}`}
                          title={`${MOCK_CORRELATION_NAMES[rowIdx]} vs ${MOCK_CORRELATION_NAMES[colIdx]}: ${value.toFixed(2)}`}
                        >
                          {value.toFixed(2)}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 圖例 */}
          <div className="flex items-center justify-center gap-4 mt-4">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-600 rounded"></div>
              <span className="text-xs text-slate-400">高相關</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-orange-500 rounded"></div>
              <span className="text-xs text-slate-400">中相關</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span className="text-xs text-slate-400">低相關</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-emerald-500 rounded"></div>
              <span className="text-xs text-slate-400">負相關</span>
            </div>
          </div>
        </div>

        {/* 解讀說明 */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <span className="text-blue-400">ℹ️</span>
            <div className="text-blue-300 text-sm">
              <p className="font-medium mb-1">相關性解讀</p>
              <ul className="text-xs space-y-0.5 text-blue-300/80">
                <li>- 高相關 (&gt;0.8): 價格走勢高度同步</li>
                <li>- 中相關 (0.4-0.8): 有一定程度連動</li>
                <li>- 低相關 (&lt;0.4): 走勢相對獨立</li>
                <li>- 分散投資建議選擇低相關性股票</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📈</span>
            <span>進階圖表分析</span>
          </h2>
          <DataSourceBadge isDemo={true} />
        </div>

        {stock && (
          <div className="text-slate-400 text-sm">
            分析標的: <span className="text-white">{stock.name} ({stock.stock_id})</span>
          </div>
        )}
      </div>

      {/* 標籤頁 */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-2 ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 內容區域 */}
      {activeTab === 'technical' && <TechnicalChart />}
      {activeTab === 'chip' && <ChipChart />}
      {activeTab === 'sector' && <SectorRotation />}
      {activeTab === 'correlation' && <CorrelationHeatmap />}
    </div>
  );
};

export default AdvancedCharts;
