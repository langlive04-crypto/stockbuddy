/**
 * portfolioManager.js - 投資組合管理服務
 * V10.37 從 App.jsx 拆分出來
 *
 * 功能：
 * - localStorage 本地存儲投資組合
 * - 新增/刪除/查詢投組股票
 */

const PORTFOLIO_KEY = 'stockbuddy_portfolio';

const PortfolioManager = {
  // 取得投組
  getPortfolio: () => {
    try {
      return JSON.parse(localStorage.getItem(PORTFOLIO_KEY) || '[]');
    } catch {
      return [];
    }
  },

  // 加入投組
  addToPortfolio: (stock) => {
    const portfolio = PortfolioManager.getPortfolio();
    // 檢查是否已存在
    if (portfolio.find(s => s.stock_id === stock.stock_id)) {
      return { success: false, message: '此股票已在投組中' };
    }

    portfolio.push({
      stock_id: stock.stock_id,
      name: stock.name,
      added_date: new Date().toISOString(),
      added_price: stock.price,
      added_score: stock.confidence,
      added_signal: stock.signal,
      added_reason: stock.reason,
      score_breakdown: stock.score_breakdown,
    });

    localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(portfolio));
    return { success: true, message: `✅ ${stock.name} 已加入投組！` };
  },

  // 從投組移除
  removeFromPortfolio: (stockId) => {
    const portfolio = PortfolioManager.getPortfolio();
    const newPortfolio = portfolio.filter(s => s.stock_id !== stockId);
    localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(newPortfolio));
    return { success: true };
  },

  // 檢查是否在投組中
  isInPortfolio: (stockId) => {
    const portfolio = PortfolioManager.getPortfolio();
    return portfolio.some(s => s.stock_id === stockId);
  },
};

export default PortfolioManager;
