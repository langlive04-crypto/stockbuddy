/**
 * storageManager.js - 本地儲存管理中心
 * V10.38 統一整合 - 所有 localStorage 相關服務
 *
 * 統一入口：
 * - PortfolioManager: 投資組合管理 (重新導出自 portfolioManager.js)
 * - HistoryManager: AI 精選歷史紀錄 (重新導出自 historyManager.js)
 * - SettingsManager: 通用設定管理
 * - CategoriesManager: 自選股分類管理
 */

// 重新導出 V10.37 拆分的服務
export { default as PortfolioManager } from './portfolioManager';
export { default as HistoryManager } from './historyManager';

// ===== 通用設定管理 =====
const SETTINGS_KEY = 'stockbuddy_settings';

export const SettingsManager = {
  // 取得設定
  getSettings() {
    try {
      return JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}');
    } catch {
      return {};
    }
  },

  // 更新設定
  updateSettings(newSettings) {
    const current = this.getSettings();
    const updated = { ...current, ...newSettings };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
    return updated;
  },

  // 取得單一設定
  get(key, defaultValue = null) {
    const settings = this.getSettings();
    return settings[key] ?? defaultValue;
  },

  // 設定單一值
  set(key, value) {
    this.updateSettings({ [key]: value });
  },

  // 清空設定
  clear() {
    localStorage.removeItem(SETTINGS_KEY);
  },
};

// ===== 自選股分類管理 =====
const CATEGORIES_KEY = 'stockbuddy_categories';

export const CategoriesManager = {
  // 取得所有分類
  getCategories() {
    try {
      return JSON.parse(localStorage.getItem(CATEGORIES_KEY) || '{}');
    } catch {
      return {};
    }
  },

  // 新增分類
  addCategory(name) {
    const categories = this.getCategories();
    if (!categories[name]) {
      categories[name] = [];
      localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categories));
      return true;
    }
    return false;
  },

  // 刪除分類
  removeCategory(name) {
    const categories = this.getCategories();
    delete categories[name];
    localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categories));
  },

  // 新增股票到分類
  addStockToCategory(category, stockId, stockName) {
    const categories = this.getCategories();
    if (!categories[category]) {
      categories[category] = [];
    }
    if (!categories[category].find((s) => s.stock_id === stockId)) {
      categories[category].push({
        stock_id: stockId,
        name: stockName,
        added_at: new Date().toISOString(),
      });
      localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categories));
      return true;
    }
    return false;
  },

  // 從分類移除股票
  removeStockFromCategory(category, stockId) {
    const categories = this.getCategories();
    if (categories[category]) {
      categories[category] = categories[category].filter((s) => s.stock_id !== stockId);
      localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categories));
    }
  },

  // 取得股票所在的分類
  getStockCategories(stockId) {
    const categories = this.getCategories();
    const result = [];
    for (const [name, stocks] of Object.entries(categories)) {
      if (stocks.find((s) => s.stock_id === stockId)) {
        result.push(name);
      }
    }
    return result;
  },
};

// ===== localStorage 工具函數 =====
export const StorageUtils = {
  // 檢查 localStorage 容量
  getUsedSpace() {
    let total = 0;
    for (const key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        total += localStorage[key].length * 2; // UTF-16 每字符 2 bytes
      }
    }
    return total;
  },

  // 格式化容量顯示
  formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  },

  // 清空所有 StockBuddy 相關的 localStorage
  clearAll() {
    const keysToRemove = [];
    for (const key in localStorage) {
      if (key.startsWith('stockbuddy_')) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    return keysToRemove.length;
  },

  // 安全的 localStorage 操作（處理 QuotaExceededError）
  safeSetItem(key, value) {
    try {
      localStorage.setItem(key, value);
      return { success: true };
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        return { success: false, error: 'storage_full', message: '本地儲存空間已滿' };
      }
      return { success: false, error: 'unknown', message: e.message };
    }
  },
};

// 預設導出所有管理器
export default {
  PortfolioManager: null, // 延遲加載，避免循環引用
  HistoryManager: null,
  SettingsManager,
  CategoriesManager,
  StorageUtils,
};
