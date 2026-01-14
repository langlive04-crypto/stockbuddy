/**
 * HistoricalPerformance.jsx - 歷史績效驗證
 * V10.31 新增
 * V10.35.2 更新：添加數據來源標示
 *
 * 功能：
 * - AI 推薦歷史準確率統計
 * - 推薦勝率統計
 * - 平均報酬率統計
 * - 績效曲線圖表
 */

import React, { useState, useMemo } from 'react';

// 數據來源標示組件
const DataSourceBadge = ({ isDemo = true }) => (
  <span className={`px-2 py-0.5 rounded text-xs ${
    isDemo
      ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
  }`}>
    {isDemo ? '示範數據' : '即時數據'}
  </span>
);

// 模擬歷史推薦數據
const MOCK_HISTORY_DATA = [
  { date: '2026-01-09', stockId: '2330', name: '台積電', signal: '強力買進', entryPrice: 985, currentPrice: 1015, confidence: 92, status: 'win' },
  { date: '2026-01-09', stockId: '2454', name: '聯發科', signal: '買進', entryPrice: 1180, currentPrice: 1210, confidence: 85, status: 'win' },
  { date: '2026-01-08', stockId: '2317', name: '鴻海', signal: '買進', entryPrice: 108, currentPrice: 105, confidence: 78, status: 'lose' },
  { date: '2026-01-08', stockId: '2412', name: '中華電', signal: '持有', entryPrice: 122, currentPrice: 123, confidence: 72, status: 'hold' },
  { date: '2026-01-07', stockId: '3008', name: '大立光', signal: '強力買進', entryPrice: 2200, currentPrice: 2350, confidence: 88, status: 'win' },
  { date: '2026-01-07', stockId: '2303', name: '聯電', signal: '買進', entryPrice: 52, currentPrice: 54, confidence: 80, status: 'win' },
  { date: '2026-01-06', stockId: '2881', name: '富邦金', signal: '持有', entryPrice: 72, currentPrice: 71, confidence: 65, status: 'hold' },
  { date: '2026-01-06', stockId: '2882', name: '國泰金', signal: '買進', entryPrice: 58, currentPrice: 60, confidence: 75, status: 'win' },
  { date: '2026-01-05', stockId: '1301', name: '台塑', signal: '買進', entryPrice: 75, currentPrice: 73, confidence: 70, status: 'lose' },
  { date: '2026-01-05', stockId: '2308', name: '台達電', signal: '強力買進', entryPrice: 340, currentPrice: 365, confidence: 90, status: 'win' },
  { date: '2026-01-04', stockId: '2002', name: '中鋼', signal: '持有', entryPrice: 26, currentPrice: 26.5, confidence: 68, status: 'hold' },
  { date: '2026-01-04', stockId: '3711', name: '日月光投控', signal: '買進', entryPrice: 145, currentPrice: 152, confidence: 82, status: 'win' },
  { date: '2026-01-03', stockId: '6505', name: '台塑化', signal: '買進', entryPrice: 88, currentPrice: 85, confidence: 73, status: 'lose' },
  { date: '2026-01-03', stockId: '2912', name: '統一超', signal: '持有', entryPrice: 268, currentPrice: 275, confidence: 77, status: 'win' },
  { date: '2026-01-02', stockId: '2357', name: '華碩', signal: '強力買進', entryPrice: 485, currentPrice: 520, confidence: 89, status: 'win' },
];

// 信號類型顏色
const SIGNAL_COLORS = {
  '強力買進': 'text-red-400 bg-red-500/20',
  '買進': 'text-orange-400 bg-orange-500/20',
  '持有': 'text-yellow-400 bg-yellow-500/20',
  '賣出': 'text-blue-400 bg-blue-500/20',
  '強力賣出': 'text-emerald-400 bg-emerald-500/20',
};

// 狀態顏色
const STATUS_COLORS = {
  win: 'text-red-400',
  lose: 'text-emerald-400',
  hold: 'text-slate-400',
};

