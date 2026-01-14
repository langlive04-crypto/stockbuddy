/**
 * ML 模型管理面板 V10.41
 *
 * 深色主題版本，與系統其他介面一致
 *
 * V10.41 更新:
 * - 新增版本管理功能 (列表、切換、比較)
 * - 新增增量訓練選項
 * - 新增訓練數據統計
 *
 * 功能：
 * - 查看模型狀態
 * - 訓練 ML 模型 (歷史數據 / 績效追蹤 / 增量)
 * - 版本管理與切換
 * - 測試股票預測
 * - 顯示特徵資訊
 */

import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../config';

// 預設股票清單選項
const STOCK_PRESETS = [
  { key: 'default', name: '預設 20 檔', count: 20, time: '30 秒', desc: '快速測試' },
  { key: 'top50', name: '市值 TOP 50', count: 50, time: '1-2 分鐘', desc: '權值股' },
  { key: 'top100', name: '市值 TOP 100 ⭐推薦', count: 100, time: '3-5 分鐘', desc: '最佳平衡' },
  { key: 'electronics50', name: '電子 TOP 50', count: 50, time: '1-2 分鐘', desc: '電子專精' },
  { key: 'electronics100', name: '電子 TOP 100', count: 100, time: '3-5 分鐘', desc: '完整電子' },
  { key: 'financials30', name: '金融 TOP 30', count: 30, time: '1 分鐘', desc: '金融專精' },
  { key: 'traditional50', name: '傳產 TOP 50', count: 50, time: '1-2 分鐘', desc: '傳產股' },
  { key: 'dividend30', name: '高股息 TOP 30', count: 30, time: '1 分鐘', desc: '存股族' },
  { key: 'custom', name: '自訂清單', count: null, time: '依數量', desc: '手動輸入' },
];

