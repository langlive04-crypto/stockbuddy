/**
 * PortfolioDashboard.jsx - 投資組合儀表板
 * V10.30 新增
 *
 * 功能：
 * - 投組總覽統計
 * - 持股分布圖表
 * - 產業配置分析
 * - 損益追蹤
 */

import React, { useState, useMemo, useEffect } from 'react';

// localStorage key
const PORTFOLIO_KEY = 'stockbuddy_portfolio';
const TRANSACTIONS_KEY = 'stockbuddy_transactions';

const PortfolioDashboard = ({ onSelectStock }) => {
  const [portfolio, setPortfolio] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [stockPrices, setStockPrices] = useState({});
  const [loading, setLoading] = useState(true);

  // 載入資料
  useEffect(() => {
    const loadData = () => {
      try {
        const savedPortfolio = localStorage.getItem(PORTFOLIO_KEY);
        const savedTransactions = localStorage.getItem(TRANSACTIONS_KEY);

        if (savedPortfolio) {
          setPortfolio(JSON.parse(savedPortfolio));
        }
        if (savedTransactions) {
          setTransactions(JSON.parse(savedTransactions));
        }
      } catch (e) {
        console.error('Failed to load portfolio data:', e);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 計算持股統計
  const holdings = useMemo(() => {
    const holdingMap = {};

    transactions.forEach((tx) => {
      if (!holdingMap[tx.stockId]) {
        holdingMap[tx.stockId] = {
          stockId: tx.stockId,
          stockName: tx.stockName,
          industry: tx.industry || '未分類',
          totalShares: 0,
          totalCost: 0,
          avgCost: 0,
          transactions: [],
        };
      }

      const holding = holdingMap[tx.stockId];

      if (tx.type === 'buy') {
        holding.totalShares += tx.shares;
        holding.totalCost += tx.shares * tx.price;
      } else if (tx.type === 'sell') {
        const sellCost = tx.shares * holding.avgCost;
        holding.totalShares -= tx.shares;
        holding.totalCost -= sellCost;
      }

      holding.avgCost = holding.totalShares > 0 ? holding.totalCost / holding.totalShares : 0;
      holding.transactions.push(tx);
    });

    return Object.values(holdingMap).filter((h) => h.totalShares > 0);
  }, [transactions]);

  // 計算總覽統計
  const summary = useMemo(() => {
    let totalValue = 0;
    let totalCost = 0;
    let totalProfit = 0;

    holdings.forEach((holding) => {
      const currentPrice = stockPrices[holding.stockId] || holding.avgCost;
      const value = holding.totalShares * currentPrice;
      const cost = holding.totalCost;
      const profit = value - cost;

      totalValue += value;
      totalCost += cost;
      totalProfit += profit;
    });

    const profitPercent = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

    return {
      totalValue,
      totalCost,
      totalProfit,
      profitPercent,
      holdingCount: holdings.length,
    };
  }, [holdings, stockPrices]);

  // 產業分布
  const industryDistribution = useMemo(() => {
    const distribution = {};

    holdings.forEach((holding) => {
      const currentPrice = stockPrices[holding.stockId] || holding.avgCost;
      const value = holding.totalShares * currentPrice;
      const industry = holding.industry || '未分類';

      if (!distribution[industry]) {
        distribution[industry] = { value: 0, count: 0 };
      }
      distribution[industry].value += value;
      distribution[industry].count += 1;
    });

    const total = Object.values(distribution).reduce((sum, item) => sum + item.value, 0);

    return Object.entries(distribution)
      .map(([industry, data]) => ({
        industry,
        value: data.value,
        count: data.count,
        percent: total > 0 ? (data.value / total) * 100 : 0,
      }))
      .sort((a, b) => b.value - a.value);
  }, [holdings, stockPrices]);

  // 產業顏色
  const getIndustryColor = (industry, index) => {
    const colors = [
      'bg-blue-500',
      'bg-emerald-500',
      'bg-purple-500',
      'bg-orange-500',
      'bg-pink-500',
      'bg-cyan-500',
      'bg-yellow-500',
      'bg-red-500',
    ];
    return colors[index % colors.length];
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 text-center">
        <div className="animate-pulse text-slate-400">載入中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 總覽卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 總市值 */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-4">
          <div className="text-blue-200 text-sm">總市值</div>
          <div className="text-2xl font-bold text-white">
            ${summary.totalValue.toLocaleString()}
          </div>
        </div>

        {/* 總成本 */}
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="text-slate-400 text-sm">投入成本</div>
          <div className="text-2xl font-bold text-white">
            ${summary.totalCost.toLocaleString()}
          </div>
        </div>

        {/* 總損益 */}
        <div
          className={`rounded-xl p-4 ${
            summary.totalProfit >= 0
              ? 'bg-gradient-to-br from-emerald-600 to-emerald-700'
              : 'bg-gradient-to-br from-red-600 to-red-700'
          }`}
        >
          <div className={summary.totalProfit >= 0 ? 'text-emerald-200' : 'text-red-200'} style={{ fontSize: '0.875rem' }}>
            未實現損益
          </div>
          <div className="text-2xl font-bold text-white">
            {summary.totalProfit >= 0 ? '+' : ''}
            ${summary.totalProfit.toLocaleString()}
          </div>
          <div className={`text-sm ${summary.totalProfit >= 0 ? 'text-emerald-200' : 'text-red-200'}`}>
            {summary.totalProfit >= 0 ? '+' : ''}
            {summary.profitPercent.toFixed(2)}%
          </div>
        </div>

        {/* 持股數量 */}
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="text-slate-400 text-sm">持股數量</div>
          <div className="text-2xl font-bold text-white">{summary.holdingCount}</div>
          <div className="text-slate-400 text-sm">檔股票</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* 產業分布 */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <span>🏭</span> 產業配置
          </h3>

          {industryDistribution.length === 0 ? (
            <div className="text-center text-slate-500 py-8">尚無持股資料</div>
          ) : (
            <div className="space-y-3">
              {industryDistribution.map((item, index) => (
                <div key={item.industry}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">{item.industry}</span>
                    <span className="text-slate-400">
                      {item.percent.toFixed(1)}% (${item.value.toLocaleString()})
                    </span>
                  </div>
                  <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getIndustryColor(item.industry, index)} transition-all duration-300`}
                      style={{ width: `${item.percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 持股列表 */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <span>📊</span> 持股明細
          </h3>

          {holdings.length === 0 ? (
            <div className="text-center text-slate-500 py-8">
              <p>尚無持股</p>
              <p className="text-sm mt-2">請先在交易記錄中新增買入記錄</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {holdings.map((holding) => {
                const currentPrice = stockPrices[holding.stockId] || holding.avgCost;
                const value = holding.totalShares * currentPrice;
                const profit = value - holding.totalCost;
                const profitPercent =
                  holding.totalCost > 0 ? (profit / holding.totalCost) * 100 : 0;

                return (
                  <div
                    key={holding.stockId}
                    onClick={() => onSelectStock?.({ stock_id: holding.stockId, name: holding.stockName })}
                    className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 cursor-pointer transition-colors"
                  >
                    <div>
                      <div className="text-white font-medium">
                        {holding.stockName}
                      </div>
                      <div className="text-slate-400 text-sm">
                        {holding.stockId} · {holding.totalShares.toLocaleString()} 股
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-white">${value.toLocaleString()}</div>
                      <div
                        className={`text-sm ${
                          profit >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}
                      >
                        {profit >= 0 ? '+' : ''}
                        {profitPercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 近期交易 */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <span>📝</span> 近期交易
        </h3>

        {transactions.length === 0 ? (
          <div className="text-center text-slate-500 py-8">尚無交易記錄</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-slate-400 text-sm border-b border-slate-700">
                  <th className="text-left pb-2">日期</th>
                  <th className="text-left pb-2">類型</th>
                  <th className="text-left pb-2">股票</th>
                  <th className="text-right pb-2">股數</th>
                  <th className="text-right pb-2">價格</th>
                  <th className="text-right pb-2">金額</th>
                </tr>
              </thead>
              <tbody>
                {transactions
                  .slice()
                  .reverse()
                  .slice(0, 10)
                  .map((tx, index) => (
                    <tr
                      key={tx.id || index}
                      className="border-b border-slate-700/50 text-sm"
                    >
                      <td className="py-2 text-slate-400">
                        {new Date(tx.date).toLocaleDateString('zh-TW')}
                      </td>
                      <td className="py-2">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            tx.type === 'buy'
                              ? 'bg-red-500/20 text-red-400'
                              : 'bg-emerald-500/20 text-emerald-400'
                          }`}
                        >
                          {tx.type === 'buy' ? '買入' : '賣出'}
                        </span>
                      </td>
                      <td className="py-2 text-white">
                        {tx.stockName} ({tx.stockId})
                      </td>
                      <td className="py-2 text-right text-slate-300">
                        {tx.shares.toLocaleString()}
                      </td>
                      <td className="py-2 text-right text-slate-300">
                        ${tx.price.toFixed(2)}
                      </td>
                      <td className="py-2 text-right text-white">
                        ${(tx.shares * tx.price).toLocaleString()}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 風險提示 */}
      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <span>⚠️</span>
          <div className="text-sm text-yellow-300">
            <div className="font-medium">投資風險提示</div>
            <p className="text-yellow-200/80 mt-1">
              本系統數據僅供參考，實際損益以券商帳戶為準。投資有風險，請謹慎評估。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioDashboard;
