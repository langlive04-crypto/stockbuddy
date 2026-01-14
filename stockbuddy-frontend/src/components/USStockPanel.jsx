/**
 * USStockPanel.jsx - 美股市場組件
 * V10.24 新增, V10.27 增加技術分析
 *
 * 功能：
 * - 美股市場狀態顯示
 * - 主要指數即時報價
 * - 熱門美股清單
 * - 產業分類瀏覽
 * - 搜尋美股
 * - 個股詳細資訊
 * - V10.27: 技術分析指標 (RSI, MACD, KD, 布林通道)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { API_STOCKS_BASE } from '../config';

const API_BASE = API_STOCKS_BASE;

// 產業中文名稱對照
const SECTOR_NAMES = {
  technology: '科技股',
  semiconductor: '半導體',
  finance: '金融股',
  consumer: '消費股',
  healthcare: '醫療保健',
  communication: '通訊服務',
  energy: '能源股',
  ai_concept: 'AI 概念股',
};

const USStockPanel = ({ onSelectStock }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [marketStatus, setMarketStatus] = useState(null);
  const [indices, setIndices] = useState({});
  const [hotStocks, setHotStocks] = useState([]);
  const [movers, setMovers] = useState({ gainers: [], losers: [] });
  const [sectorStocks, setSectorStocks] = useState([]);
  const [selectedSector, setSelectedSector] = useState('technology');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockDetail, setStockDetail] = useState(null);
  const [technicalData, setTechnicalData] = useState(null);  // V10.27: 技術分析
  const [technicalLoading, setTechnicalLoading] = useState(false);  // V10.27
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 取得市場狀態
  const fetchMarketStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/us/market-status`);
      const data = await res.json();
      setMarketStatus(data);
    } catch (e) {
      console.error('Error fetching market status:', e);
    }
  }, []);

  // 取得主要指數
  const fetchIndices = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/us/indices`);
      const data = await res.json();
      if (data.success) {
        setIndices(data.data);
      }
    } catch (e) {
      console.error('Error fetching indices:', e);
    }
  }, []);

  // 取得熱門股票
  const fetchHotStocks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/us/hot`);
      const data = await res.json();
      if (data.success) {
        setHotStocks(data.data);
      }
    } catch (e) {
      console.error('Error fetching hot stocks:', e);
    }
  }, []);

  // 取得漲跌排行
  const fetchMovers = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/us/movers`);
      const data = await res.json();
      if (data.success) {
        setMovers(data.data);
      }
    } catch (e) {
      console.error('Error fetching movers:', e);
    }
  }, []);

  // 取得產業股票
  const fetchSectorStocks = useCallback(async (sector) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/us/sector/${sector}`);
      const data = await res.json();
      if (data.success) {
        setSectorStocks(data.data);
      }
    } catch (e) {
      console.error('Error fetching sector stocks:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  // 搜尋美股
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/us/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data.success) {
        setSearchResults(data.data);
      }
    } catch (e) {
      console.error('Error searching stocks:', e);
    }
  }, [searchQuery]);

  // 取得股票詳細資訊
  const fetchStockDetail = useCallback(async (symbol) => {
    setLoading(true);
    setError(null);
    try {
      const [infoRes, profileRes] = await Promise.all([
        fetch(`${API_BASE}/us/stock/${symbol}`),
        fetch(`${API_BASE}/us/stock/${symbol}/profile`),
      ]);
      const infoData = await infoRes.json();
      const profileData = await profileRes.json();

      if (infoData.success) {
        setStockDetail({
          ...infoData.data,
          ...(profileData.success ? profileData.data : {}),
        });
      } else {
        setError(infoData.error || '無法取得股票資訊');
      }
    } catch (e) {
      setError('載入失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  // V10.27: 取得技術分析資料
  const fetchTechnicalData = useCallback(async (symbol) => {
    setTechnicalLoading(true);
    try {
      const res = await fetch(`${API_BASE}/us/stock/${symbol}/technical`);
      const data = await res.json();
      if (data.success) {
        setTechnicalData(data.data);
      } else {
        setTechnicalData(null);
      }
    } catch (e) {
      console.error('Error fetching technical data:', e);
      setTechnicalData(null);
    } finally {
      setTechnicalLoading(false);
    }
  }, []);

  // 初始載入
  useEffect(() => {
    fetchMarketStatus();
    fetchIndices();
    fetchHotStocks();
    fetchMovers();
  }, [fetchMarketStatus, fetchIndices, fetchHotStocks, fetchMovers]);

  // 產業變更時載入
  useEffect(() => {
    if (activeTab === 'sectors') {
      fetchSectorStocks(selectedSector);
    }
  }, [activeTab, selectedSector, fetchSectorStocks]);

  // 搜尋防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, handleSearch]);

  // 選擇股票
  const handleSelectStock = (symbol) => {
    setSelectedStock(symbol);
    setTechnicalData(null);  // V10.27: 重置技術分析
    fetchStockDetail(symbol);
    fetchTechnicalData(symbol);  // V10.27: 同時載入技術分析
    if (onSelectStock) {
      onSelectStock(symbol, 'US');
    }
  };

  // 格式化數字
  const formatNumber = (num) => {
    if (!num) return '-';
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    return num.toLocaleString();
  };

  // 格式化百分比
  const formatPercent = (num) => {
    if (!num && num !== 0) return '-';
    return `${(num * 100).toFixed(2)}%`;
  };

  // 渲染市場狀態
  const renderMarketStatus = () => (
    <div className={`px-4 py-2 rounded-lg text-sm font-medium ${
      marketStatus?.is_open
        ? 'bg-emerald-500/20 text-emerald-400'
        : 'bg-slate-700 text-slate-400'
    }`}>
      <span className="mr-2">{marketStatus?.is_open ? '🟢' : '🔴'}</span>
      {marketStatus?.message || '載入中...'}
      <span className="ml-2 text-xs opacity-70">{marketStatus?.local_time}</span>
    </div>
  );

  // 渲染指數
  const renderIndices = () => (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      {Object.entries(indices).map(([symbol, data]) => (
        <div
          key={symbol}
          className="bg-slate-700/50 rounded-lg p-3 hover:bg-slate-700 transition-colors"
        >
          <div className="text-slate-400 text-xs mb-1">{data.name}</div>
          <div className="text-white font-bold">{data.value?.toLocaleString()}</div>
          <div className={`text-sm ${data.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.change_percent >= 0 ? '+' : ''}{data.change_percent?.toFixed(2)}%
          </div>
        </div>
      ))}
    </div>
  );

  // 渲染股票卡片
  const renderStockCard = (stock, compact = false) => (
    <div
      key={stock.symbol}
      onClick={() => handleSelectStock(stock.symbol)}
      className={`bg-slate-700/50 rounded-lg p-3 cursor-pointer hover:bg-slate-700 transition-colors ${
        selectedStock === stock.symbol ? 'ring-2 ring-blue-500' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-white font-bold">{stock.symbol}</span>
          <span className="text-slate-400 text-xs ml-2">{stock.name}</span>
        </div>
        {!compact && (
          <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
            USD
          </span>
        )}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-white text-lg font-medium">${stock.close?.toFixed(2)}</span>
        <span className={`text-sm font-medium ${
          stock.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'
        }`}>
          {stock.change_percent >= 0 ? '+' : ''}{stock.change_percent?.toFixed(2)}%
        </span>
      </div>
      {!compact && stock.volume && (
        <div className="text-slate-500 text-xs mt-1">
          成交量: {formatNumber(stock.volume)}
        </div>
      )}
    </div>
  );

  // 渲染總覽
  const renderOverview = () => (
    <div className="space-y-6">
      {/* 主要指數 */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          <span>📊</span> 主要指數
        </h3>
        {renderIndices()}
      </div>

      {/* 漲跌排行 */}
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>🚀</span> 漲幅排行
          </h3>
          <div className="space-y-2">
            {movers.gainers?.map((stock) => renderStockCard(stock, true))}
          </div>
        </div>
        <div>
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>📉</span> 跌幅排行
          </h3>
          <div className="space-y-2">
            {movers.losers?.map((stock) => renderStockCard(stock, true))}
          </div>
        </div>
      </div>

      {/* 熱門股票 */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          <span>🔥</span> 熱門美股
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {hotStocks.map((stock) => renderStockCard(stock, true))}
        </div>
      </div>
    </div>
  );

  // 渲染產業
  const renderSectors = () => (
    <div className="space-y-4">
      {/* 產業選擇 */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(SECTOR_NAMES).map(([key, name]) => (
          <button
            key={key}
            onClick={() => setSelectedSector(key)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              selectedSector === key
                ? 'bg-blue-500 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      {/* 產業股票 */}
      {loading ? (
        <div className="text-center text-slate-400 py-8">載入中...</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {sectorStocks.map((stock) => renderStockCard(stock))}
        </div>
      )}
    </div>
  );

  // 渲染搜尋
  const renderSearch = () => (
    <div className="space-y-4">
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="輸入股票代號或名稱搜尋..."
          className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">
          🔍
        </span>
      </div>

      {searchResults.length > 0 && (
        <div className="space-y-2">
          {searchResults.map((stock) => (
            <div
              key={stock.symbol}
              onClick={() => handleSelectStock(stock.symbol)}
              className="bg-slate-700/50 rounded-lg p-3 cursor-pointer hover:bg-slate-700 transition-colors"
            >
              <span className="text-white font-bold">{stock.symbol}</span>
              <span className="text-slate-400 ml-3">{stock.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // V10.27: 渲染技術分析
  const renderTechnicalAnalysis = () => {
    if (technicalLoading) {
      return (
        <div className="bg-slate-700/50 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>📈</span> 技術分析
          </h3>
          <div className="text-center text-slate-400 py-4">載入技術分析中...</div>
        </div>
      );
    }

    if (!technicalData) {
      return (
        <div className="bg-slate-700/50 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>📈</span> 技術分析
          </h3>
          <div className="text-center text-slate-500 py-4">無技術分析資料（需要至少60天歷史資料）</div>
        </div>
      );
    }

    const getScoreColor = (score) => {
      if (score >= 70) return 'text-emerald-400';
      if (score >= 55) return 'text-blue-400';
      if (score >= 45) return 'text-yellow-400';
      if (score >= 30) return 'text-orange-400';
      return 'text-red-400';
    };

    const getSignalBadge = (signal) => {
      const signalStyles = {
        '超買': 'bg-red-500/20 text-red-400',
        '超賣': 'bg-emerald-500/20 text-emerald-400',
        '金叉': 'bg-emerald-500/20 text-emerald-400',
        '黃金交叉': 'bg-emerald-500/20 text-emerald-400',
        '死叉': 'bg-red-500/20 text-red-400',
        '死亡交叉': 'bg-red-500/20 text-red-400',
        '多頭排列': 'bg-emerald-500/20 text-emerald-400',
        '空頭排列': 'bg-red-500/20 text-red-400',
        '偏強': 'bg-blue-500/20 text-blue-400',
        '偏弱': 'bg-orange-500/20 text-orange-400',
        '中性': 'bg-slate-500/20 text-slate-400',
        '盤整': 'bg-yellow-500/20 text-yellow-400',
        '上軌': 'bg-red-500/20 text-red-400',
        '下軌': 'bg-emerald-500/20 text-emerald-400',
        '中上': 'bg-blue-500/20 text-blue-400',
        '中下': 'bg-yellow-500/20 text-yellow-400',
      };
      return signalStyles[signal] || 'bg-slate-500/20 text-slate-400';
    };

    return (
      <div className="bg-slate-700/50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium flex items-center gap-2">
            <span>📈</span> 技術分析
          </h3>
          <div className="flex items-center gap-3">
            <span className="text-slate-400 text-sm">綜合評分:</span>
            <span className={`text-2xl font-bold ${getScoreColor(technicalData.summary?.score)}`}>
              {technicalData.summary?.score}
            </span>
            <span className={`px-3 py-1 rounded-lg text-sm font-medium ${
              technicalData.summary?.recommendation === '買進' ? 'bg-emerald-500/20 text-emerald-400' :
              technicalData.summary?.recommendation === '偏多' ? 'bg-blue-500/20 text-blue-400' :
              technicalData.summary?.recommendation === '持有' ? 'bg-yellow-500/20 text-yellow-400' :
              technicalData.summary?.recommendation === '偏空' ? 'bg-orange-500/20 text-orange-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {technicalData.summary?.recommendation}
            </span>
          </div>
        </div>

        {/* 指標網格 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* RSI */}
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-slate-400 text-xs mb-1">RSI (14)</div>
            <div className="flex items-center justify-between">
              <span className={`text-xl font-bold ${
                technicalData.rsi?.value >= 70 ? 'text-red-400' :
                technicalData.rsi?.value <= 30 ? 'text-emerald-400' :
                'text-white'
              }`}>
                {technicalData.rsi?.value?.toFixed(1) || '-'}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded ${getSignalBadge(technicalData.rsi?.signal)}`}>
                {technicalData.rsi?.signal}
              </span>
            </div>
            {/* RSI 視覺條 */}
            <div className="mt-2 h-1.5 bg-slate-600 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  technicalData.rsi?.value >= 70 ? 'bg-red-400' :
                  technicalData.rsi?.value <= 30 ? 'bg-emerald-400' :
                  'bg-blue-400'
                }`}
                style={{ width: `${technicalData.rsi?.value || 0}%` }}
              />
            </div>
          </div>

          {/* MACD */}
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-slate-400 text-xs mb-1">MACD</div>
            <div className="flex items-center justify-between">
              <span className={`text-xl font-bold ${
                technicalData.macd?.histogram > 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {technicalData.macd?.histogram?.toFixed(2) || '-'}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded ${getSignalBadge(technicalData.macd?.cross)}`}>
                {technicalData.macd?.cross || '無'}
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-1">
              DIF: {technicalData.macd?.macd?.toFixed(2)} | Signal: {technicalData.macd?.signal?.toFixed(2)}
            </div>
          </div>

          {/* KD */}
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-slate-400 text-xs mb-1">KD (9)</div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-blue-400 font-bold">K:{technicalData.kd?.k?.toFixed(0)}</span>
                <span className="text-slate-400 mx-1">/</span>
                <span className="text-yellow-400 font-bold">D:{technicalData.kd?.d?.toFixed(0)}</span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${getSignalBadge(technicalData.kd?.signal)}`}>
                {technicalData.kd?.signal}
              </span>
            </div>
          </div>

          {/* MA 趨勢 */}
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-slate-400 text-xs mb-1">均線趨勢</div>
            <div className="flex items-center justify-between">
              <span className={`text-sm font-bold ${
                technicalData.ma?.trend === '多頭排列' ? 'text-emerald-400' :
                technicalData.ma?.trend === '空頭排列' ? 'text-red-400' :
                'text-yellow-400'
              }`}>
                {technicalData.ma?.trend}
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-1">
              MA5: {technicalData.ma?.ma5?.toFixed(2)}
            </div>
          </div>
        </div>

        {/* 布林通道與支撐壓力 */}
        <div className="grid grid-cols-2 gap-3 mt-3">
          {/* 布林通道 */}
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-slate-400 text-xs mb-2">布林通道 (20, 2)</div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-500">上軌</span>
              <span className="text-red-400 font-medium">${technicalData.bollinger?.upper?.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-500">中軌</span>
              <span className="text-white font-medium">${technicalData.bollinger?.middle?.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-500">下軌</span>
              <span className="text-emerald-400 font-medium">${technicalData.bollinger?.lower?.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">位置</span>
              <span className={`text-xs px-2 py-0.5 rounded ${getSignalBadge(technicalData.bollinger?.position)}`}>
                {technicalData.bollinger?.position}
              </span>
            </div>
          </div>

          {/* 支撐壓力 */}
          <div className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-slate-400 text-xs mb-2">支撐 / 壓力位</div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-500">壓力位</span>
              <span className="text-red-400 font-medium">${technicalData.support_resistance?.resistance?.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-500">支撐位</span>
              <span className="text-emerald-400 font-medium">${technicalData.support_resistance?.support?.toFixed(2)}</span>
            </div>
            {stockDetail?.close && (
              <div className="text-xs text-slate-400 mt-2 pt-2 border-t border-slate-700">
                現價距壓力: {((technicalData.support_resistance?.resistance - stockDetail.close) / stockDetail.close * 100).toFixed(1)}%
                <br />
                現價距支撐: {((stockDetail.close - technicalData.support_resistance?.support) / stockDetail.close * 100).toFixed(1)}%
              </div>
            )}
          </div>
        </div>

        {/* 移動平均線詳情 */}
        <div className="bg-slate-800/50 rounded-lg p-3 mt-3">
          <div className="text-slate-400 text-xs mb-2">移動平均線</div>
          <div className="grid grid-cols-4 gap-2 text-sm">
            <div>
              <span className="text-slate-500 text-xs">MA5</span>
              <div className="text-white font-medium">${technicalData.ma?.ma5?.toFixed(2)}</div>
            </div>
            <div>
              <span className="text-slate-500 text-xs">MA10</span>
              <div className="text-white font-medium">${technicalData.ma?.ma10?.toFixed(2)}</div>
            </div>
            <div>
              <span className="text-slate-500 text-xs">MA20</span>
              <div className="text-white font-medium">${technicalData.ma?.ma20?.toFixed(2)}</div>
            </div>
            <div>
              <span className="text-slate-500 text-xs">MA60</span>
              <div className="text-white font-medium">${technicalData.ma?.ma60?.toFixed(2)}</div>
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-500 mt-3 text-right">
          資料日期: {technicalData.date}
        </div>
      </div>
    );
  };

  // 渲染股票詳情
  const renderStockDetail = () => {
    if (!stockDetail) return null;

    return (
      <div className="space-y-4">
        {/* 返回按鈕 */}
        <button
          onClick={() => {
            setSelectedStock(null);
            setStockDetail(null);
          }}
          className="text-slate-400 hover:text-white text-sm flex items-center gap-1"
        >
          ← 返回列表
        </button>

        {/* 股票標題 */}
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-2xl font-bold text-white">{stockDetail.symbol}</h2>
              <p className="text-slate-400">{stockDetail.name}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-white">
                ${stockDetail.close?.toFixed(2)}
              </div>
              <div className={`text-lg ${
                stockDetail.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {stockDetail.change >= 0 ? '+' : ''}${stockDetail.change?.toFixed(2)}
                ({stockDetail.change_percent >= 0 ? '+' : ''}{stockDetail.change_percent?.toFixed(2)}%)
              </div>
            </div>
          </div>

          {/* 基本資訊 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">開盤</div>
              <div className="text-white">${stockDetail.open?.toFixed(2)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">最高</div>
              <div className="text-white">${stockDetail.high?.toFixed(2)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">最低</div>
              <div className="text-white">${stockDetail.low?.toFixed(2)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">成交量</div>
              <div className="text-white">{formatNumber(stockDetail.volume)}</div>
            </div>
          </div>
        </div>

        {/* 公司資訊 */}
        {stockDetail.sector && (
          <div className="bg-slate-700/50 rounded-lg p-4">
            <h3 className="text-white font-medium mb-3">公司資訊</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-slate-400">產業：</span>
                <span className="text-white ml-2">{stockDetail.sector}</span>
              </div>
              <div>
                <span className="text-slate-400">行業：</span>
                <span className="text-white ml-2">{stockDetail.industry}</span>
              </div>
              {stockDetail.employees && (
                <div>
                  <span className="text-slate-400">員工數：</span>
                  <span className="text-white ml-2">{formatNumber(stockDetail.employees)}</span>
                </div>
              )}
              {stockDetail.country && (
                <div>
                  <span className="text-slate-400">國家：</span>
                  <span className="text-white ml-2">{stockDetail.country}</span>
                </div>
              )}
            </div>
            {stockDetail.description && (
              <p className="text-slate-400 text-sm mt-3 line-clamp-3">
                {stockDetail.description}
              </p>
            )}
          </div>
        )}

        {/* 財務指標 */}
        <div className="bg-slate-700/50 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">財務指標</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">市值</div>
              <div className="text-white">${formatNumber(stockDetail.market_cap)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">本益比 (PE)</div>
              <div className="text-white">{stockDetail.pe_ratio?.toFixed(2) || '-'}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">預估 PE</div>
              <div className="text-white">{stockDetail.forward_pe?.toFixed(2) || '-'}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">殖利率</div>
              <div className="text-white">{formatPercent(stockDetail.dividend_yield)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">ROE</div>
              <div className="text-white">{formatPercent(stockDetail.roe)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">利潤率</div>
              <div className="text-white">{formatPercent(stockDetail.profit_margin)}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">52週高點</div>
              <div className="text-white">${stockDetail.fifty_two_week_high?.toFixed(2) || '-'}</div>
            </div>
            <div className="bg-slate-800/50 rounded p-2">
              <div className="text-slate-400">52週低點</div>
              <div className="text-white">${stockDetail.fifty_two_week_low?.toFixed(2) || '-'}</div>
            </div>
          </div>
        </div>

        {/* V10.27: 技術分析區塊 */}
        {renderTechnicalAnalysis()}
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
      {/* 標題列 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🇺🇸</span> 美股市場
        </h2>
        {renderMarketStatus()}
      </div>

      {/* 如果有選中股票，顯示詳情 */}
      {selectedStock && stockDetail ? (
        renderStockDetail()
      ) : (
        <>
          {/* 分頁選單 */}
          <div className="flex gap-2 mb-6 border-b border-slate-700 pb-4">
            {[
              { key: 'overview', label: '總覽', icon: '📊' },
              { key: 'sectors', label: '產業分類', icon: '🏭' },
              { key: 'search', label: '搜尋', icon: '🔍' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-blue-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </div>

          {/* 分頁內容 */}
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'sectors' && renderSectors()}
          {activeTab === 'search' && renderSearch()}
        </>
      )}

      {/* 錯誤提示 */}
      {error && (
        <div className="mt-4 bg-red-500/20 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};

export default USStockPanel;
