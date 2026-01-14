/**
 * SimulationTrading.jsx - 模擬交易練習
 * V10.34 新增
 * V10.36 新增：止損止盈建議、倉位管理、投組風險評估
 *
 * 功能：
 * - 虛擬資金交易
 * - 買賣模擬操作
 * - 損益追蹤
 * - 交易歷史記錄
 * - V10.36: 風險管理建議
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';

// 儲存鍵
const SIMULATION_KEY = 'stockbuddy_simulation';

// 初始資金
const INITIAL_CAPITAL = 1000000;

// 取得模擬數據
const getSimulationData = () => {
  try {
    const data = JSON.parse(localStorage.getItem(SIMULATION_KEY));
    if (data) return data;
  } catch {}
  return {
    cash: INITIAL_CAPITAL,
    holdings: [],
    transactions: [],
    createdAt: new Date().toISOString(),
  };
};

// 儲存模擬數據
const saveSimulationData = (data) => {
  localStorage.setItem(SIMULATION_KEY, JSON.stringify(data));
};

// 模擬股票報價
const MOCK_STOCKS = [
  { id: '2330', name: '台積電', price: 1015, change: 2.5 },
  { id: '2454', name: '聯發科', price: 1210, change: -1.2 },
  { id: '2317', name: '鴻海', price: 108, change: 0.8 },
  { id: '3008', name: '大立光', price: 2350, change: 3.2 },
  { id: '2412', name: '中華電', price: 123, change: 0.5 },
  { id: '2881', name: '富邦金', price: 72, change: -0.3 },
  { id: '2303', name: '聯電', price: 54, change: 1.5 },
  { id: '2882', name: '國泰金', price: 60, change: 0.2 },
];

const SimulationTrading = () => {
  const [simData, setSimData] = useState(getSimulationData);
  const [selectedStock, setSelectedStock] = useState(MOCK_STOCKS[0]);
  const [quantityInput, setQuantityInput] = useState('1000');
  const [orderType, setOrderType] = useState('buy');
  const [showHistory, setShowHistory] = useState(false);
  const [tradeMessage, setTradeMessage] = useState(null);

  // V10.36: 風險管理狀態
  const [riskInfo, setRiskInfo] = useState(null);
  const [positionSize, setPositionSize] = useState(null);
  const [portfolioRisk, setPortfolioRisk] = useState(null);
  const [showRiskPanel, setShowRiskPanel] = useState(true);
  const [riskLoading, setRiskLoading] = useState(false);

  // 解析數量，確保為有效數字
  const quantity = useMemo(() => {
    const num = parseInt(quantityInput, 10);
    return isNaN(num) || num < 0 ? 0 : num;
  }, [quantityInput]);

  // 處理數量輸入變化 - V10.35.4: 兼容 number input spinner
  const handleQuantityChange = useCallback((e) => {
    const value = e.target.value;
    // 空字串或純數字都接受（number input 的 spinner 會產生數字字串）
    if (value === '' || /^\d*$/.test(value)) {
      // 確保非負數
      const num = parseInt(value, 10);
      if (value === '' || isNaN(num)) {
        setQuantityInput(value);
      } else {
        setQuantityInput(String(Math.max(0, num)));
      }
    }
  }, []);

  // 快速設定數量
  const setQuickQuantity = useCallback((amt) => {
    setQuantityInput(String(amt));
  }, []);

  // 計算持倉市值
  const portfolioValue = useMemo(() => {
    return simData.holdings.reduce((total, holding) => {
      const stock = MOCK_STOCKS.find(s => s.id === holding.stockId);
      const currentPrice = stock?.price || holding.avgPrice;
      return total + (currentPrice * holding.quantity);
    }, 0);
  }, [simData.holdings]);

  // 計算總資產
  const totalAssets = simData.cash + portfolioValue;

  // 計算總損益
  const totalPnL = totalAssets - INITIAL_CAPITAL;
  const totalPnLPercent = (totalPnL / INITIAL_CAPITAL) * 100;

  // V10.36: 取得止損止盈建議
  const fetchRiskInfo = useCallback(async (stockId) => {
    setRiskLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/stocks/risk/stop-loss/${stockId}`);
      if (response.ok) {
        const data = await response.json();
        setRiskInfo(data);
      } else {
        setRiskInfo(null);
      }
    } catch (error) {
      console.error('取得風險資訊失敗:', error);
      setRiskInfo(null);
    }
    setRiskLoading(false);
  }, []);

  // V10.36: 取得倉位建議
  const fetchPositionSize = useCallback(async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/stocks/risk/position-size?capital=${simData.cash}&risk_tolerance=moderate`
      );
      if (response.ok) {
        const data = await response.json();
        setPositionSize(data);
      }
    } catch (error) {
      console.error('取得倉位建議失敗:', error);
    }
  }, [simData.cash]);

  // V10.36: 取得投組風險評估
  const fetchPortfolioRisk = useCallback(async () => {
    if (simData.holdings.length === 0) {
      setPortfolioRisk(null);
      return;
    }
    try {
      // 建構持股資料
      const holdings = simData.holdings.map(h => ({
        stock_id: h.stockId,
        stock_name: h.stockName,
        value: h.quantity * (MOCK_STOCKS.find(s => s.id === h.stockId)?.price || h.avgPrice),
        industry: '未分類', // 模擬資料無產業資訊
      }));

      const response = await fetch('http://localhost:8000/api/stocks/risk/portfolio-assessment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holdings }),
      });
      if (response.ok) {
        const data = await response.json();
        setPortfolioRisk(data);
      }
    } catch (error) {
      console.error('取得投組風險失敗:', error);
    }
  }, [simData.holdings]);

  // V10.36: 當選擇股票變更時，取得風險資訊
  useEffect(() => {
    if (selectedStock) {
      fetchRiskInfo(selectedStock.id);
    }
  }, [selectedStock, fetchRiskInfo]);

  // V10.36: 取得倉位建議和投組風險
  useEffect(() => {
    fetchPositionSize();
    fetchPortfolioRisk();
  }, [fetchPositionSize, fetchPortfolioRisk]);

  // 執行交易
  const executeTrade = useCallback(() => {
    // 清除之前的訊息
    setTradeMessage(null);

    if (quantity <= 0) {
      setTradeMessage({ type: 'error', text: '請輸入有效數量！' });
      return;
    }

    const stock = selectedStock;
    const totalCost = stock.price * quantity;
    const fee = Math.round(totalCost * 0.001425); // 0.1425% 手續費
    const tax = orderType === 'sell' ? Math.round(totalCost * 0.003) : 0; // 0.3% 證交稅

    if (orderType === 'buy') {
      // 買進
      if (simData.cash < totalCost + fee) {
        setTradeMessage({ type: 'error', text: '現金不足！無法完成此交易。' });
        return;
      }

      const newHoldings = [...simData.holdings];
      const existingIndex = newHoldings.findIndex(h => h.stockId === stock.id);

      if (existingIndex >= 0) {
        // 加碼
        const existing = newHoldings[existingIndex];
        const newQuantity = existing.quantity + quantity;
        const newAvgPrice = ((existing.avgPrice * existing.quantity) + (stock.price * quantity)) / newQuantity;
        newHoldings[existingIndex] = {
          ...existing,
          quantity: newQuantity,
          avgPrice: newAvgPrice,
        };
      } else {
        // 新建倉
        newHoldings.push({
          stockId: stock.id,
          stockName: stock.name,
          quantity: quantity,
          avgPrice: stock.price,
          buyDate: new Date().toISOString(),
        });
      }

      const newData = {
        ...simData,
        cash: simData.cash - totalCost - fee,
        holdings: newHoldings,
        transactions: [
          {
            id: Date.now(),
            type: 'buy',
            stockId: stock.id,
            stockName: stock.name,
            quantity,
            price: stock.price,
            fee,
            tax: 0,
            total: totalCost + fee,
            date: new Date().toISOString(),
          },
          ...simData.transactions,
        ],
      };

      setSimData(newData);
      saveSimulationData(newData);
      setTradeMessage({ type: 'success', text: `成功買進 ${stock.name} ${quantity.toLocaleString()} 股！` });

    } else {
      // 賣出
      const holdingIndex = simData.holdings.findIndex(h => h.stockId === stock.id);
      if (holdingIndex < 0) {
        setTradeMessage({ type: 'error', text: '沒有持有此股票！' });
        return;
      }

      const holding = simData.holdings[holdingIndex];
      if (holding.quantity < quantity) {
        setTradeMessage({ type: 'error', text: `持股數量不足！目前持有 ${holding.quantity.toLocaleString()} 股` });
        return;
      }

      const newHoldings = [...simData.holdings];
      if (holding.quantity === quantity) {
        newHoldings.splice(holdingIndex, 1);
      } else {
        newHoldings[holdingIndex] = {
          ...holding,
          quantity: holding.quantity - quantity,
        };
      }

      const pnl = (stock.price - holding.avgPrice) * quantity - fee - tax;

      const newData = {
        ...simData,
        cash: simData.cash + totalCost - fee - tax,
        holdings: newHoldings,
        transactions: [
          {
            id: Date.now(),
            type: 'sell',
            stockId: stock.id,
            stockName: stock.name,
            quantity,
            price: stock.price,
            fee,
            tax,
            total: totalCost - fee - tax,
            pnl,
            date: new Date().toISOString(),
          },
          ...simData.transactions,
        ],
      };

      setSimData(newData);
      saveSimulationData(newData);
      const pnlText = pnl >= 0 ? `獲利 $${Math.round(pnl).toLocaleString()}` : `虧損 $${Math.round(Math.abs(pnl)).toLocaleString()}`;
      setTradeMessage({ type: 'success', text: `成功賣出 ${stock.name} ${quantity.toLocaleString()} 股！${pnlText}` });
    }
  }, [selectedStock, quantity, orderType, simData]);

  // 重置模擬
  const resetSimulation = () => {
    if (window.confirm('確定要重置模擬交易？所有記錄將被清除。')) {
      const newData = {
        cash: INITIAL_CAPITAL,
        holdings: [],
        transactions: [],
        createdAt: new Date().toISOString(),
      };
      setSimData(newData);
      saveSimulationData(newData);
    }
  };

  // 格式化金額
  const formatMoney = (amount) => {
    return Math.round(amount).toLocaleString();
  };

  // 格式化日期
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString('zh-TW', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🎮</span>
          <span>模擬交易練習</span>
        </h2>

        <button
          onClick={resetSimulation}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
        >
          🔄 重置
        </button>
      </div>

      {/* 帳戶概覽 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">總資產</div>
          <div className="text-xl font-bold text-white">${formatMoney(totalAssets)}</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">可用現金</div>
          <div className="text-xl font-bold text-blue-400">${formatMoney(simData.cash)}</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">持倉市值</div>
          <div className="text-xl font-bold text-purple-400">${formatMoney(portfolioValue)}</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">總損益</div>
          <div className={`text-xl font-bold ${totalPnL >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {totalPnL >= 0 ? '+' : ''}{formatMoney(totalPnL)} ({totalPnLPercent.toFixed(2)}%)
          </div>
        </div>
      </div>

      {/* 下單面板 */}
      <div className="bg-slate-700/30 rounded-lg p-4 mb-6">
        <h3 className="text-white font-medium mb-4">下單</h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* 股票選擇 */}
          <div>
            <label className="text-slate-400 text-sm mb-2 block">股票</label>
            <select
              value={selectedStock.id}
              onChange={(e) => setSelectedStock(MOCK_STOCKS.find(s => s.id === e.target.value))}
              className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
            >
              {MOCK_STOCKS.map(stock => (
                <option key={stock.id} value={stock.id}>
                  {stock.name} ({stock.id}) ${stock.price}
                </option>
              ))}
            </select>
          </div>

          {/* 買賣方向 */}
          <div>
            <label className="text-slate-400 text-sm mb-2 block">方向</label>
            <div className="flex gap-2">
              <button
                onClick={() => setOrderType('buy')}
                className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                  orderType === 'buy'
                    ? 'bg-red-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                買進
              </button>
              <button
                onClick={() => setOrderType('sell')}
                className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                  orderType === 'sell'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                賣出
              </button>
            </div>
          </div>

          {/* 數量 - V10.35.4: 桌面端顯示 Spinner，手機端顯示快速按鈕 */}
          <div>
            <label className="text-slate-400 text-sm mb-2 block">數量 (股)</label>
            <input
              type="number"
              inputMode="numeric"
              step={1000}
              min={0}
              value={quantityInput}
              onChange={handleQuantityChange}
              placeholder="輸入數量"
              className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none input-spinner-responsive"
            />
            {/* 快速數量按鈕 - 手機端更實用 */}
            <div className="flex gap-1 mt-1">
              {[1000, 5000, 10000].map(amt => (
                <button
                  key={amt}
                  onClick={() => setQuickQuantity(amt)}
                  className="flex-1 py-1 text-xs bg-slate-600 hover:bg-slate-500 text-slate-300 rounded transition-colors"
                >
                  {amt.toLocaleString()}
                </button>
              ))}
            </div>
          </div>

          {/* 執行按鈕 */}
          <div className="flex items-end">
            <button
              onClick={executeTrade}
              disabled={quantity <= 0}
              className={`w-full py-2 rounded-lg font-medium transition-colors ${
                orderType === 'buy'
                  ? 'bg-red-600 hover:bg-red-700 disabled:bg-slate-600'
                  : 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-600'
              } text-white`}
            >
              {orderType === 'buy' ? '確認買進' : '確認賣出'}
            </button>
          </div>
        </div>

        {/* 預估金額 */}
        <div className="flex items-center justify-between text-sm p-2 bg-slate-800/50 rounded">
          <span className="text-slate-400">預估金額</span>
          <span className="text-white font-medium">
            ${formatMoney(selectedStock.price * quantity)} + 手續費 ${formatMoney(Math.round(selectedStock.price * quantity * 0.001425))}
            {orderType === 'sell' && ` + 稅 ${formatMoney(Math.round(selectedStock.price * quantity * 0.003))}`}
          </span>
        </div>

        {/* V10.36: 風險管理建議面板 */}
        {showRiskPanel && (
          <div className="mt-4 p-3 bg-slate-800/50 rounded-lg border border-slate-600/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-slate-300 flex items-center gap-1">
                <span>🛡️</span> 風險管理建議
              </h4>
              <button
                onClick={() => setShowRiskPanel(false)}
                className="text-slate-500 hover:text-slate-300 text-xs"
              >
                收起
              </button>
            </div>

            {riskLoading ? (
              <div className="text-center py-2 text-slate-500 text-sm">載入中...</div>
            ) : riskInfo ? (
              <div className="space-y-3">
                {/* 止損止盈 */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-red-500/10 p-2 rounded border border-red-500/20">
                    <div className="text-red-400 text-xs mb-1">建議止損</div>
                    <div className="text-white font-medium">${riskInfo.stop_loss?.toFixed(2) || '--'}</div>
                    <div className="text-red-400/70 text-xs">-{riskInfo.stop_loss_pct?.toFixed(1) || '--'}%</div>
                  </div>
                  <div className="bg-emerald-500/10 p-2 rounded border border-emerald-500/20">
                    <div className="text-emerald-400 text-xs mb-1">獲利目標 1</div>
                    <div className="text-white font-medium">${riskInfo.targets?.target_1?.toFixed(2) || '--'}</div>
                    <div className="text-emerald-400/70 text-xs">RR 1.5:1</div>
                  </div>
                </div>

                {/* 更多獲利目標 */}
                {riskInfo.targets && (
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-emerald-500/5 p-2 rounded border border-emerald-500/10">
                      <div className="text-emerald-400/80 text-xs mb-1">獲利目標 2</div>
                      <div className="text-slate-300 text-sm">${riskInfo.targets.target_2?.toFixed(2) || '--'}</div>
                    </div>
                    <div className="bg-emerald-500/5 p-2 rounded border border-emerald-500/10">
                      <div className="text-emerald-400/80 text-xs mb-1">獲利目標 3</div>
                      <div className="text-slate-300 text-sm">${riskInfo.targets.target_3?.toFixed(2) || '--'}</div>
                    </div>
                  </div>
                )}

                {/* 倉位建議 */}
                {positionSize && (
                  <div className="bg-blue-500/10 p-2 rounded border border-blue-500/20">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-blue-400 text-xs mb-1">建議倉位</div>
                        <div className="text-white font-medium">
                          {(positionSize.position_ratio * 100).toFixed(1)}%
                          <span className="text-slate-400 text-sm ml-1">
                            (${formatMoney(positionSize.suggested_amount)})
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-slate-500 text-xs">風險等級</div>
                        <div className={`text-sm font-medium ${
                          positionSize.risk_level === 'low' ? 'text-emerald-400' :
                          positionSize.risk_level === 'medium' ? 'text-yellow-400' :
                          'text-red-400'
                        }`}>
                          {positionSize.risk_level === 'low' ? '低風險' :
                           positionSize.risk_level === 'medium' ? '中風險' : '高風險'}
                        </div>
                      </div>
                    </div>
                    <div className="mt-1 text-slate-500 text-xs">
                      約 {Math.floor(positionSize.suggested_amount / selectedStock.price / 1000) * 1000} 股
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-2 text-slate-500 text-sm">
                無法取得風險建議
              </div>
            )}
          </div>
        )}

        {/* 收起時的簡易按鈕 */}
        {!showRiskPanel && (
          <button
            onClick={() => setShowRiskPanel(true)}
            className="mt-3 w-full py-2 text-sm text-slate-400 hover:text-slate-300 bg-slate-800/30 rounded hover:bg-slate-800/50 transition-colors"
          >
            🛡️ 顯示風險管理建議
          </button>
        )}

        {/* 交易訊息 */}
        {tradeMessage && (
          <div className={`mt-3 p-3 rounded-lg text-sm font-medium ${
            tradeMessage.type === 'success'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              : 'bg-red-500/20 text-red-300 border border-red-500/30'
          }`}>
            {tradeMessage.type === 'success' ? '✅' : '❌'} {tradeMessage.text}
          </div>
        )}
      </div>

      {/* 持倉列表 */}
      <div className="bg-slate-700/30 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium">目前持倉</h3>

          {/* V10.36: 投組風險評估 */}
          {portfolioRisk && simData.holdings.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-slate-500 text-xs">分散度</span>
              <div className={`px-2 py-0.5 rounded text-xs font-medium ${
                portfolioRisk.diversification_score >= 70 ? 'bg-emerald-500/20 text-emerald-400' :
                portfolioRisk.diversification_score >= 40 ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {portfolioRisk.diversification_score?.toFixed(0) || '--'}/100
              </div>
            </div>
          )}
        </div>

        {/* V10.36: 投組風險警告 */}
        {portfolioRisk?.warnings?.length > 0 && (
          <div className="mb-3 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-400 text-xs">
            <span className="font-medium">風險提醒:</span>
            <ul className="mt-1 space-y-0.5">
              {portfolioRisk.warnings.map((warning, idx) => (
                <li key={idx}>- {warning}</li>
              ))}
            </ul>
          </div>
        )}

        {simData.holdings.length > 0 ? (
          <div className="space-y-2">
            {simData.holdings.map(holding => {
              const stock = MOCK_STOCKS.find(s => s.id === holding.stockId);
              const currentPrice = stock?.price || holding.avgPrice;
              const marketValue = currentPrice * holding.quantity;
              const pnl = (currentPrice - holding.avgPrice) * holding.quantity;
              const pnlPercent = ((currentPrice - holding.avgPrice) / holding.avgPrice) * 100;

              return (
                <div key={holding.stockId} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div>
                    <span className="text-white font-medium">{holding.stockName}</span>
                    <span className="text-slate-500 text-sm ml-2">{holding.stockId}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-slate-400 text-sm">
                      {holding.quantity.toLocaleString()} 股 @ ${holding.avgPrice}
                    </div>
                    <div className={pnl >= 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {pnl >= 0 ? '+' : ''}{formatMoney(pnl)} ({pnlPercent.toFixed(2)}%)
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-6 text-slate-500">
            尚無持倉
          </div>
        )}
      </div>

      {/* 交易歷史 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-medium">交易紀錄</h3>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-blue-400 text-sm hover:underline"
          >
            {showHistory ? '收起' : `查看全部 (${simData.transactions.length})`}
          </button>
        </div>

        {(showHistory ? simData.transactions : simData.transactions.slice(0, 5)).map(tx => (
          <div key={tx.id} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
            <div className="flex items-center gap-3">
              <span className={`px-2 py-0.5 rounded text-xs ${
                tx.type === 'buy' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
              }`}>
                {tx.type === 'buy' ? '買進' : '賣出'}
              </span>
              <span className="text-white">{tx.stockName}</span>
              <span className="text-slate-500 text-sm">{tx.quantity.toLocaleString()} 股 @ ${tx.price}</span>
            </div>
            <div className="text-right">
              <div className="text-slate-400 text-xs">{formatDate(tx.date)}</div>
              {tx.pnl !== undefined && (
                <div className={tx.pnl >= 0 ? 'text-red-400 text-sm' : 'text-emerald-400 text-sm'}>
                  {tx.pnl >= 0 ? '+' : ''}{formatMoney(tx.pnl)}
                </div>
              )}
            </div>
          </div>
        ))}

        {simData.transactions.length === 0 && (
          <div className="text-center py-6 text-slate-500">
            尚無交易紀錄
          </div>
        )}
      </div>

      {/* 說明 */}
      <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-blue-400">💡</span>
          <div className="text-blue-300 text-sm">
            <p className="font-medium mb-1">模擬交易說明</p>
            <ul className="text-xs space-y-0.5 text-blue-300/80">
              <li>- 初始資金 100 萬元，股價為模擬數據</li>
              <li>- 手續費 0.1425%，賣出另計證交稅 0.3%</li>
              <li>- 用於練習交易策略，不涉及真實金錢</li>
              <li>- 數據僅供練習參考，不代表實際市場</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationTrading;
