/**
 * UnifiedAlerts.jsx - V10.39 新增
 *
 * 整合價格警示與智能提醒功能的統一元件
 *
 * 安裝位置: stockbuddy-frontend/src/components/UnifiedAlerts.jsx
 *
 * 原本分離的功能:
 * - PriceAlert: 價格目標警示
 * - SmartAlerts: 技術指標提醒
 *
 * 整合後提供統一介面，透過 Tab 切換
 */

import { useState } from 'react';
import PriceAlert from './PriceAlert';
import SmartAlerts from './SmartAlerts';

const UnifiedAlerts = () => {
  const [activeMode, setActiveMode] = useState('price'); // 'price' | 'smart'

  const modes = [
    { id: 'price', label: '價格警示', icon: '🔔', description: '設定目標價格通知' },
    { id: 'smart', label: '智能提醒', icon: '⚡', description: '技術指標條件提醒' },
  ];

  return (
    <div className="space-y-4">
      {/* 標題區 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          🔔 提醒通知
        </h2>
        <span className="text-sm text-slate-400">
          管理您的股價與技術指標提醒
        </span>
      </div>

      {/* 模式切換 Tab */}
      <div className="flex gap-2 p-1 bg-slate-800/80 rounded-xl w-fit border border-slate-700">
        {modes.map((mode) => (
          <button
            key={mode.id}
            onClick={() => setActiveMode(mode.id)}
            className={`
              px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
              flex items-center gap-2
              ${activeMode === mode.id
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }
            `}
          >
            <span>{mode.icon}</span>
            <span>{mode.label}</span>
          </button>
        ))}
      </div>

      {/* 模式說明 */}
      <div className="text-sm text-slate-400 bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
        {activeMode === 'price' ? (
          <div className="flex items-start gap-2">
            <span className="text-lg">💡</span>
            <div>
              <span className="text-slate-300 font-medium">價格警示</span>
              <span className="text-slate-400">: 當股票達到您設定的目標價格時，系統會發送通知提醒您。適合追蹤特定價位的買賣點。</span>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-2">
            <span className="text-lg">💡</span>
            <div>
              <span className="text-slate-300 font-medium">智能提醒</span>
              <span className="text-slate-400">: 根據技術指標（如 RSI、MACD、KD 等）自動提醒，當指標達到設定條件時通知您。</span>
            </div>
          </div>
        )}
      </div>

      {/* 內容區域 */}
      <div className="bg-slate-800/30 rounded-xl border border-slate-700/50">
        {activeMode === 'price' ? (
          <PriceAlert />
        ) : (
          <SmartAlerts />
        )}
      </div>

      {/* 底部統計 */}
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-2 text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>啟用中的提醒會在滿足條件時通知您</span>
        </div>
      </div>
    </div>
  );
};

export default UnifiedAlerts;
