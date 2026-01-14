import React, { useState, useEffect } from 'react';
import { API_BASE } from './config';

// V10.35.4 新增：日期工具函數
import {
  normalizeDate,
  formatDateDisplay,
  formatDateShort,
  formatDateLabel,
  getTodayDisplay,
  getTodayISO,
  isToday,
} from './utils/dateUtils';

// V10.15 新增組件
import CandlestickChart from './components/CandlestickChart';
import PerformanceDashboard from './components/PerformanceDashboard';
import InstitutionalChart from './components/InstitutionalChart';
import ExportButton from './components/ExportButton';
import DataStatusIndicator, { DataStatusBadge } from './components/DataStatusIndicator';

// V10.16 新增組件：綜合投資策略
import StrategyDashboard from './components/StrategyDashboard';
import StrategyPicksPanel from './components/StrategyPicksPanel';

// V10.17 新增組件：選股篩選器
import StockScreener from './components/StockScreener';

// V10.18 新增組件：股票比較
import StockComparison from './components/StockComparison';

// V10.19 新增組件：價格警示
import PriceAlert from './components/PriceAlert';

// V10.20 新增組件：交易記錄管理
import TransactionManager from './components/TransactionManager';

// V10.21 新增組件：自選股分類
import WatchlistCategories from './components/WatchlistCategories';

// V10.23 新增組件：自動刷新
import AutoRefresh from './components/AutoRefresh';

// V10.23 新增組件：績效追蹤
import PerformanceTracker from './components/PerformanceTracker';

// V10.23 新增組件：新手引導
import OnboardingGuide, { ReplayOnboardingButton } from './components/OnboardingGuide';

// V10.24 新增組件：美股市場
import USStockPanel from './components/USStockPanel';

// V10.25 新增組件：增強版 AI 分析
import EnhancedAIPanel from './components/EnhancedAIPanel';

// V10.27 新增組件：市場總覽儀表板
import MarketDashboard from './components/MarketDashboard';

// V10.27 新增組件：市場行事曆
import MarketCalendar from './components/MarketCalendar';

// V10.27 新增：鍵盤快捷鍵
import useKeyboardShortcuts from './hooks/useKeyboardShortcuts';
import KeyboardShortcutsModal, { KeySequenceIndicator } from './components/KeyboardShortcuts';

// V10.28 新增：瀏覽器通知
import useNotifications from './hooks/useNotifications';
import NotificationSettings, { NotificationBell } from './components/NotificationSettings';

// V10.28 新增：響應式設計
import useResponsive from './hooks/useResponsive';
import MobileNav from './components/MobileNav';

// V10.27/V10.28 新增：主題系統
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { ThemeToggleIcon } from './components/ThemeToggle';

// V10.29 新增：Toast 通知、骨架屏、風險計算器
import { useToast } from './components/Toast';
import Skeleton, { SkeletonStockList, SkeletonAnalysisPanel } from './components/Skeleton';
import RiskCalculator from './components/RiskCalculator';

// V10.30 新增：智能提醒、除權息計算器、投組儀表板
import SmartAlerts from './components/SmartAlerts';
import DividendCalculator from './components/DividendCalculator';
import PortfolioDashboard from './components/PortfolioDashboard';

// V10.31 新增：AI 分析報告、歷史績效驗證、進階圖表
import AIReport from './components/AIReport';
import HistoricalPerformance from './components/HistoricalPerformance';
import AdvancedCharts from './components/AdvancedCharts';

// V10.32 新增：即時數據管理、新聞整合
import RealtimeManager, { DataStatusBadge as RealtimeStatusBadge } from './components/RealtimeManager';
import NewsPanel, { NewsTicker } from './components/NewsPanel';

// V10.33 新增：技術形態辨識、投資日記
import PatternRecognition from './components/PatternRecognition';
import InvestmentDiary from './components/InvestmentDiary';

// V10.34 新增：模擬交易、策略範本
import SimulationTrading from './components/SimulationTrading';
import StrategyTemplates from './components/StrategyTemplates';

// V10.40 新增：ML 模型管理面板
import MLPanel from './components/MLPanel';

// V10.35 新增：錯誤邊界
import ErrorBoundary from './components/ErrorBoundary';

// V10.37 新增：從 App.jsx 拆分出來的服務層
import PortfolioManager from './services/portfolioManager';
import HistoryManager from './services/historyManager';

// V10.37 新增：從 App.jsx 拆分出來的 UI 組件
import { ScoreRing, MiniKLineChart, TermTooltip, ScoreBar, StockCard } from './components/ui';

// V10.38 新增：React Router 支援
import { useSearchParams, useNavigate } from 'react-router-dom';

// V10.39 新增：選單優化
import DropdownMenu from './components/DropdownMenu';
import UnifiedAlerts from './components/UnifiedAlerts';
import UnifiedPerformance from './components/UnifiedPerformance';
import { menuGroups, findGroupBySection, getUnifiedComponent } from './config/menuGroups';

// ============================================================
// 📈 StockBuddy V10.39 - 台股智能選股系統（選單優化版）
// V10.39: 選單優化 - 29 選單整合為 8 主選單、績效/提醒整合
// V10.35.4: 日期格式統一化 - dateUtils 工具函數、跨組件一致性
// V10.35.3: 回測修復、模擬交易修復、手機端響應式優化
// V10.35.2: 功能層修正 - 中文名稱、連結功能、DataSourceBadge、UX優化
// V10.35: 技術債償還 - console.log 清理、React.memo 優化、Error Boundary
// V10.34: 模擬交易練習、策略範本庫
// V10.33: 技術形態辨識、投資日記
// V10.32: 即時數據管理、新聞整合
// V10.31: AI 分析報告、歷史績效驗證、進階圖表
// V10.30: 智能提醒系統、除權息計算器、投組儀表板
// V10.29: Toast 通知、載入骨架屏、風險管理計算器
// V10.28: 瀏覽器通知、行動版響應式設計
// V10.27: 市場總覽儀表板、主題切換、鍵盤快捷鍵、市場行事曆
// V10.23: 前端顯示 KD、威廉指標、風險評估（技術分析增強）
// V10.22: 日期顯示修正、績效呈現優化
// V10.21: 自選股分類群組（組織追蹤股票）
// V10.20: 交易記錄管理（持股損益分析）
// V10.19: 價格警示功能（設定目標價通知）
// V10.18: 股票比較功能（並排比較多檔股票）
// V10.17: 選股篩選器（多條件自訂篩選）
// V10.16: 綜合投資策略系統
// V10.15: K線圖表、績效分析、匯出功能、櫃買支援
// ============================================================

// ============================================================
// V10.37: PortfolioManager 和 HistoryManager 已移至 services/
// ============================================================

// API 設定
// API_BASE 已從 config.js 導入

// API 服務
const stockAPI = {
  async getRecommendations() {
    const res = await fetch(`${API_BASE}/api/stocks/recommend`);
    return res.json();
  },
  async getStockInfo(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/info/${stockId}`);
    return res.json();
  },
  async getStockAnalysis(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/analysis/${stockId}`);
    return res.json();
  },
  async getStockHistory(stockId, months = 3) {
    const res = await fetch(`${API_BASE}/api/stocks/history/${stockId}?months=${months}`);
    return res.json();
  },
  async getMarket() {
    const res = await fetch(`${API_BASE}/api/stocks/market`);
    return res.json();
  },
  async searchStocks(query) {
    const res = await fetch(`${API_BASE}/api/stocks/search?q=${query}`);
    return res.json();
  },
  // 新聞 API
  async getStockNews(stockId, limit = 5) {
    const res = await fetch(`${API_BASE}/api/stocks/news/stock/${stockId}?limit=${limit}`);
    return res.json();
  },
  // 基本面 API
  async getFundamental(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/fundamental/${stockId}`);
    return res.json();
  },
  // 籌碼面 API
  async getInstitutional(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/institutional/${stockId}`);
    return res.json();
  },
  // 完整分析 API
  async getFullAnalysis(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/full-analysis/${stockId}`);
    return res.json();
  },
  // 自選股 API
  async getWatchlist() {
    const res = await fetch(`${API_BASE}/api/stocks/watchlist`);
    return res.json();
  },
  async addToWatchlist(stockId, note = '') {
    const res = await fetch(`${API_BASE}/api/stocks/watchlist/${stockId}?note=${encodeURIComponent(note)}`, {
      method: 'POST',
    });
    return res.json();
  },
  async removeFromWatchlist(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/watchlist/${stockId}`, {
      method: 'DELETE',
    });
    return res.json();
  },
  async checkWatchlist(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/watchlist/check/${stockId}`);
    return res.json();
  },
  // 回測 API
  async runBacktest(stockId, strategy = 'ma_crossover', months = 6) {
    const res = await fetch(`${API_BASE}/api/stocks/backtest/${stockId}?strategy=${strategy}&months=${months}`);
    return res.json();
  },
  async getBacktestStrategies() {
    const res = await fetch(`${API_BASE}/api/stocks/backtest/strategies`);
    return res.json();
  },
  // 投資組合 API
  async getPortfolio() {
    const res = await fetch(`${API_BASE}/api/stocks/portfolio`);
    return res.json();
  },
  async getPortfolioSummary() {
    const res = await fetch(`${API_BASE}/api/stocks/portfolio/summary`);
    return res.json();
  },
  async addToPortfolio(stockId, buyPrice, quantity, buyDate = null, note = '') {
    const params = new URLSearchParams({
      stock_id: stockId,
      buy_price: buyPrice,
      quantity: quantity,
    });
    if (buyDate) params.append('buy_date', buyDate);
    if (note) params.append('note', note);
    const res = await fetch(`${API_BASE}/api/stocks/portfolio/add?${params}`, {
      method: 'POST',
    });
    return res.json();
  },
  async deleteFromPortfolio(holdingId) {
    const res = await fetch(`${API_BASE}/api/stocks/portfolio/${holdingId}`, {
      method: 'DELETE',
    });
    return res.json();
  },
  async sellFromPortfolio(holdingId, sellPrice, quantity = null) {
    const params = new URLSearchParams({ sell_price: sellPrice });
    if (quantity) params.append('quantity', quantity);
    const res = await fetch(`${API_BASE}/api/stocks/portfolio/sell/${holdingId}?${params}`, {
      method: 'POST',
    });
    return res.json();
  },
  async getPortfolioTransactions(limit = 20) {
    const res = await fetch(`${API_BASE}/api/stocks/portfolio/transactions?limit=${limit}`);
    return res.json();
  },
  // ============ V10.15 新增 API ============
  // 績效分析 API
  async getPerformance(stockId, months = 12) {
    const res = await fetch(`${API_BASE}/api/stocks/performance/${stockId}?months=${months}`);
    return res.json();
  },
  async getMonthlyHeatmap(stockId, years = 3) {
    const res = await fetch(`${API_BASE}/api/stocks/performance/${stockId}/monthly-heatmap?years=${years}`);
    return res.json();
  },
  async getRiskMetrics(stockId, months = 12) {
    const res = await fetch(`${API_BASE}/api/stocks/performance/${stockId}/risk-metrics?months=${months}`);
    return res.json();
  },
  // 匯出 API
  async exportRecommendationsCSV() {
    window.location.href = `${API_BASE}/api/stocks/export/recommendations/csv`;
  },
  async exportRecommendationsExcel() {
    window.location.href = `${API_BASE}/api/stocks/export/recommendations/excel`;
  },
  // 櫃買股票 API
  async getOTCStocks() {
    const res = await fetch(`${API_BASE}/api/stocks/otc/all`);
    return res.json();
  },
  async getOTCStockInfo(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/otc/info/${stockId}`);
    return res.json();
  },
  // 資料狀態 API
  async getDataStatus() {
    const res = await fetch(`${API_BASE}/api/stocks/data-status`);
    return res.json();
  },
  // 法人追蹤 API
  async getInstitutionalTracking(stockId, days = 20) {
    const res = await fetch(`${API_BASE}/api/stocks/institutional-tracking/${stockId}?days=${days}`);
    return res.json();
  },
  // 股票評分 API
  async getStockScore(stockId) {
    const res = await fetch(`${API_BASE}/api/stocks/score/${stockId}`);
    return res.json();
  },
};

// ============================================================
// V10.37: UI 組件已移至 components/ui/
// ScoreRing, MiniKLineChart, TermTooltip, ScoreBar, StockCard
// ============================================================

