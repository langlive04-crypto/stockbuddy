/**
 * PatternRecognition.jsx - 技術形態辨識
 * V10.33 新增
 *
 * 功能：
 * - 頭肩頂/底形態辨識
 * - 雙重頂/底形態辨識
 * - 三角收斂形態辨識
 * - 旗形/楔形形態辨識
 */

import React, { useState, useMemo } from 'react';

// 形態類型定義
const PATTERN_TYPES = {
  headShoulders: {
    id: 'headShoulders',
    name: '頭肩頂',
    icon: '⛰️',
    color: 'text-red-400',
    bg: 'bg-red-500/20',
    signal: '賣出',
    description: '頭部高於兩肩，頸線跌破為賣出信號',
    reliability: 85,
  },
  inverseHeadShoulders: {
    id: 'inverseHeadShoulders',
    name: '頭肩底',
    icon: '🏔️',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/20',
    signal: '買進',
    description: '頭部低於兩肩，頸線突破為買進信號',
    reliability: 82,
  },
  doubleTop: {
    id: 'doubleTop',
    name: '雙重頂',
    icon: '🏠',
    color: 'text-red-400',
    bg: 'bg-red-500/20',
    signal: '賣出',
    description: '兩個相近高點，第二次無法突破為賣出信號',
    reliability: 78,
  },
  doubleBottom: {
    id: 'doubleBottom',
    name: '雙重底',
    icon: '🔻',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/20',
    signal: '買進',
    description: '兩個相近低點，第二次不破底為買進信號',
    reliability: 80,
  },
  ascendingTriangle: {
    id: 'ascendingTriangle',
    name: '上升三角',
    icon: '📐',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/20',
    signal: '買進',
    description: '水平上壓力線、上升下支撐線，突破為買進',
    reliability: 75,
  },
  descendingTriangle: {
    id: 'descendingTriangle',
    name: '下降三角',
    icon: '📏',
    color: 'text-red-400',
    bg: 'bg-red-500/20',
    signal: '賣出',
    description: '水平下支撐線、下降上壓力線，跌破為賣出',
    reliability: 72,
  },
  symmetricalTriangle: {
    id: 'symmetricalTriangle',
    name: '對稱三角',
    icon: '🔺',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/20',
    signal: '觀望',
    description: '收斂趨勢，等待方向確認後跟進',
    reliability: 68,
  },
  flag: {
    id: 'flag',
    name: '旗形',
    icon: '🚩',
    color: 'text-blue-400',
    bg: 'bg-blue-500/20',
    signal: '續漲/續跌',
    description: '趨勢中的休息形態，突破後順勢操作',
    reliability: 70,
  },
  wedge: {
    id: 'wedge',
    name: '楔形',
    icon: '🔷',
    color: 'text-purple-400',
    bg: 'bg-purple-500/20',
    signal: '反轉',
    description: '收斂走勢，通常預示趨勢反轉',
    reliability: 65,
  },
};

// 模擬檢測到的形態
const MOCK_DETECTED_PATTERNS = [
  {
    stockId: '2330',
    stockName: '台積電',
    pattern: 'headShoulders',
    confidence: 85,
    stage: 'forming',
    targetPrice: 950,
    stopLoss: 1020,
    detectedDate: '2026-01-10',
  },
  {
    stockId: '2454',
    stockName: '聯發科',
    pattern: 'doubleBottom',
    confidence: 78,
    stage: 'confirmed',
    targetPrice: 1350,
    stopLoss: 1120,
    detectedDate: '2026-01-09',
  },
  {
    stockId: '2317',
    stockName: '鴻海',
    pattern: 'ascendingTriangle',
    confidence: 72,
    stage: 'forming',
    targetPrice: 125,
    stopLoss: 102,
    detectedDate: '2026-01-10',
  },
  {
    stockId: '3008',
    stockName: '大立光',
    pattern: 'flag',
    confidence: 68,
    stage: 'confirmed',
    targetPrice: 2550,
    stopLoss: 2200,
    detectedDate: '2026-01-08',
  },
  {
    stockId: '2303',
    stockName: '聯電',
    pattern: 'symmetricalTriangle',
    confidence: 65,
    stage: 'forming',
    targetPrice: null,
    stopLoss: 48,
    detectedDate: '2026-01-10',
  },
];

