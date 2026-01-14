/**
 * SmartAlerts.jsx - 智能提醒系統
 * V10.30 新增
 *
 * 功能：
 * - 價格到達提醒
 * - 漲跌幅異常提醒
 * - 成交量異常提醒
 * - 技術指標訊號提醒
 */

import React, { useState, useEffect, useCallback } from 'react';

// 提醒類型
const ALERT_TYPES = {
  price: {
    id: 'price',
    label: '價格提醒',
    icon: '💰',
    desc: '股價到達目標價時通知',
  },
  change: {
    id: 'change',
    label: '漲跌幅提醒',
    icon: '📊',
    desc: '漲跌幅超過設定值時通知',
  },
  volume: {
    id: 'volume',
    label: '成交量提醒',
    icon: '📈',
    desc: '成交量異常放大時通知',
  },
  technical: {
    id: 'technical',
    label: '技術指標提醒',
    icon: '📉',
    desc: '黃金交叉、超買超賣等訊號',
  },
};

// 技術指標訊號類型
const TECHNICAL_SIGNALS = [
  { id: 'golden_cross', label: 'MACD 黃金交叉', desc: 'MACD 線突破信號線' },
  { id: 'death_cross', label: 'MACD 死亡交叉', desc: 'MACD 線跌破信號線' },
  { id: 'rsi_oversold', label: 'RSI 超賣', desc: 'RSI < 30' },
  { id: 'rsi_overbought', label: 'RSI 超買', desc: 'RSI > 70' },
  { id: 'kd_golden', label: 'KD 黃金交叉', desc: 'K 線突破 D 線' },
  { id: 'kd_death', label: 'KD 死亡交叉', desc: 'K 線跌破 D 線' },
  { id: 'bb_lower', label: '觸及布林下軌', desc: '價格觸及布林通道下軌' },
  { id: 'bb_upper', label: '觸及布林上軌', desc: '價格觸及布林通道上軌' },
];

// localStorage key
const SMART_ALERTS_KEY = 'stockbuddy_smart_alerts';

