/**
 * 綜合投資策略精選面板 V10.17
 * V10.35.1 更新：配置建議添加中文名稱
 *
 * 功能：
 * - 顯示策略精選股票列表
 * - 投資組合配置建議（含中文名稱）
 * - 市場概覽
 * - 預算規劃器（詳細配置方案）
 * - 點選個股顯示詳細分析
 *
 * V10.17 更新：
 * - 優化版面呈現
 * - 點選個股顯示詳細分析面板
 * - 預算規劃新增詳細配置明細（%數、金額、股數）
 */

import React, { useState, useEffect } from 'react';
import { getStockName } from '../services/stockNames';
import { API_BASE } from '../config';
import { formatDateTime } from '../utils/dateUtils';  // V10.35.4

// 評級配置
const RATING_CONFIG = {
  strong_buy: { color: 'bg-red-500', label: '強買', textColor: 'text-red-400', bgLight: 'bg-red-500/10' },
  buy: { color: 'bg-orange-500', label: '買入', textColor: 'text-orange-400', bgLight: 'bg-orange-500/10' },
  hold: { color: 'bg-yellow-500', label: '持有', textColor: 'text-yellow-400', bgLight: 'bg-yellow-500/10' },
  reduce: { color: 'bg-blue-500', label: '減碼', textColor: 'text-blue-400', bgLight: 'bg-blue-500/10' },
  sell: { color: 'bg-emerald-500', label: '賣出', textColor: 'text-emerald-400', bgLight: 'bg-emerald-500/10' },
};

// V10.17: 評分進度條組件
const ScoreProgressBar = ({ label, score, color = 'blue' }) => {
  const percentage = Math.min((score / 100) * 100, 100);
  const colorMap = {
    red: 'bg-red-500',
    green: 'bg-emerald-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    amber: 'bg-amber-500',
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-slate-400 text-xs w-12">{label}</span>
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorMap[color]} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-white text-xs w-8 text-right font-medium">{score}</span>
    </div>
  );
};

