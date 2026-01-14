/**
 * DividendCalculator.jsx - 除權息計算器
 * V10.30 新增
 *
 * 功能：
 * - 除權息試算
 * - 填息天數追蹤
 * - 殖利率計算
 * - 參與除息損益分析
 */

import React, { useState, useMemo } from 'react';

const DividendCalculator = ({ stock = null }) => {
  const [activeTab, setActiveTab] = useState('calculator'); // calculator | tracker | yield

  // 計算器狀態
  const [shares, setShares] = useState(1000); // 持有股數
  const [cashDividend, setCashDividend] = useState(3); // 現金股利
  const [stockDividend, setStockDividend] = useState(0); // 股票股利
  const [closingPrice, setClosingPrice] = useState(stock?.price || 100); // 除息前收盤價
  const [currentPrice, setCurrentPrice] = useState(stock?.price || 100); // 目前股價

  // 殖利率計算狀態
  const [investAmount, setInvestAmount] = useState(100000);
  const [targetYield, setTargetYield] = useState(5);

  // 除權息計算
  const dividendCalc = useMemo(() => {
    // 現金股利總額
    const totalCashDividend = shares * cashDividend;

    // 股票股利計算（每千股配 X 股）
    const stockDividendShares = Math.floor((shares * stockDividend) / 10);

    // 除息參考價 = 收盤價 - 現金股利
    const exDividendPrice = closingPrice - cashDividend;

    // 除權參考價 = 除息參考價 / (1 + 股票股利/10)
    const exRightsPrice =
      stockDividend > 0 ? exDividendPrice / (1 + stockDividend / 10) : exDividendPrice;

    // 填息價差
    const fillGap = closingPrice - exRightsPrice;

    // 填息狀態
    const isFilled = currentPrice >= closingPrice;
    const fillProgress = ((currentPrice - exRightsPrice) / fillGap) * 100;

    // 參與除息損益（不計算股票股利價值）
    const paperLoss = (exRightsPrice - closingPrice) * shares;
    const actualProfit = totalCashDividend + paperLoss + (currentPrice - exRightsPrice) * shares;

    // 殖利率
    const dividendYield = ((cashDividend + stockDividend * closingPrice / 10) / closingPrice) * 100;

    return {
      totalCashDividend,
      stockDividendShares,
      exDividendPrice,
      exRightsPrice,
      fillGap,
      isFilled,
      fillProgress: Math.min(100, Math.max(0, fillProgress)),
      paperLoss,
      actualProfit,
      dividendYield,
      totalShares: shares + stockDividendShares,
    };
  }, [shares, cashDividend, stockDividend, closingPrice, currentPrice]);

  // 殖利率計算
  const yieldCalc = useMemo(() => {
    // 需要多少股票才能達到目標殖利率的股利收入
    const targetDividendIncome = investAmount * (targetYield / 100);
    const requiredShares = Math.ceil(targetDividendIncome / cashDividend);
    const requiredInvestment = requiredShares * closingPrice;

    // 不同價位的殖利率
    const yieldAtPrices = [0.8, 0.9, 1, 1.1, 1.2].map((ratio) => {
      const price = closingPrice * ratio;
      const yieldRate = (cashDividend / price) * 100;
      return { price, yield: yieldRate };
    });

    return {
      targetDividendIncome,
      requiredShares,
      requiredInvestment,
      yieldAtPrices,
      currentYield: (cashDividend / closingPrice) * 100,
    };
  }, [investAmount, targetYield, cashDividend, closingPrice]);

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* 標題 */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>💵</span> 除權息計算器
          {stock && (
            <span className="text-sm font-normal text-slate-400">
              - {stock.name} ({stock.stock_id})
            </span>
          )}
        </h2>
      </div>

      {/* 分頁 */}
      <div className="flex border-b border-slate-700">
        {[
          { key: 'calculator', label: '除權息試算', icon: '🧮' },
          { key: 'tracker', label: '填息追蹤', icon: '📈' },
          { key: 'yield', label: '殖利率分析', icon: '💰' },
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
        {activeTab === 'calculator' && (
          <div className="space-y-4">
            {/* 輸入區 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-sm mb-1">持有股數</label>
                <input
                  type="number"
                  value={shares}
                  onChange={(e) => setShares(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">除息前收盤價</label>
                <input
                  type="number"
                  value={closingPrice}
                  onChange={(e) => setClosingPrice(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">現金股利 (元)</label>
                <input
                  type="number"
                  value={cashDividend}
                  onChange={(e) => setCashDividend(Number(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">股票股利 (元)</label>
                <input
                  type="number"
                  value={stockDividend}
                  onChange={(e) => setStockDividend(Number(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
                <p className="text-slate-500 text-xs mt-1">每股配發股票股利</p>
              </div>
            </div>

            {/* 計算結果 */}
            <div className="bg-slate-700/50 rounded-lg p-4 space-y-4">
              <h3 className="text-white font-medium">計算結果</h3>

              <div className="grid grid-cols-2 gap-4">
                {/* 現金股利 */}
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3">
                  <div className="text-emerald-400 text-sm">可領現金股利</div>
                  <div className="text-2xl font-bold text-emerald-400">
                    ${dividendCalc.totalCashDividend.toLocaleString()}
                  </div>
                </div>

                {/* 股票股利 */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                  <div className="text-blue-400 text-sm">可領股票股利</div>
                  <div className="text-2xl font-bold text-blue-400">
                    {dividendCalc.stockDividendShares.toLocaleString()} 股
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">除權息參考價</span>
                  <span className="text-white font-medium">
                    ${dividendCalc.exRightsPrice.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">填息價差</span>
                  <span className="text-yellow-400 font-medium">
                    ${dividendCalc.fillGap.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">殖利率</span>
                  <span className="text-emerald-400 font-medium">
                    {dividendCalc.dividendYield.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">配股後總股數</span>
                  <span className="text-white font-medium">
                    {dividendCalc.totalShares.toLocaleString()} 股
                  </span>
                </div>
              </div>
            </div>

            {/* 提示 */}
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <span>💡</span>
                <div className="text-sm text-yellow-300">
                  <div className="font-medium mb-1">除權息小知識</div>
                  <ul className="list-disc list-inside text-yellow-200/80 space-y-1">
                    <li>現金股利：直接發放現金到帳戶</li>
                    <li>股票股利：每張(1000股)配發對應股數</li>
                    <li>填息：股價回到除息前價位</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tracker' && (
          <div className="space-y-4">
            {/* 目前股價輸入 */}
            <div>
              <label className="block text-slate-400 text-sm mb-1">目前股價</label>
              <input
                type="number"
                value={currentPrice}
                onChange={(e) => setCurrentPrice(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* 填息進度 */}
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-white font-medium">填息進度</span>
                <span
                  className={`font-bold ${
                    dividendCalc.isFilled ? 'text-emerald-400' : 'text-yellow-400'
                  }`}
                >
                  {dividendCalc.isFilled ? '已填息 ✓' : `${dividendCalc.fillProgress.toFixed(1)}%`}
                </span>
              </div>

              {/* 進度條 */}
              <div className="relative h-6 bg-slate-600 rounded-full overflow-hidden">
                <div
                  className={`absolute left-0 top-0 h-full transition-all duration-300 ${
                    dividendCalc.isFilled ? 'bg-emerald-500' : 'bg-yellow-500'
                  }`}
                  style={{ width: `${dividendCalc.fillProgress}%` }}
                />
                <div className="absolute inset-0 flex items-center justify-between px-3 text-xs text-white">
                  <span>${dividendCalc.exRightsPrice.toFixed(2)}</span>
                  <span>${closingPrice.toFixed(2)}</span>
                </div>
              </div>

              {/* 價位標示 */}
              <div className="flex justify-between mt-2 text-xs text-slate-400">
                <span>除權息參考價</span>
                <span>填息目標價</span>
              </div>
            </div>

            {/* 損益分析 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/30 rounded-lg p-3">
                <div className="text-slate-400 text-sm">帳面損益</div>
                <div
                  className={`text-xl font-bold ${
                    dividendCalc.actualProfit >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {dividendCalc.actualProfit >= 0 ? '+' : ''}
                  ${dividendCalc.actualProfit.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-700/30 rounded-lg p-3">
                <div className="text-slate-400 text-sm">距離填息</div>
                <div className="text-xl font-bold text-white">
                  ${(closingPrice - currentPrice).toFixed(2)}
                </div>
              </div>
            </div>

            {/* 說明 */}
            <div className="text-slate-400 text-sm">
              <p>
                目前股價 <span className="text-white">${currentPrice}</span> 相較除息前收盤價{' '}
                <span className="text-white">${closingPrice}</span>
                {currentPrice >= closingPrice ? (
                  <span className="text-emerald-400"> 已完成填息！</span>
                ) : (
                  <span className="text-yellow-400">
                    {' '}
                    還差 ${(closingPrice - currentPrice).toFixed(2)} 才能填息
                  </span>
                )}
              </p>
            </div>
          </div>
        )}

        {activeTab === 'yield' && (
          <div className="space-y-4">
            {/* 輸入區 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-sm mb-1">投資金額</label>
                <input
                  type="number"
                  value={investAmount}
                  onChange={(e) => setInvestAmount(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-1">目標殖利率 (%)</label>
                <input
                  type="number"
                  value={targetYield}
                  onChange={(e) => setTargetYield(Number(e.target.value))}
                  min="1"
                  max="20"
                  step="0.5"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>

            {/* 當前殖利率 */}
            <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 rounded-lg p-4 text-center">
              <div className="text-slate-400 text-sm">當前殖利率</div>
              <div className="text-4xl font-bold text-emerald-400">
                {yieldCalc.currentYield.toFixed(2)}%
              </div>
              <div className="text-slate-400 text-sm mt-1">
                現金股利 ${cashDividend} / 股價 ${closingPrice}
              </div>
            </div>

            {/* 目標分析 */}
            <div className="bg-slate-700/50 rounded-lg p-4 space-y-3">
              <h3 className="text-white font-medium">達成目標殖利率 {targetYield}%</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">需購買股數</span>
                  <span className="text-white font-medium">
                    {yieldCalc.requiredShares.toLocaleString()} 股
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">需投資金額</span>
                  <span className="text-white font-medium">
                    ${yieldCalc.requiredInvestment.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">預估年股利收入</span>
                  <span className="text-emerald-400 font-medium">
                    ${yieldCalc.targetDividendIncome.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* 不同價位殖利率 */}
            <div className="bg-slate-700/50 rounded-lg p-4">
              <h3 className="text-white font-medium mb-3">不同價位殖利率</h3>
              <div className="space-y-2">
                {yieldCalc.yieldAtPrices.map((item, index) => (
                  <div
                    key={index}
                    className={`flex justify-between items-center p-2 rounded ${
                      Math.abs(item.price - closingPrice) < 0.01
                        ? 'bg-blue-500/20'
                        : 'bg-slate-600/30'
                    }`}
                  >
                    <span className="text-slate-300">${item.price.toFixed(2)}</span>
                    <span
                      className={`font-medium ${
                        item.yield >= 5 ? 'text-emerald-400' : 'text-slate-400'
                      }`}
                    >
                      {item.yield.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DividendCalculator;
