/**
 * StrategyTemplates.jsx - 策略範本庫
 * V10.34 新增
 *
 * 功能：
 * - 預設投資策略範本
 * - 策略條件說明
 * - 一鍵套用策略
 * - 自訂策略建立
 */

import React, { useState, useMemo } from 'react';

// 預設策略範本
const STRATEGY_TEMPLATES = [
  {
    id: 'value',
    name: '價值投資',
    icon: '💎',
    category: 'fundamental',
    difficulty: 'medium',
    riskLevel: 'low',
    description: '尋找被低估的優質股票，長期持有等待價值回歸',
    conditions: [
      { label: '本益比', operator: '<', value: 15, unit: '倍' },
      { label: '股價淨值比', operator: '<', value: 1.5, unit: '倍' },
      { label: '殖利率', operator: '>', value: 4, unit: '%' },
      { label: 'ROE', operator: '>', value: 10, unit: '%' },
    ],
    holdingPeriod: '1-3年',
    expectedReturn: '10-15%/年',
    tips: ['耐心等待好價位', '重視公司基本面', '避免追高'],
  },
  {
    id: 'growth',
    name: '成長投資',
    icon: '🚀',
    category: 'fundamental',
    difficulty: 'medium',
    riskLevel: 'high',
    description: '投資高成長潛力的公司，追求資本增值',
    conditions: [
      { label: '營收年增率', operator: '>', value: 20, unit: '%' },
      { label: 'EPS年增率', operator: '>', value: 15, unit: '%' },
      { label: '毛利率', operator: '>', value: 30, unit: '%' },
      { label: '研發費用率', operator: '>', value: 5, unit: '%' },
    ],
    holdingPeriod: '1-2年',
    expectedReturn: '20-30%/年',
    tips: ['關注產業趨勢', '接受較高波動', '設定停損'],
  },
  {
    id: 'dividend',
    name: '存股策略',
    icon: '🏦',
    category: 'income',
    difficulty: 'easy',
    riskLevel: 'low',
    description: '選擇穩定配息的股票，追求現金流收入',
    conditions: [
      { label: '連續配息年數', operator: '>', value: 5, unit: '年' },
      { label: '殖利率', operator: '>', value: 5, unit: '%' },
      { label: '配息率', operator: '<', value: 80, unit: '%' },
      { label: '填息率', operator: '>', value: 80, unit: '%' },
    ],
    holdingPeriod: '長期持有',
    expectedReturn: '5-8%/年',
    tips: ['定期定額投入', '股息再投資', '選擇穩定產業'],
  },
  {
    id: 'momentum',
    name: '動能策略',
    icon: '⚡',
    category: 'technical',
    difficulty: 'hard',
    riskLevel: 'high',
    description: '追蹤股價動能，順勢交易強勢股',
    conditions: [
      { label: 'RSI', operator: '>', value: 50, unit: '' },
      { label: '股價突破20日均線', operator: '=', value: true, unit: '' },
      { label: 'MACD', operator: '>', value: 0, unit: '' },
      { label: '成交量增加', operator: '>', value: 20, unit: '%' },
    ],
    holdingPeriod: '2週-2月',
    expectedReturn: '視市況',
    tips: ['嚴格執行停損', '順勢不逆勢', '控制單筆倉位'],
  },
  {
    id: 'contrarian',
    name: '逆向投資',
    icon: '🔄',
    category: 'technical',
    difficulty: 'hard',
    riskLevel: 'medium',
    description: '在市場恐慌時買入，在市場瘋狂時賣出',
    conditions: [
      { label: 'RSI', operator: '<', value: 30, unit: '' },
      { label: '股價跌幅', operator: '>', value: 20, unit: '%' },
      { label: '外資賣超', operator: '>', value: 3, unit: '日' },
      { label: '基本面良好', operator: '=', value: true, unit: '' },
    ],
    holdingPeriod: '3-6月',
    expectedReturn: '15-25%',
    tips: ['別接飛刀', '分批進場', '確認底部反轉'],
  },
  {
    id: 'etf',
    name: 'ETF 指數投資',
    icon: '📊',
    category: 'passive',
    difficulty: 'easy',
    riskLevel: 'low',
    description: '投資指數型ETF，獲取市場平均報酬',
    conditions: [
      { label: '管理費', operator: '<', value: 0.5, unit: '%' },
      { label: '追蹤誤差', operator: '<', value: 1, unit: '%' },
      { label: '成交量', operator: '>', value: 1000, unit: '張/日' },
      { label: '折溢價', operator: '<', value: 1, unit: '%' },
    ],
    holdingPeriod: '長期持有',
    expectedReturn: '7-10%/年',
    tips: ['定期定額', '長期持有', '不擇時進出'],
  },
  {
    id: 'breakout',
    name: '突破策略',
    icon: '💥',
    category: 'technical',
    difficulty: 'medium',
    riskLevel: 'high',
    description: '等待股價突破關鍵價位後進場',
    conditions: [
      { label: '突破前高', operator: '=', value: true, unit: '' },
      { label: '帶量突破', operator: '>', value: 50, unit: '%' },
      { label: '整理時間', operator: '>', value: 20, unit: '日' },
      { label: '趨勢向上', operator: '=', value: true, unit: '' },
    ],
    holdingPeriod: '1-4週',
    expectedReturn: '10-20%',
    tips: ['突破確認再進場', '設定突破無效停損', '關注量價配合'],
  },
  {
    id: 'swing',
    name: '波段操作',
    icon: '🌊',
    category: 'technical',
    difficulty: 'medium',
    riskLevel: 'medium',
    description: '利用股價波動做區間操作',
    conditions: [
      { label: '波動率', operator: '>', value: 15, unit: '%' },
      { label: '支撐位接近', operator: '<', value: 3, unit: '%' },
      { label: '壓力位距離', operator: '>', value: 10, unit: '%' },
      { label: 'KD低檔', operator: '<', value: 30, unit: '' },
    ],
    holdingPeriod: '1-4週',
    expectedReturn: '5-15%',
    tips: ['明確設定進出場點', '嚴守紀律', '控制槓桿'],
  },
];