const HistoricalPerformance = () => {
  const [timeRange, setTimeRange] = useState('week'); // week, month, quarter
  const [signalFilter, setSignalFilter] = useState('all'); // all, strong-buy, buy, hold

  // 計算統計數據
  const stats = useMemo(() => {
    const buySignals = MOCK_HISTORY_DATA.filter(d =>
      d.signal === '強力買進' || d.signal === '買進'
    );

    const totalTrades = buySignals.length;
    const winTrades = buySignals.filter(d => d.status === 'win').length;
    const loseTrades = buySignals.filter(d => d.status === 'lose').length;

    // 勝率
    const winRate = totalTrades > 0 ? (winTrades / totalTrades * 100) : 0;

    // 平均報酬率
    const avgReturn = buySignals.reduce((acc, d) => {
      const returnPct = ((d.currentPrice - d.entryPrice) / d.entryPrice) * 100;
      return acc + returnPct;
    }, 0) / (totalTrades || 1);

    // 最大獲利
    const maxWin = Math.max(...buySignals.map(d =>
      ((d.currentPrice - d.entryPrice) / d.entryPrice) * 100
    ));

    // 最大虧損
    const maxLoss = Math.min(...buySignals.map(d =>
      ((d.currentPrice - d.entryPrice) / d.entryPrice) * 100
    ));

    // 依信號分類的勝率
    const strongBuyStats = MOCK_HISTORY_DATA.filter(d => d.signal === '強力買進');
    const strongBuyWinRate = strongBuyStats.length > 0
      ? (strongBuyStats.filter(d => d.status === 'win').length / strongBuyStats.length * 100)
      : 0;

    const buyStats = MOCK_HISTORY_DATA.filter(d => d.signal === '買進');
    const buyWinRate = buyStats.length > 0
      ? (buyStats.filter(d => d.status === 'win').length / buyStats.length * 100)
      : 0;

    // 依信心度分層的勝率
    const highConfidence = MOCK_HISTORY_DATA.filter(d => d.confidence >= 85);
    const highConfidenceWinRate = highConfidence.length > 0
      ? (highConfidence.filter(d => d.status === 'win').length / highConfidence.length * 100)
      : 0;

    const medConfidence = MOCK_HISTORY_DATA.filter(d => d.confidence >= 70 && d.confidence < 85);
    const medConfidenceWinRate = medConfidence.length > 0
      ? (medConfidence.filter(d => d.status === 'win').length / medConfidence.length * 100)
      : 0;

    return {
      totalTrades,
      winTrades,
      loseTrades,
      winRate,
      avgReturn,
      maxWin,
      maxLoss,
      strongBuyWinRate,
      buyWinRate,
      highConfidenceWinRate,
      medConfidenceWinRate,
    };
  }, []);

  // 篩選數據
  const filteredData = useMemo(() => {
    let data = [...MOCK_HISTORY_DATA];

    if (signalFilter !== 'all') {
      if (signalFilter === 'strong-buy') {
        data = data.filter(d => d.signal === '強力買進');
      } else if (signalFilter === 'buy') {
        data = data.filter(d => d.signal === '買進');
      } else if (signalFilter === 'hold') {
        data = data.filter(d => d.signal === '持有');
      }
    }

    return data;
  }, [signalFilter]);

  // 績效曲線數據
  const performanceChartData = useMemo(() => {
    const dates = [...new Set(MOCK_HISTORY_DATA.map(d => d.date))].sort();
    let cumulativeReturn = 0;

    return dates.map(date => {
      const dayTrades = MOCK_HISTORY_DATA.filter(d => d.date === date && (d.signal === '強力買進' || d.signal === '買進'));
      const dayReturn = dayTrades.reduce((acc, d) => {
        return acc + ((d.currentPrice - d.entryPrice) / d.entryPrice) * 100;
      }, 0) / (dayTrades.length || 1);

      cumulativeReturn += dayReturn;

      return {
        date: date.slice(5), // MM-DD
        dailyReturn: dayReturn,
        cumulativeReturn,
      };
    });
  }, []);

  // 找出最大值用於縮放
  const maxCumulative = Math.max(...performanceChartData.map(d => d.cumulativeReturn), 0);
  const minCumulative = Math.min(...performanceChartData.map(d => d.cumulativeReturn), 0);
  const chartRange = Math.max(maxCumulative, Math.abs(minCumulative)) || 10;

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📊</span>
            <span>AI 推薦歷史績效驗證</span>
          </h2>
          <DataSourceBadge isDemo={true} />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-slate-700 text-white px-3 py-1.5 rounded-lg border border-slate-600 text-sm"
          >
            <option value="week">近一週</option>
            <option value="month">近一月</option>
            <option value="quarter">近一季</option>
          </select>

          <select
            value={signalFilter}
            onChange={(e) => setSignalFilter(e.target.value)}
            className="bg-slate-700 text-white px-3 py-1.5 rounded-lg border border-slate-600 text-sm"
          >
            <option value="all">全部信號</option>
            <option value="strong-buy">強力買進</option>
            <option value="buy">買進</option>
            <option value="hold">持有</option>
          </select>
        </div>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">總勝率</div>
          <div className="text-2xl font-bold text-white">{stats.winRate.toFixed(1)}%</div>
          <div className="text-xs text-slate-500 mt-1">
            {stats.winTrades}勝 / {stats.loseTrades}敗
          </div>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">平均報酬</div>
          <div className={`text-2xl font-bold ${stats.avgReturn >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {stats.avgReturn >= 0 ? '+' : ''}{stats.avgReturn.toFixed(2)}%
          </div>
          <div className="text-xs text-slate-500 mt-1">每筆交易</div>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">最大獲利</div>
          <div className="text-2xl font-bold text-red-400">
            +{stats.maxWin.toFixed(2)}%
          </div>
          <div className="text-xs text-slate-500 mt-1">單筆最佳</div>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-4">
          <div className="text-slate-400 text-sm mb-1">最大虧損</div>
          <div className="text-2xl font-bold text-emerald-400">
            {stats.maxLoss.toFixed(2)}%
          </div>
          <div className="text-xs text-slate-500 mt-1">單筆最差</div>
        </div>
      </div>

      {/* 分層勝率分析 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* 依信號類型 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">依信號類型勝率</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-red-400">強力買進</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full"
                    style={{ width: `${stats.strongBuyWinRate}%` }}
                  />
                </div>
                <span className="text-white text-sm w-12 text-right">{stats.strongBuyWinRate.toFixed(0)}%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-orange-400">買進</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 rounded-full"
                    style={{ width: `${stats.buyWinRate}%` }}
                  />
                </div>
                <span className="text-white text-sm w-12 text-right">{stats.buyWinRate.toFixed(0)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* 依信心度 */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">依信心度勝率</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-blue-400">高信心度 (85+)</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${stats.highConfidenceWinRate}%` }}
                  />
                </div>
                <span className="text-white text-sm w-12 text-right">{stats.highConfidenceWinRate.toFixed(0)}%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-purple-400">中信心度 (70-84)</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-slate-600 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full"
                    style={{ width: `${stats.medConfidenceWinRate}%` }}
                  />
                </div>
                <span className="text-white text-sm w-12 text-right">{stats.medConfidenceWinRate.toFixed(0)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 累積績效曲線 */}
      <div className="bg-slate-700/30 rounded-lg p-4 mb-6">
        <h3 className="text-white font-medium mb-3">累積報酬率曲線</h3>
        <div className="h-40 flex items-end gap-1">
          {performanceChartData.map((d, idx) => {
            const height = ((d.cumulativeReturn + chartRange) / (chartRange * 2)) * 100;
            const isPositive = d.cumulativeReturn >= 0;

            return (
              <div key={idx} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full relative"
                  style={{ height: '100%' }}
                >
                  <div
                    className={`absolute bottom-1/2 left-0 right-0 ${isPositive ? 'bg-red-500/80' : 'bg-emerald-500/80'} rounded-sm`}
                    style={{
                      height: `${Math.abs(d.cumulativeReturn) / chartRange * 50}%`,
                      bottom: isPositive ? '50%' : 'auto',
                      top: isPositive ? 'auto' : '50%'
                    }}
                    title={`${d.date}: ${d.cumulativeReturn >= 0 ? '+' : ''}${d.cumulativeReturn.toFixed(2)}%`}
                  />
                  {/* 零軸線 */}
                  <div className="absolute left-0 right-0 h-px bg-slate-500" style={{ top: '50%' }} />
                </div>
                <span className="text-xs text-slate-500 mt-1">{d.date}</span>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-slate-500 mt-2">
          <span>累積報酬: {performanceChartData[performanceChartData.length - 1]?.cumulativeReturn.toFixed(2) || 0}%</span>
          <span>交易日數: {performanceChartData.length}</span>
        </div>
      </div>

      {/* 歷史推薦明細 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3">推薦明細</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-slate-400 text-sm border-b border-slate-600">
                <th className="text-left py-2 px-2">日期</th>
                <th className="text-left py-2 px-2">股票</th>
                <th className="text-center py-2 px-2">信號</th>
                <th className="text-right py-2 px-2">進場價</th>
                <th className="text-right py-2 px-2">現價</th>
                <th className="text-right py-2 px-2">報酬率</th>
                <th className="text-center py-2 px-2">結果</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((item, idx) => {
                const returnPct = ((item.currentPrice - item.entryPrice) / item.entryPrice) * 100;
                return (
                  <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="py-2 px-2 text-slate-400 text-sm">{item.date}</td>
                    <td className="py-2 px-2">
                      <div className="text-white text-sm">{item.name}</div>
                      <div className="text-slate-500 text-xs">{item.stockId}</div>
                    </td>
                    <td className="py-2 px-2 text-center">
                      <span className={`px-2 py-0.5 rounded text-xs ${SIGNAL_COLORS[item.signal]}`}>
                        {item.signal}
                      </span>
                    </td>
                    <td className="py-2 px-2 text-right text-slate-300 text-sm">
                      ${item.entryPrice}
                    </td>
                    <td className="py-2 px-2 text-right text-white text-sm">
                      ${item.currentPrice}
                    </td>
                    <td className={`py-2 px-2 text-right text-sm ${returnPct >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
                    </td>
                    <td className={`py-2 px-2 text-center text-sm ${STATUS_COLORS[item.status]}`}>
                      {item.status === 'win' ? '獲利' : item.status === 'lose' ? '虧損' : '持平'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 說明 */}
      <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <span className="text-blue-400">ℹ️</span>
          <div className="text-blue-300 text-sm">
            <p className="font-medium mb-1">績效驗證說明</p>
            <ul className="text-xs space-y-0.5 text-blue-300/80">
              <li>- 勝率計算：只計入「買進」與「強力買進」信號</li>
              <li>- 獲利定義：現價高於進場價</li>
              <li>- 數據來源：系統自動記錄 AI 推薦</li>
              <li>- 此數據僅供參考，不構成投資建議</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoricalPerformance;
