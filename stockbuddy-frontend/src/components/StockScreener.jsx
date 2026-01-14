/**
 * 選股篩選器組件 V10.36
 *
 * 功能：
 * - 自訂篩選條件（本益比、殖利率、ROE 等）
 * - 預設篩選策略（價值投資、成長股、高殖利率等）
 * - 篩選結果展示
 * - 支援將股票加入追蹤清單
 * - V10.36: ML 預測結果顯示
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

// 預設策略配置
const PRESET_STYLES = {
  value: { icon: '💎', color: 'from-blue-500 to-cyan-500', label: '價值投資' },
  growth: { icon: '🚀', color: 'from-purple-500 to-pink-500', label: '成長股' },
  dividend: { icon: '💰', color: 'from-amber-500 to-orange-500', label: '高殖利率' },
  momentum: { icon: '📈', color: 'from-red-500 to-rose-500', label: '動能股' },
  defensive: { icon: '🛡️', color: 'from-emerald-500 to-teal-500', label: '防禦型' },
  small_cap: { icon: '💡', color: 'from-indigo-500 to-violet-500', label: '小型成長' },
  blue_chip: { icon: '🏆', color: 'from-slate-500 to-slate-600', label: '績優藍籌' },
};

// V10.17: 篩選結果卡片（修正：顯示中文名稱 + 代號）
const ScreenerResultCard = ({ stock, onSelect, onTrack }) => {
  const getValuationColor = (comment) => {
    if (!comment) return 'text-slate-400';
    if (comment.includes('低估') || comment.includes('低於淨值')) return 'text-emerald-400';
    if (comment.includes('高估') || comment.includes('過高')) return 'text-red-400';
    return 'text-slate-400';
  };

  // V10.17: 獲取股票名稱（優先使用 name，其次 stock_name）
  const stockName = stock.name || stock.stock_name || stock.stock_id;

  return (
    <div
      className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-blue-500/50 cursor-pointer transition-all group"
      onClick={() => onSelect(stock)}
    >
      {/* V10.17: 標題列 - 中文名稱 + 代號並列 */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold group-hover:text-blue-400 transition-colors">
              {stockName}
            </span>
            <span className="text-slate-500 text-sm">({stock.stock_id})</span>
          </div>
          <div className="text-slate-500 text-xs mt-0.5">{stock.sector || '未分類'}</div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onTrack(stock);
          }}
          className="px-2 py-1 bg-slate-700 hover:bg-blue-600 text-slate-300 hover:text-white rounded text-xs transition-colors"
        >
          + 追蹤
        </button>
      </div>

      {/* 市值 */}
      <div className="text-lg font-bold text-white mb-3">
        {stock.market_cap_display || 'N/A'}
      </div>

      {/* 關鍵指標 */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <div className="text-slate-500 text-xs">本益比</div>
          <div className="text-white font-medium">
            {stock.pe_ratio ? stock.pe_ratio.toFixed(1) : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-slate-500 text-xs">股價淨值比</div>
          <div className="text-white font-medium">
            {stock.pb_ratio ? stock.pb_ratio.toFixed(2) : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-slate-500 text-xs">殖利率</div>
          <div className={`font-medium ${stock.dividend_yield >= 5 ? 'text-amber-400' : 'text-white'}`}>
            {stock.dividend_yield ? `${stock.dividend_yield.toFixed(2)}%` : 'N/A'}
          </div>
        </div>
        <div>
          <div className="text-slate-500 text-xs">ROE</div>
          <div className={`font-medium ${stock.roe >= 15 ? 'text-emerald-400' : 'text-white'}`}>
            {stock.roe ? `${stock.roe.toFixed(1)}%` : 'N/A'}
          </div>
        </div>
      </div>

      {/* 估值評論 */}
      <div className={`text-xs ${getValuationColor(stock.valuation_comment)}`}>
        {stock.valuation_comment || ''}
      </div>

      {/* V10.36: ML 預測結果 */}
      {stock.ml_prediction && (
        <div className="mt-3 pt-3 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-slate-500 text-xs">ML 預測</span>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              stock.ml_prediction === 'up'
                ? 'bg-red-500/20 text-red-400'
                : stock.ml_prediction === 'down'
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {stock.ml_prediction === 'up' && `📈 看漲 ${Math.round(stock.ml_probability * 100)}%`}
              {stock.ml_prediction === 'down' && `📉 看跌 ${Math.round((1 - stock.ml_probability) * 100)}%`}
              {stock.ml_prediction === 'neutral' && `⟺ 中性`}
            </span>
          </div>
          <div className="text-slate-600 text-[10px] mt-1 text-right">
            信心: {stock.ml_confidence || 'medium'}
          </div>
        </div>
      )}
    </div>
  );
};

// 預設策略選擇器
const PresetSelector = ({ presets, selectedPreset, onSelect, loading }) => {
  return (
    <div className="space-y-3">
      <h3 className="text-white font-semibold flex items-center gap-2">
        <span>⚡</span> 快速篩選
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
        {presets.map((preset) => {
          const style = PRESET_STYLES[preset.id] || { icon: '📊', color: 'from-slate-500 to-slate-600' };
          const isSelected = selectedPreset === preset.id;

          return (
            <button
              key={preset.id}
              onClick={() => onSelect(preset.id)}
              disabled={loading && isSelected}
              className={`p-3 rounded-xl text-center transition-all relative ${
                isSelected
                  ? `bg-gradient-to-br ${style.color} text-white shadow-lg scale-105`
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
              } ${loading && isSelected ? 'opacity-80' : ''}`}
            >
              {loading && isSelected && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/30 rounded-xl">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                </div>
              )}
              <div className="text-2xl mb-1">{style.icon}</div>
              <div className="text-xs font-medium">{style.label}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

// 自訂篩選表單
const CustomFilterForm = ({ filters, onChange, onSubmit, loading }) => {
  const handleChange = (field, value) => {
    onChange({ ...filters, [field]: value === '' ? null : Number(value) });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-white font-semibold flex items-center gap-2">
        <span>🔧</span> 自訂篩選
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* 本益比 */}
        <div className="space-y-1">
          <label className="text-slate-400 text-xs">本益比上限</label>
          <input
            type="number"
            value={filters.pe_max || ''}
            onChange={(e) => handleChange('pe_max', e.target.value)}
            placeholder="例: 15"
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 outline-none"
          />
        </div>

        {/* 股價淨值比 */}
        <div className="space-y-1">
          <label className="text-slate-400 text-xs">股價淨值比上限</label>
          <input
            type="number"
            step="0.1"
            value={filters.pb_max || ''}
            onChange={(e) => handleChange('pb_max', e.target.value)}
            placeholder="例: 1.5"
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 outline-none"
          />
        </div>

        {/* 殖利率 */}
        <div className="space-y-1">
          <label className="text-slate-400 text-xs">殖利率下限 (%)</label>
          <input
            type="number"
            step="0.5"
            value={filters.dividend_yield_min || ''}
            onChange={(e) => handleChange('dividend_yield_min', e.target.value)}
            placeholder="例: 3"
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 outline-none"
          />
        </div>

        {/* ROE */}
        <div className="space-y-1">
          <label className="text-slate-400 text-xs">ROE 下限 (%)</label>
          <input
            type="number"
            value={filters.roe_min || ''}
            onChange={(e) => handleChange('roe_min', e.target.value)}
            placeholder="例: 10"
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 outline-none"
          />
        </div>
      </div>

      {/* 市值規模 */}
      <div className="space-y-2">
        <label className="text-slate-400 text-xs">市值規模</label>
        <div className="flex gap-2">
          {[
            { value: '', label: '不限' },
            { value: 'large', label: '大型股 (>500億)' },
            { value: 'mid', label: '中型股 (50-500億)' },
            { value: 'small', label: '小型股 (<50億)' },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleChange('market_cap_size', opt.value || null)}
              className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                (filters.market_cap_size || '') === opt.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* 執行按鈕 */}
      <div className="flex gap-2">
        <button
          onClick={onSubmit}
          disabled={loading}
          className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors"
        >
          {loading ? '篩選中...' : '🔍 執行篩選'}
        </button>
        <button
          onClick={() => onChange({})}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors"
        >
          清除
        </button>
      </div>
    </div>
  );
};

// 篩選條件標籤
const FilterTags = ({ filters }) => {
  if (!filters || filters.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((filter, i) => (
        <span
          key={i}
          className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs border border-blue-500/30"
        >
          {filter.label}: {filter.condition}
        </span>
      ))}
    </div>
  );
};

// 主組件
const StockScreener = ({ onSelectStock }) => {
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [customFilters, setCustomFilters] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('preset'); // 'preset' or 'custom'

  // 載入預設策略
  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/stocks/screener/presets`);
        const data = await res.json();
        if (data.success) {
          setPresets(data.presets);
        }
      } catch (err) {
        console.error('載入預設策略失敗:', err);
      }
    };
    fetchPresets();
  }, []);

  // V10.36: 取得 ML 預測結果
  const fetchMLPredictions = async (stocks) => {
    if (!stocks || stocks.length === 0) return stocks;

    try {
      // 批次預測
      const stockIds = stocks.map(s => s.stock_id).slice(0, 10); // 限制前 10 檔
      const predictions = await Promise.all(
        stockIds.map(async (id) => {
          try {
            const res = await fetch(`${API_BASE}/api/stocks/ml/predict/${id}`);
            const data = await res.json();
            return data.success ? { stock_id: id, ...data } : null;
          } catch {
            return null;
          }
        })
      );

      // 合併預測結果到股票資料
      return stocks.map(stock => {
        const prediction = predictions.find(p => p && p.stock_id === stock.stock_id);
        if (prediction) {
          return {
            ...stock,
            ml_prediction: prediction.prediction,
            ml_probability: prediction.probability,
            ml_confidence: prediction.confidence,
          };
        }
        return stock;
      });
    } catch (err) {
      console.error('ML 預測失敗:', err);
      return stocks;
    }
  };

  // 預設策略篩選
  const handlePresetSelect = async (presetId) => {
    setSelectedPreset(presetId);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/stocks/screener/preset/${presetId}?limit=20`);
      const data = await res.json();
      if (data.success) {
        // V10.36: 取得 ML 預測
        const stocksWithML = await fetchMLPredictions(data.stocks);
        setResults({ ...data, stocks: stocksWithML });
      }
    } catch (err) {
      console.error('篩選失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  // 自訂篩選
  const handleCustomScreen = async () => {
    setSelectedPreset(null);
    setLoading(true);

    try {
      const params = new URLSearchParams();
      Object.entries(customFilters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          params.append(key, value);
        }
      });

      const res = await fetch(`${API_BASE}/api/stocks/screener/screen?${params}`);
      const data = await res.json();
      if (data.success) {
        // V10.36: 取得 ML 預測
        const stocksWithML = await fetchMLPredictions(data.stocks);
        setResults({ ...data, stocks: stocksWithML });
      }
    } catch (err) {
      console.error('篩選失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  // 追蹤股票
  const handleTrackStock = (stock) => {
    const tracked = JSON.parse(localStorage.getItem('trackedStocks') || '[]');
    if (!tracked.find(t => t.stock_id === stock.stock_id)) {
      tracked.push({
        stock_id: stock.stock_id,
        name: stock.stock_id,
        added_at: new Date().toISOString(),
      });
      localStorage.setItem('trackedStocks', JSON.stringify(tracked));
      alert(`已將 ${stock.stock_id} 加入追蹤清單`);
    } else {
      alert(`${stock.stock_id} 已在追蹤清單中`);
    }
  };

  return (
    <div className="space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🔍</span> 選股篩選器
        </h2>
        <div className="text-slate-500 text-sm">
          股票池: {presets.length > 0 ? `${results?.matched_count || '70+'}檔股票` : '載入中...'}
        </div>
      </div>

      {/* 篩選模式切換 */}
      <div className="flex gap-2 border-b border-slate-700 pb-2">
        <button
          onClick={() => setActiveTab('preset')}
          className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
            activeTab === 'preset'
              ? 'bg-slate-800 text-white border-b-2 border-blue-500'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          ⚡ 快速篩選
        </button>
        <button
          onClick={() => setActiveTab('custom')}
          className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
            activeTab === 'custom'
              ? 'bg-slate-800 text-white border-b-2 border-blue-500'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          🔧 自訂條件
        </button>
      </div>

      {/* 篩選區域 */}
      <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50">
        {activeTab === 'preset' ? (
          <PresetSelector
            presets={presets}
            selectedPreset={selectedPreset}
            onSelect={handlePresetSelect}
            loading={loading}
          />
        ) : (
          <CustomFilterForm
            filters={customFilters}
            onChange={setCustomFilters}
            onSubmit={handleCustomScreen}
            loading={loading}
          />
        )}
      </div>

      {/* 篩選結果 */}
      {results && (
        <div className="space-y-4">
          {/* 結果標題 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h3 className="text-white font-semibold">
                篩選結果
                {results.preset && (
                  <span className="ml-2 text-sm text-slate-400">
                    ({results.preset.name})
                  </span>
                )}
              </h3>
              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-sm">
                {results.matched_count} 檔符合
              </span>
            </div>
            <div className="text-slate-500 text-xs">
              掃描 {results.total_scanned} 檔 / 耗時 {results.execution_time}s
            </div>
          </div>

          {/* 套用的篩選條件 */}
          <FilterTags filters={results.filters_applied} />

          {/* 結果卡片 */}
          {results.stocks && results.stocks.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {results.stocks.map((stock) => (
                <ScreenerResultCard
                  key={stock.stock_id}
                  stock={stock}
                  onSelect={onSelectStock}
                  onTrack={handleTrackStock}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-4">🔍</div>
              <p>沒有符合條件的股票</p>
              <p className="text-sm mt-2">請嘗試調整篩選條件</p>
            </div>
          )}
        </div>
      )}

      {/* 空狀態 */}
      {!results && !loading && (
        <div className="text-center py-12 text-slate-500">
          <div className="text-4xl mb-4">📊</div>
          <p>選擇篩選策略或設定條件開始篩選</p>
        </div>
      )}

      {/* 載入中 */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-3 text-slate-400">篩選中...</span>
        </div>
      )}

      {/* 說明 */}
      <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/50">
        <h4 className="text-white font-medium mb-2">📖 篩選說明</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-400">
          <div>
            <p className="font-medium text-slate-300 mb-1">預設策略</p>
            <ul className="list-disc list-inside space-y-1">
              <li>價值投資：PE &lt; 15, 殖利率 &gt; 3%</li>
              <li>成長股：ROE &gt; 15%, PE &lt; 30</li>
              <li>高殖利率：殖利率 &gt; 5%</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-slate-300 mb-1">市值規模</p>
            <ul className="list-disc list-inside space-y-1">
              <li>大型股：市值 &gt; 500 億</li>
              <li>中型股：50 億 ~ 500 億</li>
              <li>小型股：市值 &lt; 50 億</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockScreener;