// 分類定義
const CATEGORIES = {
  all: { label: '全部', icon: '📋' },
  fundamental: { label: '基本面', icon: '📊' },
  technical: { label: '技術面', icon: '📈' },
  income: { label: '收益型', icon: '💰' },
  passive: { label: '被動型', icon: '🔄' },
};

// 難度定義
const DIFFICULTY_STYLES = {
  easy: { label: '入門', color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
  medium: { label: '進階', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
  hard: { label: '高級', color: 'text-red-400', bg: 'bg-red-500/20' },
};

// 風險等級定義
const RISK_STYLES = {
  low: { label: '低風險', color: 'text-emerald-400', icon: '🟢' },
  medium: { label: '中風險', color: 'text-yellow-400', icon: '🟡' },
  high: { label: '高風險', color: 'text-red-400', icon: '🔴' },
};

const StrategyTemplates = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStrategy, setSelectedStrategy] = useState(null);

  // 篩選策略
  const filteredStrategies = useMemo(() => {
    if (selectedCategory === 'all') return STRATEGY_TEMPLATES;
    return STRATEGY_TEMPLATES.filter(s => s.category === selectedCategory);
  }, [selectedCategory]);

  // 套用策略
  const applyStrategy = (strategy) => {
    // 這裡可以跳轉到篩選器並套用條件
    alert(`已套用「${strategy.name}」策略！\n可至選股篩選器查看符合條件的股票。`);
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📚</span>
          <span>策略範本庫</span>
        </h2>

        <span className="text-slate-400 text-sm">
          共 {STRATEGY_TEMPLATES.length} 種策略
        </span>
      </div>

      {/* 分類篩選 */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {Object.entries(CATEGORIES).map(([key, cat]) => (
          <button
            key={key}
            onClick={() => setSelectedCategory(key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-2 ${
              selectedCategory === key
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <span>{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* 策略列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredStrategies.map(strategy => {
          const difficulty = DIFFICULTY_STYLES[strategy.difficulty];
          const risk = RISK_STYLES[strategy.riskLevel];

          return (
            <div
              key={strategy.id}
              className="bg-slate-700/30 rounded-lg p-4 hover:bg-slate-700/50 transition-colors cursor-pointer"
              onClick={() => setSelectedStrategy(
                selectedStrategy?.id === strategy.id ? null : strategy
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{strategy.icon}</span>
                  <div>
                    <h3 className="text-white font-medium">{strategy.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 rounded text-xs ${difficulty.bg} ${difficulty.color}`}>
                        {difficulty.label}
                      </span>
                      <span className={`text-xs ${risk.color}`}>
                        {risk.icon} {risk.label}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <p className="text-slate-400 text-sm mb-3">{strategy.description}</p>

              <div className="flex items-center gap-4 text-xs text-slate-500 mb-3">
                <span>持有期間: {strategy.holdingPeriod}</span>
                <span>預期報酬: {strategy.expectedReturn}</span>
              </div>

              {/* 展開詳情 */}
              {selectedStrategy?.id === strategy.id && (
                <div className="mt-4 pt-4 border-t border-slate-600">
                  {/* 條件列表 */}
                  <div className="mb-4">
                    <h4 className="text-white text-sm font-medium mb-2">篩選條件</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {strategy.conditions.map((cond, idx) => (
                        <div key={idx} className="bg-slate-800/50 rounded px-2 py-1.5 text-xs">
                          <span className="text-slate-400">{cond.label}</span>
                          <span className="text-white ml-1">
                            {cond.operator} {typeof cond.value === 'boolean' ? '是' : cond.value}{cond.unit}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 操作建議 */}
                  <div className="mb-4">
                    <h4 className="text-white text-sm font-medium mb-2">操作建議</h4>
                    <ul className="space-y-1">
                      {strategy.tips.map((tip, idx) => (
                        <li key={idx} className="text-slate-400 text-xs flex items-center gap-1">
                          <span className="text-blue-400">•</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 套用按鈕 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      applyStrategy(strategy);
                    }}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                  >
                    套用此策略
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 說明 */}
      <div className="mt-6 p-4 bg-slate-700/30 rounded-lg">
        <h4 className="text-white font-medium mb-3">策略選擇指南</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <h5 className="text-emerald-400 font-medium mb-1">🟢 新手適用</h5>
            <p className="text-slate-400 text-xs">存股策略、ETF指數投資，風險較低，適合長期持有</p>
          </div>
          <div>
            <h5 className="text-yellow-400 font-medium mb-1">🟡 進階適用</h5>
            <p className="text-slate-400 text-xs">價值投資、成長投資，需要基本面分析能力</p>
          </div>
          <div>
            <h5 className="text-red-400 font-medium mb-1">🔴 高階適用</h5>
            <p className="text-slate-400 text-xs">動能策略、逆向投資，需要豐富交易經驗</p>
          </div>
        </div>
      </div>

      {/* 風險提示 */}
      <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-yellow-400">⚠️</span>
          <div className="text-yellow-300 text-sm">
            <p className="font-medium mb-1">風險提示</p>
            <p className="text-xs text-yellow-300/80">
              所有策略範本僅供參考學習，不構成投資建議。投資有風險，請依個人風險承受度審慎評估。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyTemplates;