// 特徵類別定義
const FEATURE_CATEGORIES = [
  { key: 'price', name: '價格特徵', count: 13, color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  { key: 'momentum', name: '動能指標', count: 8, color: 'bg-green-500/20 text-green-400 border-green-500/30' },
  { key: 'volume', name: '成交量', count: 6, color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
  { key: 'volatility', name: '波動率', count: 6, color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
  { key: 'chip', name: '籌碼面', count: 8, color: 'bg-red-500/20 text-red-400 border-red-500/30' },
  { key: 'fundamental', name: '基本面', count: 8, color: 'bg-teal-500/20 text-teal-400 border-teal-500/30' },
  { key: 'market', name: '市場環境', count: 4, color: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' },
  { key: 'score', name: '評分', count: 2, color: 'bg-pink-500/20 text-pink-400 border-pink-500/30' },
];

const MLPanel = () => {
  // 狀態
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // 訓練設定
  const [trainMode, setTrainMode] = useState('historical');
  const [minSamples, setMinSamples] = useState(100);
  const [useFullFeatures, setUseFullFeatures] = useState(true);
  const [trainResult, setTrainResult] = useState(null);

  // 歷史數據訓練設定
  const [histPeriod, setHistPeriod] = useState('1y');
  const [predictDays, setPredictDays] = useState(5);
  const [selectedPreset, setSelectedPreset] = useState('top100');  // 預設選擇 TOP 100
  const [customStocks, setCustomStocks] = useState('');

  // V10.41: 增量訓練設定
  const [replayRatio, setReplayRatio] = useState(0.3);
  const [incrementalDataSource, setIncrementalDataSource] = useState('performance');

  // V10.41: 版本管理
  const [versions, setVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [trainingStats, setTrainingStats] = useState(null);

  // 預測測試
  const [testStockId, setTestStockId] = useState('2330');
  const [predictionResult, setPredictionResult] = useState(null);

  // 載入模型資訊
  const fetchModelInfo = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/stocks/ml/model-info`);
      const data = await res.json();
      if (data.success) {
        setModelInfo(data);
      } else {
        setError(data.error || '無法取得模型資訊');
      }
    } catch (err) {
      setError('連線失敗: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModelInfo();
    fetchVersions();
    fetchTrainingStats();
  }, [fetchModelInfo]);

  // V10.41: 載入版本列表
  const fetchVersions = async () => {
    setLoadingVersions(true);
    try {
      const res = await fetch(`${API_BASE}/api/stocks/ml/versions?limit=10`);
      const data = await res.json();
      if (data.success) {
        setVersions(data.versions || []);
      }
    } catch (err) {
      console.error('載入版本列表失敗:', err);
    } finally {
      setLoadingVersions(false);
    }
  };

  // V10.41: 載入訓練數據統計
  const fetchTrainingStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stocks/ml/training-data/stats`);
      const data = await res.json();
      if (data.success) {
        setTrainingStats(data.stats);
      }
    } catch (err) {
      console.error('載入訓練統計失敗:', err);
    }
  };

  // V10.41: 切換模型版本
  const handleActivateVersion = async (versionId) => {
    if (!window.confirm(`確定要切換到版本 ${versionId} 嗎？`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/stocks/ml/versions/${versionId}/activate`, {
        method: 'POST',
      });
      const data = await res.json();
      if (data.success) {
        setSuccess(`已切換到版本 ${versionId}`);
        fetchModelInfo();
        fetchVersions();
      } else {
        setError(data.error || '切換版本失敗');
      }
    } catch (err) {
      setError('切換版本請求失敗: ' + err.message);
    }
  };

  // 訓練模型
  const handleTrain = async () => {
    setTraining(true);
    setError(null);
    setSuccess(null);
    setTrainResult(null);

    try {
      let url;
      if (trainMode === 'historical') {
        url = `${API_BASE}/api/stocks/ml/train-historical?period=${histPeriod}&predict_days=${predictDays}&min_samples=${minSamples}`;
        // 優先使用預設清單，custom 模式則使用自訂股票
        if (selectedPreset === 'custom') {
          if (customStocks.trim()) {
            url += `&stock_ids=${encodeURIComponent(customStocks.trim())}`;
          }
        } else {
          url += `&preset=${selectedPreset}`;
        }
      } else if (trainMode === 'incremental') {
        // V10.41: 增量訓練
        url = `${API_BASE}/api/stocks/ml/train-incremental?data_source=${incrementalDataSource}&replay_ratio=${replayRatio}&min_new_samples=50`;
      } else if (trainMode === 'hybrid') {
        // V10.41: 混合訓練
        url = `${API_BASE}/api/stocks/ml/train-hybrid?min_samples=${minSamples}`;
      } else {
        url = `${API_BASE}/api/stocks/ml/train?min_samples=${minSamples}&use_full_features=${useFullFeatures}`;
      }

      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();

      if (data.success) {
        setTrainResult(data);
        setSuccess(`模型訓練成功！版本: ${data.version || data.model_version}`);
        fetchModelInfo();
        fetchVersions();
        fetchTrainingStats();
      } else {
        setError(data.error || '訓練失敗');
      }
    } catch (err) {
      setError('訓練請求失敗: ' + err.message);
    } finally {
      setTraining(false);
    }
  };

  // 測試預測
  const handlePredict = async () => {
    if (!testStockId.trim()) {
      setError('請輸入股票代碼');
      return;
    }

    setPredicting(true);
    setError(null);
    setPredictionResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/stocks/ml/predict/${testStockId.trim()}`);
      const data = await res.json();

      if (data.success) {
        setPredictionResult(data);
      } else {
        setError(data.error || '預測失敗');
      }
    } catch (err) {
      setError('預測請求失敗: ' + err.message);
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6 space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          ML 模型管理
        </h2>
        <button
          onClick={fetchModelInfo}
          disabled={loading}
          className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? '載入中...' : '重新整理'}
        </button>
      </div>

      {/* 錯誤/成功訊息 */}
      {error && (
        <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400 text-sm">
          {success}
        </div>
      )}

      {/* 模型狀態卡片 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>📊</span> 模型狀態
        </h3>

        {loading ? (
          <div className="text-center py-8 text-slate-400">載入中...</div>
        ) : modelInfo ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-slate-400 text-xs mb-1">模型狀態</div>
              <div className={`text-lg font-bold ${modelInfo.has_model ? 'text-green-400' : 'text-yellow-400'}`}>
                {modelInfo.has_model ? '✅ 已訓練' : '⚠️ 未訓練'}
              </div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-slate-400 text-xs mb-1">模型版本</div>
              <div className="text-lg font-bold text-white">
                {modelInfo.model_info?.model_version || modelInfo.model_version || 'N/A'}
              </div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-slate-400 text-xs mb-1">特徵數量</div>
              <div className="text-lg font-bold text-blue-400">
                {modelInfo.model_info?.feature_count || (modelInfo.has_model ? '55' : '0')} 個
              </div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-slate-400 text-xs mb-1">訓練樣本</div>
              <div className="text-lg font-bold text-purple-400">
                {modelInfo.model_info?.samples || '0'} 筆
              </div>
            </div>

            {modelInfo.model_info?.metrics && (
              <>
                <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/20">
                  <div className="text-slate-400 text-xs mb-1">CV 準確率</div>
                  <div className="text-lg font-bold text-blue-400">
                    {(modelInfo.model_info.metrics.cv_accuracy * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
                  <div className="text-slate-400 text-xs mb-1">測試準確率</div>
                  <div className="text-lg font-bold text-green-400">
                    {(modelInfo.model_info.metrics.test_accuracy * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/20">
                  <div className="text-slate-400 text-xs mb-1">F1 分數</div>
                  <div className="text-lg font-bold text-purple-400">
                    {(modelInfo.model_info.metrics.test_f1 * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-3">
                  <div className="text-slate-400 text-xs mb-1">訓練時間</div>
                  <div className="text-sm font-medium text-slate-300">
                    {modelInfo.model_info.trained_at?.split('T')[0] || 'N/A'}
                  </div>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">無法取得模型資訊</div>
        )}
      </div>

      {/* 特徵資訊 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>🧬</span> 55 特徵分類
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {FEATURE_CATEGORIES.map((cat) => (
            <div
              key={cat.key}
              className={`p-2 rounded-lg border ${cat.color}`}
            >
              <div className="text-xs font-medium">{cat.name}</div>
              <div className="text-lg font-bold">{cat.count} 個</div>
            </div>
          ))}
        </div>
        <div className="mt-3 text-xs text-slate-500 text-center">
          總計 55 個特徵，涵蓋技術面、籌碼面、基本面、市場環境
        </div>
      </div>

      {/* 訓練區塊 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>🎯</span> 訓練模型
        </h3>

        {/* 訓練模式切換 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
          <button
            onClick={() => setTrainMode('historical')}
            className={`py-2 px-3 rounded-lg font-medium transition-colors text-sm ${
              trainMode === 'historical'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            📊 歷史數據 (推薦)
          </button>
          <button
            onClick={() => setTrainMode('incremental')}
            className={`py-2 px-3 rounded-lg font-medium transition-colors text-sm ${
              trainMode === 'incremental'
                ? 'bg-green-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            📈 增量訓練
          </button>
          <button
            onClick={() => setTrainMode('hybrid')}
            className={`py-2 px-3 rounded-lg font-medium transition-colors text-sm ${
              trainMode === 'hybrid'
                ? 'bg-purple-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            🔄 混合訓練
          </button>
          <button
            onClick={() => setTrainMode('tracker')}
            className={`py-2 px-3 rounded-lg font-medium transition-colors text-sm ${
              trainMode === 'tracker'
                ? 'bg-orange-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
          >
            📋 績效追蹤
          </button>
        </div>

        {/* 歷史數據訓練設定 */}
        {trainMode === 'historical' && (
          <div className="space-y-4 mb-4">
            {/* 快速選項區 */}
            <div>
              <label className="text-slate-400 text-xs mb-2 block">📋 快速選擇訓練股票</label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
                {STOCK_PRESETS.map((preset) => (
                  <button
                    key={preset.key}
                    onClick={() => setSelectedPreset(preset.key)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      selectedPreset === preset.key
                        ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                        : 'bg-slate-700/50 border-slate-600 text-slate-300 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-medium text-sm">{preset.name}</div>
                    <div className="text-xs mt-1 opacity-70">
                      {preset.count ? `${preset.count} 檔` : '自訂'} · {preset.time}
                    </div>
                    <div className="text-xs text-slate-500">{preset.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* 自訂股票輸入 (僅當選擇 custom 時顯示) */}
            {selectedPreset === 'custom' && (
              <div>
                <label className="text-slate-400 text-xs mb-1 block">
                  輸入股票代碼 (逗號分隔)
                </label>
                <textarea
                  value={customStocks}
                  onChange={(e) => setCustomStocks(e.target.value)}
                  placeholder="例: 2330,2317,2454,2881,1301,2882,2884,2886,2891,1303..."
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none placeholder-slate-500"
                />
                <p className="text-xs text-slate-500 mt-1">
                  可輸入任意數量股票代碼，建議 50-200 檔以獲得最佳訓練效果
                </p>
              </div>
            )}

            {/* 其他訓練參數 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">歷史期間</label>
                <select
                  value={histPeriod}
                  onChange={(e) => setHistPeriod(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="6mo">6 個月</option>
                  <option value="1y">1 年 (推薦)</option>
                  <option value="2y">2 年</option>
                  <option value="5y">5 年</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">預測天數</label>
                <select
                  value={predictDays}
                  onChange={(e) => setPredictDays(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value={3}>3 天後</option>
                  <option value={5}>5 天後 (推薦)</option>
                  <option value={10}>10 天後</option>
                  <option value={20}>20 天後</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">最少樣本數</label>
                <input
                  type="number"
                  value={minSamples}
                  onChange={(e) => setMinSamples(Number(e.target.value))}
                  min={10}
                  max={10000}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleTrain}
                  disabled={training}
                  className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                    training
                      ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {training ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      訓練中...
                    </span>
                  ) : '開始訓練'}
                </button>
              </div>
            </div>

            {/* 目前選擇的說明 */}
            <div className="p-3 bg-slate-700/30 rounded-lg text-sm">
              <span className="text-slate-400">目前選擇：</span>
              <span className="text-white font-medium ml-1">
                {STOCK_PRESETS.find(p => p.key === selectedPreset)?.name || '未選擇'}
              </span>
              {selectedPreset !== 'custom' && (
                <span className="text-slate-500 ml-2">
                  ({STOCK_PRESETS.find(p => p.key === selectedPreset)?.count} 檔股票，預估 {STOCK_PRESETS.find(p => p.key === selectedPreset)?.time})
                </span>
              )}
            </div>
          </div>
        )}

        {/* V10.41: 增量訓練設定 */}
        {trainMode === 'incremental' && (
          <div className="space-y-4 mb-4">
            <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20 text-green-300 text-sm">
              <strong>增量訓練：</strong> 在現有模型基礎上繼續訓練，使用經驗回放防止遺忘舊知識。
              {!modelInfo?.has_model && (
                <span className="text-yellow-400 ml-2">⚠️ 需要先訓練基礎模型</span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">新數據來源</label>
                <select
                  value={incrementalDataSource}
                  onChange={(e) => setIncrementalDataSource(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value="performance">績效追蹤數據</option>
                  <option value="historical">歷史數據</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">經驗回放比例</label>
                <select
                  value={replayRatio}
                  onChange={(e) => setReplayRatio(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                >
                  <option value={0.1}>10% (快速學習)</option>
                  <option value={0.3}>30% (推薦)</option>
                  <option value={0.5}>50% (平衡)</option>
                  <option value={0.7}>70% (保守)</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleTrain}
                  disabled={training || !modelInfo?.has_model}
                  className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                    training || !modelInfo?.has_model
                      ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {training ? '訓練中...' : '增量訓練'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* V10.41: 混合訓練設定 */}
        {trainMode === 'hybrid' && (
          <div className="space-y-4 mb-4">
            <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20 text-purple-300 text-sm">
              <strong>混合訓練：</strong> 結合歷史數據和績效追蹤數據進行完整訓練，適合重新建立模型。
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">最少樣本數</label>
                <input
                  type="number"
                  value={minSamples}
                  onChange={(e) => setMinSamples(Number(e.target.value))}
                  min={10}
                  max={10000}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleTrain}
                  disabled={training}
                  className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                    training
                      ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }`}
                >
                  {training ? '訓練中...' : '混合訓練'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 績效追蹤訓練設定 */}
        {trainMode === 'tracker' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div>
              <label className="text-slate-400 text-xs mb-1 block">最少樣本數</label>
              <input
                type="number"
                value={minSamples}
                onChange={(e) => setMinSamples(Number(e.target.value))}
                min={10}
                max={1000}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-400 text-xs mb-1 block">特徵模式</label>
              <select
                value={useFullFeatures ? 'full' : 'basic'}
                onChange={(e) => setUseFullFeatures(e.target.value === 'full')}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="full">完整 55 特徵 (推薦)</option>
                <option value="basic">基礎 2 特徵</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={handleTrain}
                disabled={training}
                className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                  training
                    ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                }`}
              >
                {training ? '訓練中...' : '開始訓練'}
              </button>
            </div>
          </div>
        )}

        {/* 訓練結果 */}
        {trainResult && (
          <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20 mb-4">
            <h4 className="font-medium text-green-400 mb-2">訓練完成</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <span className="text-slate-400">版本:</span>
                <span className="ml-1 text-white font-medium">{trainResult.model_version}</span>
              </div>
              <div>
                <span className="text-slate-400">樣本:</span>
                <span className="ml-1 text-white font-medium">{trainResult.samples} 筆</span>
              </div>
              <div>
                <span className="text-slate-400">特徵:</span>
                <span className="ml-1 text-white font-medium">{trainResult.feature_count} 個</span>
              </div>
              <div>
                <span className="text-slate-400">CV 準確率:</span>
                <span className="ml-1 text-white font-medium">{(trainResult.cv_accuracy * 100).toFixed(2)}%</span>
              </div>
              <div>
                <span className="text-slate-400">測試準確率:</span>
                <span className="ml-1 text-white font-medium">{(trainResult.test_accuracy * 100).toFixed(2)}%</span>
              </div>
              <div>
                <span className="text-slate-400">F1 分數:</span>
                <span className="ml-1 text-white font-medium">{(trainResult.test_f1 * 100).toFixed(2)}%</span>
              </div>
              {trainResult.stocks_used && (
                <div>
                  <span className="text-slate-400">使用股票:</span>
                  <span className="ml-1 text-white font-medium">{trainResult.stocks_used} 檔</span>
                </div>
              )}
              {trainResult.class_distribution && (
                <div>
                  <span className="text-slate-400">類別分佈:</span>
                  <span className="ml-1 text-white font-medium">
                    上漲 {(trainResult.class_distribution.up * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 訓練說明 */}
        <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20 text-sm text-blue-300">
          {trainMode === 'historical' ? (
            <>
              <strong>歷史數據訓練:</strong> 使用 Yahoo Finance 歷史股價自動生成訓練樣本，適合快速建立模型。
            </>
          ) : (
            <>
              <strong>績效追蹤訓練:</strong> 使用系統累積的推薦股票績效數據，需累積足夠數據。
            </>
          )}
        </div>
      </div>

      {/* 預測測試區塊 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>🔮</span> 預測測試
        </h3>

        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={testStockId}
            onChange={(e) => setTestStockId(e.target.value)}
            placeholder="輸入股票代碼 (如 2330)"
            className="flex-1 px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none placeholder-slate-500"
          />
          <button
            onClick={handlePredict}
            disabled={predicting}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              predicting
                ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            {predicting ? '預測中...' : '預測'}
          </button>
        </div>

        {/* 預測結果 */}
        {predictionResult && (
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-white">
                {predictionResult.stock_id} 預測結果
              </h4>
              <span className="text-xs text-slate-500">
                模型: {predictionResult.model_version}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <div className="text-slate-400 text-xs mb-1">預測方向</div>
                <div className={`text-xl font-bold px-3 py-1 rounded-full inline-block ${
                  predictionResult.prediction === 'up'
                    ? 'bg-green-500/20 text-green-400'
                    : predictionResult.prediction === 'down'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-slate-600 text-slate-300'
                }`}>
                  {predictionResult.prediction === 'up' ? '📈 上漲' :
                   predictionResult.prediction === 'down' ? '📉 下跌' : '➡️ 持平'}
                </div>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <div className="text-slate-400 text-xs mb-1">上漲機率</div>
                <div className="text-2xl font-bold text-blue-400">
                  {(predictionResult.probability * 100).toFixed(1)}%
                </div>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <div className="text-slate-400 text-xs mb-1">信心等級</div>
                <div className={`text-xl font-bold ${
                  predictionResult.confidence === 'high' ? 'text-green-400' :
                  predictionResult.confidence === 'medium' ? 'text-yellow-400' : 'text-slate-400'
                }`}>
                  {predictionResult.confidence === 'high' ? '高' :
                   predictionResult.confidence === 'medium' ? '中' : '低'}
                </div>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <div className="text-slate-400 text-xs mb-1">預期報酬</div>
                <div className={`text-xl font-bold ${
                  predictionResult.expected_return > 0 ? 'text-green-400' :
                  predictionResult.expected_return < 0 ? 'text-red-400' : 'text-slate-400'
                }`}>
                  {predictionResult.expected_return > 0 ? '+' : ''}
                  {predictionResult.expected_return?.toFixed(2) || '0'}%
                </div>
              </div>
            </div>

            <div className="mt-3 text-xs text-slate-500 text-center">
              使用 {predictionResult.features_used} 個特徵 |
              預測時間: {predictionResult.timestamp?.split('T')[0]}
            </div>
          </div>
        )}
      </div>

      {/* V10.41: 版本管理區塊 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>📦</span> 模型版本管理
          <button
            onClick={fetchVersions}
            className="ml-auto px-2 py-1 text-xs bg-slate-600 hover:bg-slate-500 text-slate-300 rounded transition-colors"
          >
            重新整理
          </button>
        </h3>

        {loadingVersions ? (
          <div className="text-center py-4 text-slate-400">載入版本列表中...</div>
        ) : versions.length === 0 ? (
          <div className="text-center py-4 text-slate-400">尚無訓練版本，請先訓練模型</div>
        ) : (
          <div className="space-y-2">
            {versions.map((version) => (
              <div
                key={version.version}
                className={`p-3 rounded-lg border ${
                  version.is_current
                    ? 'bg-blue-500/10 border-blue-500/30'
                    : 'bg-slate-700/50 border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-mono ${version.is_current ? 'text-blue-400' : 'text-slate-300'}`}>
                      {version.version}
                    </span>
                    {version.is_current && (
                      <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded-full">
                        當前使用
                      </span>
                    )}
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      version.training_method === 'full' ? 'bg-blue-500/20 text-blue-400' :
                      version.training_method === 'incremental' ? 'bg-green-500/20 text-green-400' :
                      version.training_method === 'hybrid' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-slate-600 text-slate-400'
                    }`}>
                      {version.training_method === 'full' ? '完整' :
                       version.training_method === 'incremental' ? '增量' :
                       version.training_method === 'hybrid' ? '混合' : version.training_method}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400">
                      準確率: <span className="text-green-400">{(version.test_accuracy * 100).toFixed(1)}%</span>
                    </span>
                    <span className="text-xs text-slate-400">
                      F1: <span className="text-purple-400">{(version.test_f1 * 100).toFixed(1)}%</span>
                    </span>
                    <span className="text-xs text-slate-500">
                      {version.samples_count} 樣本
                    </span>
                    {!version.is_current && (
                      <button
                        onClick={() => handleActivateVersion(version.version)}
                        className="px-2 py-1 text-xs bg-slate-600 hover:bg-blue-600 text-slate-300 rounded transition-colors"
                      >
                        切換使用
                      </button>
                    )}
                  </div>
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  建立時間: {version.created_at?.split('T')[0] || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* V10.41: 訓練數據統計 */}
      {trainingStats && trainingStats.total_samples > 0 && (
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <span>📊</span> 訓練數據統計
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-slate-400 text-xs mb-1">總樣本數</div>
              <div className="text-xl font-bold text-white">{trainingStats.total_samples.toLocaleString()}</div>
            </div>
            <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/20">
              <div className="text-slate-400 text-xs mb-1">歷史數據</div>
              <div className="text-xl font-bold text-blue-400">
                {trainingStats.by_source?.historical?.toLocaleString() || 0}
              </div>
            </div>
            <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/20">
              <div className="text-slate-400 text-xs mb-1">績效追蹤</div>
              <div className="text-xl font-bold text-green-400">
                {trainingStats.by_source?.performance?.toLocaleString() || 0}
              </div>
            </div>
            <div className="bg-purple-500/10 rounded-lg p-3 border border-purple-500/20">
              <div className="text-slate-400 text-xs mb-1">高品質樣本</div>
              <div className="text-xl font-bold text-purple-400">
                {trainingStats.by_quality?.high?.toLocaleString() || 0}
              </div>
            </div>
          </div>

          <div className="mt-3 text-xs text-slate-500 text-center">
            上漲樣本: {trainingStats.by_label?.positive?.toLocaleString() || 0} |
            下跌樣本: {trainingStats.by_label?.negative?.toLocaleString() || 0}
          </div>
        </div>
      )}

      {/* 使用說明 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>📖</span> 使用說明
        </h3>
        <div className="space-y-2 text-sm">
          <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20 text-blue-300">
            <strong>1. 歷史數據訓練 (推薦)</strong>
            <p className="text-blue-200/70 mt-1">使用 Yahoo Finance 歷史數據，立即可用，無需等待。</p>
          </div>
          <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20 text-green-300">
            <strong>2. 增量訓練 (V10.41)</strong>
            <p className="text-green-200/70 mt-1">在現有模型基礎上繼續學習，使用經驗回放防止遺忘。</p>
          </div>
          <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20 text-purple-300">
            <strong>3. 混合訓練 (V10.41)</strong>
            <p className="text-purple-200/70 mt-1">結合歷史數據和績效追蹤數據，建立更全面的模型。</p>
          </div>
          <div className="p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20 text-yellow-300">
            <strong>4. 版本管理 (V10.41)</strong>
            <p className="text-yellow-200/70 mt-1">每次訓練保留版本記錄，支持隨時切換和比較。</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLPanel;