const SmartAlerts = ({ stocks = [], onTrigger }) => {
  const [alerts, setAlerts] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState(null);
  const [triggeredAlerts, setTriggeredAlerts] = useState([]);

  // 新增提醒表單狀態
  const [formData, setFormData] = useState({
    type: 'price',
    stockId: '',
    stockName: '',
    condition: 'above', // above | below
    value: '',
    technicalSignals: [],
    enabled: true,
  });

  // 載入提醒
  useEffect(() => {
    const saved = localStorage.getItem(SMART_ALERTS_KEY);
    if (saved) {
      try {
        setAlerts(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load smart alerts:', e);
      }
    }
  }, []);

  // 儲存提醒
  const saveAlerts = useCallback((newAlerts) => {
    setAlerts(newAlerts);
    localStorage.setItem(SMART_ALERTS_KEY, JSON.stringify(newAlerts));
  }, []);

  // 檢查提醒條件
  useEffect(() => {
    if (!stocks || stocks.length === 0) return;

    const triggered = [];

    alerts.forEach((alert) => {
      if (!alert.enabled) return;

      const stock = stocks.find(
        (s) => s.stock_id === alert.stockId || s.symbol === alert.stockId
      );
      if (!stock) return;

      let shouldTrigger = false;
      let message = '';

      switch (alert.type) {
        case 'price':
          if (alert.condition === 'above' && stock.price >= alert.value) {
            shouldTrigger = true;
            message = `${alert.stockName} 股價已突破 $${alert.value}，目前 $${stock.price}`;
          } else if (alert.condition === 'below' && stock.price <= alert.value) {
            shouldTrigger = true;
            message = `${alert.stockName} 股價已跌破 $${alert.value}，目前 $${stock.price}`;
          }
          break;

        case 'change':
          const changePercent = Math.abs(stock.change_percent || 0) * 100;
          if (changePercent >= alert.value) {
            shouldTrigger = true;
            const direction = stock.change_percent >= 0 ? '上漲' : '下跌';
            message = `${alert.stockName} ${direction} ${changePercent.toFixed(2)}%，超過設定的 ${alert.value}%`;
          }
          break;

        case 'volume':
          if (stock.volume_ratio && stock.volume_ratio >= alert.value) {
            shouldTrigger = true;
            message = `${alert.stockName} 成交量放大 ${stock.volume_ratio.toFixed(1)} 倍，超過設定的 ${alert.value} 倍`;
          }
          break;

        case 'technical':
          // 技術指標檢查（需要後端支援）
          if (stock.technical) {
            alert.technicalSignals?.forEach((signal) => {
              // 這裡可以根據後端返回的技術指標數據進行判斷
              // 暫時跳過，待後端整合
            });
          }
          break;
      }

      if (shouldTrigger) {
        triggered.push({
          ...alert,
          message,
          timestamp: new Date().toISOString(),
        });
      }
    });

    if (triggered.length > 0) {
      setTriggeredAlerts((prev) => [...prev, ...triggered]);
      onTrigger?.(triggered);
    }
  }, [stocks, alerts, onTrigger]);

  // 新增提醒
  const handleAddAlert = () => {
    if (!formData.stockId || !formData.value) return;

    const newAlert = {
      id: Date.now(),
      ...formData,
      createdAt: new Date().toISOString(),
    };

    saveAlerts([...alerts, newAlert]);
    setShowAddModal(false);
    resetForm();
  };

  // 刪除提醒
  const handleDeleteAlert = (alertId) => {
    saveAlerts(alerts.filter((a) => a.id !== alertId));
  };

  // 切換啟用狀態
  const handleToggleAlert = (alertId) => {
    saveAlerts(
      alerts.map((a) =>
        a.id === alertId ? { ...a, enabled: !a.enabled } : a
      )
    );
  };

  // 重設表單
  const resetForm = () => {
    setFormData({
      type: 'price',
      stockId: '',
      stockName: '',
      condition: 'above',
      value: '',
      technicalSignals: [],
      enabled: true,
    });
    setEditingAlert(null);
  };

  // 清除已觸發提醒
  const clearTriggered = () => {
    setTriggeredAlerts([]);
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* 標題 */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>🔔</span> 智能提醒
          {alerts.filter((a) => a.enabled).length > 0 && (
            <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
              {alerts.filter((a) => a.enabled).length} 個啟用
            </span>
          )}
        </h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors"
        >
          + 新增提醒
        </button>
      </div>

      {/* 已觸發提醒 */}
      {triggeredAlerts.length > 0 && (
        <div className="p-4 bg-yellow-500/10 border-b border-yellow-500/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-yellow-400 font-medium">⚡ 已觸發提醒</span>
            <button
              onClick={clearTriggered}
              className="text-yellow-400 text-sm hover:text-yellow-300"
            >
              清除全部
            </button>
          </div>
          <div className="space-y-2">
            {triggeredAlerts.slice(-5).map((alert, index) => (
              <div
                key={`${alert.id}-${index}`}
                className="p-2 bg-yellow-500/20 rounded-lg text-yellow-200 text-sm"
              >
                {alert.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 提醒列表 */}
      <div className="p-4">
        {alerts.length === 0 ? (
          <div className="text-center text-slate-500 py-8">
            <p>尚未設定任何提醒</p>
            <p className="text-sm mt-2">點擊「新增提醒」開始設定</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border transition-colors ${
                  alert.enabled
                    ? 'bg-slate-700/50 border-slate-600'
                    : 'bg-slate-800/50 border-slate-700 opacity-60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{ALERT_TYPES[alert.type]?.icon}</span>
                    <div>
                      <div className="text-white font-medium">
                        {alert.stockName} ({alert.stockId})
                      </div>
                      <div className="text-slate-400 text-sm">
                        {alert.type === 'price' && (
                          <>
                            {alert.condition === 'above' ? '突破' : '跌破'} ${alert.value}
                          </>
                        )}
                        {alert.type === 'change' && (
                          <>漲跌幅超過 {alert.value}%</>
                        )}
                        {alert.type === 'volume' && (
                          <>成交量超過 {alert.value} 倍</>
                        )}
                        {alert.type === 'technical' && (
                          <>技術指標訊號</>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="relative inline-flex cursor-pointer">
                      <input
                        type="checkbox"
                        checked={alert.enabled}
                        onChange={() => handleToggleAlert(alert.id)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-600 rounded-full peer peer-checked:bg-blue-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                    </label>
                    <button
                      onClick={() => handleDeleteAlert(alert.id)}
                      className="p-1.5 hover:bg-slate-600 rounded text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 新增提醒 Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-white mb-4">新增智能提醒</h3>

            {/* 提醒類型 */}
            <div className="mb-4">
              <label className="block text-slate-400 text-sm mb-2">提醒類型</label>
              <div className="grid grid-cols-2 gap-2">
                {Object.values(ALERT_TYPES).map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setFormData({ ...formData, type: type.id })}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      formData.type === type.id
                        ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                        : 'bg-slate-700/50 border-slate-600 text-slate-300 hover:border-slate-500'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{type.icon}</span>
                      <span className="text-sm">{type.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* 股票代號 */}
            <div className="mb-4">
              <label className="block text-slate-400 text-sm mb-2">股票代號</label>
              <input
                type="text"
                value={formData.stockId}
                onChange={(e) => setFormData({ ...formData, stockId: e.target.value.toUpperCase() })}
                placeholder="例：2330"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* 股票名稱 */}
            <div className="mb-4">
              <label className="block text-slate-400 text-sm mb-2">股票名稱</label>
              <input
                type="text"
                value={formData.stockName}
                onChange={(e) => setFormData({ ...formData, stockName: e.target.value })}
                placeholder="例：台積電"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* 條件設定 */}
            {formData.type === 'price' && (
              <div className="mb-4 grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 text-sm mb-2">條件</label>
                  <select
                    value={formData.condition}
                    onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  >
                    <option value="above">突破 (高於)</option>
                    <option value="below">跌破 (低於)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 text-sm mb-2">目標價</label>
                  <input
                    type="number"
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: Number(e.target.value) })}
                    placeholder="0"
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            )}

            {formData.type === 'change' && (
              <div className="mb-4">
                <label className="block text-slate-400 text-sm mb-2">漲跌幅閾值 (%)</label>
                <input
                  type="number"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: Number(e.target.value) })}
                  placeholder="例：5"
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}

            {formData.type === 'volume' && (
              <div className="mb-4">
                <label className="block text-slate-400 text-sm mb-2">成交量倍數</label>
                <input
                  type="number"
                  value={formData.value}
                  onChange={(e) => setFormData({ ...formData, value: Number(e.target.value) })}
                  placeholder="例：2"
                  min="1"
                  step="0.5"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
                <p className="text-slate-500 text-xs mt-1">相對於近期平均成交量的倍數</p>
              </div>
            )}

            {formData.type === 'technical' && (
              <div className="mb-4">
                <label className="block text-slate-400 text-sm mb-2">技術指標訊號</label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {TECHNICAL_SIGNALS.map((signal) => (
                    <label key={signal.id} className="flex items-center gap-2 p-2 bg-slate-700/50 rounded-lg cursor-pointer hover:bg-slate-700">
                      <input
                        type="checkbox"
                        checked={formData.technicalSignals.includes(signal.id)}
                        onChange={(e) => {
                          const newSignals = e.target.checked
                            ? [...formData.technicalSignals, signal.id]
                            : formData.technicalSignals.filter((s) => s !== signal.id);
                          setFormData({ ...formData, technicalSignals: newSignals });
                        }}
                        className="rounded bg-slate-600 border-slate-500 text-blue-500 focus:ring-blue-500"
                      />
                      <div>
                        <div className="text-white text-sm">{signal.label}</div>
                        <div className="text-slate-400 text-xs">{signal.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* 按鈕 */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  resetForm();
                }}
                className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddAlert}
                disabled={!formData.stockId || (!formData.value && formData.type !== 'technical')}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                確認新增
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartAlerts;
