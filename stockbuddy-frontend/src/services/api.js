/**
 * api.js - API 服務層
 * V10.35 新增
 * V10.37 修復：緩存 key 包含完整 URL 和參數
 *
 * 功能：
 * - 統一 API 請求處理
 * - 錯誤處理與重試機制
 * - 請求緩存管理
 */

import { API_BASE } from '../config';

// 請求配置
const DEFAULT_OPTIONS = {
  timeout: 30000,
  retries: 2,
  retryDelay: 1000,
};

// 簡單的內存緩存
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5分鐘

/**
 * 帶超時的 fetch
 */
const fetchWithTimeout = async (url, options = {}, timeout = DEFAULT_OPTIONS.timeout) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

/**
 * 帶重試的請求
 */
const fetchWithRetry = async (url, options = {}, retries = DEFAULT_OPTIONS.retries) => {
  let lastError;

  for (let i = 0; i <= retries; i++) {
    try {
      const response = await fetchWithTimeout(url, options);
      if (!response.ok && i < retries) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response;
    } catch (error) {
      lastError = error;
      if (i < retries) {
        await new Promise(resolve => setTimeout(resolve, DEFAULT_OPTIONS.retryDelay * (i + 1)));
      }
    }
  }

  throw lastError;
};

/**
 * 生成緩存 key (V10.37 修復：包含完整 URL 和參數)
 */
const generateCacheKey = (endpoint, params = {}) => {
  const paramStr = Object.keys(params).length > 0
    ? `?${new URLSearchParams(params).toString()}`
    : '';
  return `${endpoint}${paramStr}`;
};

/**
 * 帶緩存的 GET 請求
 * V10.37 修復：緩存 key 現在包含完整路徑和查詢參數
 */
export const cachedGet = async (endpoint, options = {}) => {
  // 從 endpoint 解析出參數，用於生成完整的緩存 key
  const [path, queryString] = endpoint.split('?');
  const params = queryString
    ? Object.fromEntries(new URLSearchParams(queryString))
    : {};
  const cacheKey = generateCacheKey(path, params);

  const cached = cache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  try {
    const response = await fetchWithRetry(`${API_BASE}${endpoint}`, options);
    const data = await response.json();

    cache.set(cacheKey, {
      data,
      timestamp: Date.now(),
    });

    return data;
  } catch (error) {
    // 如果有舊緩存，即使過期也返回
    if (cached) {
      console.warn(`Using stale cache for ${endpoint}`);
      return cached.data;
    }
    throw error;
  }
};

/**
 * 清除緩存
 */
export const clearCache = (endpoint = null) => {
  if (endpoint) {
    cache.delete(endpoint);
  } else {
    cache.clear();
  }
};

/**
 * API 端點
 */
export const api = {
  // 股票相關
  stocks: {
    list: () => cachedGet('/api/stocks/stocks/list'),
    analyze: (stockId) => cachedGet(`/api/stocks/analyze/${stockId}`),
    recommendations: () => cachedGet('/api/stocks/recommendations'),
    hot: () => cachedGet('/api/stocks/hot-stocks'),
    volume: () => cachedGet('/api/stocks/volume-hot'),
    darkHorse: () => cachedGet('/api/stocks/dark-horses'),
    market: () => cachedGet('/api/stocks/market'),
    dataStatus: () => cachedGet('/api/stocks/data-status'),
  },

  // 籌碼相關
  chip: {
    analysis: (stockId) => cachedGet(`/api/stocks/chip/analysis/${stockId}`),
  },

  // 新聞相關
  news: {
    list: (stockId = null) => cachedGet(stockId ? `/api/stocks/news/${stockId}` : '/api/stocks/news'),
  },

  // 歷史績效
  performance: {
    history: (days = 30) => cachedGet(`/api/stocks/performance/history?days=${days}`),
  },

  // 形態辨識
  patterns: {
    detect: (stockId) => cachedGet(`/api/stocks/patterns/${stockId}`),
    list: () => cachedGet('/api/stocks/patterns'),
  },

  // 圖表數據
  charts: {
    kline: (stockId, period = '1m') => cachedGet(`/api/stocks/kline/${stockId}?period=${period}`),
    sector: () => cachedGet('/api/stocks/sector-analysis'),
    correlation: () => cachedGet('/api/stocks/correlation'),
  },
};

export default api;
