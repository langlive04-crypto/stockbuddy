/**
 * historyManager.js - AI 精選歷史快照管理
 * V10.37 從 App.jsx 拆分出來
 *
 * 功能：
 * - localStorage 本地存儲歷史推薦
 * - 保存/查詢歷史快照
 * - 日期格式統一化
 */

import {
  normalizeDate,
  formatDateDisplay,
  formatDateLabel as formatDateLabelUtil,
} from '../utils/dateUtils';

const HISTORY_KEY = 'stockbuddy_ai_picks_history';
const MAX_HISTORY_DAYS = 5;

const HistoryManager = {
  // 保存快照 - V10.35.4: 使用 dateUtils 統一日期格式
  saveSnapshot: (recommendations, dataDate) => {
    if (!dataDate || !recommendations || recommendations.length === 0) return;

    try {
      const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '{}');
      const dateKey = normalizeDate(dataDate);  // 統一轉換為 YYYY-MM-DD

      // 只有資料日期不同才保存
      if (!history[dateKey]) {
        history[dateKey] = {
          date: dateKey,
          data_date: formatDateDisplay(dataDate),  // 存儲顯示格式 YYYY/MM/DD
          saved_at: new Date().toISOString(),
          recommendations: recommendations.slice(0, 30).map(stock => ({
            stock_id: stock.stock_id,
            name: stock.name,
            price: stock.price,
            change_percent: stock.change_percent,
            confidence: stock.confidence,
            signal: stock.signal,
            reason: stock.reason,
            score_breakdown: stock.score_breakdown,
            industry: stock.industry,
            pe_ratio: stock.pe_ratio,
            dividend_yield: stock.dividend_yield,
          })),
        };

        // 清理超過 MAX_HISTORY_DAYS 天的資料
        const dates = Object.keys(history).sort().reverse();
        if (dates.length > MAX_HISTORY_DAYS) {
          dates.slice(MAX_HISTORY_DAYS).forEach(d => delete history[d]);
        }

        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
      }
    } catch (e) {
      console.error('保存歷史快照失敗:', e);
    }
  },

  // 取得可用的歷史日期
  getAvailableDates: () => {
    try {
      const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '{}');
      return Object.keys(history).sort().reverse();
    } catch {
      return [];
    }
  },

  // 取得指定日期的資料
  getHistoryData: (dateKey) => {
    try {
      const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '{}');
      return history[dateKey] || null;
    } catch {
      return null;
    }
  },

  // 格式化日期顯示 - V10.35.4: 使用 dateUtils
  formatDateLabel: (dateKey) => formatDateLabelUtil(dateKey),
};

export default HistoryManager;
