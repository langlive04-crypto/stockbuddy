import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8000';

// ============================================================
// 🤖 StockBuddy V10 - AI 智能選股系統
// ============================================================

export default function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);

  // 載入 AI 選股結果
  const loadAIPicks = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API_BASE}/api/stocks/ai/picks?top_n=15`);
      const result = await res.json();
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      setData(result);
      
      // 自動選中第一名
      if (result.top_picks && result.top_picks.length > 0) {
        setSelectedStock(result.top_picks[0]);
      }
    } catch (e) {
      console.error('載入失敗:', e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAIPicks();
  }, [loadAIPicks]);

  // 選擇股票
  const handleSelectStock = (stock) => {
    setSelectedStock(stock);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-sm border-b border-gray-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-3xl">🤖</div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  StockBuddy AI
                </h1>
                <p className="text-xs text-gray-400">智能選股系統 V10</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {data && (
                <div className="text-right text-sm">
                  <div className="text-gray-400">全市場掃描</div>
                  <div className="text-cyan-400 font-bold">{data.scanned_count || 0} 檔</div>
                </div>
              )}
              
              <button
                onClick={loadAIPicks}
                disabled={loading}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg font-medium transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">⚙️</span>
                    AI 分析中...
                  </>
                ) : (
                  <>🔄 重新分析</>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading && !data ? (
          <LoadingScreen />
        ) : error ? (
          <ErrorScreen error={error} onRetry={loadAIPicks} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左側：AI Top 排行榜 */}
            <div className="lg:col-span-1">
              <AIRankingPanel 
                picks={data?.top_picks || []} 
                selectedId={selectedStock?.stock_id}
                onSelect={handleSelectStock}
                loading={loading}
              />
            </div>
            
            {/* 右側：詳細分析 */}
            <div className="lg:col-span-2">
              {selectedStock ? (
                <StockDetailPanel stock={selectedStock} />
              ) : (
                <EmptyPanel />
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700/50 mt-8 py-4 text-center text-sm text-gray-500">
        <p>⚠️ 本系統僅供參考，不構成投資建議。投資有風險，請自行判斷。</p>
        <p className="mt-1">
          更新時間: {data?.updated_at ? new Date(data.updated_at).toLocaleString('zh-TW') : '-'}
        </p>
      </footer>
    </div>
  );
}

// ============================================================
// Loading / Error 畫面
// ============================================================

function LoadingScreen() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="text-6xl animate-bounce mb-4">🤖</div>
      <h2 className="text-2xl font-bold text-cyan-400 mb-2">AI 正在分析全市場...</h2>
      <p className="text-gray-400">整合技術面、籌碼面、基本面進行多維度評估</p>
      <div className="mt-6 flex gap-2">
        {['掃描股票', '技術分析', '籌碼分析', '基本面', 'AI 評分'].map((step, i) => (
          <div key={step} className="px-3 py-1 bg-gray-800 rounded-full text-sm animate-pulse" style={{ animationDelay: `${i * 0.2}s` }}>
            {step}
          </div>
        ))}
      </div>
      <p className="mt-4 text-gray-500 text-sm">首次載入約需 30-60 秒</p>
    </div>
  );
}

function ErrorScreen({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="text-6xl mb-4">😵</div>
      <h2 className="text-xl font-bold text-red-400 mb-2">分析失敗</h2>
      <p className="text-gray-400 mb-4">{error}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg"
      >
        重試
      </button>
    </div>
  );
}

function EmptyPanel() {
  return (
    <div className="bg-gray-800/50 rounded-2xl p-8 text-center">
      <div className="text-4xl mb-4">👈</div>
      <p className="text-gray-400">請從左側選擇一檔股票查看詳細分析</p>
    </div>
  );
}

// ============================================================
// AI 排行榜面板
// ============================================================

function AIRankingPanel({ picks, selectedId, onSelect, loading }) {
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 overflow-hidden">
      {/* 標題 */}
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🏆</span>
          <div>
            <h2 className="font-bold">AI 精選 Top {picks.length}</h2>
            <p className="text-xs text-cyan-200">多維度分析 · 即時更新</p>
          </div>
        </div>
      </div>
      
      {/* 列表 */}
      <div className="divide-y divide-gray-700/50 max-h-[calc(100vh-300px)] overflow-y-auto">
        {picks.map((stock, index) => (
          <StockRankItem
            key={stock.stock_id}
            stock={stock}
            rank={index + 1}
            isSelected={stock.stock_id === selectedId}
            onClick={() => onSelect(stock)}
          />
        ))}
        
        {picks.length === 0 && !loading && (
          <div className="p-8 text-center text-gray-500">
            暫無資料
          </div>
        )}
      </div>
    </div>
  );
}

function StockRankItem({ stock, rank, isSelected, onClick }) {
  const scoreColor = stock.ai_score >= 80 ? 'text-green-400' :
                     stock.ai_score >= 70 ? 'text-cyan-400' :
                     stock.ai_score >= 60 ? 'text-yellow-400' : 'text-gray-400';
  
  const changeColor = stock.change_percent >= 0 ? 'text-red-400' : 'text-green-400';
  
  const rankBadge = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`;
  
  return (
    <div
      onClick={onClick}
      className={`p-4 cursor-pointer transition-all hover:bg-gray-700/50 ${
        isSelected ? 'bg-cyan-900/30 border-l-4 border-cyan-400' : ''
      }`}
    >
      <div className="flex items-center gap-3">
        {/* 排名 */}
        <div className="text-xl w-8 text-center">
          {typeof rankBadge === 'string' && rankBadge.startsWith('#') ? (
            <span className="text-sm text-gray-500">{rankBadge}</span>
          ) : rankBadge}
        </div>
        
        {/* 股票資訊 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-bold">{stock.name || stock.stock_id}</span>
            <span className="text-xs text-gray-500">{stock.stock_id}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-400">${stock.price?.toFixed(0)}</span>
            <span className={changeColor}>
              {stock.change_percent >= 0 ? '+' : ''}{stock.change_percent?.toFixed(2)}%
            </span>
          </div>
        </div>
        
        {/* AI 分數 */}
        <div className="text-right">
          <div className={`text-2xl font-bold ${scoreColor}`}>
            {stock.ai_score}
          </div>
          <div className="text-xs text-gray-500">{stock.signal}</div>
        </div>
      </div>
      
      {/* 快速標籤 */}
      {stock.reasons && stock.reasons.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {stock.reasons.slice(0, 2).map((reason, i) => (
            <span key={i} className="text-xs px-2 py-0.5 bg-gray-700/50 rounded-full text-gray-300 truncate max-w-[150px]">
              {reason.replace(/^[📈💰📊🔥⚠️✅]\s*/, '')}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// 股票詳細分析面板
// ============================================================

function StockDetailPanel({ stock }) {
  if (!stock) return null;
  
  const scoreColor = stock.ai_score >= 80 ? 'from-green-500 to-emerald-600' :
                     stock.ai_score >= 70 ? 'from-cyan-500 to-blue-600' :
                     stock.ai_score >= 60 ? 'from-yellow-500 to-orange-600' : 'from-gray-500 to-gray-600';

  return (
    <div className="space-y-4">
      {/* 頂部：股票基本資訊 + AI 分數 */}
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-3xl font-bold">{stock.name || stock.stock_id}</h2>
              <span className="text-gray-500">{stock.stock_id}</span>
              {stock.industry && (
                <span className="px-2 py-0.5 bg-blue-900/50 text-blue-300 rounded text-sm">
                  {stock.industry}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 text-lg">
              <span className="text-2xl font-bold">${stock.price?.toFixed(2)}</span>
              <span className={stock.change_percent >= 0 ? 'text-red-400' : 'text-green-400'}>
                {stock.change_percent >= 0 ? '▲' : '▼'} {Math.abs(stock.change_percent)?.toFixed(2)}%
              </span>
            </div>
          </div>
          
          {/* AI 分數環 */}
          <div className="text-center">
            <div className={`w-24 h-24 rounded-full bg-gradient-to-br ${scoreColor} flex items-center justify-center shadow-lg`}>
              <div className="bg-gray-900 w-20 h-20 rounded-full flex flex-col items-center justify-center">
                <span className="text-3xl font-bold">{stock.ai_score}</span>
                <span className="text-xs text-gray-400">AI 分數</span>
              </div>
            </div>
            <div className="mt-2 text-lg font-bold text-cyan-400">{stock.signal}</div>
          </div>
        </div>
        
        {/* 標籤 */}
        {stock.tags && stock.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {stock.tags.map((tag, i) => (
              <span key={i} className="px-2 py-1 bg-purple-900/50 text-purple-300 rounded text-sm">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 三維度分數對比 */}
      <div className="grid grid-cols-3 gap-4">
        <ScoreCard 
          title="技術面" 
          score={stock.technical_score} 
          icon="📈"
          signals={stock.technical_detail?.signals}
        />
        <ScoreCard 
          title="籌碼面" 
          score={stock.chip_score} 
          icon="💰"
          signals={stock.chip_detail?.signals}
        />
        <ScoreCard 
          title="基本面" 
          score={stock.fundamental_score} 
          icon="📊"
          signals={stock.fundamental_detail?.signals}
        />
      </div>

      {/* 詳細分析 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 推薦理由 */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-4">
          <h3 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
            <span>💡</span> AI 推薦理由
          </h3>
          <ul className="space-y-2">
            {stock.reasons?.map((reason, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-green-400 mt-0.5">✓</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
        
        {/* 風險提示 */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-4">
          <h3 className="font-bold text-orange-400 mb-3 flex items-center gap-2">
            <span>⚠️</span> 風險提示
          </h3>
          <ul className="space-y-2">
            {stock.risks?.map((risk, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="mt-0.5">{risk.startsWith('✅') ? '' : '•'}</span>
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 操作建議 */}
      <div className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 backdrop-blur-sm rounded-2xl border border-cyan-700/50 p-4">
        <h3 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
          <span>🎯</span> AI 操作建議
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-gray-400 text-sm">建議操作</div>
            <div className="text-xl font-bold text-cyan-400">{stock.signal}</div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">目標價</div>
            <div className="text-xl font-bold text-green-400">${stock.target?.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">止損價</div>
            <div className="text-xl font-bold text-red-400">${stock.stop_loss?.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-gray-400 text-sm">潛在報酬</div>
            <div className="text-xl font-bold text-yellow-400">
              {stock.price ? `+${((stock.target - stock.price) / stock.price * 100).toFixed(1)}%` : '-'}
            </div>
          </div>
        </div>
      </div>

      {/* 技術指標詳情 */}
      {stock.technical_detail && (
        <TechnicalDetailPanel detail={stock.technical_detail} />
      )}
      
      {/* 籌碼詳情 */}
      {stock.chip_detail && (
        <ChipDetailPanel detail={stock.chip_detail} />
      )}
      
      {/* 基本面詳情 */}
      {stock.fundamental_detail && (
        <FundamentalDetailPanel detail={stock.fundamental_detail} />
      )}
    </div>
  );
}

function ScoreCard({ title, score, icon, signals }) {
  const getScoreColor = (s) => {
    if (s >= 70) return 'text-green-400';
    if (s >= 50) return 'text-cyan-400';
    if (s >= 30) return 'text-yellow-400';
    return 'text-red-400';
  };
  
  const getBarColor = (s) => {
    if (s >= 70) return 'bg-green-500';
    if (s >= 50) return 'bg-cyan-500';
    if (s >= 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className={`text-2xl font-bold ${getScoreColor(score)}`}>{score}</span>
      </div>
      <div className="text-sm font-medium mb-2">{title}</div>
      
      {/* 進度條 */}
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${getBarColor(score)} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
      
      {/* 信號 */}
      {signals && signals.length > 0 && (
        <div className="mt-2 text-xs text-gray-400">
          {signals.slice(0, 2).join(' · ')}
        </div>
      )}
    </div>
  );
}

function TechnicalDetailPanel({ detail }) {
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-4">
      <h3 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
        <span>📈</span> 技術指標詳情
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricItem label="MA5" value={detail.ma5} />
        <MetricItem label="MA20" value={detail.ma20} />
        <MetricItem label="MA60" value={detail.ma60} />
        <MetricItem label="RSI" value={detail.rsi?.toFixed(1)} suffix="" />
        <MetricItem label="MACD" value={detail.macd?.toFixed(3)} />
        <MetricItem label="Signal" value={detail.macd_signal?.toFixed(3)} />
        <MetricItem label="成交量比" value={detail.volume_ratio?.toFixed(2)} suffix="x" />
      </div>
    </div>
  );
}

function ChipDetailPanel({ detail }) {
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-4">
      <h3 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
        <span>💰</span> 籌碼面詳情
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricItem 
          label="外資" 
          value={detail.foreign_net} 
          suffix="張"
          isPositive={detail.foreign_net > 0}
        />
        <MetricItem 
          label="投信" 
          value={detail.trust_net} 
          suffix="張"
          isPositive={detail.trust_net > 0}
        />
        <MetricItem 
          label="自營商" 
          value={detail.dealer_net} 
          suffix="張"
          isPositive={detail.dealer_net > 0}
        />
        <MetricItem 
          label="法人合計" 
          value={detail.total_net} 
          suffix="張"
          isPositive={detail.total_net > 0}
        />
        <MetricItem label="融資餘額" value={detail.margin_balance?.toLocaleString()} suffix="張" />
        <MetricItem label="融券餘額" value={detail.short_balance?.toLocaleString()} suffix="張" />
      </div>
    </div>
  );
}

function FundamentalDetailPanel({ detail }) {
  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-4">
      <h3 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
        <span>📊</span> 基本面詳情
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricItem label="本益比" value={detail.per?.toFixed(1)} suffix="倍" />
        <MetricItem label="淨值比" value={detail.pbr?.toFixed(2)} suffix="倍" />
        <MetricItem label="殖利率" value={detail.dividend_yield?.toFixed(2)} suffix="%" />
        <MetricItem 
          label="營收年增" 
          value={detail.revenue_yoy?.toFixed(1)} 
          suffix="%"
          isPositive={detail.revenue_yoy > 0}
        />
      </div>
    </div>
  );
}

function MetricItem({ label, value, suffix = '', isPositive = null }) {
  let valueColor = 'text-white';
  if (isPositive === true) valueColor = 'text-red-400';
  if (isPositive === false) valueColor = 'text-green-400';
  
  return (
    <div className="text-center p-2 bg-gray-700/30 rounded-lg">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-lg font-bold ${valueColor}`}>
        {value !== undefined && value !== null ? (
          <>
            {isPositive === true && value > 0 && '+'}
            {value}{suffix}
          </>
        ) : '-'}
      </div>
    </div>
  );
}