// ===== 新聞列表組件 =====
const NewsList = ({ news }) => {
  if (!news || !news.news || news.news.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>📰 暫無相關新聞</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-3">
      {/* 新聞摘要 */}
      {news.summary && (
        <div className={`p-4 rounded-xl border ${
          news.summary.trend === 'positive' || news.summary.trend === 'very_positive'
            ? 'bg-red-500/10 border-red-500/30'
            : news.summary.trend === 'negative' || news.summary.trend === 'very_negative'
            ? 'bg-emerald-500/10 border-emerald-500/30'
            : 'bg-slate-700/30 border-slate-600/30'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">
              {news.summary.trend === 'very_positive' ? '🚀' :
               news.summary.trend === 'positive' ? '📈' :
               news.summary.trend === 'negative' ? '📉' :
               news.summary.trend === 'very_negative' ? '⚠️' : '📊'}
            </span>
            <span className="text-white font-medium">
              {news.summary.trend_display || '中性'}
            </span>
          </div>
          <p className="text-slate-400 text-sm">{news.summary.summary}</p>
        </div>
      )}
      
      {/* 新聞列表 */}
      <div className="space-y-2">
        {news.news.slice(0, 5).map((item, i) => (
          <div key={i} className="flex items-start gap-3 p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors">
            <span className={`text-lg ${
              item.sentiment === 'positive' ? '📈' :
              item.sentiment === 'negative' ? '📉' : '📰'
            }`}>
              {item.sentiment === 'positive' ? '📈' :
               item.sentiment === 'negative' ? '📉' : '📰'}
            </span>
            <div className="flex-1 min-w-0">
              <a 
                href={item.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-white hover:text-blue-400 text-sm line-clamp-2 transition-colors"
              >
                {item.title}
              </a>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-slate-500">{item.source}</span>
                <span className="text-xs text-slate-600">•</span>
                <span className="text-xs text-slate-500">{item.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ===== 詳細分析面板 =====
const AnalysisPanel = ({ stock, onClose, onSelectStock }) => {
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState(null);
  const [news, setNews] = useState(null);
  const [fundamental, setFundamental] = useState(null);
  const [institutional, setInstitutional] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('technical');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [analysisData, historyData, newsData, fundamentalData, institutionalData] = await Promise.all([
          stockAPI.getStockAnalysis(stock.stock_id).catch(() => null),
          stockAPI.getStockHistory(stock.stock_id, 3).catch(() => null),
          stockAPI.getStockNews(stock.stock_id, 5).catch(() => null),
          stockAPI.getFundamental(stock.stock_id).catch(() => null),
          stockAPI.getInstitutional(stock.stock_id).catch(() => null),
        ]);
        setAnalysis(analysisData?.analysis || analysisData);  // 修正：存取巢狀的 analysis 物件
        setHistory(historyData?.data || []);
        setNews(newsData);
        setFundamental(fundamentalData?.fundamental);
        setInstitutional(institutionalData?.institutional);
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [stock.stock_id]);

  const tabs = [
    { id: 'technical', label: '技術面', icon: '📊' },
    { id: 'chart', label: 'K線圖', icon: '📈' },  // V10.15 新增
    { id: 'fundamental', label: '基本面', icon: '💰' },
    { id: 'chip', label: '籌碼面', icon: '🏦' },
    { id: 'performance', label: '績效', icon: '🎯' },  // V10.15 新增
    { id: 'strategy', label: '策略', icon: '📋' },  // V10.16 新增
    { id: 'news', label: '新聞', icon: '📰' },
  ];

  const isUp = (stock.change_percent || 0) >= 0;

  return (
    <div className="bg-slate-800/90 rounded-2xl border border-slate-700 overflow-hidden">
      {/* 標題列 */}
      <div className="p-4 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-white text-xl font-bold">{stock.name}</span>
              <span className="text-slate-400">{stock.stock_id}</span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-white text-2xl font-bold">${stock.price?.toLocaleString()}</span>
              <span className={`text-lg font-medium ${isUp ? 'text-red-400' : 'text-emerald-400'}`}>
                {isUp ? '▲' : '▼'} {Math.abs(stock.change || 0).toFixed(2)} ({isUp ? '+' : ''}{stock.change_percent?.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-2"
        >
          ✕
        </button>
      </div>

      {/* Tab 切換 */}
      <div className="flex border-b border-slate-700">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-500/10'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* 內容區 */}
      <div className="p-4 max-h-[60vh] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            {/* 技術面 */}
            {activeTab === 'technical' && (
              <div className="space-y-4">
                {/* 建議操作 */}
                <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl p-4 border border-blue-500/30">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-white font-semibold text-lg">AI 建議</span>
                    <ScoreRing score={stock.confidence} size={60} />
                  </div>
                  
                  {/* V10.10: 多維度分數明細（含新聞+產業） */}
                  {stock.score_breakdown && (
                    <div className="mb-4">
                      <div className="grid grid-cols-4 gap-2 mb-2">
                        <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                          <div className="text-slate-400 text-xs">技術面</div>
                          <div className={`text-lg font-bold ${
                            stock.score_breakdown.technical >= 70 ? 'text-red-400' : 
                            stock.score_breakdown.technical >= 55 ? 'text-yellow-400' : 'text-slate-400'
                          }`}>
                            {stock.score_breakdown.technical}
                          </div>
                          <div className="text-slate-500 text-xs">50%</div>
                        </div>
                        <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                          <div className="text-slate-400 text-xs">基本面</div>
                          <div className={`text-lg font-bold ${
                            stock.score_breakdown.fundamental >= 65 ? 'text-emerald-400' : 
                            stock.score_breakdown.fundamental >= 50 ? 'text-yellow-400' : 'text-orange-400'
                          }`}>
                            {stock.score_breakdown.fundamental}
                          </div>
                          <div className="text-slate-500 text-xs">25%</div>
                        </div>
                        <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                          <div className="text-slate-400 text-xs">籌碼面</div>
                          <div className={`text-lg font-bold ${
                            stock.score_breakdown.chip >= 60 ? 'text-blue-400' : 
                            stock.score_breakdown.chip >= 45 ? 'text-slate-400' : 'text-orange-400'
                          }`}>
                            {stock.score_breakdown.chip}
                          </div>
                          <div className="text-slate-500 text-xs">15%</div>
                        </div>
                        <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                          <div className="text-slate-400 text-xs">新聞面</div>
                          <div className={`text-lg font-bold ${
                            stock.score_breakdown.news >= 60 ? 'text-purple-400' : 
                            stock.score_breakdown.news >= 45 ? 'text-slate-400' : 'text-orange-400'
                          }`}>
                            {stock.score_breakdown.news || 50}
                          </div>
                          <div className="text-slate-500 text-xs">10%</div>
                        </div>
                      </div>
                      {/* 產業熱度加分 */}
                      {stock.score_breakdown.industry_bonus !== 0 && stock.score_breakdown.industry_bonus && (
                        <div className={`text-center text-sm ${
                          stock.score_breakdown.industry_bonus > 0 ? 'text-amber-400' : 'text-slate-400'
                        }`}>
                          {stock.score_breakdown.industry_bonus > 0 ? '🔥' : '📉'} 產業熱度 
                          <span className="font-bold ml-1">
                            {stock.score_breakdown.industry_bonus > 0 ? '+' : ''}{stock.score_breakdown.industry_bonus}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-slate-400 text-xs">建議操作</div>
                      <div className={`text-lg font-bold ${
                        stock.signal === '強力買進' || stock.signal === '買進' ? 'text-red-400' :
                        stock.signal === '持有' ? 'text-yellow-400' : 'text-slate-400'
                      }`}>{stock.signal}</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-xs">止損價</div>
                      <div className="text-emerald-400 font-bold">${stock.stop_loss?.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-xs">目標價</div>
                      <div className="text-red-400 font-bold">${stock.target?.toLocaleString()}</div>
                    </div>
                  </div>
                  {stock.reason && (
                    <p className="text-slate-300 text-sm mt-3 pt-3 border-t border-slate-600/50">
                      💡 {stock.reason}
                    </p>
                  )}
                </div>

                {/* 技術指標 */}
                {analysis && (
                  <div className="grid grid-cols-2 gap-4">
                    {/* RSI */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">RSI (14)</div>
                      <div className={`text-xl font-bold ${
                        analysis.rsi?.value > 70 ? 'text-red-400' :
                        analysis.rsi?.value < 30 ? 'text-emerald-400' : 'text-white'
                      }`}>
                        {analysis.rsi?.value?.toFixed(1) || '-'}
                      </div>
                      <div className="text-slate-500 text-xs">{analysis.rsi?.status || '-'}</div>
                    </div>
                    
                    {/* MACD */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">MACD</div>
                      <div className={`text-xl font-bold ${
                        analysis.macd?.signal === '金叉' || analysis.macd?.signal === '多方' ? 'text-red-400' :
                        analysis.macd?.signal === '死叉' || analysis.macd?.signal === '空方' ? 'text-emerald-400' : 'text-white'
                      }`}>
                        {analysis.macd?.signal || '-'}
                      </div>
                      <div className="text-slate-500 text-xs">
                        DIF: {analysis.macd?.macd_value?.toFixed(2) || '-'}
                      </div>
                    </div>
                    
                    {/* 均線 */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">均線趨勢</div>
                      <div className={`text-xl font-bold ${
                        analysis.trend?.above_ma20 ? 'text-red-400' : 'text-emerald-400'
                      }`}>
                        {analysis.trend?.trend_desc || analysis.trend?.trend || '-'}
                      </div>
                      <div className="text-slate-500 text-xs">
                        {analysis.trend?.above_ma5 ? '站上5日線' : '跌破5日線'}
                      </div>
                    </div>
                    
                    {/* 成交量 */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">成交量比</div>
                      <div className={`text-xl font-bold ${
                        (stock.volume_ratio || 1) > 1.5 ? 'text-red-400' :
                        (stock.volume_ratio || 1) < 0.5 ? 'text-emerald-400' : 'text-white'
                      }`}>
                        {stock.volume_ratio?.toFixed(2) || '-'}x
                      </div>
                      <div className="text-slate-500 text-xs">
                        {(stock.volume_ratio || 1) > 1.5 ? '放量' : (stock.volume_ratio || 1) < 0.5 ? '縮量' : '正常'}
                      </div>
                    </div>

                    {/* V10.23: KD 指標 */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">KD 指標</div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xl font-bold ${
                          analysis.kd?.K > 80 ? 'text-red-400' :
                          analysis.kd?.K < 20 ? 'text-emerald-400' : 'text-white'
                        }`}>
                          K: {analysis.kd?.K?.toFixed(1) || '-'}
                        </span>
                        <span className="text-slate-500">/</span>
                        <span className="text-lg text-slate-300">
                          D: {analysis.kd?.D?.toFixed(1) || '-'}
                        </span>
                      </div>
                      <div className="text-slate-500 text-xs flex items-center gap-1">
                        <span>{analysis.kd?.status || '-'}</span>
                        {analysis.kd?.signal && (
                          <span className={`px-1 rounded ${
                            analysis.kd?.signal === '黃金交叉' ? 'bg-red-500/30 text-red-400' :
                            analysis.kd?.signal === '死亡交叉' ? 'bg-emerald-500/30 text-emerald-400' : ''
                          }`}>
                            {analysis.kd?.signal}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* V10.23: 威廉指標 */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">威廉指標 %R</div>
                      <div className={`text-xl font-bold ${
                        analysis.williams_r?.value > -20 ? 'text-red-400' :
                        analysis.williams_r?.value < -80 ? 'text-emerald-400' : 'text-white'
                      }`}>
                        {analysis.williams_r?.value?.toFixed(1) || '-'}
                      </div>
                      <div className="text-slate-500 text-xs">{analysis.williams_r?.status || '-'}</div>
                    </div>

                    {/* V10.23: 風險評估 */}
                    <div className="bg-slate-700/30 rounded-lg p-3">
                      <div className="text-slate-400 text-sm">風險評估</div>
                      <div className={`text-xl font-bold ${
                        analysis.risk?.risk_score >= 75 ? 'text-red-400' :
                        analysis.risk?.risk_score >= 50 ? 'text-yellow-400' :
                        analysis.risk?.risk_score >= 25 ? 'text-emerald-400' : 'text-blue-400'
                      }`}>
                        {analysis.risk?.risk_level || '-'}
                      </div>
                      <div className="text-slate-500 text-xs">
                        波動率: {analysis.risk?.volatility?.toFixed(2) || '-'}%
                      </div>
                    </div>
                  </div>
                )}

                {/* V10.25: 增強版 AI 分析 */}
                <div className="mt-4">
                  <EnhancedAIPanel
                    stockId={stock.stock_id}
                    stockName={stock.name}
                    onSelectStock={onSelectStock}
                  />
                </div>
              </div>
            )}

            {/* 基本面 */}
            {activeTab === 'fundamental' && (
              <div className="bg-slate-800/30 rounded-xl p-4">
                <h3 className="text-white font-semibold mb-4">基本面分析</h3>
                {fundamental ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                      <div className="text-slate-400 text-sm">本益比 P/E</div>
                      <div className="text-2xl font-bold text-white mt-1">
                        {fundamental.pe_ratio?.toFixed(1) || '-'}
                      </div>
                      <div className="text-xs text-slate-500">
                        {fundamental.pe_ratio < 15 ? '低估值' : fundamental.pe_ratio > 30 ? '高估值' : '合理範圍'}
                      </div>
                    </div>
                    <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                      <div className="text-slate-400 text-sm">股價淨值比 P/B</div>
                      <div className="text-2xl font-bold text-white mt-1">
                        {fundamental.pb_ratio?.toFixed(2) || '-'}
                      </div>
                      <div className="text-xs text-slate-500">
                        {fundamental.pb_ratio < 1.5 ? '低於淨值' : '略高於淨值'}
                      </div>
                    </div>
                    <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                      <div className="text-slate-400 text-sm">殖利率</div>
                      <div className={`text-2xl font-bold mt-1 ${
                        (fundamental.dividend_yield || 0) > 4 ? 'text-red-400' : 'text-white'
                      }`}>
                        {fundamental.dividend_yield?.toFixed(2) || '-'}%
                      </div>
                      <div className="text-xs text-slate-500">
                        {(fundamental.dividend_yield || 0) > 4 ? '高殖利率' : '一般'}
                      </div>
                    </div>
                    <div className="text-center p-4 bg-slate-700/30 rounded-lg">
                      <div className="text-slate-400 text-sm">ROE</div>
                      <div className={`text-2xl font-bold mt-1 ${
                        (fundamental.roe || 0) > 15 ? 'text-red-400' : 'text-white'
                      }`}>
                        {fundamental.roe?.toFixed(1) || '-'}%
                      </div>
                      <div className="text-xs text-slate-500">
                        {(fundamental.roe || 0) > 15 ? '獲利能力佳' : '一般'}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>📊 基本面資料載入中...</p>
                    <p className="text-sm mt-2">若持續無法載入，可能是資料暫時無法取得</p>
                  </div>
                )}
              </div>
            )}

            {/* 籌碼面 */}
            {activeTab === 'chip' && (
              <div className="bg-slate-800/30 rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-semibold">籌碼分析</h3>
                  {/* V10.13.4: 顯示資料日期 */}
                  {(institutional?.date) && (
                    <span className="text-xs text-slate-500 bg-slate-700/50 px-2 py-1 rounded">
                      📅 資料日期: {institutional.date.replace(/(\d{4})(\d{2})(\d{2})/, '$1/$2/$3')}
                    </span>
                  )}
                </div>
                {institutional ? (
                  <div className="space-y-3">
                    {/* 外資 - V10.13.4: 修正數據結構對應 */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">🌍</span>
                          <span className="text-white font-medium">外資</span>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold text-lg ${
                            (institutional.foreign?.net || institutional.foreign_net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {institutional.foreign?.net_display || institutional.foreign_net_display || (institutional.foreign_net ? `${institutional.foreign_net.toLocaleString()} 張` : '-')}
                          </div>
                        </div>
                      </div>
                      {/* 買賣明細 */}
                      {(institutional.foreign?.buy || institutional.foreign?.sell) && (
                        <div className="flex justify-end gap-4 mt-1 text-xs">
                          <span className="text-red-400/70">買 {(institutional.foreign?.buy || 0).toLocaleString()}</span>
                          <span className="text-emerald-400/70">賣 {(institutional.foreign?.sell || 0).toLocaleString()}</span>
                        </div>
                      )}
                    </div>

                    {/* 投信 - V10.13.4: 修正數據結構對應 */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">🏦</span>
                          <span className="text-white font-medium">投信</span>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold text-lg ${
                            (institutional.investment_trust?.net || institutional.trust_net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {institutional.investment_trust?.net_display || institutional.trust_net_display || (institutional.trust_net ? `${institutional.trust_net.toLocaleString()} 張` : '-')}
                          </div>
                        </div>
                      </div>
                      {(institutional.investment_trust?.buy || institutional.investment_trust?.sell) && (
                        <div className="flex justify-end gap-4 mt-1 text-xs">
                          <span className="text-red-400/70">買 {(institutional.investment_trust?.buy || 0).toLocaleString()}</span>
                          <span className="text-emerald-400/70">賣 {(institutional.investment_trust?.sell || 0).toLocaleString()}</span>
                        </div>
                      )}
                    </div>

                    {/* 自營商 - V10.13.4: 修正數據結構對應 */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">🏢</span>
                          <span className="text-white font-medium">自營商</span>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold text-lg ${
                            (institutional.dealer?.net || institutional.dealer_net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {institutional.dealer?.net_display || institutional.dealer_net_display || (institutional.dealer_net ? `${institutional.dealer_net.toLocaleString()} 張` : '-')}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 三大法人合計 - V10.13.4: 修正數據結構對應 */}
                    <div className={`mt-2 p-4 rounded-lg border-2 ${
                      (institutional.total_net || 0) >= 0
                        ? 'bg-red-500/10 border-red-500/30'
                        : 'bg-emerald-500/10 border-emerald-500/30'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="text-white font-medium">三大法人合計</span>
                        <div className={`font-bold text-xl ${
                          (institutional.total_net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                        }`}>
                          {institutional.total_net_display || (institutional.total_net ? `${institutional.total_net.toLocaleString()} 張` : '-')}
                        </div>
                      </div>
                      <div className="text-slate-400 text-sm mt-2">
                        {(institutional.total_net || 0) > 0 
                          ? '📈 法人偏多，籌碼面正向' 
                          : (institutional.total_net || 0) < 0 
                            ? '📉 法人偏空，籌碼面負向'
                            : '➡️ 法人中性'}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>🏦 籌碼資料載入中...</p>
                    <p className="text-sm mt-2">若持續無法載入，可能是資料暫時無法取得</p>
                  </div>
                )}
              </div>
            )}

            {/* V10.15: K線圖 */}
            {activeTab === 'chart' && (
              <div className="space-y-4">
                {history && history.length > 0 ? (
                  <CandlestickChart
                    data={history}
                    stockId={stock.stock_id}
                    stockName={stock.name}
                    width={700}
                    height={400}
                    showVolume={true}
                    showMA={true}
                  />
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>📊 K線資料載入中...</p>
                  </div>
                )}

                {/* 法人買賣追蹤圖 */}
                <InstitutionalChart
                  stockId={stock.stock_id}
                  stockName={stock.name}
                  days={20}
                />
              </div>
            )}

            {/* V10.15: 績效分析 */}
            {activeTab === 'performance' && (
              <PerformanceDashboard
                stockId={stock.stock_id}
                stockName={stock.name}
              />
            )}

            {/* V10.16: 綜合投資策略 */}
            {activeTab === 'strategy' && (
              <StrategyDashboard
                stockId={stock.stock_id}
                stockName={stock.name}
              />
            )}

            {/* 新聞 */}
            {activeTab === 'news' && (
              <NewsList news={news} />
            )}
          </>
        )}
      </div>
    </div>
  );
};

// ===== 投資組合面板 =====
const PortfolioPanel = ({ onSelectStock }) => {
  const [holdings, setHoldings] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    stockId: '',
    buyPrice: '',
    quantity: '',
    buyDate: new Date().toISOString().split('T')[0],
    note: ''
  });

  // 🆕 V10.14: 追蹤股票列表（localStorage）
  const [trackedStocks, setTrackedStocks] = useState([]);

  // 🆕 V10.15: 追蹤股票即時價格
  const [trackedPrices, setTrackedPrices] = useState({});
  const [pricesLoading, setPricesLoading] = useState(false);

  // 🆕 V10.15: 計算追蹤股票總覽
  const [trackedSummary, setTrackedSummary] = useState(null);

  const fetchPortfolio = async () => {
    setLoading(true);
    try {
      const [holdingsRes, summaryRes] = await Promise.all([
        stockAPI.getPortfolio(),
        stockAPI.getPortfolioSummary()
      ]);
      setHoldings(holdingsRes.holdings || []);
      setSummary(summaryRes.summary);
    } catch (err) {
      console.error('載入投資組合失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  // 🆕 V10.14: 載入追蹤股票
  const loadTrackedStocks = () => {
    setTrackedStocks(PortfolioManager.getPortfolio());
  };

  // 🆕 V10.15: 獲取追蹤股票的即時價格
  const fetchTrackedPrices = async (stocks) => {
    if (!stocks || stocks.length === 0) return;

    setPricesLoading(true);
    const prices = {};

    try {
      await Promise.all(
        stocks.map(async (stock) => {
          try {
            const res = await stockAPI.getStockInfo(stock.stock_id);
            if (res.stock) {
              prices[stock.stock_id] = {
                price: res.stock.close || res.stock.price,
                change: res.stock.change || 0,
                change_percent: res.stock.change_percent || 0,
              };
            }
          } catch (e) {
            // 靜默處理價格獲取失敗
          }
        })
      );

      setTrackedPrices(prices);

      // 計算追蹤股票總覽
      let totalProfitLoss = 0;
      let profitCount = 0;
      let lossCount = 0;

      stocks.forEach(stock => {
        const currentPrice = prices[stock.stock_id]?.price;
        if (currentPrice && stock.added_price) {
          const profitPct = ((currentPrice - stock.added_price) / stock.added_price) * 100;
          totalProfitLoss += profitPct;
          if (profitPct >= 0) profitCount++;
          else lossCount++;
        }
      });

      setTrackedSummary({
        count: stocks.length,
        avgProfitLoss: stocks.length > 0 ? (totalProfitLoss / stocks.length).toFixed(2) : 0,
        profitCount,
        lossCount,
        winRate: stocks.length > 0 ? ((profitCount / stocks.length) * 100).toFixed(1) : 0,
      });

    } catch (err) {
      console.error('取得即時價格失敗:', err);
    } finally {
      setPricesLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    loadTrackedStocks();
  }, []);

  // 🆕 V10.15: 載入追蹤股票時更新價格
  useEffect(() => {
    if (trackedStocks.length > 0) {
      fetchTrackedPrices(trackedStocks);
    }
  }, [trackedStocks]);
  
  // 🆕 V10.14: 移除追蹤
  const handleRemoveTracked = (stockId) => {
    if (!window.confirm('確定要取消追蹤嗎？')) return;
    PortfolioManager.removeFromPortfolio(stockId);
    loadTrackedStocks();
  };

  const handleAddHolding = async (e) => {
    e.preventDefault();
    if (!formData.stockId || !formData.buyPrice || !formData.quantity) {
      alert('請填寫必要欄位');
      return;
    }
    try {
      await stockAPI.addToPortfolio(
        formData.stockId,
        parseFloat(formData.buyPrice),
        parseInt(formData.quantity),
        formData.buyDate,
        formData.note
      );
      setShowAddForm(false);
      setFormData({ stockId: '', buyPrice: '', quantity: '', buyDate: new Date().toISOString().split('T')[0], note: '' });
      fetchPortfolio();
    } catch (err) {
      alert('新增失敗: ' + err.message);
    }
  };

  const handleDelete = async (holdingId) => {
    if (!window.confirm('確定要刪除這筆持股嗎？')) return;
    try {
      await stockAPI.deleteFromPortfolio(holdingId);
      fetchPortfolio();
    } catch (err) {
      alert('刪除失敗: ' + err.message);
    }
  };

  const handleSell = async (holding) => {
    const sellPrice = prompt('請輸入賣出價格:', holding.current_price || holding.buy_price);
    if (!sellPrice) return;
    try {
      const result = await stockAPI.sellFromPortfolio(holding.id, parseFloat(sellPrice));
      if (result.success) {
        alert(`賣出成功！損益: ${result.profit >= 0 ? '+' : ''}${result.profit?.toFixed(0)} 元`);
        fetchPortfolio();
      }
    } catch (err) {
      alert('賣出失敗: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* 🆕 V10.15: 追蹤股票區塊（含即時損益） */}
      {trackedStocks.length > 0 && (
        <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 rounded-xl p-6 border border-amber-500/30">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-white font-bold text-lg">⭐ 追蹤股票</h3>
              {pricesLoading && (
                <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
              )}
            </div>
            <div className="flex items-center gap-4">
              {/* 🆕 V10.15: 追蹤股票統計 */}
              {trackedSummary && (
                <div className="flex items-center gap-3 text-sm">
                  <span className={`font-medium ${parseFloat(trackedSummary.avgProfitLoss) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    平均 {parseFloat(trackedSummary.avgProfitLoss) >= 0 ? '+' : ''}{trackedSummary.avgProfitLoss}%
                  </span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400">
                    勝率 <span className="text-white">{trackedSummary.winRate}%</span>
                  </span>
                </div>
              )}
              <span className="text-amber-400 text-sm bg-amber-500/20 px-2 py-1 rounded">{trackedStocks.length} 檔</span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-3">
            {trackedStocks.map(stock => {
              const addedDate = new Date(stock.added_date);
              const dateStr = `${addedDate.getMonth() + 1}/${addedDate.getDate()}`;
              const priceInfo = trackedPrices[stock.stock_id];
              const currentPrice = priceInfo?.price;
              const profitPct = currentPrice && stock.added_price
                ? ((currentPrice - stock.added_price) / stock.added_price * 100)
                : null;
              const isProfit = profitPct !== null && profitPct >= 0;

              // 止損/目標判斷
              const stopLoss = stock.added_price * 0.95;
              const target = stock.added_price * 1.10;
              const hitStopLoss = currentPrice && currentPrice <= stopLoss;
              const hitTarget = currentPrice && currentPrice >= target;

              return (
                <div
                  key={stock.stock_id}
                  className={`bg-slate-800/50 rounded-lg p-3 border transition-colors cursor-pointer hover:bg-slate-700/50 ${
                    hitStopLoss ? 'border-red-500/50' :
                    hitTarget ? 'border-emerald-500/50' :
                    'border-slate-700/50'
                  }`}
                  onClick={() => onSelectStock && onSelectStock(stock)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-semibold">{stock.name}</span>
                        <span className="text-slate-500 text-sm">{stock.stock_id}</span>
                        {hitTarget && <span className="text-xs px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded">達標</span>}
                        {hitStopLoss && <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">止損</span>}
                      </div>

                      {/* 🆕 V10.15: 即時價格與損益 */}
                      <div className="flex items-center gap-4 mt-2">
                        <div>
                          <span className="text-slate-500 text-xs">現價</span>
                          <div className="text-white font-medium">
                            {currentPrice ? `$${currentPrice.toFixed(2)}` : '-'}
                            {priceInfo && (
                              <span className={`text-xs ml-1 ${priceInfo.change_percent >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                ({priceInfo.change_percent >= 0 ? '+' : ''}{priceInfo.change_percent?.toFixed(2)}%)
                              </span>
                            )}
                          </div>
                        </div>
                        <div>
                          <span className="text-slate-500 text-xs">買入價</span>
                          <div className="text-slate-300">${stock.added_price?.toFixed(2)}</div>
                        </div>
                        {profitPct !== null && (
                          <div>
                            <span className="text-slate-500 text-xs">損益</span>
                            <div className={`font-bold ${isProfit ? 'text-red-400' : 'text-emerald-400'}`}>
                              {isProfit ? '+' : ''}{profitPct.toFixed(2)}%
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-3 mt-2 text-sm">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          stock.added_score >= 70 ? 'bg-red-500/20 text-red-400' :
                          stock.added_score >= 55 ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>
                          {stock.added_score}分
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          stock.added_signal?.includes('買') ? 'bg-red-500/20 text-red-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>
                          {stock.added_signal}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                        <span>📅 {dateStr} 加入</span>
                        <span className="text-slate-600">|</span>
                        <span className={hitStopLoss ? 'text-red-400' : ''}>止損 ${stopLoss.toFixed(0)}</span>
                        <span className="text-slate-600">|</span>
                        <span className={hitTarget ? 'text-emerald-400' : ''}>目標 ${target.toFixed(0)}</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveTracked(stock.stock_id);
                      }}
                      className="px-2 py-1 text-xs text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                      title="取消追蹤"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 🆕 V10.15: 重新整理按鈕 */}
          <div className="flex justify-end mt-4">
            <button
              onClick={() => fetchTrackedPrices(trackedStocks)}
              disabled={pricesLoading}
              className="px-3 py-1 text-xs text-amber-400 hover:bg-amber-500/10 rounded transition-colors disabled:opacity-50"
            >
              🔄 更新價格
            </button>
          </div>
        </div>
      )}
      
      {/* 總覽卡片 */}
      {summary && (
        <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
          <h3 className="text-white font-bold text-lg mb-4">💼 投資組合總覽</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-slate-400 text-xs">持股數量</div>
              <div className="text-2xl font-bold text-white">{summary.total_holdings}</div>
            </div>
            <div className="text-center">
              <div className="text-slate-400 text-xs">投入成本</div>
              <div className="text-xl font-bold text-white">${summary.total_cost?.toLocaleString()}</div>
            </div>
            <div className="text-center">
              <div className="text-slate-400 text-xs">市值</div>
              <div className="text-xl font-bold text-white">${summary.total_market_value?.toLocaleString() || '-'}</div>
            </div>
            <div className="text-center">
              <div className="text-slate-400 text-xs">損益</div>
              <div className={`text-xl font-bold ${(summary.total_profit || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {(summary.total_profit || 0) >= 0 ? '+' : ''}{summary.total_profit?.toLocaleString() || 0}
                <span className="text-sm ml-1">({summary.total_profit_percent?.toFixed(1)}%)</span>
              </div>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-600/50 flex justify-between text-sm">
            <span className="text-slate-400">勝率: <span className="text-white">{summary.win_rate}%</span></span>
            <span className="text-red-400">獲利: {summary.profitable_count}</span>
            <span className="text-emerald-400">虧損: {summary.loss_count}</span>
          </div>
        </div>
      )}

      {/* 新增/匯出按鈕 */}
      <div className="flex justify-between items-center">
        <h3 className="text-white font-semibold">持股列表</h3>
        <div className="flex gap-2">
          {/* 🆕 V10.15: 匯出投組按鈕 */}
          <ExportButton type="portfolio" label="匯出" />
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors"
          >
            {showAddForm ? '取消' : '➕ 新增持股'}
          </button>
        </div>
      </div>

      {/* 新增表單 */}
      {showAddForm && (
        <form onSubmit={handleAddHolding} className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 text-sm">股票代號 *</label>
              <input
                type="text"
                value={formData.stockId}
                onChange={(e) => setFormData({...formData, stockId: e.target.value})}
                placeholder="例: 2330"
                className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm">買入價格 *</label>
              <input
                type="number"
                step="0.01"
                value={formData.buyPrice}
                onChange={(e) => setFormData({...formData, buyPrice: e.target.value})}
                placeholder="例: 580"
                className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm">股數 *</label>
              <input
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                placeholder="例: 1000"
                className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 text-sm">買入日期</label>
              <input
                type="date"
                value={formData.buyDate}
                onChange={(e) => setFormData({...formData, buyDate: e.target.value})}
                className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-slate-400 text-sm">備註</label>
            <input
              type="text"
              value={formData.note}
              onChange={(e) => setFormData({...formData, note: e.target.value})}
              placeholder="選填"
              className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
            />
          </div>
          <button
            type="submit"
            className="w-full py-2 bg-green-600 hover:bg-green-500 rounded-lg font-medium transition-colors"
          >
            確認新增
          </button>
        </form>
      )}

      {/* 持股列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : holdings.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <p className="text-4xl mb-4">📊</p>
          <p>尚無持股</p>
          <p className="text-sm mt-2">點擊上方「新增持股」開始建立投資組合</p>
        </div>
      ) : (
        <div className="space-y-3">
          {holdings.map(holding => {
            const isProfit = (holding.profit || 0) >= 0;
            return (
              <div
                key={holding.id}
                className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-semibold">{holding.stock_name}</span>
                      <span className="text-slate-500 text-sm">{holding.stock_id}</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
                      <div>
                        <span className="text-slate-500">買入價</span>
                        <div className="text-white">${holding.buy_price}</div>
                      </div>
                      <div>
                        <span className="text-slate-500">現價</span>
                        <div className="text-white">${holding.current_price?.toFixed(2) || '-'}</div>
                      </div>
                      <div>
                        <span className="text-slate-500">股數</span>
                        <div className="text-white">{holding.quantity?.toLocaleString()}</div>
                      </div>
                      <div>
                        <span className="text-slate-500">損益</span>
                        <div className={isProfit ? 'text-red-400' : 'text-emerald-400'}>
                          {isProfit ? '+' : ''}{holding.profit?.toFixed(0) || 0}
                          <span className="text-xs ml-1">({holding.profit_percent?.toFixed(1) || 0}%)</span>
                        </div>
                      </div>
                    </div>
                    {holding.note && (
                      <div className="text-slate-500 text-xs mt-2">📝 {holding.note}</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSell(holding)}
                      className="px-3 py-1 bg-orange-600/80 hover:bg-orange-500 rounded text-xs transition-colors"
                    >
                      賣出
                    </button>
                    <button
                      onClick={() => handleDelete(holding.id)}
                      className="px-3 py-1 bg-red-600/80 hover:bg-red-500 rounded text-xs transition-colors"
                    >
                      刪除
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ===== 回測面板 =====
const BacktestPanel = () => {
  // 預設策略清單
  const defaultStrategies = [
    { id: 'ma_crossover', name: '均線交叉策略', description: '當 MA5 向上穿越 MA20 時買進', risk: '中' },
    { id: 'rsi', name: 'RSI 超買超賣策略', description: 'RSI < 30 買進，RSI > 70 賣出', risk: '中' },
    { id: 'macd', name: 'MACD 策略', description: 'MACD 線穿越零軸', risk: '中' },
    { id: 'bollinger', name: '布林通道策略', description: '價格觸及上下軌', risk: '低' },
    { id: 'volume_breakout', name: '量價突破策略', description: '帶量突破均線', risk: '高' },
    { id: 'combined', name: '綜合策略', description: 'MA + RSI + MACD 綜合判斷', risk: '低' },
  ];
  
  const [strategies, setStrategies] = useState(defaultStrategies);
  const [selectedStock, setSelectedStock] = useState('2330');
  const [selectedStockName, setSelectedStockName] = useState('台積電');
  const [selectedStrategy, setSelectedStrategy] = useState('ma_crossover');
  const [months, setMonths] = useState(6);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // 🆕 完整股票清單（從 API 載入）
  const [allStocksList, setAllStocksList] = useState([]);
  const [stocksLoading, setStocksLoading] = useState(true);

  // 股票名稱對照表（只放確定正確的，其他依賴 API 清單）
  const stockNameMap = {
    // 個股
    '2374': '佳能', '2330': '台積電', '2454': '聯發科', '2303': '聯電',
    '2317': '鴻海', '2382': '廣達', '2881': '富邦金', '2891': '中信金',
    '3711': '日月光投控', '2308': '台達電', '3034': '聯詠', '2357': '華碩',
    '2379': '瑞昱',
    // ETF（5-6碼）
    '0050': '元大台灣50', '0056': '元大高股息', '006208': '富邦台50',
    '00878': '國泰永續高股息', '00919': '群益台灣精選高息',
    '00893': '國泰智能電動車', '00891': '中信關鍵半導體',
    '00892': '富邦台灣半導體', '00881': '國泰台灣5G+',
    '00713': '元大台灣高息低波', '00850': '元大臺灣ESG永續',
    '00692': '富邦公司治理', '00701': '國泰低波動股利30',
    '00733': '富邦臺灣中小', '00757': '統一FANG+',
    '00861': '元大全球未來關鍵科技', '00830': '國泰費城半導體',
    '00882': '中信中國高股息', '00885': '富邦越南',
    '00896': '中信綠能及電動車', '00900': '富邦特選高股息30',
    '00912': '中信臺灣智慧50', '00915': '凱基優選高股息30',
    '00929': '復華台灣科技優息', '00934': '中信成長高股息',
    '00936': '台新臺灣永續高息中小',
  };

  // 查詢股票名稱
  const fetchStockName = async (stockId) => {
    // 1. 先從完整清單找（API 載入的）
    const foundInAll = allStocksList.find(s => s.id === stockId);
    if (foundInAll) {
      setSelectedStockName(foundInAll.name);
      return;
    }
    
    // 2. 從 popularStocks 找
    const found = popularStocks.find(s => s.id === stockId);
    if (found) {
      setSelectedStockName(found.name);
      return;
    }
    
    // 3. 從備用對照表找
    if (stockNameMap[stockId]) {
      setSelectedStockName(stockNameMap[stockId]);
      return;
    }
    
    // 4. 從 API 查詢（嘗試多個端點）
    try {
      // 先試 info API
      let res = await fetch(`${API_BASE}/api/stocks/info/${stockId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.name) {
          setSelectedStockName(data.name);
          return;
        }
      }
      
      // 再試 TWSE API
      res = await fetch(`${API_BASE}/api/stocks/twse/stock/${stockId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.name) {
          setSelectedStockName(data.name);
          return;
        }
      }
      
      // 都找不到
      setSelectedStockName('（未知）');
    } catch (err) {
      console.error('查詢股票名稱失敗:', err);
      setSelectedStockName('');
    }
  };

  // 擴充股票清單（含標籤，支援名稱搜尋）
  const popularStocks = [
    // 半導體
    { id: '2330', name: '台積電', tags: ['半導體', 'AI', '先進製程', '晶圓代工'] },
    { id: '2454', name: '聯發科', tags: ['半導體', 'IC設計', 'AI', '手機晶片'] },
    { id: '2303', name: '聯電', tags: ['半導體', '晶圓代工', '成熟製程'] },
    { id: '3711', name: '日月光投控', tags: ['半導體', '封測', '先進封裝'] },
    { id: '2379', name: '瑞昱', tags: ['半導體', 'IC設計', '網通晶片'] },
    { id: '3034', name: '聯詠', tags: ['半導體', 'IC設計', '驅動IC'] },
    { id: '2344', name: '華邦電', tags: ['半導體', '記憶體', 'Flash'] },
    { id: '3037', name: '欣興', tags: ['半導體', 'PCB', 'ABF載板'] },
    { id: '6415', name: '矽力-KY', tags: ['半導體', 'IC設計', '電源管理'] },
    { id: '2408', name: '南亞科', tags: ['半導體', '記憶體', 'DRAM'] },
    // 電子/AI伺服器
    { id: '2317', name: '鴻海', tags: ['電子', '代工', 'AI伺服器', '電動車'] },
    { id: '2382', name: '廣達', tags: ['電子', 'AI伺服器', 'GB200', '筆電'] },
    { id: '2357', name: '華碩', tags: ['電子', '筆電', '主機板', 'AI'] },
    { id: '2395', name: '研華', tags: ['電子', '工業電腦', 'AIoT'] },
    { id: '3231', name: '緯創', tags: ['電子', 'AI伺服器', '筆電'] },
    { id: '2308', name: '台達電', tags: ['電子', '電源', '電動車', '充電樁'] },
    { id: '2301', name: '光寶科', tags: ['電子', '電源', 'LED'] },
    { id: '2356', name: '英業達', tags: ['電子', 'AI伺服器', '筆電'] },
    { id: '2324', name: '仁寶', tags: ['電子', '筆電', '代工'] },
    { id: '3017', name: '奇鋐', tags: ['電子', '散熱', 'AI伺服器'] },
    // 金融
    { id: '2881', name: '富邦金', tags: ['金融', '金控', '壽險', '銀行'] },
    { id: '2882', name: '國泰金', tags: ['金融', '金控', '壽險'] },
    { id: '2891', name: '中信金', tags: ['金融', '金控', '銀行'] },
    { id: '2884', name: '玉山金', tags: ['金融', '金控', '銀行'] },
    { id: '2886', name: '兆豐金', tags: ['金融', '金控', '銀行', '官股'] },
    { id: '2887', name: '台新金', tags: ['金融', '金控', '銀行'] },
    { id: '2892', name: '第一金', tags: ['金融', '金控', '銀行', '官股'] },
    { id: '2880', name: '華南金', tags: ['金融', '金控', '銀行', '官股'] },
    { id: '5880', name: '合庫金', tags: ['金融', '金控', '銀行', '官股'] },
    { id: '5876', name: '上海商銀', tags: ['金融', '銀行'] },
    // 傳產
    { id: '1301', name: '台塑', tags: ['傳產', '塑膠', '石化'] },
    { id: '1303', name: '南亞', tags: ['傳產', '塑膠', 'PCB'] },
    { id: '1326', name: '台化', tags: ['傳產', '塑膠', '石化'] },
    { id: '2002', name: '中鋼', tags: ['傳產', '鋼鐵', '基建'] },
    { id: '1101', name: '台泥', tags: ['傳產', '水泥', '基建'] },
    { id: '1216', name: '統一', tags: ['傳產', '食品', '零售'] },
    { id: '2912', name: '統一超', tags: ['傳產', '零售', '7-11'] },
    { id: '9910', name: '豐泰', tags: ['傳產', '製鞋', 'Nike'] },
    { id: '1227', name: '佳格', tags: ['傳產', '食品'] },
    { id: '2207', name: '和泰車', tags: ['傳產', '汽車', 'Toyota'] },
    // 航運/航空
    { id: '2603', name: '長榮', tags: ['航運', '貨櫃', '海運'] },
    { id: '2609', name: '陽明', tags: ['航運', '貨櫃', '海運'] },
    { id: '2615', name: '萬海', tags: ['航運', '貨櫃', '海運'] },
    { id: '2610', name: '華航', tags: ['航空', '客運'] },
    { id: '2618', name: '長榮航', tags: ['航空', '客運'] },
    // 電信
    { id: '2412', name: '中華電', tags: ['電信', '5G', '官股'] },
    { id: '3045', name: '台灣大', tags: ['電信', '5G'] },
    { id: '4904', name: '遠傳', tags: ['電信', '5G'] },
    // 生技
    { id: '6446', name: '藥華藥', tags: ['生技', '新藥', '罕病'] },
    { id: '4743', name: '合一', tags: ['生技', '新藥'] },
    { id: '6472', name: '保瑞', tags: ['生技', 'CDMO'] },
    // AI/伺服器
    { id: '2345', name: '智邦', tags: ['電子', 'AI', '網通', '交換器'] },
    { id: '6669', name: '緯穎', tags: ['電子', 'AI伺服器', '雲端'] },
    { id: '3653', name: '健策', tags: ['電子', 'AI伺服器', '散熱'] },
    { id: '2049', name: '上銀', tags: ['傳產', '自動化', '機器人'] },
    { id: '2059', name: '川湖', tags: ['電子', '伺服器', '滑軌'] },
    // ETF - 市值型
    { id: '0050', name: '元大台灣50', tags: ['ETF', '台股', '大型股', '指數'] },
    { id: '006208', name: '富邦台50', tags: ['ETF', '台股', '大型股', '指數'] },
    { id: '00850', name: '元大臺灣ESG永續', tags: ['ETF', '台股', 'ESG', '永續'] },
    { id: '00692', name: '富邦公司治理', tags: ['ETF', '台股', '公司治理'] },
    { id: '00733', name: '富邦臺灣中小', tags: ['ETF', '台股', '中小型股'] },
    // ETF - 高股息
    { id: '0056', name: '元大高股息', tags: ['ETF', '高股息', '配息', '存股'] },
    { id: '00878', name: '國泰永續高股息', tags: ['ETF', '高股息', '配息', 'ESG', '存股'] },
    { id: '00919', name: '群益台灣精選高息', tags: ['ETF', '高股息', '配息', '存股'] },
    { id: '00713', name: '元大台灣高息低波', tags: ['ETF', '高股息', '低波動', '存股'] },
    { id: '00701', name: '國泰低波動股利30', tags: ['ETF', '高股息', '低波動'] },
    { id: '00929', name: '復華台灣科技優息', tags: ['ETF', '高股息', '科技', '月配'] },
    { id: '00934', name: '中信成長高股息', tags: ['ETF', '高股息', '成長'] },
    { id: '00936', name: '台新臺灣永續高息中小', tags: ['ETF', '高股息', '中小型'] },
    // ETF - 主題型
    { id: '00893', name: '國泰智能電動車', tags: ['ETF', '電動車', 'EV', '特斯拉', '新能源'] },
    { id: '00896', name: '中信綠能及電動車', tags: ['ETF', '電動車', '綠能', '新能源'] },
    { id: '00891', name: '中信關鍵半導體', tags: ['ETF', '半導體', 'AI', '晶片'] },
    { id: '00892', name: '富邦台灣半導體', tags: ['ETF', '半導體', '台積電'] },
    { id: '00881', name: '國泰台灣5G+', tags: ['ETF', '5G', '通訊', '電信'] },
    { id: '00757', name: '統一FANG+', tags: ['ETF', '美股', '科技', 'FANG'] },
    { id: '00830', name: '國泰費城半導體', tags: ['ETF', '美股', '半導體', 'SOX'] },
    { id: '00861', name: '元大全球未來關鍵科技', tags: ['ETF', '全球', '科技', 'AI'] },
    // 其他熱門
    { id: '3008', name: '大立光', tags: ['電子', '光學', '鏡頭', 'iPhone'] },
    { id: '2474', name: '可成', tags: ['電子', '機殼', '金屬'] },
    { id: '2377', name: '微星', tags: ['電子', '主機板', '電競', '顯卡'] },
    { id: '2353', name: '宏碁', tags: ['電子', '筆電', '電競'] },
    { id: '2327', name: '國巨', tags: ['電子', '被動元件', 'MLCC'] },
    { id: '3443', name: '創意', tags: ['半導體', 'IC設計', 'ASIC'] },
    { id: '6550', name: '北極星藥業-KY', tags: ['生技', '新藥'] },
    { id: '2923', name: '鼎固-KY', tags: ['傳產', '不動產'] },
    { id: '2436', name: '偉詮電', tags: ['半導體', 'IC設計'] },
    { id: '2449', name: '京元電子', tags: ['半導體', '封測', '測試'] },
  ];

  // 載入策略清單 + 完整股票清單
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const data = await stockAPI.getBacktestStrategies();
        if (data.strategies && data.strategies.length > 0) {
          setStrategies(data.strategies);
        } else {
          setStrategies(defaultStrategies);
        }
      } catch (err) {
        console.error('載入策略失敗，使用預設清單:', err);
        setStrategies(defaultStrategies);
      }
    };
    
    // 🆕 載入完整股票清單
    const loadAllStocks = async () => {
      setStocksLoading(true);
      try {
        const res = await fetch('${API_BASE}/api/stocks/stocks/list');
        if (res.ok) {
          const data = await res.json();
          if (data.success && data.stocks && data.stocks.length > 0) {
            setAllStocksList(data.stocks);
          } else {
            setAllStocksList(popularStocks);
          }
        } else {
          setAllStocksList(popularStocks);
        }
      } catch (err) {
        console.error('載入股票清單失敗:', err);
        setAllStocksList(popularStocks);
      } finally {
        setStocksLoading(false);
      }
    };
    
    loadStrategies();
    loadAllStocks();
  }, []);

  // 執行回測
  const handleRunBacktest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await stockAPI.runBacktest(selectedStock, selectedStrategy, months);
      if (data.error) {
        // 支援新的錯誤格式
        setError({
          error: data.error,
          reason: data.reason || null,
          suggestions: data.suggestions || null
        });
      } else {
        setResult(data);
      }
    } catch (err) {
      setError({ error: '回測執行失敗: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  // 淨值曲線組件
  const EquityCurve = ({ data }) => {
    if (!data || data.length === 0) return null;
    
    const width = 500;
    const height = 200;
    const padding = 40;
    
    const values = data.map(d => d.value);
    const minVal = Math.min(...values) * 0.99;
    const maxVal = Math.max(...values) * 1.01;
    
    const xScale = (i) => padding + (i / (data.length - 1)) * (width - padding * 2);
    const yScale = (v) => height - padding - ((v - minVal) / (maxVal - minVal)) * (height - padding * 2);
    
    const points = data.map((d, i) => `${xScale(i)},${yScale(d.value)}`).join(' ');
    
    // 初始資金線
    const initialLine = yScale(data[0]?.value || 1000000);
    
    return (
      <svg width="100%" viewBox={`0 0 ${width} ${height}`} className="mt-4">
        {/* 背景格線 */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#334155" />
        
        {/* 初始資金線 */}
        <line x1={padding} y1={initialLine} x2={width - padding} y2={initialLine} stroke="#6b7280" strokeDasharray="4" />
        
        {/* 淨值曲線 */}
        <polyline
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          points={points}
        />
        
        {/* 起點和終點標記 */}
        <circle cx={xScale(0)} cy={yScale(values[0])} r="4" fill="#3b82f6" />
        <circle cx={xScale(data.length - 1)} cy={yScale(values[values.length - 1])} r="4" fill={values[values.length - 1] >= values[0] ? '#ef4444' : '#10b981'} />
        
        {/* 標籤 */}
        <text x={padding} y={height - 10} fill="#94a3b8" fontSize="12">{data[0]?.date}</text>
        <text x={width - padding} y={height - 10} fill="#94a3b8" fontSize="12" textAnchor="end">{data[data.length - 1]?.date}</text>
        <text x={padding - 5} y={initialLine + 4} fill="#6b7280" fontSize="10" textAnchor="end">初始</text>
      </svg>
    );
  };

  // 股票輸入狀態
  const [stockInput, setStockInput] = useState('2330');
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // 🆕 優先使用 API 載入的完整清單，fallback 到 popularStocks
  // 合併股票清單（優先使用 popularStocks 的名稱，因為更完整）
  const searchableStocks = (() => {
    if (allStocksList.length === 0) return popularStocks;
    
    // 建立 ID -> 名稱 對照（優先使用 popularStocks 和 stockNameMap）
    const nameMap = {};
    popularStocks.forEach(s => { nameMap[s.id] = s.name; });
    Object.entries(stockNameMap).forEach(([id, name]) => { nameMap[id] = name; });
    
    // 合併清單
    const merged = allStocksList.map(s => ({
      id: s.id,
      name: nameMap[s.id] || s.name  // 優先使用我們定義的名稱
    }));
    
    // 加入 popularStocks 中有但 API 沒有的
    popularStocks.forEach(ps => {
      if (!merged.find(m => m.id === ps.id)) {
        merged.push(ps);
      }
    });
    
    return merged;
  })();
  
  // 過濾建議清單（從完整清單中搜尋）
  const filteredStocks = stockInput 
    ? searchableStocks.filter(s => 
        s.id.includes(stockInput) || 
        s.name.includes(stockInput)
      ).slice(0, 10)  // 顯示更多結果
    : popularStocks.slice(0, 8);  // 沒輸入時顯示熱門股票

  return (
    <div className="space-y-6">
      {/* 設定區 */}
      <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-500/30">
        <h3 className="text-white font-bold text-lg mb-4">📈 回測設定</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 股票選擇 - 合併為單一搜尋框 */}
          <div className="relative">
            <label className="text-slate-400 text-sm block mb-2">
              股票代號/名稱 
              {stocksLoading ? (
                <span className="text-yellow-400 ml-2">（載入中...）</span>
              ) : (
                <span className="text-green-400 ml-2">（{searchableStocks.length} 檔可搜尋）</span>
              )}
            </label>
            <input
              type="text"
              value={stockInput}
              onChange={(e) => {
                setStockInput(e.target.value);
                setShowSuggestions(true);
                // 如果是有效代號，同步更新並查詢名稱
                if (e.target.value.match(/^\d{4,6}$/)) {
                  setSelectedStock(e.target.value);
                  fetchStockName(e.target.value);
                }
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="輸入代號或名稱搜尋..."
              className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none placeholder-slate-500"
            />
            {/* 顯示當前選擇 */}
            <p className="text-emerald-400 text-xs mt-1">
              ✓ 已選擇: {selectedStock} {selectedStockName}
            </p>
            
            {/* 下拉建議 */}
            {showSuggestions && filteredStocks.length > 0 && (
              <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                {filteredStocks.map(stock => (
                  <div
                    key={stock.id}
                    className="px-3 py-2 hover:bg-slate-700 cursor-pointer flex justify-between items-center"
                    onClick={() => {
                      setSelectedStock(stock.id);
                      setSelectedStockName(stock.name);
                      setStockInput(stock.id);
                      setShowSuggestions(false);
                    }}
                  >
                    <span className="text-white">{stock.name}</span>
                    <span className="text-slate-400 text-sm">{stock.id}</span>
                  </div>
                ))}
                {stockInput.match(/^\d{4,6}$/) && !filteredStocks.find(s => s.id === stockInput) && (
                  <div
                    className="px-3 py-2 hover:bg-slate-700 cursor-pointer border-t border-slate-600"
                    onClick={() => {
                      setSelectedStock(stockInput);
                      fetchStockName(stockInput);
                      setShowSuggestions(false);
                    }}
                  >
                    <span className="text-cyan-400">🔍 搜尋 {stockInput}</span>
                    <span className="text-slate-500 text-xs ml-2">(全市場)</span>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* 策略選擇 */}
          <div>
            <label className="text-slate-400 text-sm block mb-2">選擇策略</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
            >
              {strategies.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.risk === '高' ? '⚠️高風險' : s.risk === '低' ? '✅低風險' : '⚡中風險'})
                </option>
              ))}
            </select>
            {/* 顯示選中策略的說明 */}
            <p className="text-slate-500 text-xs mt-1">
              {strategies.find(s => s.id === selectedStrategy)?.description || ''}
            </p>
          </div>
          
          {/* 回測期間 */}
          <div>
            <label className="text-slate-400 text-sm block mb-2">回測期間</label>
            <select
              value={months}
              onChange={(e) => setMonths(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none"
            >
              <option value={3}>3 個月</option>
              <option value={6}>6 個月</option>
              <option value={12}>12 個月</option>
            </select>
          </div>
        </div>
        
        {/* 策略說明 */}
        {selectedStrategy && strategies.length > 0 && (
          <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
            <p className="text-slate-300 text-sm">
              {strategies.find(s => s.id === selectedStrategy)?.description}
            </p>
            <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs ${
              strategies.find(s => s.id === selectedStrategy)?.risk === '低' ? 'bg-green-500/20 text-green-400' :
              strategies.find(s => s.id === selectedStrategy)?.risk === '高' ? 'bg-red-500/20 text-red-400' :
              'bg-yellow-500/20 text-yellow-400'
            }`}>
              風險: {strategies.find(s => s.id === selectedStrategy)?.risk}
            </span>
          </div>
        )}
        
        {/* 執行按鈕 */}
        <button
          onClick={handleRunBacktest}
          disabled={loading}
          className="mt-4 w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {loading ? '⏳ 回測執行中...' : '🚀 開始回測'}
        </button>
      </div>
      
      {/* 錯誤訊息 */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <p className="text-red-400 font-semibold">❌ {typeof error === 'string' ? error : error.error || '回測失敗'}</p>
          {error.reason && (
            <p className="text-red-300/70 text-sm mt-1">原因：{error.reason}</p>
          )}
          {error.suggestions && (
            <ul className="text-slate-400 text-sm mt-2 list-disc list-inside">
              {error.suggestions.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          )}
        </div>
      )}
      
      {/* 回測結果 */}
      {result && result.stats && (
        <div className="space-y-4">
          {/* 績效統計 */}
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h4 className="text-white font-semibold mb-4">📊 績效統計</h4>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                <div className="text-slate-400 text-xs">總報酬率</div>
                <div className={`text-xl font-bold ${result.stats.total_return_pct >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {result.stats.total_return_pct >= 0 ? '+' : ''}{result.stats.total_return_pct}%
                </div>
              </div>
              <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                <div className="text-slate-400 text-xs">年化報酬</div>
                <div className={`text-xl font-bold ${result.stats.annual_return_pct >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {result.stats.annual_return_pct >= 0 ? '+' : ''}{result.stats.annual_return_pct}%
                </div>
              </div>
              <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                <div className="text-slate-400 text-xs">勝率</div>
                <div className="text-xl font-bold text-white">{result.stats.win_rate}%</div>
              </div>
              <div className="text-center p-3 bg-slate-700/50 rounded-lg">
                <div className="text-slate-400 text-xs">最大回撤</div>
                <div className="text-xl font-bold text-orange-400">-{result.stats.max_drawdown_pct}%</div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="text-center">
                <span className="text-slate-500 text-sm">初始資金</span>
                <div className="text-white">${result.stats.initial_capital?.toLocaleString()}</div>
              </div>
              <div className="text-center">
                <span className="text-slate-500 text-sm">最終淨值</span>
                <div className="text-white">${result.stats.final_value?.toLocaleString()}</div>
              </div>
              <div className="text-center">
                <span className="text-slate-500 text-sm">總交易次數</span>
                <div className="text-white">{result.stats.total_trades}</div>
              </div>
              <div className="text-center">
                <span className="text-slate-500 text-sm">夏普比率</span>
                <div className="text-white">{result.stats.sharpe_ratio}</div>
              </div>
            </div>
          </div>
          
          {/* 淨值曲線 */}
          {result.daily_values && result.daily_values.length > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
              <h4 className="text-white font-semibold mb-2">📈 淨值曲線</h4>
              <EquityCurve data={result.daily_values} />
            </div>
          )}
          
          {/* 交易記錄 */}
          {result.trades && result.trades.length > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
              <h4 className="text-white font-semibold mb-4">📝 交易記錄（最近 {result.trades.length} 筆）</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-700">
                      <th className="text-left py-2">日期</th>
                      <th className="text-left py-2">類型</th>
                      <th className="text-right py-2">價格</th>
                      <th className="text-right py-2">股數</th>
                      <th className="text-right py-2">損益</th>
                      <th className="text-left py-2">原因</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((trade, i) => (
                      <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="py-2 text-slate-300">{trade.date}</td>
                        <td className={`py-2 ${trade.type === 'buy' ? 'text-red-400' : 'text-emerald-400'}`}>
                          {trade.type === 'buy' ? '買進' : '賣出'}
                        </td>
                        <td className="py-2 text-right text-white">${trade.price?.toFixed(2)}</td>
                        <td className="py-2 text-right text-white">{trade.shares?.toLocaleString()}</td>
                        <td className={`py-2 text-right ${(trade.profit || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                          {trade.profit ? `${trade.profit >= 0 ? '+' : ''}${trade.profit.toFixed(0)}` : '-'}
                        </td>
                        <td className="py-2 text-slate-400 text-xs max-w-[150px] truncate">{trade.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* 空狀態 */}
      {!result && !loading && !error && (
        <div className="text-center py-12 text-slate-500">
          <p className="text-4xl mb-4">📊</p>
          <p>選擇股票和策略，然後點擊「開始回測」</p>
          <p className="text-sm mt-2">系統會模擬過去的交易，計算策略績效</p>
        </div>
      )}
      
      {/* 免責聲明 */}
      <div className="text-center text-slate-500 text-xs">
        ⚠️ 回測結果僅供參考，過去績效不代表未來表現
      </div>
    </div>
  );
};

// ===== 股票分析面板 =====
const SearchPanel = () => {
  const [searchInput, setSearchInput] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 股票名稱對照
  const stockNameMap = {
    '2330': '台積電', '2454': '聯發科', '2303': '聯電', '2317': '鴻海',
    '2382': '廣達', '2881': '富邦金', '2891': '中信金', '2379': '瑞昱',
    '3711': '日月光投控', '2308': '台達電', '3034': '聯詠', '2357': '華碩',
    '0050': '元大台灣50', '0056': '元大高股息', '006208': '富邦台50',
    '00878': '國泰永續高股息', '00893': '國泰智能電動車',
    '00891': '中信關鍵半導體', '00881': '國泰台灣5G+',
  };
  
  // 🆕 V10.13.3: 生成 AI 建議說明
  const _generateReason = (tech, fund, chip) => {
    const reasons = [];
    
    // 技術面
    if (tech) {
      const macd = tech.macd?.signal;
      if (macd === '金叉' || macd === '多方') reasons.push('MACD 多方');
      else if (macd === '死叉' || macd === '空方') reasons.push('MACD 空方');
      
      const rsi = tech.rsi?.value;
      if (rsi < 30) reasons.push('RSI 超賣');
      else if (rsi > 70) reasons.push('RSI 超買');
      
      const volume = tech.volume?.ratio;
      if (volume > 2) reasons.push('量能放大');
    }
    
    // 基本面
    if (fund) {
      const pe = fund.pe_ratio;
      if (pe && pe < 15) reasons.push('P/E 偏低');
      else if (pe && pe > 30) reasons.push('P/E 偏高');
      
      const dy = fund.dividend_yield;
      if (dy && dy > 4) reasons.push('高殖利率');
    }
    
    // 籌碼面
    if (chip) {
      const foreign = chip.foreign_net;
      const trust = chip.trust_net;
      if (foreign > 1000) reasons.push('外資買超');
      else if (foreign < -1000) reasons.push('外資賣超');
      if (trust > 500) reasons.push('投信買超');
    }
    
    return reasons.length > 0 ? reasons.join('、') : '資料分析中';
  };
  
  // 執行分析
  const handleSearch = async () => {
    if (!searchInput.match(/^\d{4,6}$/)) {
      setError('請輸入 4-6 碼的股票代號');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSearchResult(null);
    
    try {
      // 🆕 V10.13.4: 取得完整分析資料（新增 score 端點）
      const [infoRes, analysisRes, fundamentalRes, chipRes, newsRes, scoreRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/stocks/info/${searchInput}`),
        fetch(`${API_BASE}/api/stocks/analysis/${searchInput}`),
        fetch(`${API_BASE}/api/stocks/fundamental/${searchInput}`),
        fetch(`${API_BASE}/api/stocks/institutional/${searchInput}`),
        fetch(`${API_BASE}/api/stocks/news/stock/${searchInput}`),
        fetch(`${API_BASE}/api/stocks/score/${searchInput}`),  // 🆕 V10.13.4
      ]);
      
      // 處理結果
      const info = infoRes.status === 'fulfilled' && infoRes.value.ok ? await infoRes.value.json() : null;
      const analysis = analysisRes.status === 'fulfilled' && analysisRes.value.ok ? await analysisRes.value.json() : null;
      const fundamental = fundamentalRes.status === 'fulfilled' && fundamentalRes.value.ok ? await fundamentalRes.value.json() : null;
      const chip = chipRes.status === 'fulfilled' && chipRes.value.ok ? await chipRes.value.json() : null;
      const news = newsRes.status === 'fulfilled' && newsRes.value.ok ? await newsRes.value.json() : null;
      const score = scoreRes.status === 'fulfilled' && scoreRes.value.ok ? await scoreRes.value.json() : null;  // 🆕 V10.13.4
      
      // 🆕 V10.13.4: 多來源取得股票名稱
      const stockName = score?.name || info?.name || stockNameMap[searchInput] || searchInput;
      
      // 提取技術分析（後端返回 { analysis: {...} } 的巢狀結構）
      const technicalData = analysis?.analysis || null;
      
      // 組合結果
      // 🆕 V10.13.3: 修正數據格式（後端返回嵌套結構）
      const fundamentalData = fundamental?.fundamental || fundamental || {};
      const chipData = chip?.institutional || chip || {};
      
      // 🆕 V10.13.4: 使用後端評分（與 AI 精選一致）
      const finalConfidence = score?.scores?.total || 50;
      const finalSignal = score?.signal || '觀望';
      const finalReason = score?.reason || '資料分析中';
      
      setSearchResult({
        stock_id: searchInput,
        name: stockName,
        price: info?.price || info?.close,
        change: info?.change,
        change_percent: info?.change_percent,
        confidence: finalConfidence,  // 🆕 V10.13.4: 使用後端評分
        signal: finalSignal,
        reason: finalReason,
        technical: technicalData,
        fundamental: fundamentalData,
        chip: chipData,
        news: news?.news || [],
        // 🆕 V10.13.4: 保存分數明細
        scoreBreakdown: score?.scores,
        // 保存原始數據用於除錯
        _raw: { info, analysis, fundamental, chip, news, score }
      });
      
    } catch (err) {
      setError('分析失敗：' + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // 分數顏色
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-red-400';
    if (score >= 70) return 'text-orange-400';
    if (score >= 55) return 'text-yellow-400';
    return 'text-slate-400';
  };
  
  // 訊號顏色
  const getSignalColor = (signal) => {
    if (signal?.includes('買') || signal?.includes('進')) return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (signal?.includes('賣') || signal?.includes('減')) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };
  
  return (
    <div className="space-y-6">
      {/* 搜尋區 */}
      <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
        <h3 className="text-white font-bold text-lg mb-4">🔍 股票分析查詢</h3>
        <p className="text-slate-400 text-sm mb-4">
          輸入任意股票代號，取得 AI 完整分析報告（包含未在推薦清單中的股票）
        </p>
        
        <div className="flex gap-4">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value.replace(/\D/g, '').slice(0, 6))}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="輸入股票代號（如 2330、006208）"
            className="flex-1 bg-slate-800 text-white px-4 py-3 rounded-lg border border-slate-600 focus:border-purple-500 focus:outline-none"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !searchInput}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors"
          >
            {loading ? '⏳ 分析中...' : '🔍 開始分析'}
          </button>
        </div>
        
        {error && (
          <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}
      </div>
      
      {/* 分析結果 */}
      {searchResult && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
          {/* 標題區 */}
          <div className="bg-slate-800 p-6 border-b border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white">
                  {searchResult.name}
                  <span className="text-slate-400 text-lg ml-2">({searchResult.stock_id})</span>
                </h2>
                {searchResult.price && (
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-3xl font-bold text-white">${searchResult.price?.toFixed(2)}</span>
                    <span className={`text-lg ${searchResult.change_percent >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {searchResult.change_percent >= 0 ? '+' : ''}{searchResult.change_percent?.toFixed(2)}%
                    </span>
                  </div>
                )}
              </div>
              
              {/* V10.35.5: AI 動能評分 (方案 E) */}
              <div className="text-center">
                <div className={`text-5xl font-bold ${getScoreColor(searchResult.confidence)}`}>
                  {searchResult.confidence}
                </div>
                <div className="text-amber-400 text-sm font-medium">動能評分</div>
                <div className="text-slate-500 text-xs">適合短線</div>
                <div className={`mt-2 px-4 py-1 rounded-full text-sm border ${getSignalColor(searchResult.signal)}`}>
                  {searchResult.signal}
                </div>
              </div>
            </div>
            
            {/* AI 建議 */}
            <div className="mt-4 p-4 bg-slate-900/50 rounded-lg">
              <p className="text-white">💡 {searchResult.reason}</p>
            </div>
            
            {/* 🆕 V10.14: 分數明細 + 操作建議 */}
            {searchResult.scoreBreakdown && (
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className={`p-3 rounded-lg ${searchResult.scoreBreakdown.technical >= 70 ? 'bg-red-500/10 border border-red-500/30' : searchResult.scoreBreakdown.technical >= 55 ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-slate-500/10 border border-slate-500/30'}`}>
                  <div className="text-slate-400 text-xs">技術面</div>
                  <div className={`text-2xl font-bold ${searchResult.scoreBreakdown.technical >= 70 ? 'text-red-400' : searchResult.scoreBreakdown.technical >= 55 ? 'text-yellow-400' : 'text-slate-400'}`}>
                    {searchResult.scoreBreakdown.technical}
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${searchResult.scoreBreakdown.fundamental >= 65 ? 'bg-emerald-500/10 border border-emerald-500/30' : searchResult.scoreBreakdown.fundamental >= 50 ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-orange-500/10 border border-orange-500/30'}`}>
                  <div className="text-slate-400 text-xs">基本面</div>
                  <div className={`text-2xl font-bold ${searchResult.scoreBreakdown.fundamental >= 65 ? 'text-emerald-400' : searchResult.scoreBreakdown.fundamental >= 50 ? 'text-yellow-400' : 'text-orange-400'}`}>
                    {searchResult.scoreBreakdown.fundamental}
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${searchResult.scoreBreakdown.chip >= 60 ? 'bg-blue-500/10 border border-blue-500/30' : searchResult.scoreBreakdown.chip >= 45 ? 'bg-slate-500/10 border border-slate-500/30' : 'bg-orange-500/10 border border-orange-500/30'}`}>
                  <div className="text-slate-400 text-xs">籌碼面</div>
                  <div className={`text-2xl font-bold ${searchResult.scoreBreakdown.chip >= 60 ? 'text-blue-400' : searchResult.scoreBreakdown.chip >= 45 ? 'text-slate-400' : 'text-orange-400'}`}>
                    {searchResult.scoreBreakdown.chip}
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${(searchResult.scoreBreakdown.news || 50) >= 55 ? 'bg-purple-500/10 border border-purple-500/30' : 'bg-slate-500/10 border border-slate-500/30'}`}>
                  <div className="text-slate-400 text-xs">新聞面</div>
                  <div className={`text-2xl font-bold ${(searchResult.scoreBreakdown.news || 50) >= 55 ? 'text-purple-400' : 'text-slate-400'}`}>
                    {searchResult.scoreBreakdown.news || 50}
                  </div>
                </div>
              </div>
            )}

            {/* V10.35.5 方案 C: 穩定度指標 */}
            {searchResult.stability_score !== undefined && (
              <div className="mt-3 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-sm">穩定度</span>
                    <span className={`text-lg font-bold ${
                      searchResult.stability_score >= 70 ? 'text-emerald-400' :
                      searchResult.stability_score >= 50 ? 'text-yellow-400' : 'text-orange-400'
                    }`}>
                      {searchResult.stability_score}
                    </span>
                  </div>
                  <div className="text-slate-500 text-xs">
                    波動率: {searchResult.volatility?.toFixed(2) || 0}%
                  </div>
                </div>
                <div className="mt-2 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      searchResult.stability_score >= 70 ? 'bg-emerald-500' :
                      searchResult.stability_score >= 50 ? 'bg-yellow-500' : 'bg-orange-500'
                    }`}
                    style={{ width: `${searchResult.stability_score}%` }}
                  />
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {searchResult.stability_score >= 70 ? '適合長期持有' :
                   searchResult.stability_score >= 50 ? '適合波段操作' : '短線交易為主'}
                </div>
              </div>
            )}
            
            {/* 🆕 V10.14: 操作建議區 */}
            {searchResult.price && (
              <div className="mt-4 p-4 bg-gradient-to-r from-amber-500/10 to-orange-500/10 rounded-lg border border-amber-500/30">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-slate-400 text-xs mb-1">建議買入價</div>
                    <div className="text-white font-bold">
                      ${(searchResult.price * 0.98).toFixed(2)} - ${searchResult.price?.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-400 text-xs mb-1">止損價位</div>
                    <div className="text-emerald-400 font-bold">
                      ${(searchResult.price * 0.95).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-400 text-xs mb-1">目標價位</div>
                    <div className="text-red-400 font-bold">
                      ${(searchResult.price * 1.10).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* 🆕 V10.14: 加入投組按鈕 */}
            <div className="mt-4">
              {PortfolioManager.isInPortfolio(searchResult.stock_id) ? (
                <div className="w-full py-3 bg-emerald-500/20 text-emerald-400 text-center rounded-lg border border-emerald-500/30">
                  ✅ 此股票已在投組追蹤中
                </div>
              ) : (
                <button
                  onClick={() => {
                    const result = PortfolioManager.addToPortfolio({
                      stock_id: searchResult.stock_id,
                      name: searchResult.name,
                      price: searchResult.price,
                      confidence: searchResult.confidence,
                      signal: searchResult.signal,
                      reason: searchResult.reason,
                      score_breakdown: searchResult.scoreBreakdown,
                    });
                    alert(result.message);
                    if (result.success) {
                      setSearchResult({ ...searchResult });  // 觸發重新渲染
                    }
                  }}
                  className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-lg transition-colors"
                >
                  ⭐ 加入我的投組追蹤
                </button>
              )}
            </div>
          </div>
          
          {/* 詳細分析 */}
          <div className="p-6 space-y-6">
            {/* 技術分析 */}
            {searchResult.technical ? (
              <div className="space-y-3">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  📊 技術分析
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {searchResult.technical.ma && (
                    <div className="bg-slate-900/50 p-3 rounded-lg">
                      <div className="text-slate-400 text-xs">均線</div>
                      <div className="text-white">{searchResult.technical.ma.trend || '-'}</div>
                    </div>
                  )}
                  {searchResult.technical.rsi !== undefined && (
                    <div className="bg-slate-900/50 p-3 rounded-lg">
                      <div className="text-slate-400 text-xs">RSI</div>
                      <div className="text-white">{searchResult.technical.rsi?.value?.toFixed(1) || '-'}</div>
                    </div>
                  )}
                  {searchResult.technical.macd && (
                    <div className="bg-slate-900/50 p-3 rounded-lg">
                      <div className="text-slate-400 text-xs">MACD</div>
                      <div className="text-white">{searchResult.technical.macd.signal || '-'}</div>
                    </div>
                  )}
                  {searchResult.technical.volume && (
                    <div className="bg-slate-900/50 p-3 rounded-lg">
                      <div className="text-slate-400 text-xs">成交量</div>
                      <div className="text-white">{searchResult.technical.volume.ratio?.toFixed(1)}x</div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
                <div className="flex items-center gap-2 text-slate-500">
                  <span>📊</span>
                  <span>技術分析：資料不足（需要至少 20 天歷史資料）</span>
                </div>
              </div>
            )}
            
            {/* 基本面 */}
            {searchResult.fundamental ? (
              <div className="space-y-3">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  📈 基本面分析
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">本益比 (P/E)</div>
                    <div className="text-white">{searchResult.fundamental.pe_ratio?.toFixed(2) || '-'}</div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">殖利率</div>
                    <div className="text-yellow-400">{searchResult.fundamental.dividend_yield?.toFixed(2) || '-'}%</div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">淨值比 (P/B)</div>
                    <div className="text-white">{searchResult.fundamental.pb_ratio?.toFixed(2) || '-'}</div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">ROE</div>
                    <div className="text-white">{searchResult.fundamental.roe?.toFixed(2) || '-'}%</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
                <div className="flex items-center gap-2 text-slate-500">
                  <span>📈</span>
                  <span>基本面分析：無法取得資料</span>
                </div>
              </div>
            )}
            
            {/* 籌碼面 */}
            {searchResult.chip ? (
              <div className="space-y-3">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  🏦 籌碼面分析
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">外資</div>
                    <div className={searchResult.chip.foreign_net > 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {searchResult.chip.foreign_net > 0 ? '+' : ''}{searchResult.chip.foreign_net?.toLocaleString() || '-'} 張
                    </div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">投信</div>
                    <div className={searchResult.chip.trust_net > 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {searchResult.chip.trust_net > 0 ? '+' : ''}{searchResult.chip.trust_net?.toLocaleString() || '-'} 張
                    </div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded-lg">
                    <div className="text-slate-400 text-xs">自營商</div>
                    <div className={searchResult.chip.dealer_net > 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {searchResult.chip.dealer_net > 0 ? '+' : ''}{searchResult.chip.dealer_net?.toLocaleString() || '-'} 張
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
                <div className="flex items-center gap-2 text-slate-500">
                  <span>🏦</span>
                  <span>籌碼面分析：無法取得三大法人資料</span>
                </div>
              </div>
            )}
            
            {/* 相關新聞 */}
            {searchResult.news && searchResult.news.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  📰 相關新聞
                </h3>
                <div className="space-y-2">
                  {searchResult.news.slice(0, 5).map((item, i) => (
                    <a
                      key={i}
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-3 bg-slate-900/50 rounded-lg hover:bg-slate-900/80 transition-colors"
                    >
                      <div className="flex items-start gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          item.sentiment === 'positive' ? 'bg-red-500/20 text-red-400' :
                          item.sentiment === 'negative' ? 'bg-emerald-500/20 text-emerald-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>
                          {item.sentiment === 'positive' ? '利多' : item.sentiment === 'negative' ? '利空' : '中性'}
                        </span>
                        <span className="text-white text-sm flex-1">{item.title}</span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* 提示 */}
      {!searchResult && !loading && (
        <div className="text-center py-12 text-slate-500">
          <p className="text-4xl mb-4">🔍</p>
          <p className="text-lg">輸入股票代號開始分析</p>
          <p className="text-sm mt-2">支援任意台股代號（4碼）或 ETF（5-6碼）</p>
          <p className="text-xs mt-4 text-slate-600">範例：2330（台積電）、006208（富邦台50）、00893（國泰智能電動車）</p>
        </div>
      )}
    </div>
  );
};

// ===== 載入動畫 =====
const Loading = () => (
  <div className="flex items-center justify-center py-12">
    <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
  </div>
);

// ===== 主應用 =====
export default function App() {
  const [recommendations, setRecommendations] = useState([]);
  const [hotStocks, setHotStocks] = useState([]);
  const [volumeHot, setVolumeHot] = useState([]);
  const [darkHorses, setDarkHorses] = useState([]);
  const [market, setMarket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [scanned, setScanned] = useState(0);
  const [analyzed, setAnalyzed] = useState(0);
  const [dataDate, setDataDate] = useState(null);  // 🆕 V10.13.5: 資料日期
  // V10.38: URL 參數同步
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // 從 URL 讀取初始 section，預設為 'ai'
  const initialSection = searchParams.get('section') || 'ai';
  const [activeSection, setActiveSection] = useState(initialSection); // 'ai' | 'hot' | 'volume' | 'dark'

  // V10.38: URL 同步 - 當 activeSection 改變時更新 URL
  useEffect(() => {
    const currentSection = searchParams.get('section');
    if (currentSection !== activeSection) {
      setSearchParams({ section: activeSection }, { replace: true });
    }
  }, [activeSection, searchParams, setSearchParams]);

  // 🆕 V10.14: 歷史快照相關狀態
  const [selectedHistoryDate, setSelectedHistoryDate] = useState('today');
  const [availableHistoryDates, setAvailableHistoryDates] = useState([]);
  const [historyData, setHistoryData] = useState(null);

  // V10.27: 鍵盤快捷鍵狀態
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);

  // V10.28: 通知設定狀態
  const [showNotificationSettings, setShowNotificationSettings] = useState(false);

  // V10.27: 使用鍵盤快捷鍵 Hook
  const { keySequence } = useKeyboardShortcuts({
    onNavigate: (tabId) => setActiveSection(tabId),
    onRefresh: () => fetchData(),
    onShowHelp: () => setShowKeyboardHelp(true),
    onCloseModal: () => {
      setShowKeyboardHelp(false);
      setShowNotificationSettings(false);
    },
    enabled: true,
  });

  // V10.28: 使用通知 Hook
  const { unreadCount, sendRecommendationNotification } = useNotifications();

  // V10.28: 使用響應式 Hook
  const { isMobile } = useResponsive();

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await stockAPI.getRecommendations();
      setRecommendations(data.recommendations || []);
      setHotStocks(data.hot_stocks || []);
      setVolumeHot(data.volume_hot || []);
      setDarkHorses(data.dark_horses || []);
      setMarket(data.market);
      setScanned(data.scanned || 0);
      setAnalyzed(data.analyzed || 0);
      setDataDate(data.data_date || null);  // 🆕 V10.13.5: 資料日期
      setLastUpdate(new Date().toLocaleTimeString('zh-TW'));
      
      // 🆕 V10.14: 保存歷史快照
      if (data.data_date && data.recommendations && data.recommendations.length > 0) {
        HistoryManager.saveSnapshot(data.recommendations, data.data_date);
        setAvailableHistoryDates(HistoryManager.getAvailableDates());
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('無法連接到 API，請確認後端服務是否正在執行');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // 初始載入歷史日期列表
    setAvailableHistoryDates(HistoryManager.getAvailableDates());
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  // 🆕 V10.14: 處理歷史日期切換
  useEffect(() => {
    if (selectedHistoryDate === 'today') {
      setHistoryData(null);
    } else {
      const data = HistoryManager.getHistoryData(selectedHistoryDate);
      setHistoryData(data);
    }
  }, [selectedHistoryDate]);

  // V10.39: 保留資料映射（用於列表視圖）
  const sectionDataMap = {
    'ai': { data: recommendations, desc: '依技術分析評分排序' },
    'hot': { data: hotStocks, desc: '當日漲幅最大' },
    'volume': { data: volumeHot, desc: '成交量比率最高' },
    'dark': { data: darkHorses, desc: '評分中等但有上漲潛力' },
  };

  // V10.39: 從 menuGroups 中查找當前 section
  const currentSectionInfo = findGroupBySection(activeSection);
  const currentSection = sectionDataMap[activeSection] || { data: [], desc: currentSectionInfo?.items?.find(i => i.id === activeSection)?.desc || '' };

  return (
    <ErrorBoundary level="page">
    <div className="min-h-screen theme-gradient">
      {/* V10.23: 新手引導 */}
      <OnboardingGuide />

      {/* Header - V10.35.3: 手機端優化 */}
      <header className="theme-bg-primary/80 backdrop-blur-sm border-b theme-border-primary sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 md:px-4 py-2 md:py-3">
          <div className="flex items-center justify-between">
            {/* Logo - 手機端縮小 */}
            <div className="flex items-center gap-2 md:gap-3">
              <span className="text-2xl md:text-3xl">📈</span>
              <div>
                <h1 className="text-lg md:text-xl font-bold theme-text-primary">StockBuddy</h1>
                <p className="theme-text-muted text-xs hidden sm:block">台股智能選股系統 V10.35.4</p>
              </div>
            </div>

            {/* 右側按鈕區 */}
            <div className="flex items-center gap-2 md:gap-4">
              {/* 大盤指數 - 手機端精簡顯示 */}
              {market && (
                <div className="text-right">
                  <div className="theme-text-muted text-xs hidden sm:block">加權指數</div>
                  <div className={`text-sm md:text-base font-medium ${market.change_percent >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    <span className="hidden sm:inline">{market.value?.toLocaleString()}</span>
                    <span className="sm:hidden">{market.value ? (market.value / 1000).toFixed(1) + 'K' : ''}</span>
                    <span className="text-xs md:text-sm ml-1">
                      ({market.change_percent >= 0 ? '+' : ''}{market.change_percent?.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              )}

              {/* V10.28: 通知鈴鐺 - 手機端保留 */}
              <NotificationBell
                onClick={() => setShowNotificationSettings(true)}
                unreadCount={unreadCount}
              />

              {/* V10.28: 主題切換 - 手機端保留 */}
              <ThemeToggleIcon />

              {/* 桌面版額外按鈕 - 手機端隱藏 */}
              <div className="hidden md:flex items-center gap-2">
                {/* V10.23: 自動刷新 */}
                <AutoRefresh onRefresh={fetchData} />
                {/* V10.15: 匯出按鈕 */}
                <ExportButton type="recommendations" label="匯出" />
              </div>

              {/* 更新按鈕 - 手機端簡化 */}
              <button
                onClick={fetchData}
                disabled={loading}
                className="p-2 md:px-3 md:py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors disabled:opacity-50 min-w-[40px] min-h-[40px] flex items-center justify-center"
                title="更新資料"
              >
                {loading ? (
                  <span className="animate-spin">⏳</span>
                ) : (
                  <>
                    <span className="md:hidden">🔄</span>
                    <span className="hidden md:inline">🔄 更新</span>
                  </>
                )}
              </button>

              {/* 強制更新按鈕 - 手機端隱藏 */}
              <button
                onClick={async () => {
                  if (window.confirm('確定要強制清除所有快取並重新獲取資料？\n\n這會清除：\n• 籌碼快取\n• TWSE 快取\n• yfinance 快取')) {
                    try {
                      // 清除後端快取
                      const res = await fetch(`${API_BASE}/api/stocks/clear-cache`, { method: 'POST' });
                      const data = await res.json();

                      // 重新獲取資料
                      await fetchData();

                      alert(`✅ 快取已清除！\n已清除: ${data.cleared?.join(', ') || '全部'}`);
                    } catch (err) {
                      console.error('清除快取失敗:', err);
                      alert('❌ 清除快取失敗: ' + err.message);
                    }
                  }
                }}
                disabled={loading}
                className="hidden md:block px-3 py-1.5 bg-orange-600 hover:bg-orange-500 rounded-lg text-sm transition-colors disabled:opacity-50"
                title="清除所有快取並重新獲取最新資料"
              >
                🗑️ 強制更新
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 md:px-4 py-4 md:py-6">
        {/* V10.15: 資料狀態指示器 */}
        <DataStatusIndicator onRefresh={fetchData} />

        {/* 狀態欄 - V10.35.3: 手機端優化 */}
        <div className="mb-3 md:mb-4 flex items-center justify-between text-xs md:text-sm mt-2 md:mt-3">
          <div className="theme-text-muted flex items-center flex-wrap gap-1 md:gap-2">
            <span className="hidden sm:inline">📡 掃描 {scanned} 檔 | 分析 {analyzed} 檔</span>
            <span className="sm:hidden">📡 {scanned}/{analyzed}</span>
            {/* V10.35.4: 使用 dateUtils 統一日期格式 */}
            {(() => {
              const todayDisplay = getTodayDisplay();  // YYYY/MM/DD
              const displayDate = formatDateShort(new Date());  // M/D
              const normalizedDataDate = dataDate ? formatDateDisplay(dataDate) : '';  // 統一格式
              const isOldData = normalizedDataDate && normalizedDataDate !== todayDisplay;

              return (
                <span className={isOldData ? 'text-yellow-400' : 'text-emerald-400'}>
                  📅 {displayDate}
                  {isOldData && (
                    <span className="ml-1 px-1 md:px-1.5 py-0.5 bg-yellow-500/20 rounded text-xs">
                      ⚠️ <span className="hidden sm:inline">{normalizedDataDate} 舊資料</span>
                    </span>
                  )}
                  {!isOldData && dataDate && (
                    <span className="ml-1 text-xs text-emerald-300 hidden sm:inline">最新資料</span>
                  )}
                </span>
              );
            })()}
            {lastUpdate && <span className="hidden md:inline">⏱️ {lastUpdate} 更新</span>}
          </div>
        </div>

        {/* V10.39: 選單優化 - 8 個主選單群組 */}
        <div className="flex flex-wrap gap-1.5 md:gap-2 mb-4 md:mb-6">
          {menuGroups.map(group => (
            <DropdownMenu
              key={group.id}
              group={group}
              activeSection={activeSection}
              onSelect={setActiveSection}
            />
          ))}
        </div>

        {error ? (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
            <p className="text-red-400">❌ {error}</p>
            <button
              onClick={fetchData}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm"
            >
              重試
            </button>
          </div>
        ) : activeSection === 'dashboard' ? (
          // V10.27: 市場總覽儀表板
          <MarketDashboard onSelectStock={setSelectedStock} />
        ) : activeSection === 'strategy' ? (
          // 綜合投資策略視圖
          <StrategyPicksPanel onSelectStock={setSelectedStock} />
        ) : activeSection === 'screener' ? (
          // 選股篩選器視圖
          <StockScreener onSelectStock={setSelectedStock} />
        ) : activeSection === 'compare' ? (
          // 股票比較視圖
          <StockComparison onSelectStock={setSelectedStock} />
        ) : activeSection === 'alerts' || activeSection === 'smart-alerts' ? (
          // V10.39: 提醒功能整合 (alerts + smart-alerts)
          <UnifiedAlerts />
        ) : activeSection === 'transactions' ? (
          // 交易記錄視圖
          <TransactionManager onSelectStock={setSelectedStock} />
        ) : activeSection === 'categories' ? (
          // 股票分類視圖
          <WatchlistCategories
            trackedStocks={PortfolioManager.getPortfolio()}
            onSelectStock={setSelectedStock}
          />
        ) : activeSection === 'tracker' || activeSection === 'history-perf' ? (
          // V10.39: 績效功能整合 (tracker + history-perf)
          <UnifiedPerformance />
        ) : activeSection === 'us-stocks' ? (
          // V10.24: 美股市場視圖
          <USStockPanel
            onSelectStock={(symbol, market) => {
              // 可擴展：處理美股選擇事件
            }}
          />
        ) : activeSection === 'calendar' ? (
          // V10.27: 市場行事曆視圖
          <MarketCalendar />
        ) : activeSection === 'portfolio' ? (
          // 投資組合視圖
          <PortfolioPanel onSelectStock={setSelectedStock} />
        ) : activeSection === 'backtest' ? (
          // 回測視圖
          <BacktestPanel />
        ) : activeSection === 'risk' ? (
          // V10.29: 風險管理視圖
          <RiskCalculator stock={selectedStock} />
        ) : activeSection === 'dividend' ? (
          // V10.30: 除權息計算器視圖
          <DividendCalculator stock={selectedStock} />
        ) : activeSection === 'ai-report' ? (
          // V10.31: AI 分析報告視圖
          <AIReport stock={selectedStock} portfolio={PortfolioManager.getPortfolio()} />
        ) : activeSection === 'adv-charts' ? (
          // V10.31: 進階圖表視圖
          <AdvancedCharts stock={selectedStock} />
        ) : activeSection === 'news' ? (
          // V10.32: 財經新聞視圖
          <NewsPanel watchlist={PortfolioManager.getPortfolio()} selectedStock={selectedStock} />
        ) : activeSection === 'patterns' ? (
          // V10.33: 技術形態辨識視圖
          <PatternRecognition />
        ) : activeSection === 'diary' ? (
          // V10.33: 投資日記視圖
          <InvestmentDiary />
        ) : activeSection === 'simulation' ? (
          // V10.34: 模擬交易視圖
          <SimulationTrading />
        ) : activeSection === 'templates' ? (
          // V10.34: 策略範本視圖
          <StrategyTemplates />
        ) : activeSection === 'ml-panel' ? (
          // V10.40: ML 模型管理面板
          <MLPanel />
        ) : activeSection === 'search' ? (
          // 股票分析視圖
          <SearchPanel />
        ) : loading && recommendations.length === 0 ? (
          <Loading />
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* 股票列表 */}
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-white font-semibold">{currentSectionInfo?.items?.find(i => i.id === activeSection)?.label || currentSectionInfo?.label || activeSection}</h2>
                <div className="flex items-center gap-3">
                  {/* 🆕 V10.14: AI 精選的日期選擇器 */}
                  {activeSection === 'ai' && availableHistoryDates.length > 0 && (
                    <select
                      value={selectedHistoryDate}
                      onChange={(e) => setSelectedHistoryDate(e.target.value)}
                      className="bg-slate-800 text-slate-300 text-sm px-3 py-1.5 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="today">📅 今天 {dataDate ? `(${dataDate})` : ''}</option>
                      {availableHistoryDates.map(date => (
                        <option key={date} value={date}>
                          📆 {HistoryManager.formatDateLabel(date)}
                        </option>
                      ))}
                    </select>
                  )}
                  <span className="text-slate-500 text-sm">{currentSection.desc}</span>
                </div>
              </div>
              
              {/* 🆕 V10.14: 歷史資料警告 */}
              {activeSection === 'ai' && historyData && (
                <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-center gap-2">
                  <span className="text-yellow-400">⚠️</span>
                  <span className="text-yellow-400 text-sm">
                    這是 <strong>{historyData.data_date}</strong> 的歷史資料，當前評分可能已變動
                  </span>
                  <button
                    onClick={() => setSelectedHistoryDate('today')}
                    className="ml-auto text-xs px-2 py-1 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded transition-colors"
                  >
                    返回今天
                  </button>
                </div>
              )}
              
              <div className="grid md:grid-cols-2 gap-3">
                {/* 🆕 V10.14: 根據是否有歷史資料決定顯示內容 */}
                {(activeSection === 'ai' && historyData ? historyData.recommendations : currentSection.data).slice(0, 20).map((stock, index) => (
                  <div key={stock.stock_id} className="relative">
                    <div className={`absolute -left-2 -top-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white z-10 ${
                      historyData ? 'bg-yellow-600' : 'bg-blue-600'
                    }`}>
                      {index + 1}
                    </div>
                    {/* 🆕 V10.14: 歷史資料卡片標記 */}
                    {historyData && (
                      <div className="absolute -right-2 -top-2 px-2 py-0.5 bg-yellow-500 text-black text-xs font-bold rounded-full z-10">
                        歷史
                      </div>
                    )}
                    <StockCard
                      stock={stock}
                      onClick={setSelectedStock}
                      isSelected={selectedStock?.stock_id === stock.stock_id}
                      showAddButton={!historyData}  // 歷史資料不顯示加入按鈕
                    />
                  </div>
                ))}
              </div>
              {(activeSection === 'ai' && historyData ? historyData.recommendations : currentSection.data).length === 0 && !loading && (
                <div className="text-center py-12 text-slate-500">
                  <p>暫無資料</p>
                </div>
              )}
            </div>

            {/* 詳細分析 */}
            <div className="lg:col-span-1">
              {selectedStock ? (
                <AnalysisPanel
                  stock={selectedStock}
                  onClose={() => setSelectedStock(null)}
                  onSelectStock={setSelectedStock}
                />
              ) : (
                <div className="bg-slate-800/50 rounded-xl p-6 text-center border border-slate-700">
                  <p className="text-slate-400 text-lg mb-2">👈 選擇一檔股票</p>
                  <p className="text-slate-500 text-sm">查看詳細技術分析、基本面、籌碼面資訊</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-8 py-4 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-xs">
          <p>⚠️ 免責聲明：本工具僅供參考，不構成投資建議。投資有風險，過去績效不代表未來表現。</p>
          <p className="mt-1 text-slate-600">按 <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">?</kbd> 查看鍵盤快捷鍵</p>
        </div>
      </footer>

      {/* V10.27: 鍵盤快捷鍵說明視窗 */}
      <KeyboardShortcutsModal
        isOpen={showKeyboardHelp}
        onClose={() => setShowKeyboardHelp(false)}
      />

      {/* V10.27: 按鍵序列指示器 */}
      <KeySequenceIndicator sequence={keySequence} />

      {/* V10.28: 通知設定面板 */}
      <NotificationSettings
        isOpen={showNotificationSettings}
        onClose={() => setShowNotificationSettings(false)}
      />

      {/* V10.28: 行動版底部導航 */}
      <MobileNav
        activeSection={activeSection}
        onNavigate={setActiveSection}
      />
    </div>
    </ErrorBoundary>
  );
}
