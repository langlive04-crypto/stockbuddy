/**
 * stockAPI.js - 股票 API 服務
 * V10.26 重構：從 App.jsx 提取
 *
 * 包含：
 * - API 請求方法
 * - 錯誤處理
 * - 快取管理
 */

import { API_BASE } from '../config';

// 快取
const cache = {
  data: {},
  timestamp: {},
  TTL: 60000, // 1 分鐘

  get(key) {
    const now = Date.now();
    if (this.data[key] && now - this.timestamp[key] < this.TTL) {
      return this.data[key];
    }
    return null;
  },

  set(key, value) {
    this.data[key] = value;
    this.timestamp[key] = Date.now();
  },

  clear() {
    this.data = {};
    this.timestamp = {};
  },
};

// API 方法
export const stockAPI = {
  // AI 精選推薦
  async getRecommendations() {
    const cached = cache.get('recommendations');
    if (cached) return cached;

    try {
      const res = await fetch(`${API_BASE}/api/stocks/ai/picks`, {
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cache.set('recommendations', data);
      return data;
    } catch (error) {
      console.error('取得 AI 推薦失敗:', error);
      throw error;
    }
  },

  // 個股分析
  async getAnalysis(stockId) {
    const cacheKey = `analysis_${stockId}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    try {
      const res = await fetch(`${API_BASE}/api/stocks/analysis/${stockId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cache.set(cacheKey, data);
      return data;
    } catch (error) {
      console.error(`取得 ${stockId} 分析失敗:`, error);
      throw error;
    }
  },

  // 個股新聞
  async getNews(stockId) {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/news/${stockId}`);
      if (!res.ok) return [];
      return await res.json();
    } catch (error) {
      console.error(`取得 ${stockId} 新聞失敗:`, error);
      return [];
    }
  },

  // 熱門股票
  async getHotStocks() {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/top-gainers?limit=10`);
      if (!res.ok) return [];
      return await res.json();
    } catch (error) {
      console.error('取得熱門股票失敗:', error);
      return [];
    }
  },

  // 成交量熱門
  async getVolumeHot() {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/volume-hot?limit=10`);
      if (!res.ok) return [];
      return await res.json();
    } catch (error) {
      console.error('取得成交熱門失敗:', error);
      return [];
    }
  },

  // 基本面資料
  async getFundamental(stockId) {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/fundamental/${stockId}`);
      if (!res.ok) return null;
      return await res.json();
    } catch (error) {
      console.error(`取得 ${stockId} 基本面失敗:`, error);
      return null;
    }
  },

  // 歷史K線
  async getHistory(stockId, months = 3) {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/${stockId}/history?months=${months}`);
      if (!res.ok) return [];
      return await res.json();
    } catch (error) {
      console.error(`取得 ${stockId} 歷史資料失敗:`, error);
      return [];
    }
  },

  // 籌碼資料
  async getChipData(stockId) {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/chip/${stockId}`);
      if (!res.ok) return null;
      return await res.json();
    } catch (error) {
      console.error(`取得 ${stockId} 籌碼失敗:`, error);
      return null;
    }
  },

  // 綜合投資策略
  async getStrategy() {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/strategy`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (error) {
      console.error('取得策略失敗:', error);
      throw error;
    }
  },

  // 搜尋股票
  async search(query) {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/search?q=${encodeURIComponent(query)}`);
      if (!res.ok) return [];
      return await res.json();
    } catch (error) {
      console.error('搜尋失敗:', error);
      return [];
    }
  },

  // 清除快取
  clearCache() {
    cache.clear();
  },
};

export default stockAPI;
