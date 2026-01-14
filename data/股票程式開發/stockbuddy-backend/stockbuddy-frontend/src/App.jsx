import React, { useState, useEffect } from 'react';

// ============================================================
// 📈 StockBuddy V10.6 - 台股智能選股系統
// 恢復 V9.5 介面 + 修正資料源
// ============================================================

// API 設定
const API_BASE = 'http://localhost:8000';

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
};

// ===== 分數環組件 =====
const ScoreRing = ({ score, size = 60 }) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = ((score || 0) / 100) * circumference;
  
  const getColor = (s) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#eab308';
    if (s >= 40) return '#f97316';
    return '#ef4444';
  };
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none" stroke="#334155" strokeWidth="4"
        />
        <circle
          cx={size/2} cy={size/2} r={radius}
          fill="none" stroke={getColor(score)} strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-white font-bold" style={{ fontSize: size * 0.28 }}>
          {score || '-'}
        </span>
      </div>
    </div>
  );
};

// ===== 迷你 K 線圖 =====
const MiniKLineChart = ({ data, width = 100, height = 40 }) => {
  if (!data || data.length < 2) return null;
  
  const prices = data.map(d => d.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice || 1;
  
  const points = prices.map((price, i) => {
    const x = (i / (prices.length - 1)) * width;
    const y = height - ((price - minPrice) / range) * height;
    return `${x},${y}`;
  }).join(' ');
  
  const isUp = prices[prices.length - 1] >= prices[0];
  
  return (
    <svg width={width} height={height} className="opacity-60">
      <polyline
        points={points}
        fill="none"
        stroke={isUp ? '#ef4444' : '#22c55e'}
        strokeWidth="1.5"
      />
    </svg>
  );
};

// ===== 股票卡片 =====
const StockCard = ({ stock, onClick, isSelected }) => {
  const isUp = (stock.change_percent || 0) >= 0;
  const breakdown = stock.score_breakdown || {};
  
  return (
    <div
      onClick={() => onClick(stock)}
      className={`p-4 rounded-xl cursor-pointer transition-all duration-200 ${
        isSelected
          ? 'bg-gradient-to-r from-blue-600/30 to-purple-600/30 border border-blue-500/50 shadow-lg shadow-blue-500/20'
          : 'bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold truncate">{stock.name}</span>
            <span className="text-slate-500 text-sm">{stock.stock_id}</span>
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-white text-lg font-bold">
              ${stock.price?.toLocaleString()}
            </span>
            <span className={`text-sm font-medium ${isUp ? 'text-red-400' : 'text-emerald-400'}`}>
              {isUp ? '+' : ''}{stock.change_percent?.toFixed(2)}%
            </span>
          </div>
          {/* V10.10: 多維度分數指標（含新聞+產業） */}
          {breakdown.technical && (
            <div className="flex flex-wrap items-center gap-1.5 mt-2 text-xs">
              <span className={`px-1.5 py-0.5 rounded ${breakdown.technical >= 70 ? 'bg-red-500/20 text-red-400' : breakdown.technical >= 55 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-500/20 text-slate-400'}`}>
                技{breakdown.technical}
              </span>
              <span className={`px-1.5 py-0.5 rounded ${breakdown.fundamental >= 65 ? 'bg-emerald-500/20 text-emerald-400' : breakdown.fundamental >= 50 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-orange-500/20 text-orange-400'}`}>
                基{breakdown.fundamental}
              </span>
              <span className={`px-1.5 py-0.5 rounded ${breakdown.chip >= 60 ? 'bg-blue-500/20 text-blue-400' : breakdown.chip >= 45 ? 'bg-slate-500/20 text-slate-400' : 'bg-orange-500/20 text-orange-400'}`}>
                籌{breakdown.chip}
              </span>
              <span className={`px-1.5 py-0.5 rounded ${(breakdown.news || 50) >= 55 ? 'bg-purple-500/20 text-purple-400' : (breakdown.news || 50) >= 45 ? 'bg-slate-500/20 text-slate-400' : 'bg-orange-500/20 text-orange-400'}`}>
                聞{breakdown.news || 50}
              </span>
              {breakdown.industry_bonus !== 0 && breakdown.industry_bonus && (
                <span className={`px-1.5 py-0.5 rounded ${breakdown.industry_bonus > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-500/20 text-slate-400'}`}>
                  {breakdown.industry_bonus > 0 ? '🔥' : '📉'}{breakdown.industry_bonus > 0 ? '+' : ''}{breakdown.industry_bonus}
                </span>
              )}
            </div>
          )}
          {/* V10.8: 基本面快速指標 */}
          <div className="flex items-center gap-3 mt-1 text-xs">
            {stock.pe_ratio && (
              <span className={`${stock.pe_ratio < 15 ? 'text-emerald-400' : stock.pe_ratio > 30 ? 'text-red-400' : 'text-slate-400'}`}>
                P/E {stock.pe_ratio.toFixed(1)}
              </span>
            )}
            {stock.dividend_yield && stock.dividend_yield > 0 && (
              <span className={`${stock.dividend_yield >= 4 ? 'text-yellow-400' : 'text-slate-400'}`}>
                殖利率 {stock.dividend_yield.toFixed(1)}%
              </span>
            )}
          </div>
          {/* 標籤 */}
          {(stock.industry || (stock.tags && stock.tags.length > 0)) && (
            <div className="flex flex-wrap gap-1 mt-2">
              {stock.industry && (
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full">
                  {stock.industry}
                </span>
              )}
              {stock.tags?.slice(0, 2).map((tag, i) => (
                <span key={i} className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          )}
          {/* 訊號和理由 */}
          <div className="mt-2 flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              stock.signal === '強力買進' ? 'bg-red-500/20 text-red-400' :
              stock.signal === '買進' ? 'bg-orange-500/20 text-orange-400' :
              stock.signal === '持有' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-slate-500/20 text-slate-400'
            }`}>
              {stock.signal}
            </span>
          </div>
          {stock.reason && (
            <p className="text-slate-400 text-xs mt-1 truncate">{stock.reason}</p>
          )}
        </div>
        <ScoreRing score={stock.confidence} size={50} />
      </div>
    </div>
  );
};

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
const AnalysisPanel = ({ stock, onClose }) => {
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
    { id: 'fundamental', label: '基本面', icon: '📈' },
    { id: 'chip', label: '籌碼面', icon: '🏦' },
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
                  </div>
                )}
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
                  {institutional?.date && (
                    <span className="text-xs text-slate-500 bg-slate-700/50 px-2 py-1 rounded">
                      📅 {institutional.date}
                    </span>
                  )}
                </div>
                {institutional ? (
                  <div className="space-y-3">
                    {/* 外資 */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">🌍</span>
                          <span className="text-white font-medium">外資</span>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold text-lg ${
                            (institutional.foreign?.net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {institutional.foreign?.net_display || '-'}
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

                    {/* 投信 */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">🏦</span>
                          <span className="text-white font-medium">投信</span>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold text-lg ${
                            (institutional.investment_trust?.net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {institutional.investment_trust?.net_display || '-'}
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

                    {/* 自營商 */}
                    <div className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">🏢</span>
                          <span className="text-white font-medium">自營商</span>
                        </div>
                        <div className="text-right">
                          <div className={`font-bold text-lg ${
                            (institutional.dealer?.net || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {institutional.dealer?.net_display || '-'}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 三大法人合計 */}
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
                          {institutional.total_net_display || '-'}
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

  useEffect(() => {
    fetchPortfolio();
  }, []);

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

      {/* 新增按鈕 */}
      <div className="flex justify-between items-center">
        <h3 className="text-white font-semibold">持股列表</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors"
        >
          {showAddForm ? '取消' : '➕ 新增持股'}
        </button>
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
  const [selectedStrategy, setSelectedStrategy] = useState('ma_crossover');
  const [months, setMonths] = useState(6);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 擴充股票清單（78 檔核心股票）
  const popularStocks = [
    // 半導體
    { id: '2330', name: '台積電' },
    { id: '2454', name: '聯發科' },
    { id: '2303', name: '聯電' },
    { id: '3711', name: '日月光投控' },
    { id: '2379', name: '瑞昱' },
    { id: '3034', name: '聯詠' },
    { id: '2344', name: '華邦電' },
    { id: '3037', name: '欣興' },
    { id: '6415', name: '矽力-KY' },
    { id: '2408', name: '南亞科' },
    // 電子
    { id: '2317', name: '鴻海' },
    { id: '2382', name: '廣達' },
    { id: '2357', name: '華碩' },
    { id: '2395', name: '研華' },
    { id: '3231', name: '緯創' },
    { id: '2308', name: '台達電' },
    { id: '2301', name: '光寶科' },
    { id: '2356', name: '英業達' },
    { id: '2324', name: '仁寶' },
    { id: '3017', name: '奇鋐' },
    // 金融
    { id: '2881', name: '富邦金' },
    { id: '2882', name: '國泰金' },
    { id: '2891', name: '中信金' },
    { id: '2884', name: '玉山金' },
    { id: '2886', name: '兆豐金' },
    { id: '2887', name: '台新金' },
    { id: '2892', name: '第一金' },
    { id: '2880', name: '華南金' },
    { id: '5880', name: '合庫金' },
    { id: '5876', name: '上海商銀' },
    // 傳產
    { id: '1301', name: '台塑' },
    { id: '1303', name: '南亞' },
    { id: '1326', name: '台化' },
    { id: '2002', name: '中鋼' },
    { id: '1101', name: '台泥' },
    { id: '1216', name: '統一' },
    { id: '2912', name: '統一超' },
    { id: '9910', name: '豐泰' },
    { id: '1227', name: '佳格' },
    { id: '2207', name: '和泰車' },
    // 航運/航空
    { id: '2603', name: '長榮' },
    { id: '2609', name: '陽明' },
    { id: '2615', name: '萬海' },
    { id: '2610', name: '華航' },
    { id: '2618', name: '長榮航' },
    // 電信
    { id: '2412', name: '中華電' },
    { id: '3045', name: '台灣大' },
    { id: '4904', name: '遠傳' },
    // 生技
    { id: '6446', name: '藥華藥' },
    { id: '4743', name: '合一' },
    { id: '6472', name: '保瑞' },
    // AI/伺服器
    { id: '2345', name: '智邦' },
    { id: '6669', name: '緯穎' },
    { id: '3653', name: '健策' },
    { id: '2049', name: '上銀' },
    { id: '2059', name: '川湖' },
    // ETF
    { id: '0050', name: '元大台灣50' },
    { id: '0056', name: '元大高股息' },
    { id: '00878', name: '國泰永續高股息' },
    { id: '00919', name: '群益台灣精選高息' },
    // 其他熱門
    { id: '3008', name: '大立光' },
    { id: '2474', name: '可成' },
    { id: '2377', name: '微星' },
    { id: '2353', name: '宏碁' },
    { id: '2327', name: '國巨' },
    { id: '3443', name: '創意' },
    { id: '6550', name: '北極星藥業-KY' },
    { id: '2923', name: '鼎固-KY' },
    { id: '2436', name: '偉詮電' },
    { id: '2449', name: '京元電子' },
  ];

  // 載入策略清單
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
    loadStrategies();
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
  
  // 過濾建議清單
  const filteredStocks = stockInput 
    ? popularStocks.filter(s => 
        s.id.includes(stockInput) || 
        s.name.includes(stockInput)
      ).slice(0, 8)
    : popularStocks.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* 設定區 */}
      <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-500/30">
        <h3 className="text-white font-bold text-lg mb-4">📈 回測設定</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 股票選擇 - 合併為單一搜尋框 */}
          <div className="relative">
            <label className="text-slate-400 text-sm block mb-2">股票代號/名稱</label>
            <input
              type="text"
              value={stockInput}
              onChange={(e) => {
                setStockInput(e.target.value);
                setShowSuggestions(true);
                // 如果是有效代號，同步更新
                if (e.target.value.match(/^\d{4,6}$/)) {
                  setSelectedStock(e.target.value);
                }
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="輸入代號或名稱搜尋..."
              className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-blue-500 outline-none placeholder-slate-500"
            />
            {/* 顯示當前選擇 */}
            <p className="text-emerald-400 text-xs mt-1">
              ✓ 已選擇: {selectedStock} {popularStocks.find(s => s.id === selectedStock)?.name || ''}
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
  const [activeSection, setActiveSection] = useState('ai'); // 'ai' | 'hot' | 'volume' | 'dark'

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
      setLastUpdate(new Date().toLocaleTimeString('zh-TW'));
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('無法連接到 API，請確認後端服務是否正在執行');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const sections = [
    { id: 'ai', label: '🎯 AI 精選', data: recommendations, desc: '依技術分析評分排序' },
    { id: 'hot', label: '🔥 熱門飆股', data: hotStocks, desc: '當日漲幅最大' },
    { id: 'volume', label: '📊 成交熱門', data: volumeHot, desc: '成交量比率最高' },
    { id: 'dark', label: '🐴 潛力黑馬', data: darkHorses, desc: '評分中等但有上漲潛力' },
    { id: 'portfolio', label: '💼 我的投組', data: [], desc: '管理你的投資組合', isPortfolio: true },
    { id: 'backtest', label: '📈 回測', data: [], desc: '策略回測模擬', isBacktest: true },
  ];

  const currentSection = sections.find(s => s.id === activeSection) || sections[0];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📈</span>
              <div>
                <h1 className="text-xl font-bold text-white">StockBuddy</h1>
                <p className="text-slate-400 text-xs">台股智能選股系統 V10.6</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {market && (
                <div className="text-right">
                  <div className="text-slate-400 text-xs">加權指數</div>
                  <div className={`font-medium ${market.change_percent >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {market.value?.toLocaleString()} ({market.change_percent >= 0 ? '+' : ''}{market.change_percent?.toFixed(2)}%)
                  </div>
                </div>
              )}
              <button
                onClick={fetchData}
                disabled={loading}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors disabled:opacity-50"
              >
                {loading ? '更新中...' : '🔄 更新'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* 狀態欄 */}
        <div className="mb-4 flex items-center justify-between text-sm">
          <div className="text-slate-400">
            📡 掃描 {scanned} 檔 | 分析 {analyzed} 檔
            {lastUpdate && <span className="ml-3">⏱️ {lastUpdate} 更新</span>}
          </div>
        </div>

        {/* 6 分類 Tab */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {sections.map(section => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                activeSection === section.id
                  ? section.isPortfolio ? 'bg-purple-600 text-white' 
                    : section.isBacktest ? 'bg-emerald-600 text-white'
                    : 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {section.label}
              {!section.isPortfolio && !section.isBacktest && (
                <span className="ml-2 text-xs opacity-70">({section.data.length})</span>
              )}
            </button>
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
        ) : activeSection === 'portfolio' ? (
          // 投資組合視圖
          <PortfolioPanel onSelectStock={setSelectedStock} />
        ) : activeSection === 'backtest' ? (
          // 回測視圖
          <BacktestPanel />
        ) : loading && recommendations.length === 0 ? (
          <Loading />
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* 股票列表 */}
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-white font-semibold">{currentSection.label}</h2>
                <span className="text-slate-500 text-sm">{currentSection.desc}</span>
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                {currentSection.data.slice(0, 20).map((stock, index) => (
                  <div key={stock.stock_id} className="relative">
                    <div className="absolute -left-2 -top-2 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold text-white z-10">
                      {index + 1}
                    </div>
                    <StockCard
                      stock={stock}
                      onClick={setSelectedStock}
                      isSelected={selectedStock?.stock_id === stock.stock_id}
                    />
                  </div>
                ))}
              </div>
              {currentSection.data.length === 0 && !loading && (
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
        </div>
      </footer>
    </div>
  );
}
