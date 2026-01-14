/**
 * UnifiedPerformance.jsx - V10.39 新增
 *
 * 整合績效追蹤與歷史績效功能的統一元件
 *
 * 安裝位置: stockbuddy-frontend/src/components/UnifiedPerformance.jsx
 *
 * 整合前:
 * - PerformanceTracker: 追蹤 AI 推薦的後續表現
 * - HistoricalPerformance: AI 推薦歷史準確率統計
 *
 * 整合後:
 * - 統一介面，透過 Tab 切換不同視圖
 */

import { useState } from 'react';
import PerformanceTracker from './PerformanceTracker';
import HistoricalPerformance from './HistoricalPerformance';

const UnifiedPerformance = () => {
  const [activeTab, setActiveTab] = useState('tracker');

  const tabs = [
    {
      id: 'tracker',
      label: '推薦追蹤',
      icon: '📈',
      description: '追蹤 AI 推薦的後續表現'
    },
    {
      id: 'history',
      label: '歷史績效',
      icon: '📊',
      description: 'AI 推薦準確率驗證'
    },
  ];

  return (
    <div className="space-y-4">
      {/* 標題區 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          📈 績效驗證
        </h2>
        <span className="text-sm text-slate-400">
          追蹤與驗證 AI 推薦的表現
        </span>
      </div>

      {/* Tab 切換 */}
      <div className="flex gap-2 p-1 bg-slate-800/80 rounded-xl w-fit border border-slate-700">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
              flex items-center gap-2
              ${activeTab === tab.id
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }
            `}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab 說明 */}
      <div className="text-sm text-slate-400 bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
        <div className="flex items-start gap-2">
          <span className="text-lg">💡</span>
          <div>
            <span className="text-slate-300 font-medium">
              {tabs.find(t => t.id === activeTab)?.label}
            </span>
            <span className="text-slate-400">
              : {tabs.find(t => t.id === activeTab)?.description}
            </span>
          </div>
        </div>
      </div>

      {/* 內容區域 */}
      <div className="bg-slate-800/30 rounded-xl border border-slate-700/50 overflow-hidden">
        {activeTab === 'tracker' && <PerformanceTracker />}
        {activeTab === 'history' && <HistoricalPerformance />}
      </div>

      {/* 底部統計摘要 */}
      <div className="flex gap-4 text-sm text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>數據每日自動更新</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          <span>點擊股票可查看詳情</span>
        </div>
      </div>
    </div>
  );
};

export default UnifiedPerformance;
