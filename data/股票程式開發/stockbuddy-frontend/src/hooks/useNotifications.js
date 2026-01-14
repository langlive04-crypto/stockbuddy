/**
 * useNotifications.js - 瀏覽器通知 Hook
 * V10.28 新增
 *
 * 功能：
 * - 瀏覽器推播通知
 * - 價格警示通知
 * - 通知權限管理
 * - 通知歷史記錄
 */

import { useState, useEffect, useCallback } from 'react';

// 通知設定 localStorage key
const NOTIFICATION_SETTINGS_KEY = 'stockbuddy_notification_settings';
const NOTIFICATION_HISTORY_KEY = 'stockbuddy_notification_history';

/**
 * 瀏覽器通知 Hook
 */
const useNotifications = () => {
  const [permission, setPermission] = useState('default');
  const [isSupported, setIsSupported] = useState(false);
  const [settings, setSettings] = useState({
    enabled: true,
    priceAlerts: true,
    marketOpen: true,
    recommendations: true,
    sound: true,
  });
  const [history, setHistory] = useState([]);

  // 初始化
  useEffect(() => {
    // 檢查瀏覽器支援
    const supported = 'Notification' in window;
    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
    }

    // 載入設定
    const savedSettings = localStorage.getItem(NOTIFICATION_SETTINGS_KEY);
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error('Failed to load notification settings:', e);
      }
    }

    // 載入歷史
    const savedHistory = localStorage.getItem(NOTIFICATION_HISTORY_KEY);
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Failed to load notification history:', e);
      }
    }
  }, []);

  // 儲存設定
  const saveSettings = useCallback((newSettings) => {
    setSettings(newSettings);
    localStorage.setItem(NOTIFICATION_SETTINGS_KEY, JSON.stringify(newSettings));
  }, []);

  // 儲存歷史
  const saveHistory = useCallback((newHistory) => {
    // 只保留最近 50 條
    const trimmed = newHistory.slice(-50);
    setHistory(trimmed);
    localStorage.setItem(NOTIFICATION_HISTORY_KEY, JSON.stringify(trimmed));
  }, []);

  // 請求通知權限
  const requestPermission = useCallback(async () => {
    if (!isSupported) {
      return { success: false, error: '瀏覽器不支援通知功能' };
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);

      if (result === 'granted') {
        return { success: true };
      } else if (result === 'denied') {
        return { success: false, error: '通知權限已被拒絕，請在瀏覽器設定中開啟' };
      } else {
        return { success: false, error: '使用者未授予通知權限' };
      }
    } catch (e) {
      return { success: false, error: e.message };
    }
  }, [isSupported]);

  // 發送通知
  const sendNotification = useCallback(
    (title, options = {}) => {
      if (!isSupported || permission !== 'granted' || !settings.enabled) {
        return null;
      }

      const defaultOptions = {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'stockbuddy-notification',
        requireInteraction: false,
        silent: !settings.sound,
        ...options,
      };

      try {
        const notification = new Notification(title, defaultOptions);

        // 記錄歷史
        const record = {
          id: Date.now(),
          title,
          body: options.body || '',
          type: options.type || 'general',
          timestamp: new Date().toISOString(),
          read: false,
        };
        saveHistory([...history, record]);

        // 點擊通知時聚焦視窗
        notification.onclick = () => {
          window.focus();
          notification.close();
          if (options.onClick) {
            options.onClick();
          }
        };

        return notification;
      } catch (e) {
        console.error('Failed to send notification:', e);
        return null;
      }
    },
    [isSupported, permission, settings, history, saveHistory]
  );

  // 發送價格警示通知
  const sendPriceAlert = useCallback(
    (stock, alertType, currentPrice, targetPrice) => {
      if (!settings.priceAlerts) return null;

      const isAbove = alertType === 'above';
      const title = isAbove
        ? `📈 ${stock.name} 突破目標價！`
        : `📉 ${stock.name} 跌破警示價！`;

      const body = `目前價格: $${currentPrice.toFixed(2)}
${isAbove ? '突破' : '跌破'}目標: $${targetPrice.toFixed(2)}`;

      return sendNotification(title, {
        body,
        type: 'price_alert',
        tag: `price-alert-${stock.stock_id}`,
        requireInteraction: true,
        data: { stock, alertType, currentPrice, targetPrice },
      });
    },
    [settings.priceAlerts, sendNotification]
  );

  // 發送市場開盤通知
  const sendMarketOpenNotification = useCallback(
    (market) => {
      if (!settings.marketOpen) return null;

      const isTW = market === 'TW';
      const title = isTW ? '🔔 台股開盤' : '🔔 美股開盤';
      const body = isTW ? '台灣股市已經開盤，祝您投資順利！' : '美國股市已經開盤，開始交易吧！';

      return sendNotification(title, {
        body,
        type: 'market_open',
        tag: `market-open-${market}`,
      });
    },
    [settings.marketOpen, sendNotification]
  );

  // 發送推薦通知
  const sendRecommendationNotification = useCallback(
    (stocks) => {
      if (!settings.recommendations || !stocks || stocks.length === 0) return null;

      const topStock = stocks[0];
      const title = '🎯 今日 AI 推薦';
      const body = `${topStock.name} (${topStock.stock_id}) 評分 ${topStock.confidence}
信號: ${topStock.signal}`;

      return sendNotification(title, {
        body,
        type: 'recommendation',
        tag: 'daily-recommendation',
        data: { stocks },
      });
    },
    [settings.recommendations, sendNotification]
  );

  // 更新設定
  const updateSettings = useCallback(
    (key, value) => {
      const newSettings = { ...settings, [key]: value };
      saveSettings(newSettings);
    },
    [settings, saveSettings]
  );

  // 標記通知已讀
  const markAsRead = useCallback(
    (notificationId) => {
      const newHistory = history.map((item) =>
        item.id === notificationId ? { ...item, read: true } : item
      );
      saveHistory(newHistory);
    },
    [history, saveHistory]
  );

  // 清除歷史
  const clearHistory = useCallback(() => {
    saveHistory([]);
  }, [saveHistory]);

  // 取得未讀數量
  const unreadCount = history.filter((item) => !item.read).length;

  return {
    // 狀態
    isSupported,
    permission,
    settings,
    history,
    unreadCount,

    // 操作
    requestPermission,
    sendNotification,
    sendPriceAlert,
    sendMarketOpenNotification,
    sendRecommendationNotification,
    updateSettings,
    markAsRead,
    clearHistory,
  };
};

export default useNotifications;
