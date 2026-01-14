/**
 * 應用配置
 * 根據環境變數自動選擇 API 地址
 */

// API 基礎地址
// 開發環境: http://localhost:8000
// 生產環境: 從 Vercel 環境變數讀取
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// 帶 /api/stocks 路徑的基礎地址
export const API_STOCKS_BASE = `${API_BASE}/api/stocks`;

// 導出配置對象
export default {
  API_BASE,
  API_STOCKS_BASE,
};
