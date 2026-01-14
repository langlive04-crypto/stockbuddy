/**
 * PerformanceTracker.jsx - 歷史績效追蹤組件
 * V10.23 新增
 * V10.36 新增：進階統計（按週期/訊號/評分區間）
 *
 * 功能：
 * - 追蹤 AI 推薦的後續表現
 * - 顯示勝率、平均報酬率等統計
 * - 查看進行中和已關閉的推薦
 * - 每日績效圖表
 * - V10.36: 按週期、訊號、評分區間統計
 */

import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../config';

const PerformanceTracker = () => {
  const [statistics, setStatistics] = useState(null);
  const [activeRecs, setActiveRecs] = useState([]);
  const [closedRecs, setClosedRecs] = useState([]);
  const [dailyPerformance, setDailyPerformance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview'); // overview, active, closed, daily, advanced

  // V10.36: 進階統計狀態
  const [advancedStats, setAdvancedStats] = useState(null);
  const [advancedLoading, setAdvancedLoading] = useState(false);

  // 取得所有資料
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, activeRes, closedRes, dailyRes] = await Promise.all([
        fetch(`${API_BASE}/api/stocks/performance-tracker/statistics`).then(r => r.json()),
        fetch(`${API_BASE}/api/stocks/performance-tracker/active`).then(r => r.json()),
        fetch(`${API_BASE}/api/stocks/performance-tracker/closed?limit=30`).then(r => r.json()),
        fetch(`${API_BASE}/api/stocks/performance-tracker/daily?days=14`).then(r => r.json()),
      ]);

      setStatistics(statsRes.statistics);
      setActiveRecs(activeRes.recommendations || []);
      setClosedRecs(closedRes.recommendations || []);
      setDailyPerformance(dailyRes.daily_performance || []);
    } catch (err) {
      console.error('Failed to fetch performance data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // V10.36: 取得進階統計
  const fetchAdvancedStats = useCallback(async () => {
    setAdvancedLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/stocks/performance-tracker/comprehensive`);
      if (response.ok) {
        const data = await response.json();
        setAdvancedStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch advanced stats:', err);
    } finally {
      setAdvancedLoading(false);
    }
  }, []);

  // V10.36: 當切換到進階分析 tab 時載入資料
  useEffect(() => {
    if (activeTab === 'advanced' && !advancedStats && !advancedLoading) {
      fetchAdvancedStats();
    }
  }, [activeTab, advancedStats, advancedLoading, fetchAdvancedStats]);

  // 關閉推薦
  const handleClose = async (stockId, exitPrice) => {
    try {
      await fetch(`${API_BASE}/api/stocks/performance-tracker/close/${stockId}?exit_price=${exitPrice}&reason=手動關閉`, {
        method: 'POST',
      });
      fetchData();
    } catch (err) {
      console.error('Failed to close recommendation:', err);
    }
  };

  // 統計卡片組件
  const StatCard = ({ label, value, subValue, color = 'blue', icon }) => (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-slate-400 text-sm">{label}</span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold text-${color}-400`}>{value}</div>
      {subValue && <div className="text-slate-500 text-xs mt-1">{subValue}</div>}
    </div>
  );

  // 推薦卡片組件
  const RecommendationCard = ({ rec, showClose = false }) => {
    const isProfit = (rec.return_percent || rec.final_return_percent || 0) >= 0;

    return (
      <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/50">
        <div className="flex items-center justify-between mb-2">
          <div>
            <span className="text-white font-medium">{rec.name}</span>
            <span className="text-slate-500 ml-2">({rec.stock_id})</span>
          </div>
          <div className={`px-2 py-0.5 rounded text-xs font-medium ${
            rec.status === 'active' ? 'bg-blue-500/20 text-blue-400' :
            rec.status === 'closed' ? 'bg-slate-600/50 text-slate-400' :
            'bg-yellow-500/20 text-yellow-400'
          }`}>
            {rec.status === 'active' ? '追蹤中' : rec.status === 'closed' ? '已關閉' : '已過期'}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 text-sm mb-2">
          <div>
            <div className="text-slate-500 text-xs">進場價</div>
            <div className="text-white">${rec.entry_price?.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-slate-500 text-xs">
              {rec.status === 'closed' ? '出場價' : '現價'}
            </div>
            <div className="text-white">
              ${(rec.exit_price || rec.current_price)?.toLocaleString() || '-'}
            </div>
          </div>
          <div>
            <div className="text-slate-500 text-xs">報酬率</div>
            <div className={`font-medium ${isProfit ? 'text-red-400' : 'text-emerald-400'}`}>
              {isProfit ? '+' : ''}{(rec.return_percent || rec.final_return_percent || 0).toFixed(2)}%
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>推薦日期: {rec.date}</span>
          <span>持有 {rec.days_held} 天</span>
        </div>

        {rec.signal && (
          <div className="mt-2 text-xs">
            <span className={`px-2 py-0.5 rounded ${
              rec.signal.includes('買') ? 'bg-red-500/20 text-red-400' : 'bg-slate-600/50 text-slate-400'
            }`}>
              {rec.signal} (信心 {rec.confidence})
            </span>
          </div>
        )}

        {showClose && rec.status === 'active' && rec.current_price && (
          <div className="mt-3 pt-3 border-t border-slate-700">
            <button
              onClick={() => {
                if (window.confirm(`確定要以 $${rec.current_price} 關閉 ${rec.name} 的追蹤？`)) {
                  handleClose(rec.stock_id, rec.current_price);
                }
              }}
              className="w-full px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-sm transition-colors"
            >
              關閉追蹤
            </button>
          </div>
        )}
      </div>
    );
  };

  // 每日績效條
  const DailyBar = ({ data }) => {
    const maxRecs = Math.max(...dailyPerformance.map(d => d.recommendations), 1);
    const width = (data.recommendations / maxRecs) * 100;
    const winRate = data.recommendations > 0 ? (data.winners / data.recommendations * 100) : 0;

    return (
      <div className="flex items-center gap-3 py-2 border-b border-slate-700/50 last:border-0">
        <div className="w-20 text-slate-400 text-sm">{data.date.slice(5)}</div>
        <div className="flex-1">
          <div className="h-6 bg-slate-700/30 rounded-full overflow-hidden flex">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-l-full"
              style={{ width: `${winRate}%` }}
            />
            <div
              className="h-full bg-gradient-to-r from-red-500 to-red-600 rounded-r-full"
              style={{ width: `${100 - winRate}%` }}
            />
          </div>
        </div>
        <div className="w-16 text-right">
          <span className="text-white font-medium">{data.recommendations}</span>
          <span className="text-slate-500 text-sm"> 檔</span>
        </div>
        <div className={`w-20 text-right font-medium ${
          data.avg_return >= 0 ? 'text-red-400' : 'text-emerald-400'
        }`}>
          {data.avg_return >= 0 ? '+' : ''}{data.avg_return.toFixed(1)}%
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">📊 績效追蹤</h2>
          <p className="text-slate-400 text-sm">追蹤 AI 推薦的歷史表現</p>
        </div>
        <button
          onClick={fetchData}
          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
        >
          🔄 刷新
        </button>
      </div>

      {/* Tab 切換 */}
      <div className="flex gap-2 bg-slate-800/30 p-1 rounded-lg overflow-x-auto">
        {[
          { id: 'overview', label: '總覽', icon: '📈' },
          { id: 'active', label: `追蹤中 (${activeRecs.length})`, icon: '🎯' },
          { id: 'closed', label: `已關閉 (${closedRecs.length})`, icon: '✅' },
          { id: 'daily', label: '每日績效', icon: '📅' },
          { id: 'advanced', label: '進階分析', icon: '🔬' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-500/20 text-blue-400'
                : 'text-slate-400 hover:bg-slate-700/50'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* 總覽 */}
      {activeTab === 'overview' && statistics && (
        <div className="space-y-6">
          {/* 統計卡片 */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="勝率"
              value={`${statistics.win_rate}%`}
              subValue={`${statistics.closed_count} 筆已結算`}
              color={statistics.win_rate >= 50 ? 'emerald' : 'red'}
              icon="🎯"
            />
            <StatCard
              label="平均報酬"
              value={`${statistics.avg_return >= 0 ? '+' : ''}${statistics.avg_return}%`}
              subValue="所有推薦"
              color={statistics.avg_return >= 0 ? 'red' : 'emerald'}
              icon="💰"
            />
            <StatCard
              label="最佳報酬"
              value={`+${statistics.best_return}%`}
              subValue=""
              color="red"
              icon="🚀"
            />
            <StatCard
              label="最差報酬"
              value={`${statistics.worst_return}%`}
              subValue=""
              color="emerald"
              icon="📉"
            />
          </div>

          {/* 追蹤摘要 */}
          <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white font-medium mb-4">追蹤摘要</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold text-white">{statistics.total_recommendations}</div>
                <div className="text-slate-400 text-sm">總推薦數</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-400">{statistics.active_count}</div>
                <div className="text-slate-400 text-sm">進行中</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-400">{statistics.closed_count}</div>
                <div className="text-slate-400 text-sm">已結算</div>
              </div>
            </div>
          </div>

          {/* 最近表現最好/最差的推薦 */}
          <div className="grid lg:grid-cols-2 gap-4">
            {/* 表現最好 */}
            <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <span className="text-lg">🏆</span> 表現最佳
              </h3>
              {activeRecs.filter(r => r.return_percent > 0).slice(0, 3).map((rec, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                  <span className="text-white">{rec.name}</span>
                  <span className="text-red-400 font-medium">+{rec.return_percent?.toFixed(2)}%</span>
                </div>
              ))}
              {activeRecs.filter(r => r.return_percent > 0).length === 0 && (
                <div className="text-slate-500 text-sm text-center py-4">暫無獲利推薦</div>
              )}
            </div>

            {/* 表現最差 */}
            <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <span className="text-lg">⚠️</span> 需關注
              </h3>
              {activeRecs.filter(r => r.return_percent < 0).slice(-3).reverse().map((rec, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                  <span className="text-white">{rec.name}</span>
                  <span className="text-emerald-400 font-medium">{rec.return_percent?.toFixed(2)}%</span>
                </div>
              ))}
              {activeRecs.filter(r => r.return_percent < 0).length === 0 && (
                <div className="text-slate-500 text-sm text-center py-4">暫無虧損推薦</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 進行中 */}
      {activeTab === 'active' && (
        <div className="space-y-4">
          {activeRecs.length > 0 ? (
            <div className="grid lg:grid-cols-2 gap-4">
              {activeRecs.map((rec, i) => (
                <RecommendationCard key={i} rec={rec} showClose={true} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <p className="text-xl mb-2">📭</p>
              <p>目前沒有追蹤中的推薦</p>
            </div>
          )}
        </div>
      )}

      {/* 已關閉 */}
      {activeTab === 'closed' && (
        <div className="space-y-4">
          {closedRecs.length > 0 ? (
            <div className="grid lg:grid-cols-2 gap-4">
              {closedRecs.map((rec, i) => (
                <RecommendationCard key={i} rec={rec} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <p className="text-xl mb-2">📭</p>
              <p>目前沒有已關閉的推薦</p>
            </div>
          )}
        </div>
      )}

      {/* 每日績效 */}
      {activeTab === 'daily' && (
        <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
          <h3 className="text-white font-medium mb-4">每日績效</h3>
          {dailyPerformance.length > 0 ? (
            <div>
              <div className="flex items-center gap-3 pb-2 mb-2 border-b border-slate-700 text-xs text-slate-500">
                <div className="w-20">日期</div>
                <div className="flex-1">
                  <span className="text-emerald-400">獲利</span>
                  <span className="mx-2">/</span>
                  <span className="text-red-400">虧損</span>
                </div>
                <div className="w-16 text-right">推薦數</div>
                <div className="w-20 text-right">平均報酬</div>
              </div>
              {dailyPerformance.map((data, i) => (
                <DailyBar key={i} data={data} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>暫無每日績效資料</p>
            </div>
          )}
        </div>
      )}

      {/* V10.36: 進階分析 */}
      {activeTab === 'advanced' && (
        <div className="space-y-6">
          {advancedLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : advancedStats ? (
            <>
              {/* 按追蹤週期統計 */}
              <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
                <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                  <span>⏱️</span> 按追蹤週期統計
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {advancedStats.by_period && Object.entries(advancedStats.by_period).map(([period, data]) => (
                    <div key={period} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                      <div className="text-lg font-bold text-white mb-2">{period} 天</div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-400">樣本數</span>
                          <span className="text-white">{data.count || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">勝率</span>
                          <span className={`font-medium ${(data.win_rate || 0) >= 50 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(data.win_rate || 0).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">平均報酬</span>
                          <span className={`font-medium ${(data.avg_return || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(data.avg_return || 0) >= 0 ? '+' : ''}{(data.avg_return || 0).toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  {(!advancedStats.by_period || Object.keys(advancedStats.by_period).length === 0) && (
                    <div className="col-span-3 text-center text-slate-500 py-4">尚無週期統計資料</div>
                  )}
                </div>
              </div>

              {/* 按訊號類型統計 */}
              <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
                <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                  <span>🏷️</span> 按訊號類型統計
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left text-slate-400 py-2 px-2">訊號</th>
                        <th className="text-center text-slate-400 py-2 px-2">推薦數</th>
                        <th className="text-center text-slate-400 py-2 px-2">勝率</th>
                        <th className="text-center text-slate-400 py-2 px-2">平均報酬</th>
                      </tr>
                    </thead>
                    <tbody>
                      {advancedStats.by_signal && Object.entries(advancedStats.by_signal).map(([signal, data]) => (
                        <tr key={signal} className="border-b border-slate-700/50">
                          <td className="py-2 px-2">
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              signal.includes('買') ? 'bg-red-500/20 text-red-400' :
                              signal.includes('賣') ? 'bg-emerald-500/20 text-emerald-400' :
                              'bg-slate-600/50 text-slate-400'
                            }`}>
                              {signal}
                            </span>
                          </td>
                          <td className="text-center text-white py-2 px-2">{data.count || 0}</td>
                          <td className={`text-center py-2 px-2 font-medium ${
                            (data.win_rate || 0) >= 50 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {(data.win_rate || 0).toFixed(1)}%
                          </td>
                          <td className={`text-center py-2 px-2 font-medium ${
                            (data.avg_return || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {(data.avg_return || 0) >= 0 ? '+' : ''}{(data.avg_return || 0).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                      {(!advancedStats.by_signal || Object.keys(advancedStats.by_signal).length === 0) && (
                        <tr>
                          <td colSpan="4" className="text-center text-slate-500 py-4">尚無訊號統計資料</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 按評分區間統計 */}
              <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
                <h3 className="text-white font-medium mb-4 flex items-center gap-2">
                  <span>📊</span> 按評分區間統計
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {advancedStats.by_score_range && Object.entries(advancedStats.by_score_range).map(([range, data]) => (
                    <div key={range} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                      <div className="text-sm font-medium text-blue-400 mb-2">{range}</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-slate-400">推薦數</span>
                          <span className="text-white">{data.count || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">勝率</span>
                          <span className={`${(data.win_rate || 0) >= 50 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(data.win_rate || 0).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">平均報酬</span>
                          <span className={`${(data.avg_return || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(data.avg_return || 0) >= 0 ? '+' : ''}{(data.avg_return || 0).toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  {(!advancedStats.by_score_range || Object.keys(advancedStats.by_score_range).length === 0) && (
                    <div className="col-span-4 text-center text-slate-500 py-4">尚無評分區間統計資料</div>
                  )}
                </div>
              </div>

              {/* 重新載入 */}
              <div className="text-center">
                <button
                  onClick={fetchAdvancedStats}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
                >
                  🔄 重新載入進階統計
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <p className="text-xl mb-2">📊</p>
              <p>無法載入進階統計</p>
              <button
                onClick={fetchAdvancedStats}
                className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors"
              >
                重試
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PerformanceTracker;
