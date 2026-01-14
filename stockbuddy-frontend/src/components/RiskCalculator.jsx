/**
 * RiskCalculator.jsx - 風險管理計算器
 * V10.29 新增
 *
 * 功能：
 * - 停損/停利計算
 * - 倉位大小計算
 * - 風險報酬比計算
 * - 最大損失計算
 */

import React, { useState, useMemo } from 'react';

const RiskCalculator = ({ stock = null, onClose }) => {
  const [activeTab, setActiveTab] = useState('position'); // position | stoploss | rr

  // 倉位計算器狀態
  const [totalCapital, setTotalCapital] = useState(1000000); // 總資金
  const [riskPercent, setRiskPercent] = useState(2); // 單筆風險比例 %
  const [entryPrice, setEntryPrice] = useState(stock?.price || 100);
  const [stopLossPrice, setStopLossPrice] = useState(stock?.price ? stock.price * 0.95 : 95);

  // 停損停利計算器狀態
  const [holdingShares, setHoldingShares] = useState(1000);
  const [avgCost, setAvgCost] = useState(stock?.price || 100);
  const [targetProfit, setTargetProfit] = useState(10); // %
  const [targetLoss, setTargetLoss] = useState(5); // %

  // 風險報酬比計算器狀態
  const [rrEntryPrice, setRREntryPrice] = useState(stock?.price || 100);
  const [rrStopLoss, setRRStopLoss] = useState(stock?.price ? stock.price * 0.95 : 95);
  const [rrTakeProfit, setRRTakeProfit] = useState(stock?.price ? stock.price * 1.15 : 115);

  // 倉位計算
  const positionCalc = useMemo(() => {
    const riskAmount = totalCapital * (riskPercent / 100);
    const riskPerShare = entryPrice - stopLossPrice;

    if (riskPerShare <= 0) {
      return { shares: 0, cost: 0, maxLoss: 0, error: '停損價必須低於進場價' };
    }

    const shares = Math.floor(riskAmount / riskPerShare);
    const cost = shares * entryPrice;
    const maxLoss = shares * riskPerShare;
    const costPercent = (cost / totalCapital) * 100;

    return {
      shares,
      cost,
      maxLoss,
      costPercent,
      riskAmount,
      riskPerShare,
    };
  }, [totalCapital, riskPercent, entryPrice, stopLossPrice]);

  // 停損停利計算
  const stopCalc = useMemo(() => {
    const totalCost = holdingShares * avgCost;
    const takeProfitPrice = avgCost * (1 + targetProfit / 100);
    const stopLossPrice = avgCost * (1 - targetLoss / 100);
    const profitAmount = holdingShares * (takeProfitPrice - avgCost);
    const lossAmount = holdingShares * (avgCost - stopLossPrice);

    return {
      totalCost,
      takeProfitPrice,
      stopLossPrice,
      profitAmount,
      lossAmount,
      profitPercent: targetProfit,
      lossPercent: targetLoss,
    };
  }, [holdingShares, avgCost, targetProfit, targetLoss]);

  // 風險報酬比計算
  const rrCalc = useMemo(() => {
    const risk = rrEntryPrice - rrStopLoss;
    const reward = rrTakeProfit - rrEntryPrice;

    if (risk <= 0 || reward <= 0) {
      return { ratio: 0, riskPercent: 0, rewardPercent: 0, error: '請確認價格設定正確' };
    }

    const ratio = reward / risk;
    const riskPercent = (risk / rrEntryPrice) * 100;
    const rewardPercent = (reward / rrEntryPrice) * 100;

    return {
      ratio,
      risk,
      reward,
      riskPercent,
      rewardPercent,
    };
  }, [rrEntryPrice, rrStopLoss, rrTakeProfit]);

  // 評分顏色
  const getRatioColor = (ratio) => {
    if (ratio >= 3) return 'text-emerald-400';
    if (ratio >= 2) return 'text-blue-400';
    if (ratio >= 1) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getRatioLabel = (ratio) => {
    if (ratio >= 3) return '優良';
    if (ratio >= 2) return '良好';
    if (ratio >= 1) return '一般';
    return '偏低';
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* 標題 */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>🛡️</span> 風險管理計算器
          {stock && (
            <span className="text-sm font-normal text-slate-400">
              - {stock.name} ({stock.stock_id})
            </span>
          )}
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {/* 分頁 */}
      <div className="flex border-b border-slate-700">
        {[
          { key: 'position', label: '倉位計算', icon: '📊' },
          { key: 'stoploss', label: '停損停利', icon: '🎯' },
          { key: 'rr', label: '風險報酬', icon: '⚖️' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-blue-400 border-b-2 border-blue-400 bg-slate-700/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/20'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* 內容 */}
      <div className="p-4">
        {activeTab === 'position' && (
          <div className="space-y-4">
            {/* 輸入區 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-sm mb-1">總資金</label>
                <input
                  type="number"
                  value={totalCapital}
                  onChange={(e) => setTotalCapital(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">單筆風險 (%)</label>
                <input
                  type="number"
                  value={riskPercent}
                  onChange={(e) => setRiskPercent(Number(e.target.value))}
                  min="0.5"
                  max="10"
                  step="0.5"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">進場價</label>
                <input
                  type="number"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">停損價</label>
                <input
                  type="number"
                  value={stopLossPrice}
                  onChange={(e) => setStopLossPrice(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* 結果區 */}
            <div className="bg-slate-700/50 rounded-lg p-4 space-y-3">
              <h3 className="text-white font-medium mb-3">計算結果</h3>

              {positionCalc.error ? (
                <div className="text-red-400">{positionCalc.error}</div>
              ) : (
                <>
                  <div className="flex justify-between">
                    <span className="text-slate-400">建議買進股數</span>
                    <span className="text-white font-medium">
                      {positionCalc.shares.toLocaleString()} 股
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">預估投入金額</span>
                    <span className="text-white font-medium">
                      ${positionCalc.cost.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">佔總資金比例</span>
                    <span className="text-blue-400 font-medium">
                      {positionCalc.costPercent?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-slate-600 pt-3">
                    <span className="text-slate-400">最大損失金額</span>
                    <span className="text-red-400 font-medium">
                      -${positionCalc.maxLoss?.toLocaleString()}
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* 建議 */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <span>💡</span>
                <div className="text-sm text-blue-300">
                  <div className="font-medium mb-1">風險管理建議</div>
                  <ul className="list-disc list-inside text-blue-200/80 space-y-1">
                    <li>單筆交易風險建議控制在總資金的 1-2%</li>
                    <li>同時持有部位不超過總資金的 20-30%</li>
                    <li>設定停損後務必嚴格執行</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'stoploss' && (
          <div className="space-y-4">
            {/* 輸入區 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-sm mb-1">持有股數</label>
                <input
                  type="number"
                  value={holdingShares}
                  onChange={(e) => setHoldingShares(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">平均成本</label>
                <input
                  type="number"
                  value={avgCost}
                  onChange={(e) => setAvgCost(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">目標獲利 (%)</label>
                <input
                  type="number"
                  value={targetProfit}
                  onChange={(e) => setTargetProfit(Number(e.target.value))}
                  min="1"
                  max="100"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">停損幅度 (%)</label>
                <input
                  type="number"
                  value={targetLoss}
                  onChange={(e) => setTargetLoss(Number(e.target.value))}
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* 結果區 */}
            <div className="grid grid-cols-2 gap-4">
              {/* 停利 */}
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                <div className="text-emerald-400 text-sm mb-2">停利價位</div>
                <div className="text-2xl font-bold text-emerald-400">
                  ${stopCalc.takeProfitPrice.toFixed(2)}
                </div>
                <div className="text-emerald-300/70 text-sm mt-2">
                  預估獲利: +${stopCalc.profitAmount.toLocaleString()}
                </div>
              </div>

              {/* 停損 */}
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <div className="text-red-400 text-sm mb-2">停損價位</div>
                <div className="text-2xl font-bold text-red-400">
                  ${stopCalc.stopLossPrice.toFixed(2)}
                </div>
                <div className="text-red-300/70 text-sm mt-2">
                  最大損失: -${stopCalc.lossAmount.toLocaleString()}
                </div>
              </div>
            </div>

            {/* 總成本 */}
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <span className="text-slate-400">總投入成本: </span>
              <span className="text-white font-medium">${stopCalc.totalCost.toLocaleString()}</span>
            </div>
          </div>
        )}

        {activeTab === 'rr' && (
          <div className="space-y-4">
            {/* 輸入區 */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-slate-400 text-sm mb-1">進場價</label>
                <input
                  type="number"
                  value={rrEntryPrice}
                  onChange={(e) => setRREntryPrice(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">停損價</label>
                <input
                  type="number"
                  value={rrStopLoss}
                  onChange={(e) => setRRStopLoss(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">目標價</label>
                <input
                  type="number"
                  value={rrTakeProfit}
                  onChange={(e) => setRRTakeProfit(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* 結果區 */}
            {rrCalc.error ? (
              <div className="text-red-400 text-center py-4">{rrCalc.error}</div>
            ) : (
              <>
                {/* 風險報酬比顯示 */}
                <div className="bg-slate-700/50 rounded-lg p-6 text-center">
                  <div className="text-slate-400 text-sm mb-2">風險報酬比</div>
                  <div className={`text-4xl font-bold ${getRatioColor(rrCalc.ratio)}`}>
                    1 : {rrCalc.ratio.toFixed(2)}
                  </div>
                  <div className={`text-sm mt-2 ${getRatioColor(rrCalc.ratio)}`}>
                    {getRatioLabel(rrCalc.ratio)}
                  </div>
                </div>

                {/* 細節 */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                    <div className="text-red-400 text-sm">風險 (下跌空間)</div>
                    <div className="text-red-400 font-medium">
                      ${rrCalc.risk?.toFixed(2)} ({rrCalc.riskPercent?.toFixed(1)}%)
                    </div>
                  </div>
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                    <div className="text-emerald-400 text-sm">報酬 (上漲空間)</div>
                    <div className="text-emerald-400 font-medium">
                      ${rrCalc.reward?.toFixed(2)} ({rrCalc.rewardPercent?.toFixed(1)}%)
                    </div>
                  </div>
                </div>

                {/* 視覺化 */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <div className="relative h-8 bg-slate-600 rounded-full overflow-hidden">
                    <div
                      className="absolute left-0 top-0 h-full bg-red-500/50"
                      style={{ width: `${(1 / (1 + rrCalc.ratio)) * 100}%` }}
                    />
                    <div
                      className="absolute right-0 top-0 h-full bg-emerald-500/50"
                      style={{ width: `${(rrCalc.ratio / (1 + rrCalc.ratio)) * 100}%` }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center text-white text-sm font-medium">
                      風險 vs 報酬
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* 說明 */}
            <div className="bg-slate-700/30 rounded-lg p-3 text-sm text-slate-400">
              <div className="font-medium text-white mb-1">風險報酬比說明</div>
              <ul className="list-disc list-inside space-y-1">
                <li>1:2 以上為良好的交易機會</li>
                <li>1:3 以上為優質的交易機會</li>
                <li>建議只進行風險報酬比 1:1.5 以上的交易</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskCalculator;