const PatternRecognition = () => {
  const [selectedPattern, setSelectedPattern] = useState('all');
  const [selectedStage, setSelectedStage] = useState('all');

  // 篩選形態
  const filteredPatterns = useMemo(() => {
    let patterns = [...MOCK_DETECTED_PATTERNS];

    if (selectedPattern !== 'all') {
      patterns = patterns.filter(p => p.pattern === selectedPattern);
    }

    if (selectedStage !== 'all') {
      patterns = patterns.filter(p => p.stage === selectedStage);
    }

    return patterns.sort((a, b) => b.confidence - a.confidence);
  }, [selectedPattern, selectedStage]);

  // 形態統計
  const patternStats = useMemo(() => {
    const bullish = MOCK_DETECTED_PATTERNS.filter(p =>
      ['inverseHeadShoulders', 'doubleBottom', 'ascendingTriangle'].includes(p.pattern)
    ).length;
    const bearish = MOCK_DETECTED_PATTERNS.filter(p =>
      ['headShoulders', 'doubleTop', 'descendingTriangle'].includes(p.pattern)
    ).length;
    const neutral = MOCK_DETECTED_PATTERNS.length - bullish - bearish;

    return { bullish, bearish, neutral, total: MOCK_DETECTED_PATTERNS.length };
  }, []);

  // 形態圖解組件
  const PatternDiagram = ({ patternType }) => {
    const diagrams = {
      headShoulders: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,50 20,30 35,45 50,15 65,45 80,30 95,50"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="20" y1="45" x2="80" y2="45" stroke="currentColor" strokeDasharray="3" />
          <text x="50" y="58" fontSize="8" textAnchor="middle" fill="currentColor">頸線</text>
        </svg>
      ),
      inverseHeadShoulders: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,10 20,30 35,15 50,45 65,15 80,30 95,10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="20" y1="15" x2="80" y2="15" stroke="currentColor" strokeDasharray="3" />
          <text x="50" y="8" fontSize="8" textAnchor="middle" fill="currentColor">頸線</text>
        </svg>
      ),
      doubleTop: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,50 25,15 45,35 65,15 95,50"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="5" y1="35" x2="95" y2="35" stroke="currentColor" strokeDasharray="3" />
        </svg>
      ),
      doubleBottom: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,10 25,45 45,25 65,45 95,10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="5" y1="25" x2="95" y2="25" stroke="currentColor" strokeDasharray="3" />
        </svg>
      ),
      ascendingTriangle: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,50 25,15 40,50 55,15 70,40 85,15 95,30"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="5" y1="15" x2="95" y2="15" stroke="currentColor" strokeWidth="1" />
          <line x1="5" y1="50" x2="95" y2="20" stroke="currentColor" strokeWidth="1" />
        </svg>
      ),
      descendingTriangle: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,10 25,45 40,20 55,45 70,30 85,45 95,35"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="5" y1="45" x2="95" y2="45" stroke="currentColor" strokeWidth="1" />
          <line x1="5" y1="10" x2="95" y2="40" stroke="currentColor" strokeWidth="1" />
        </svg>
      ),
      symmetricalTriangle: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,30 25,10 40,45 55,18 70,38 85,25 95,30"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="5" y1="10" x2="95" y2="30" stroke="currentColor" strokeWidth="1" />
          <line x1="5" y1="50" x2="95" y2="30" stroke="currentColor" strokeWidth="1" />
        </svg>
      ),
      flag: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,55 30,15 40,25 50,18 60,28 70,20 95,5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <rect x="30" y="15" width="40" height="15" fill="none" stroke="currentColor" strokeDasharray="2" />
        </svg>
      ),
      wedge: (
        <svg viewBox="0 0 100 60" className="w-full h-full">
          <polyline
            points="5,50 25,20 40,45 55,25 70,40 85,30 95,35"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line x1="5" y1="20" x2="95" y2="35" stroke="currentColor" strokeWidth="1" />
          <line x1="5" y1="50" x2="95" y2="35" stroke="currentColor" strokeWidth="1" />
        </svg>
      ),
    };

    return diagrams[patternType] || null;
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🔍</span>
          <span>技術形態辨識</span>
        </h2>

        <div className="flex items-center gap-2">
          {/* 形態統計 */}
          <span className="text-emerald-400 text-sm">📈 {patternStats.bullish}</span>
          <span className="text-red-400 text-sm">📉 {patternStats.bearish}</span>
          <span className="text-yellow-400 text-sm">➖ {patternStats.neutral}</span>
        </div>
      </div>

      {/* 形態類型選擇 */}
      <div className="mb-4">
        <label className="text-slate-400 text-sm mb-2 block">形態類型</label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedPattern('all')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              selectedPattern === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
            }`}
          >
            全部
          </button>
          {Object.values(PATTERN_TYPES).map(pt => (
            <button
              key={pt.id}
              onClick={() => setSelectedPattern(pt.id)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors flex items-center gap-1 ${
                selectedPattern === pt.id
                  ? `${pt.bg} ${pt.color}`
                  : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
              }`}
            >
              <span>{pt.icon}</span>
              <span>{pt.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 階段篩選 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setSelectedStage('all')}
          className={`px-3 py-1 rounded text-xs ${
            selectedStage === 'all' ? 'bg-slate-600 text-white' : 'bg-slate-700/50 text-slate-400'
          }`}
        >
          全部階段
        </button>
        <button
          onClick={() => setSelectedStage('forming')}
          className={`px-3 py-1 rounded text-xs ${
            selectedStage === 'forming' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-700/50 text-slate-400'
          }`}
        >
          🔄 形成中
        </button>
        <button
          onClick={() => setSelectedStage('confirmed')}
          className={`px-3 py-1 rounded text-xs ${
            selectedStage === 'confirmed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-400'
          }`}
        >
          ✅ 已確認
        </button>
      </div>

      {/* 形態列表 */}
      <div className="space-y-4">
        {filteredPatterns.map((detected, idx) => {
          const patternInfo = PATTERN_TYPES[detected.pattern];

          return (
            <div
              key={idx}
              className={`rounded-lg p-4 border ${patternInfo.bg} border-slate-600/50`}
            >
              <div className="flex items-start gap-4">
                {/* 形態圖解 */}
                <div className={`w-24 h-16 ${patternInfo.color}`}>
                  <PatternDiagram patternType={detected.pattern} />
                </div>

                {/* 形態資訊 */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-lg ${patternInfo.color}`}>{patternInfo.icon}</span>
                    <span className="text-white font-medium">{patternInfo.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      detected.stage === 'confirmed'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {detected.stage === 'confirmed' ? '已確認' : '形成中'}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs ${patternInfo.bg} ${patternInfo.color}`}>
                      {patternInfo.signal}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 mb-2">
                    <span className="text-white">{detected.stockName}</span>
                    <span className="text-slate-500 text-sm">{detected.stockId}</span>
                    <span className="text-slate-500 text-sm">{detected.detectedDate}</span>
                  </div>

                  <p className="text-slate-400 text-sm mb-2">{patternInfo.description}</p>

                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <span className="text-slate-500">信心度:</span>
                      <span className="text-white font-medium">{detected.confidence}%</span>
                    </div>
                    {detected.targetPrice && (
                      <div className="flex items-center gap-1">
                        <span className="text-slate-500">目標價:</span>
                        <span className="text-emerald-400">${detected.targetPrice}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <span className="text-slate-500">停損:</span>
                      <span className="text-red-400">${detected.stopLoss}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-slate-500">可靠度:</span>
                      <span className="text-blue-400">{patternInfo.reliability}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {filteredPatterns.length === 0 && (
          <div className="text-center py-8">
            <span className="text-4xl">🔍</span>
            <p className="text-slate-400 mt-2">沒有符合條件的形態</p>
          </div>
        )}
      </div>

      {/* 形態說明 */}
      <div className="mt-6 p-4 bg-slate-700/30 rounded-lg">
        <h4 className="text-white font-medium mb-3">形態辨識說明</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {Object.values(PATTERN_TYPES).slice(0, 6).map(pt => (
            <div key={pt.id} className="flex items-center gap-2">
              <span>{pt.icon}</span>
              <span className={`text-sm ${pt.color}`}>{pt.name}</span>
              <span className="text-slate-500 text-xs">({pt.signal})</span>
            </div>
          ))}
        </div>
      </div>

      {/* 風險提示 */}
      <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-yellow-400">⚠️</span>
          <div className="text-yellow-300 text-sm">
            <p className="font-medium mb-1">風險提示</p>
            <ul className="text-xs space-y-0.5 text-yellow-300/80">
              <li>- 形態辨識僅供參考，不保證 100% 準確</li>
              <li>- 建議搭配其他技術指標綜合判斷</li>
              <li>- 務必設定停損點控制風險</li>
              <li>- 過去績效不代表未來表現</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatternRecognition;
