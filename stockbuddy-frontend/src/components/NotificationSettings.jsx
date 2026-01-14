/**
 * NotificationSettings.jsx - 通知設定面板
 * V10.28 新增
 *
 * 功能：
 * - 通知權限管理
 * - 通知類型設定
 * - 通知歷史查看
 */

import React, { useState } from 'react';
import useNotifications from '../hooks/useNotifications';

const NotificationSettings = ({ isOpen, onClose }) => {
  const {
    isSupported,
    permission,
    settings,
    history,
    unreadCount,
    requestPermission,
    updateSettings,
    markAsRead,
    clearHistory,
    sendNotification,
  } = useNotifications();

  const [activeTab, setActiveTab] = useState('settings');

  // 處理權限請求
  const handleRequestPermission = async () => {
    const result = await requestPermission();
    if (!result.success) {
      alert(result.error);
    }
  };

  // 測試通知
  const handleTestNotification = () => {
    sendNotification('🧪 測試通知', {
      body: '如果您看到這則通知，表示通知功能正常運作！',
      type: 'test',
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div
        className="bg-slate-800 rounded-xl border border-slate-700 max-w-lg w-full max-h-[80vh] overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 標題 */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🔔</span> 通知設定
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                {unreadCount}
              </span>
            )}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* 分頁 */}
        <div className="flex border-b border-slate-700">
          {[
            { key: 'settings', label: '設定', icon: '⚙️' },
            { key: 'history', label: '歷史', icon: '📜' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* 內容 */}
        <div className="p-4 overflow-y-auto max-h-[50vh]">
          {activeTab === 'settings' ? (
            <div className="space-y-4">
              {/* 瀏覽器支援狀態 */}
              {!isSupported ? (
                <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-red-400">
                    <span>⚠️</span>
                    <span>您的瀏覽器不支援通知功能</span>
                  </div>
                </div>
              ) : permission === 'denied' ? (
                <div className="p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-yellow-400">
                    <span>⚠️</span>
                    <span>通知權限已被拒絕，請在瀏覽器設定中開啟</span>
                  </div>
                </div>
              ) : permission !== 'granted' ? (
                <div className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-blue-400">
                      <span>💡</span>
                      <span>啟用通知以接收價格警示</span>
                    </div>
                    <button
                      onClick={handleRequestPermission}
                      className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors"
                    >
                      啟用通知
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-emerald-500/20 border border-emerald-500/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-emerald-400">
                      <span>✅</span>
                      <span>通知已啟用</span>
                    </div>
                    <button
                      onClick={handleTestNotification}
                      className="px-3 py-1.5 bg-slate-600 hover:bg-slate-500 text-white text-sm rounded-lg transition-colors"
                    >
                      測試通知
                    </button>
                  </div>
                </div>
              )}

              {/* 通知開關 */}
              <div className="space-y-3">
                <h3 className="text-white font-medium">通知類型</h3>

                {/* 總開關 */}
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div>
                    <div className="text-white">啟用通知</div>
                    <div className="text-slate-400 text-sm">總開關</div>
                  </div>
                  <label className="relative inline-flex cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.enabled}
                      onChange={(e) => updateSettings('enabled', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-checked:bg-blue-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                  </label>
                </div>

                {/* 價格警示 */}
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div>
                    <div className="text-white">📈 價格警示</div>
                    <div className="text-slate-400 text-sm">當股價觸及目標價時通知</div>
                  </div>
                  <label className="relative inline-flex cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.priceAlerts}
                      onChange={(e) => updateSettings('priceAlerts', e.target.checked)}
                      disabled={!settings.enabled}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-checked:bg-blue-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all disabled:opacity-50"></div>
                  </label>
                </div>

                {/* 市場開盤 */}
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div>
                    <div className="text-white">🔔 市場開盤提醒</div>
                    <div className="text-slate-400 text-sm">台股/美股開盤時通知</div>
                  </div>
                  <label className="relative inline-flex cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.marketOpen}
                      onChange={(e) => updateSettings('marketOpen', e.target.checked)}
                      disabled={!settings.enabled}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-checked:bg-blue-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                  </label>
                </div>

                {/* AI 推薦 */}
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div>
                    <div className="text-white">🎯 AI 推薦通知</div>
                    <div className="text-slate-400 text-sm">每日 AI 精選股票通知</div>
                  </div>
                  <label className="relative inline-flex cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.recommendations}
                      onChange={(e) => updateSettings('recommendations', e.target.checked)}
                      disabled={!settings.enabled}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-checked:bg-blue-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                  </label>
                </div>

                {/* 音效 */}
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div>
                    <div className="text-white">🔊 通知音效</div>
                    <div className="text-slate-400 text-sm">播放通知提示音</div>
                  </div>
                  <label className="relative inline-flex cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.sound}
                      onChange={(e) => updateSettings('sound', e.target.checked)}
                      disabled={!settings.enabled}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-600 rounded-full peer peer-checked:bg-blue-500 peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
                  </label>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* 歷史列表 */}
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-white font-medium">通知歷史</h3>
                {history.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="text-slate-400 hover:text-red-400 text-sm"
                  >
                    清除全部
                  </button>
                )}
              </div>

              {history.length === 0 ? (
                <div className="text-center text-slate-500 py-8">暫無通知記錄</div>
              ) : (
                <div className="space-y-2">
                  {[...history].reverse().map((item) => (
                    <div
                      key={item.id}
                      onClick={() => markAsRead(item.id)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        item.read
                          ? 'bg-slate-700/30 text-slate-400'
                          : 'bg-slate-700/50 text-white'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">{item.title}</span>
                        {!item.read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </div>
                      <div className="text-sm opacity-70">{item.body}</div>
                      <div className="text-xs opacity-50 mt-1">
                        {new Date(item.timestamp).toLocaleString('zh-TW')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 底部 */}
        <div className="p-4 border-t border-slate-700 bg-slate-800/50">
          <button
            onClick={onClose}
            className="w-full py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  );
};

// 通知鈴鐺按鈕
export const NotificationBell = ({ onClick, unreadCount = 0 }) => {
  return (
    <button
      onClick={onClick}
      className="relative p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
      title="通知設定"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </button>
  );
};

export default NotificationSettings;