// V10.17: 詳細分析面板（點選個股時顯示）
const StockDetailPanel = ({ pick, onClose }) => {
  if (!pick) return null;

  const ratingConfig = RATING_CONFIG[pick.rating] || RATING_CONFIG.hold;

  return (
    <div className="bg-slate-800/90 backdrop-blur-sm rounded-xl p-5 border border-slate-600 shadow-xl">
      {/* 標題區 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold text-white">{pick.stock_name}</span>
              <span className="text-slate-400">{pick.stock_id}</span>
            </div>
            <div className="text-2xl font-bold text-white mt-1">${pick.current_price?.toLocaleString()}</div>
          </div>
        </div>
        <div className="text-right">
          <div className={`${ratingConfig.color} text-white px-3 py-1 rounded-lg text-sm font-bold mb-1`}>
            {ratingConfig.label}
          </div>
          <div className="text-3xl font-bold text-amber-400">{pick.rating_score}</div>
        </div>
      </div>

      {/* 四維評分 */}
      <div className="bg-slate-900/50 rounded-lg p-3 mb-4">
        <h4 className="text-white font-medium mb-2 text-sm">多維度分析</h4>
        <div className="space-y-2">
          <ScoreProgressBar label="技術面" score={pick.technical_score || 50} color="red" />
          <ScoreProgressBar label="基本面" score={pick.fundamental_score || 50} color="green" />
          <ScoreProgressBar label="籌碼面" score={pick.chip_score || 50} color="blue" />
          <ScoreProgressBar label="產業熱度" score={pick.industry_score || 50} color="amber" />
        </div>
      </div>

      {/* 評級理由 */}
      {pick.rating_reasons && pick.rating_reasons.length > 0 && (
        <div className="mb-4">
          <h4 className="text-white font-medium mb-2 text-sm">分析重點</h4>
          <div className="flex flex-wrap gap-1">
            {pick.rating_reasons.map((reason, i) => (
              <span
                key={i}
                className={`px-2 py-1 rounded text-xs ${ratingConfig.textColor} ${ratingConfig.bgLight} border border-current/20`}
              >
                {reason}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 交易策略 */}
      {pick.trading_strategy && (
        <div className="bg-slate-900/50 rounded-lg p-3 mb-4">
          <h4 className="text-white font-medium mb-3 text-sm">交易策略建議</h4>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-2">
              <div className="text-slate-400 text-xs mb-1">建議進場價</div>
              <div className="text-blue-400 font-bold">${pick.trading_strategy.entry_price}</div>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2">
              <div className="text-slate-400 text-xs mb-1">止損價位</div>
              <div className="text-emerald-400 font-bold">${pick.trading_strategy.stop_loss_price}</div>
              <div className="text-emerald-400/60 text-[10px]">-{pick.trading_strategy.stop_loss_percent || 5}%</div>
            </div>
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2">
              <div className="text-slate-400 text-xs mb-1">目標價位</div>
              <div className="text-red-400 font-bold">${pick.trading_strategy.target_price_1}</div>
              <div className="text-red-400/60 text-[10px]">+{pick.trading_strategy.target_profit_1 || 10}%</div>
            </div>
          </div>
          {pick.trading_strategy.holding_period && (
            <div className="mt-3 text-center text-sm text-slate-400">
              建議持有期間：<span className="text-white">{pick.trading_strategy.holding_period}</span>
            </div>
          )}
        </div>
      )}

      {/* 白話文建議 */}
      <div className={`${ratingConfig.bgLight} border border-current/20 rounded-lg p-3 mb-4`}>
        <h4 className={`${ratingConfig.textColor} font-medium mb-1 text-sm`}>投資建議（白話文）</h4>
        <p className="text-slate-300 text-sm">
          {pick.rating === 'strong_buy' && '這檔股票各方面表現都很優秀，是目前市場上的優質標的，可以積極考慮買進。'}
          {pick.rating === 'buy' && '整體表現良好，技術面和基本面都有不錯的支撐，可以找適當時機進場。'}
          {pick.rating === 'hold' && '目前表現中等，如果已經持有可以繼續觀望，暫時不需要急著買賣。'}
          {pick.rating === 'reduce' && '股票近期走勢較弱，如果有持股可以考慮減少部位，控制風險。'}
          {pick.rating === 'sell' && '目前不建議持有，技術面轉弱，建議觀望或尋找其他標的。'}
        </p>
      </div>

      {/* 關閉按鈕 */}
      <button
        onClick={onClose}
        className="w-full py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
      >
        關閉詳細分析
      </button>
    </div>
  );
};

// 策略精選卡片
const StrategyPickCard = ({ pick, rank, onSelect }) => {
  const ratingConfig = RATING_CONFIG[pick.rating] || RATING_CONFIG.hold;

  return (
    <div
      className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-blue-500/50 cursor-pointer transition-all"
      onClick={() => onSelect(pick)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* 排名 */}
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
            rank <= 3 ? 'bg-gradient-to-br from-amber-400 to-amber-600' : 'bg-slate-600'
          }`}>
            {rank}
          </div>

          {/* 股票資訊 */}
          <div>
            <div className="text-white font-semibold">{pick.stock_name}</div>
            <div className="text-slate-500 text-xs">{pick.stock_id}</div>
          </div>
        </div>

        {/* 評級 */}
        <div className={`${ratingConfig.color} text-white px-2 py-1 rounded text-xs font-bold`}>
          {ratingConfig.label}
        </div>
      </div>

      {/* 價格和評分 */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-2xl font-bold text-white">${pick.current_price}</div>
        </div>
        {/* V10.35.5: 價值評分 (方案 E) */}
        <div className="text-right group relative">
          <div className="text-3xl font-bold text-blue-400">{pick.rating_score}</div>
          <div className="text-xs text-blue-400/70">價值評分</div>
          <div className="text-[10px] text-slate-500">適合中長線</div>
          {/* 評分說明提示 */}
          <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
            <div className="font-bold text-blue-400">價值評分說明</div>
            <div className="text-slate-400 mt-1">技術面 30% | 籌碼面 30%</div>
            <div className="text-slate-400">基本面 25% | 產業 15%</div>
          </div>
        </div>
      </div>

      {/* 多維度分數 */}
      <div className="grid grid-cols-4 gap-2 text-center text-xs">
        <div>
          <div className="text-slate-500">技術</div>
          <div className="text-white font-medium">{pick.technical_score}</div>
        </div>
        <div>
          <div className="text-slate-500">基本</div>
          <div className="text-white font-medium">{pick.fundamental_score}</div>
        </div>
        <div>
          <div className="text-slate-500">籌碼</div>
          <div className="text-white font-medium">{pick.chip_score}</div>
        </div>
        <div>
          <div className="text-slate-500">產業</div>
          <div className="text-white font-medium">{pick.industry_score}</div>
        </div>
      </div>

      {/* 關鍵訊號 */}
      {pick.rating_reasons && pick.rating_reasons.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {pick.rating_reasons.slice(0, 3).map((reason, i) => (
            <span
              key={i}
              className={`px-2 py-0.5 rounded text-xs ${ratingConfig.textColor} bg-slate-700/50`}
            >
              {reason}
            </span>
          ))}
        </div>
      )}

      {/* 交易建議快照 */}
      {pick.trading_strategy && (
        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-700 text-xs">
          <div>
            <div className="text-slate-500">進場價</div>
            <div className="text-red-400 font-medium">${pick.trading_strategy.entry_price}</div>
          </div>
          <div>
            <div className="text-slate-500">止損價</div>
            <div className="text-emerald-400 font-medium">${pick.trading_strategy.stop_loss_price}</div>
          </div>
          <div>
            <div className="text-slate-500">目標價</div>
            <div className="text-amber-400 font-medium">${pick.trading_strategy.target_price_1}</div>
          </div>
        </div>
      )}
    </div>
  );
};

// 市場概覽卡片
const MarketOverviewCard = ({ overview }) => {
  if (!overview) return null;

  const isPositive = (overview.taiex_change_pct || 0) >= 0;

  return (
    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-4 border border-slate-700">
      <h4 className="text-slate-400 text-sm mb-2">加權指數</h4>
      <div className="flex items-end gap-3">
        <div className="text-2xl font-bold text-white">
          {overview.taiex_value?.toLocaleString()}
        </div>
        <div className={`text-lg font-medium ${isPositive ? 'text-red-400' : 'text-emerald-400'}`}>
          {isPositive ? '+' : ''}{overview.taiex_change} ({isPositive ? '+' : ''}{overview.taiex_change_pct}%)
        </div>
      </div>
      <div className={`text-sm mt-2 ${isPositive ? 'text-red-400' : 'text-emerald-400'}`}>
        市場情緒: {overview.market_sentiment === 'bullish' ? '偏多 📈' : '偏空 📉'}
      </div>
    </div>
  );
};

// 投資組合配置卡片
const PortfolioAllocationCard = ({ allocation, onViewDetail }) => {
  if (!allocation || !allocation.allocations) return null;

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span>📊</span> 投資組合配置建議
      </h4>

      <div className="space-y-2">
        {allocation.allocations.slice(0, 5).map((item, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-28 text-white font-medium text-sm">
              <span className="text-slate-400">{item.stock_id}</span>
              <span className="ml-1">{getStockName(item.stock_id)}</span>
            </div>
            <div className="flex-1">
              <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                  style={{ width: `${item.weight_percent}%` }}
                />
              </div>
            </div>
            <div className="w-12 text-right text-slate-400 text-sm">
              {item.weight_percent}%
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-700 text-sm text-slate-400">
        {allocation.strategy}
      </div>
    </div>
  );
};

// V10.17: 預算規劃器（增強版 - 顯示詳細配置）
const BudgetPlanner = ({ onCalculate, strategyPicks }) => {
  const [budget, setBudget] = useState(100000);
  const [riskLevel, setRiskLevel] = useState('medium');
  const [showResult, setShowResult] = useState(false);
  const [allocation, setAllocation] = useState([]);

  // 計算配置方案
  const calculateAllocation = () => {
    if (!strategyPicks || strategyPicks.length === 0) {
      alert('請等待策略精選資料載入');
      return;
    }

    // 根據風險等級決定股票數量
    const stockCount = riskLevel === 'low' ? 5 : riskLevel === 'medium' ? 8 : 12;
    const selectedStocks = strategyPicks.slice(0, stockCount);

    // 計算權重（根據評分加權）
    const totalScore = selectedStocks.reduce((sum, s) => sum + (s.rating_score || 70), 0);

    const result = selectedStocks.map((stock, index) => {
      const weight = ((stock.rating_score || 70) / totalScore) * 100;
      const allocatedAmount = Math.round(budget * (weight / 100));
      const pricePerShare = stock.current_price || 100;
      const suggestedShares = Math.floor(allocatedAmount / (pricePerShare * 1000)); // 以張計算
      const actualAmount = suggestedShares * pricePerShare * 1000;
      const remainingCash = allocatedAmount - actualAmount;

      return {
        rank: index + 1,
        stock_id: stock.stock_id,
        stock_name: stock.stock_name,
        rating: stock.rating,
        rating_score: stock.rating_score,
        weight_percent: weight.toFixed(1),
        allocated_amount: allocatedAmount,
        price_per_share: pricePerShare,
        suggested_lots: suggestedShares, // 張數
        suggested_shares: suggestedShares * 1000, // 股數
        actual_amount: actualAmount,
        remaining: remainingCash,
      };
    });

    setAllocation(result);
    setShowResult(true);

    // 觸發外部回調
    if (onCalculate) {
      onCalculate(budget, riskLevel, result);
    }
  };

  // 計算總計
  const getTotals = () => {
    const totalAllocated = allocation.reduce((sum, a) => sum + a.actual_amount, 0);
    const totalRemaining = budget - totalAllocated;
    return { totalAllocated, totalRemaining };
  };

  return (
    <div className="bg-gradient-to-br from-emerald-600/20 to-teal-600/20 rounded-xl p-4 border border-emerald-500/30">
      <h4 className="text-white font-semibold mb-4 flex items-center gap-2">
        <span>💰</span> 預算規劃器
      </h4>

      <div className="space-y-4">
        {/* 預算輸入 */}
        <div>
          <label className="text-slate-400 text-sm block mb-2">投資預算 (NT$)</label>
          <input
            type="number"
            value={budget}
            onChange={(e) => {
              setBudget(Number(e.target.value));
              setShowResult(false);
            }}
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-lg font-medium"
            min="10000"
            step="10000"
          />
          <div className="text-xs text-slate-500 mt-1">
            建議金額：
            <button onClick={() => setBudget(50000)} className="text-emerald-400 mx-1 hover:underline">5萬</button>
            <button onClick={() => setBudget(100000)} className="text-emerald-400 mx-1 hover:underline">10萬</button>
            <button onClick={() => setBudget(300000)} className="text-emerald-400 mx-1 hover:underline">30萬</button>
            <button onClick={() => setBudget(500000)} className="text-emerald-400 mx-1 hover:underline">50萬</button>
          </div>
        </div>

        {/* 風險等級 */}
        <div>
          <label className="text-slate-400 text-sm block mb-2">風險承受度</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: 'low', label: '保守', desc: '5檔分散', icon: '🛡️' },
              { value: 'medium', label: '穩健', desc: '8檔平衡', icon: '⚖️' },
              { value: 'high', label: '積極', desc: '12檔進取', icon: '🚀' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => {
                  setRiskLevel(opt.value);
                  setShowResult(false);
                }}
                className={`p-2 rounded-lg text-center transition-all ${
                  riskLevel === opt.value
                    ? 'bg-emerald-500 text-white shadow-lg'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                <div className="text-lg">{opt.icon}</div>
                <div className="font-medium text-sm">{opt.label}</div>
                <div className="text-xs opacity-75">{opt.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 計算按鈕 */}
        <button
          onClick={calculateAllocation}
          className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 text-white rounded-lg font-bold transition-colors flex items-center justify-center gap-2"
        >
          <span>📊</span> 計算配置方案
        </button>

        {/* V10.17: 詳細配置結果表格 */}
        {showResult && allocation.length > 0 && (
          <div className="mt-4 bg-slate-900/50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-3">
              <h5 className="text-white font-medium">詳細配置明細</h5>
              <span className="text-xs text-slate-400">
                預算 ${budget.toLocaleString()} | {riskLevel === 'low' ? '保守' : riskLevel === 'medium' ? '穩健' : '積極'}
              </span>
            </div>

            {/* 配置表格 */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700">
                    <th className="text-left py-2 px-1">#</th>
                    <th className="text-left py-2 px-1">股票</th>
                    <th className="text-right py-2 px-1">配置比例</th>
                    <th className="text-right py-2 px-1">配置金額</th>
                    <th className="text-right py-2 px-1">參考股價</th>
                    <th className="text-right py-2 px-1">建議張數</th>
                    <th className="text-right py-2 px-1">實際金額</th>
                  </tr>
                </thead>
                <tbody>
                  {allocation.map((item, i) => {
                    const ratingConfig = RATING_CONFIG[item.rating] || RATING_CONFIG.hold;
                    return (
                      <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-2 px-1">
                          <span className={`w-5 h-5 rounded-full inline-flex items-center justify-center text-white text-[10px] ${
                            i < 3 ? 'bg-amber-500' : 'bg-slate-600'
                          }`}>
                            {item.rank}
                          </span>
                        </td>
                        <td className="py-2 px-1">
                          <div className="flex items-center gap-1">
                            <span className="text-white font-medium">{item.stock_name}</span>
                            <span className={`px-1 py-0.5 rounded text-[10px] ${ratingConfig.color} text-white`}>
                              {ratingConfig.label}
                            </span>
                          </div>
                          <div className="text-slate-500">{item.stock_id}</div>
                        </td>
                        <td className="py-2 px-1 text-right">
                          <div className="text-emerald-400 font-medium">{item.weight_percent}%</div>
                        </td>
                        <td className="py-2 px-1 text-right">
                          <div className="text-white">${item.allocated_amount.toLocaleString()}</div>
                        </td>
                        <td className="py-2 px-1 text-right">
                          <div className="text-slate-400">${item.price_per_share}</div>
                        </td>
                        <td className="py-2 px-1 text-right">
                          <div className="text-amber-400 font-bold">
                            {item.suggested_lots > 0 ? `${item.suggested_lots} 張` : '零股'}
                          </div>
                          {item.suggested_lots === 0 && (
                            <div className="text-slate-500 text-[10px]">
                              約 {Math.floor(item.allocated_amount / item.price_per_share)} 股
                            </div>
                          )}
                        </td>
                        <td className="py-2 px-1 text-right">
                          <div className="text-white font-medium">${item.actual_amount.toLocaleString()}</div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="bg-slate-800/50 font-medium">
                    <td colSpan="3" className="py-2 px-1 text-slate-400">合計</td>
                    <td className="py-2 px-1 text-right text-white">${budget.toLocaleString()}</td>
                    <td className="py-2 px-1"></td>
                    <td className="py-2 px-1 text-right text-amber-400">
                      {allocation.reduce((sum, a) => sum + a.suggested_lots, 0)} 張
                    </td>
                    <td className="py-2 px-1 text-right text-emerald-400">
                      ${getTotals().totalAllocated.toLocaleString()}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* 剩餘現金提示 */}
            {getTotals().totalRemaining > 0 && (
              <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs">
                <span className="text-amber-400">💡 剩餘現金：</span>
                <span className="text-white ml-1 font-medium">${getTotals().totalRemaining.toLocaleString()}</span>
                <span className="text-slate-400 ml-2">（可保留作為加碼或手續費）</span>
              </div>
            )}

            {/* 購買提示 */}
            <div className="mt-3 p-2 bg-blue-500/10 border border-blue-500/30 rounded-lg text-xs text-slate-400">
              <span className="text-blue-400">📝 購買提示：</span>
              <ul className="mt-1 space-y-0.5 list-disc list-inside">
                <li>以上為建議配置，實際買進請依當時股價調整</li>
                <li>建議使用券商 App 的「整股+零股」功能購買</li>
                <li>可分批進場，降低買進成本風險</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 主組件
const StrategyPicksPanel = ({ onSelectStock }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPlanner, setShowPlanner] = useState(false);
  const [selectedPick, setSelectedPick] = useState(null);  // V10.17: 選中的個股

  const fetchStrategyPicks = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/stocks/strategy-picks?top_n=10`);
      if (!res.ok) throw new Error('取得策略精選失敗');

      const result = await res.json();
      if (result.success) {
        setData(result);
      } else {
        throw new Error(result.error || '未知錯誤');
      }
    } catch (err) {
      console.error('策略精選載入失敗:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStrategyPicks();
  }, []);

  // V10.17: 點選個股時的處理
  const handlePickSelect = (pick) => {
    setSelectedPick(pick);
    // 同時通知父組件（如果需要在右側面板顯示）
    if (onSelectStock) {
      onSelectStock({
        stock_id: pick.stock_id,
        name: pick.stock_name,
        price: pick.current_price,
        confidence: pick.rating_score,
        signal: RATING_CONFIG[pick.rating]?.label || '持有',
        score_breakdown: {
          technical: pick.technical_score,
          fundamental: pick.fundamental_score,
          chip: pick.chip_score,
          news: pick.industry_score,
        },
      });
    }
  };

  const handleCalculate = (budget, riskLevel, allocation) => {
    // 可擴展：處理配置計算結果
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-slate-400">分析市場中，請稍候...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={fetchStrategyPicks}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
        >
          重試
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 標題列 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🎯</span> 綜合投資策略精選
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPlanner(!showPlanner)}
            className={`px-3 py-1 rounded-lg text-sm transition-colors ${
              showPlanner ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            💰 預算規劃
          </button>
          <button
            onClick={fetchStrategyPicks}
            className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm"
          >
            🔄 更新
          </button>
        </div>
      </div>

      {/* 更新時間 - V10.35.4: 使用統一日期格式 */}
      {data?.updated_at && (
        <div className="text-xs text-slate-500">
          最後更新: {formatDateTime(data.updated_at)}
        </div>
      )}

      {/* 備用方案警告 */}
      {data?.is_fallback && (
        <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg p-3 text-amber-400 text-sm">
          <span className="font-medium">⚠️ 網路連線受限</span>
          <span className="text-amber-400/80 ml-2">
            {data.fallback_reason || '使用備用股票清單進行分析'}
          </span>
        </div>
      )}

      {/* 市場概覽與配置建議 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MarketOverviewCard overview={data?.market_overview} />
        <PortfolioAllocationCard allocation={data?.portfolio_allocation} />
      </div>

      {/* V10.17: 預算規劃器（全寬顯示） */}
      {showPlanner && (
        <BudgetPlanner
          onCalculate={handleCalculate}
          strategyPicks={data?.strategy_picks || []}
        />
      )}

      {/* V10.17: 點選個股時顯示詳細分析 */}
      {selectedPick && (
        <div className="lg:grid lg:grid-cols-3 lg:gap-4">
          <div className="lg:col-span-2">
            <StockDetailPanel
              pick={selectedPick}
              onClose={() => setSelectedPick(null)}
            />
          </div>
          <div className="hidden lg:block">
            {/* 側邊快速跳轉列表 */}
            <div className="bg-slate-800/50 rounded-xl p-3 border border-slate-700 sticky top-20">
              <h4 className="text-white font-medium mb-2 text-sm">其他精選</h4>
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {data?.strategy_picks?.filter(p => p.stock_id !== selectedPick.stock_id).slice(0, 5).map((pick) => {
                  const rc = RATING_CONFIG[pick.rating] || RATING_CONFIG.hold;
                  return (
                    <button
                      key={pick.stock_id}
                      onClick={() => setSelectedPick(pick)}
                      className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-900/50 hover:bg-slate-700/50 transition-colors text-left"
                    >
                      <div>
                        <div className="text-white text-sm">{pick.stock_name}</div>
                        <div className="text-slate-500 text-xs">{pick.stock_id}</div>
                      </div>
                      <span className={`${rc.color} text-white text-xs px-2 py-0.5 rounded`}>
                        {rc.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 策略精選列表（未選中個股時顯示） */}
      {!selectedPick && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.strategy_picks?.map((pick, i) => (
            <StrategyPickCard
              key={pick.stock_id}
              pick={pick}
              rank={i + 1}
              onSelect={handlePickSelect}
            />
          ))}
        </div>
      )}

      {/* 空狀態 */}
      {(!data?.strategy_picks || data.strategy_picks.length === 0) && (
        <div className="text-center py-8 text-slate-500">
          <p className="text-4xl mb-4">📊</p>
          <p>目前無策略精選資料</p>
        </div>
      )}

      {/* 免責聲明 */}
      <div className="text-center text-slate-500 text-xs pt-4 border-t border-slate-800">
        ⚠️ 以上內容僅供參考，不構成投資建議。投資有風險，入市需謹慎。
      </div>
    </div>
  );
};

export default StrategyPicksPanel;
