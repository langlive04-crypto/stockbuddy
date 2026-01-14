/**
 * 價格警示組件 V10.19
 *
 * 功能：
 * - 設定價格警示
 * - 警示列表管理
 * - 即時檢查警示觸發
 * - 警示通知
 */

import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../config';
const ALERTS_STORAGE_KEY = 'stockbuddy_price_alerts';

// 警示類型配置
const ALERT_TYPES = {
  above: { label: '突破價格', icon: '📈', color: 'text-red-400' },
  below: { label: '跌破價格', icon: '📉', color: 'text-emerald-400' },
  percent_up: { label: '漲幅達標', icon: '🚀', color: 'text-red-400' },
  percent_down: { label: '跌幅達標', icon: '⚠️', color: 'text-emerald-400' },
};

// 警示卡片
const AlertCard = ({ alert, onDelete, onCheck, checking }) => {
  const typeConfig = ALERT_TYPES[alert.alert_type] || ALERT_TYPES.above;
  const isTriggered = alert.status === 'triggered';

  return (
    <div
      className={`bg-slate-800/50 rounded-xl p-4 border ${
        isTriggered
          ? 'border-amber-500/50 bg-amber-500/10'
          : 'border-slate-700'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{typeConfig.icon}</span>
          <div>
            <div className="text-white font-semibold">{alert.stock_id}</div>
            <div className="text-slate-500 text-xs">{typeConfig.label}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isTriggered && (
            <span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs">
              已觸發
            </span>
          )}
          <button
            onClick={() => onDelete(alert.id)}
            className="text-slate-500 hover:text-red-400 transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 目標條件 */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        {alert.target_price && (
          <div>
            <div className="text-slate-500 text-xs">目標價格</div>
            <div className={`font-medium ${typeConfig.color}`}>
              ${alert.target_price}
            </div>
          </div>
        )}
        {alert.target_percent && (
          <div>
            <div className="text-slate-500 text-xs">目標幅度</div>
            <div className={`font-medium ${typeConfig.color}`}>
              {alert.target_percent}%
            </div>
          </div>
        )}
        {alert.current_price && (
          <div>
            <div className="text-slate-500 text-xs">當前價格</div>
            <div className="text-white font-medium">${alert.current_price}</div>
          </div>
        )}
        {alert.base_price && (
          <div>
            <div className="text-slate-500 text-xs">基準價格</div>
            <div className="text-slate-400">${alert.base_price}</div>
          </div>
        )}
      </div>

      {/* 觸發訊息 */}
      {alert.message && (
        <div className="p-2 bg-amber-500/10 rounded text-amber-400 text-sm mb-3">
          {alert.message}
        </div>
      )}

      {/* 建立時間 */}
      <div className="text-slate-500 text-xs">
        建立於 {new Date(alert.created_at).toLocaleString()}
      </div>
    </div>
  );
};

// 新增警示表單
const AddAlertForm = ({ onAdd, onCancel }) => {
  const [stockId, setStockId] = useState('');
  const [alertType, setAlertType] = useState('above');
  const [targetPrice, setTargetPrice] = useState('');
  const [targetPercent, setTargetPercent] = useState('');
  const [basePrice, setBasePrice] = useState('');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [loading, setLoading] = useState(false);

  const isPriceType = alertType === 'above' || alertType === 'below';

  // 取得當前價格
  const fetchCurrentPrice = async () => {
    if (!stockId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/stocks/alerts/price/${stockId}`);
      const data = await res.json();
      if (data.success) {
        setCurrentPrice(data.price);
        if (!basePrice) {
          setBasePrice(data.price?.toString() || '');
        }
      }
    } catch (err) {
      console.error('取得價格失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (stockId.length >= 4) {
      const timer = setTimeout(fetchCurrentPrice, 500);
      return () => clearTimeout(timer);
    }
  }, [stockId]);

  const handleSubmit = () => {
    if (!stockId) return;

    const alert = {
      id: `alert_${Date.now()}`,
      stock_id: stockId.toUpperCase(),
      alert_type: alertType,
      target_price: isPriceType ? parseFloat(targetPrice) : null,
      target_percent: !isPriceType ? parseFloat(targetPercent) : null,
      base_price: !isPriceType ? parseFloat(basePrice) : null,
      current_price: currentPrice,
      created_at: new Date().toISOString(),
      status: 'active',
    };

    onAdd(alert);
  };

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-blue-500/30">
      <h3 className="text-white font-semibold mb-4">新增價格警示</h3>

      <div className="space-y-4">
        {/* 股票代號 */}
        <div>
          <label className="text-slate-400 text-sm block mb-1">股票代號</label>
          <input
            type="text"
            value={stockId}
            onChange={(e) => setStockId(e.target.value.toUpperCase())}
            placeholder="例: 2330"
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
          />
          {currentPrice && (
            <div className="mt-1 text-sm text-slate-400">
              當前價格: <span className="text-white">${currentPrice}</span>
            </div>
          )}
        </div>

        {/* 警示類型 */}
        <div>
          <label className="text-slate-400 text-sm block mb-1">警示類型</label>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(ALERT_TYPES).map(([key, config]) => (
              <button
                key={key}
                onClick={() => setAlertType(key)}
                className={`p-2 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                  alertType === key
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                <span>{config.icon}</span>
                <span>{config.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 目標價格/百分比 */}
        {isPriceType ? (
          <div>
            <label className="text-slate-400 text-sm block mb-1">目標價格</label>
            <input
              type="number"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              placeholder={`例: ${currentPrice ? (alertType === 'above' ? Math.round(currentPrice * 1.05) : Math.round(currentPrice * 0.95)) : ''}`}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
            />
          </div>
        ) : (
          <>
            <div>
              <label className="text-slate-400 text-sm block mb-1">目標幅度 (%)</label>
              <input
                type="number"
                value={targetPercent}
                onChange={(e) => setTargetPercent(e.target.value)}
                placeholder="例: 5"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm block mb-1">基準價格</label>
              <input
                type="number"
                value={basePrice}
                onChange={(e) => setBasePrice(e.target.value)}
                placeholder="計算漲跌幅的基準"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 outline-none"
              />
            </div>
          </>
        )}

        {/* 按鈕 */}
        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={!stockId || (isPriceType ? !targetPrice : !targetPercent)}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
          >
            建立警示
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  );
};

// 主組件
const PriceAlert = () => {
  const [alerts, setAlerts] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [checking, setChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  // 載入警示
  useEffect(() => {
    const saved = localStorage.getItem(ALERTS_STORAGE_KEY);
    if (saved) {
      try {
        setAlerts(JSON.parse(saved));
      } catch (e) {
        console.error('載入警示失敗:', e);
      }
    }
  }, []);

  // 儲存警示
  useEffect(() => {
    localStorage.setItem(ALERTS_STORAGE_KEY, JSON.stringify(alerts));
  }, [alerts]);

  // 新增警示
  const handleAddAlert = (alert) => {
    setAlerts([alert, ...alerts]);
    setShowAddForm(false);
  };

  // 刪除警示
  const handleDeleteAlert = (alertId) => {
    setAlerts(alerts.filter((a) => a.id !== alertId));
  };

  // 檢查所有警示
  const checkAllAlerts = useCallback(async () => {
    const activeAlerts = alerts.filter((a) => a.status === 'active');
    if (activeAlerts.length === 0) return;

    setChecking(true);

    try {
      const res = await fetch(`${API_BASE}/api/stocks/alerts/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(activeAlerts),
      });

      const data = await res.json();

      if (data.success) {
        // 更新警示狀態
        const updatedAlerts = alerts.map((alert) => {
          const result = data.results.find((r) => r.alert_id === alert.id);
          if (result) {
            return {
              ...alert,
              current_price: result.current_price,
              status: result.is_triggered ? 'triggered' : alert.status,
              message: result.message,
              last_checked: new Date().toISOString(),
            };
          }
          return alert;
        });

        setAlerts(updatedAlerts);
        setLastChecked(new Date());

        // 顯示觸發通知
        if (data.triggered_count > 0) {
          data.triggered.forEach((t) => {
            if (Notification.permission === 'granted') {
              new Notification('StockBuddy 價格警示', {
                body: t.message,
                icon: '📈',
              });
            }
          });
        }
      }
    } catch (err) {
      console.error('檢查警示失敗:', err);
    } finally {
      setChecking(false);
    }
  }, [alerts]);

  // 請求通知權限
  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        new Notification('StockBuddy', {
          body: '通知已啟用，當警示觸發時會收到通知',
        });
      }
    }
  };

  // 自動檢查（每分鐘）
  useEffect(() => {
    const interval = setInterval(checkAllAlerts, 60000);
    return () => clearInterval(interval);
  }, [checkAllAlerts]);

  const activeAlerts = alerts.filter((a) => a.status === 'active');
  const triggeredAlerts = alerts.filter((a) => a.status === 'triggered');

  return (
    <div className="space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🔔</span> 價格警示
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={checkAllAlerts}
            disabled={checking || activeAlerts.length === 0}
            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-slate-300 rounded-lg text-sm transition-colors"
          >
            {checking ? '檢查中...' : '🔄 檢查'}
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors"
          >
            + 新增警示
          </button>
        </div>
      </div>

      {/* 統計 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div className="text-slate-400 text-sm">活躍警示</div>
          <div className="text-2xl font-bold text-white">{activeAlerts.length}</div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-amber-500/30">
          <div className="text-slate-400 text-sm">已觸發</div>
          <div className="text-2xl font-bold text-amber-400">{triggeredAlerts.length}</div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div className="text-slate-400 text-sm">總警示數</div>
          <div className="text-2xl font-bold text-white">{alerts.length}</div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div className="text-slate-400 text-sm">最後檢查</div>
          <div className="text-sm text-white">
            {lastChecked ? lastChecked.toLocaleTimeString() : '尚未檢查'}
          </div>
        </div>
      </div>

      {/* 通知提示 */}
      {'Notification' in window && Notification.permission !== 'granted' && (
        <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-3 flex items-center justify-between">
          <span className="text-blue-400 text-sm">啟用通知以在警示觸發時收到提醒</span>
          <button
            onClick={requestNotificationPermission}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm"
          >
            啟用通知
          </button>
        </div>
      )}

      {/* 新增表單 */}
      {showAddForm && (
        <AddAlertForm
          onAdd={handleAddAlert}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      {/* 已觸發警示 */}
      {triggeredAlerts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-amber-400 font-semibold flex items-center gap-2">
            <span>⚠️</span> 已觸發警示
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {triggeredAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onDelete={handleDeleteAlert}
                onCheck={checkAllAlerts}
                checking={checking}
              />
            ))}
          </div>
        </div>
      )}

      {/* 活躍警示 */}
      {activeAlerts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-white font-semibold">活躍警示</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onDelete={handleDeleteAlert}
                onCheck={checkAllAlerts}
                checking={checking}
              />
            ))}
          </div>
        </div>
      )}

      {/* 空狀態 */}
      {alerts.length === 0 && !showAddForm && (
        <div className="text-center py-12 text-slate-500">
          <div className="text-4xl mb-4">🔔</div>
          <p>尚無價格警示</p>
          <p className="text-sm mt-2">點擊「新增警示」開始設定</p>
        </div>
      )}

      {/* 說明 */}
      <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50 text-sm text-slate-400">
        <h4 className="text-white font-medium mb-2">💡 使用說明</h4>
        <ul className="list-disc list-inside space-y-1">
          <li>突破價格：當股價上漲到目標價時觸發</li>
          <li>跌破價格：當股價下跌到目標價時觸發</li>
          <li>漲幅達標：當漲幅達到目標百分比時觸發</li>
          <li>跌幅達標：當跌幅達到目標百分比時觸發</li>
          <li>警示每分鐘自動檢查一次，也可手動點擊檢查</li>
        </ul>
      </div>
    </div>
  );
};

export default PriceAlert;
