/**
 * StockBuddy V10.20 - 交易記錄管理組件
 * 提供完整的交易記錄與持股分析功能
 *
 * 功能：
 * - 新增/編輯/刪除交易記錄
 * - 持股損益計算（平均成本法）
 * - 股息記錄
 * - 交易統計報表
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { API_BASE } from '../config';

// 交易類型配置
const TRANSACTION_TYPES = [
  { type: 'buy', label: '買入', icon: '📈', color: '#ef4444' },
  { type: 'sell', label: '賣出', icon: '📉', color: '#22c55e' },
  { type: 'dividend', label: '股息', icon: '💰', color: '#f59e0b' },
];

// localStorage key
const STORAGE_KEY = 'stockbuddy_transactions';

export default function TransactionManager({ onSelectStock }) {
  // 交易記錄
  const [transactions, setTransactions] = useState([]);

  // 持股分析結果
  const [analysis, setAnalysis] = useState(null);

  // 交易摘要
  const [summary, setSummary] = useState(null);

  // UI 狀態
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [activeTab, setActiveTab] = useState('holdings'); // holdings, transactions, summary

  // 表單狀態
  const [formData, setFormData] = useState({
    stock_id: '',
    name: '',
    type: 'buy',
    shares: '',
    price: '',
    fee: '',
    tax: '',
    date: new Date().toISOString().split('T')[0],
    note: '',
  });

  // 費用計算結果
  const [feeCalc, setFeeCalc] = useState(null);

  // 載入交易記錄
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setTransactions(parsed);
      } catch (e) {
        console.error('載入交易記錄失敗:', e);
      }
    }
  }, []);

  // 儲存交易記錄
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(transactions));
  }, [transactions]);

  // 分析持股
  const analyzeHoldings = useCallback(async () => {
    if (transactions.length === 0) {
      setAnalysis(null);
      setSummary(null);
      return;
    }

    setLoading(true);
    try {
      // 分析持股損益
      const analysisRes = await fetch(`${API_BASE}/api/stocks/transactions/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transactions }),
      });
      const analysisData = await analysisRes.json();
      if (analysisData.success) {
        setAnalysis(analysisData);
      }

      // 取得交易摘要
      const summaryRes = await fetch(`${API_BASE}/api/stocks/transactions/summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transactions }),
      });
      const summaryData = await summaryRes.json();
      if (summaryData.success) {
        setSummary(summaryData);
      }
    } catch (error) {
      console.error('分析持股失敗:', error);
    } finally {
      setLoading(false);
    }
  }, [transactions]);

  // 交易記錄變更時重新分析
  useEffect(() => {
    if (transactions.length > 0) {
      analyzeHoldings();
    }
  }, [transactions, analyzeHoldings]);

  // 計算手續費
  const calculateFee = async () => {
    const { type, shares, price } = formData;
    if (!shares || !price || type === 'dividend') {
      setFeeCalc(null);
      return;
    }

    try {
      const res = await fetch(
        `${API_BASE}/api/stocks/transactions/calculate-fee?tx_type=${type}&shares=${shares}&price=${price}`
      );
      const data = await res.json();
      if (data.success) {
        setFeeCalc(data);
        // 自動填入費用
        setFormData(prev => ({
          ...prev,
          fee: data.fee.toString(),
          tax: data.tax.toString(),
        }));
      }
    } catch (error) {
      console.error('計算費用失敗:', error);
    }
  };

  // 監聽表單變更以計算費用
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.shares && formData.price && formData.type !== 'dividend') {
        calculateFee();
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [formData.shares, formData.price, formData.type]);

  // 新增交易
  const handleSubmit = (e) => {
    e.preventDefault();

    const newTransaction = {
      id: editingId || `tx_${Date.now()}`,
      stock_id: formData.stock_id.trim(),
      name: formData.name.trim() || formData.stock_id.trim(),
      type: formData.type,
      shares: parseFloat(formData.shares) || 0,
      price: parseFloat(formData.price) || 0,
      fee: parseFloat(formData.fee) || 0,
      tax: parseFloat(formData.tax) || 0,
      date: formData.date,
      note: formData.note.trim(),
      created_at: new Date().toISOString(),
    };

    if (editingId) {
      // 更新現有交易
      setTransactions(prev =>
        prev.map(t => t.id === editingId ? newTransaction : t)
      );
    } else {
      // 新增交易
      setTransactions(prev => [...prev, newTransaction]);
    }

    // 重設表單
    resetForm();
  };

  // 重設表單
  const resetForm = () => {
    setFormData({
      stock_id: '',
      name: '',
      type: 'buy',
      shares: '',
      price: '',
      fee: '',
      tax: '',
      date: new Date().toISOString().split('T')[0],
      note: '',
    });
    setFeeCalc(null);
    setShowForm(false);
    setEditingId(null);
  };

  // 編輯交易
  const handleEdit = (tx) => {
    setFormData({
      stock_id: tx.stock_id,
      name: tx.name,
      type: tx.type,
      shares: tx.shares.toString(),
      price: tx.price.toString(),
      fee: tx.fee.toString(),
      tax: tx.tax.toString(),
      date: tx.date,
      note: tx.note || '',
    });
    setEditingId(tx.id);
    setShowForm(true);
  };

  // 刪除交易
  const handleDelete = (id) => {
    if (window.confirm('確定要刪除這筆交易記錄嗎？')) {
      setTransactions(prev => prev.filter(t => t.id !== id));
    }
  };

  // 格式化金額
  const formatMoney = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // 格式化百分比
  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  // 取得損益顏色
  const getProfitColor = (value) => {
    if (value > 0) return '#22c55e';
    if (value < 0) return '#ef4444';
    return '#6b7280';
  };

  // 排序後的交易記錄
  const sortedTransactions = useMemo(() => {
    return [...transactions].sort((a, b) =>
      new Date(b.date) - new Date(a.date)
    );
  }, [transactions]);

  return (
    <div style={{
      backgroundColor: '#1a1a2e',
      borderRadius: 12,
      padding: 20,
      minHeight: 400,
    }}>
      {/* 標題列 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
      }}>
        <h2 style={{ margin: 0, fontSize: 20, color: '#fff' }}>
          📊 交易記錄管理
        </h2>
        <button
          onClick={() => setShowForm(true)}
          style={{
            padding: '8px 16px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          + 新增交易
        </button>
      </div>

      {/* 標籤切換 */}
      <div style={{
        display: 'flex',
        gap: 8,
        marginBottom: 20,
      }}>
        {[
          { id: 'holdings', label: '📈 持股損益' },
          { id: 'transactions', label: '📋 交易記錄' },
          { id: 'summary', label: '📊 統計摘要' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '8px 16px',
              backgroundColor: activeTab === tab.id ? '#3b82f6' : '#2d2d44',
              color: activeTab === tab.id ? '#fff' : '#a0a0b0',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 載入中 */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
          分析中...
        </div>
      )}

      {/* 持股損益 */}
      {!loading && activeTab === 'holdings' && (
        <div>
          {/* 總覽卡片 */}
          {analysis?.summary && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: 12,
              marginBottom: 20,
            }}>
              <div style={{
                backgroundColor: '#2d2d44',
                padding: 16,
                borderRadius: 8,
                textAlign: 'center',
              }}>
                <div style={{ color: '#888', fontSize: 12 }}>持股檔數</div>
                <div style={{ color: '#fff', fontSize: 24, fontWeight: 600 }}>
                  {analysis.summary.total_stocks}
                </div>
              </div>
              <div style={{
                backgroundColor: '#2d2d44',
                padding: 16,
                borderRadius: 8,
                textAlign: 'center',
              }}>
                <div style={{ color: '#888', fontSize: 12 }}>總成本</div>
                <div style={{ color: '#fff', fontSize: 18, fontWeight: 600 }}>
                  {formatMoney(analysis.summary.total_cost)}
                </div>
              </div>
              <div style={{
                backgroundColor: '#2d2d44',
                padding: 16,
                borderRadius: 8,
                textAlign: 'center',
              }}>
                <div style={{ color: '#888', fontSize: 12 }}>總市值</div>
                <div style={{ color: '#fff', fontSize: 18, fontWeight: 600 }}>
                  {formatMoney(analysis.summary.total_market_value)}
                </div>
              </div>
              <div style={{
                backgroundColor: '#2d2d44',
                padding: 16,
                borderRadius: 8,
                textAlign: 'center',
              }}>
                <div style={{ color: '#888', fontSize: 12 }}>總損益</div>
                <div style={{
                  color: getProfitColor(analysis.summary.total_return),
                  fontSize: 18,
                  fontWeight: 600,
                }}>
                  {formatMoney(analysis.summary.total_return)}
                  <span style={{ fontSize: 12, marginLeft: 4 }}>
                    ({formatPercent(analysis.summary.total_return_percent)})
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 持股列表 */}
          {analysis?.holdings?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {analysis.holdings.map(holding => (
                <div
                  key={holding.stock_id}
                  onClick={() => onSelectStock?.(holding.stock_id)}
                  style={{
                    backgroundColor: '#2d2d44',
                    padding: 16,
                    borderRadius: 8,
                    cursor: 'pointer',
                    transition: 'transform 0.2s',
                  }}
                  onMouseOver={e => e.currentTarget.style.transform = 'scale(1.01)'}
                  onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 12,
                  }}>
                    <div>
                      <span style={{ color: '#fff', fontWeight: 600, fontSize: 16 }}>
                        {holding.name}
                      </span>
                      <span style={{ color: '#888', marginLeft: 8 }}>
                        {holding.stock_id}
                      </span>
                    </div>
                    <div style={{
                      color: getProfitColor(holding.unrealized_percent),
                      fontWeight: 600,
                      fontSize: 18,
                    }}>
                      {formatPercent(holding.unrealized_percent)}
                    </div>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: 12,
                    fontSize: 13,
                  }}>
                    <div>
                      <div style={{ color: '#888' }}>持股</div>
                      <div style={{ color: '#fff' }}>{holding.shares.toLocaleString()} 股</div>
                    </div>
                    <div>
                      <div style={{ color: '#888' }}>均價</div>
                      <div style={{ color: '#fff' }}>${holding.avg_cost}</div>
                    </div>
                    <div>
                      <div style={{ color: '#888' }}>現價</div>
                      <div style={{ color: '#fff' }}>${holding.current_price || '-'}</div>
                    </div>
                    <div>
                      <div style={{ color: '#888' }}>未實現損益</div>
                      <div style={{ color: getProfitColor(holding.unrealized_profit) }}>
                        {formatMoney(holding.unrealized_profit)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
              {transactions.length === 0 ? '尚無交易記錄' : '目前無持股'}
            </div>
          )}
        </div>
      )}

      {/* 交易記錄 */}
      {!loading && activeTab === 'transactions' && (
        <div>
          {sortedTransactions.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#2d2d44' }}>
                    <th style={{ padding: 12, textAlign: 'left', color: '#888' }}>日期</th>
                    <th style={{ padding: 12, textAlign: 'left', color: '#888' }}>股票</th>
                    <th style={{ padding: 12, textAlign: 'center', color: '#888' }}>類型</th>
                    <th style={{ padding: 12, textAlign: 'right', color: '#888' }}>股數</th>
                    <th style={{ padding: 12, textAlign: 'right', color: '#888' }}>價格</th>
                    <th style={{ padding: 12, textAlign: 'right', color: '#888' }}>金額</th>
                    <th style={{ padding: 12, textAlign: 'center', color: '#888' }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedTransactions.map(tx => {
                    const typeConfig = TRANSACTION_TYPES.find(t => t.type === tx.type);
                    const amount = tx.shares * tx.price;

                    return (
                      <tr
                        key={tx.id}
                        style={{ borderBottom: '1px solid #3d3d54' }}
                      >
                        <td style={{ padding: 12, color: '#fff' }}>{tx.date}</td>
                        <td style={{ padding: 12 }}>
                          <span style={{ color: '#fff' }}>{tx.name}</span>
                          <span style={{ color: '#888', marginLeft: 6 }}>{tx.stock_id}</span>
                        </td>
                        <td style={{ padding: 12, textAlign: 'center' }}>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '4px 8px',
                            backgroundColor: typeConfig?.color + '20',
                            color: typeConfig?.color,
                            borderRadius: 4,
                            fontSize: 12,
                          }}>
                            {typeConfig?.icon} {typeConfig?.label}
                          </span>
                        </td>
                        <td style={{ padding: 12, textAlign: 'right', color: '#fff' }}>
                          {tx.shares.toLocaleString()}
                        </td>
                        <td style={{ padding: 12, textAlign: 'right', color: '#fff' }}>
                          ${tx.price}
                        </td>
                        <td style={{ padding: 12, textAlign: 'right', color: '#fff' }}>
                          {formatMoney(amount)}
                        </td>
                        <td style={{ padding: 12, textAlign: 'center' }}>
                          <button
                            onClick={() => handleEdit(tx)}
                            style={{
                              padding: '4px 8px',
                              marginRight: 4,
                              backgroundColor: '#3b82f6',
                              color: '#fff',
                              border: 'none',
                              borderRadius: 4,
                              cursor: 'pointer',
                            }}
                          >
                            編輯
                          </button>
                          <button
                            onClick={() => handleDelete(tx.id)}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#ef4444',
                              color: '#fff',
                              border: 'none',
                              borderRadius: 4,
                              cursor: 'pointer',
                            }}
                          >
                            刪除
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
              尚無交易記錄，點擊上方「新增交易」開始記錄
            </div>
          )}
        </div>
      )}

      {/* 統計摘要 */}
      {!loading && activeTab === 'summary' && summary && (
        <div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 16,
            marginBottom: 20,
          }}>
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>總買入金額</div>
              <div style={{ color: '#ef4444', fontSize: 20, fontWeight: 600 }}>
                {formatMoney(summary.total_buy)}
              </div>
            </div>
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>總賣出金額</div>
              <div style={{ color: '#22c55e', fontSize: 20, fontWeight: 600 }}>
                {formatMoney(summary.total_sell)}
              </div>
            </div>
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>淨投資金額</div>
              <div style={{ color: '#fff', fontSize: 20, fontWeight: 600 }}>
                {formatMoney(summary.net_investment)}
              </div>
            </div>
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>總股息收入</div>
              <div style={{ color: '#f59e0b', fontSize: 20, fontWeight: 600 }}>
                {formatMoney(summary.total_dividends)}
              </div>
            </div>
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>總手續費</div>
              <div style={{ color: '#888', fontSize: 20, fontWeight: 600 }}>
                {formatMoney(summary.total_fee)}
              </div>
            </div>
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <div style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>總交易稅</div>
              <div style={{ color: '#888', fontSize: 20, fontWeight: 600 }}>
                {formatMoney(summary.total_tax)}
              </div>
            </div>
          </div>

          {/* 月度交易統計 */}
          {summary.transactions_by_month && Object.keys(summary.transactions_by_month).length > 0 && (
            <div style={{ backgroundColor: '#2d2d44', padding: 16, borderRadius: 8 }}>
              <h3 style={{ color: '#fff', margin: '0 0 16px 0', fontSize: 16 }}>
                月度交易統計
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {Object.entries(summary.transactions_by_month).slice(0, 6).map(([month, data]) => (
                  <div
                    key={month}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      backgroundColor: '#1a1a2e',
                      borderRadius: 6,
                    }}
                  >
                    <span style={{ color: '#fff' }}>{month}</span>
                    <div style={{ display: 'flex', gap: 16 }}>
                      <span style={{ color: '#ef4444' }}>
                        買 {formatMoney(data.buy)}
                      </span>
                      <span style={{ color: '#22c55e' }}>
                        賣 {formatMoney(data.sell)}
                      </span>
                      {data.dividends > 0 && (
                        <span style={{ color: '#f59e0b' }}>
                          息 {formatMoney(data.dividends)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 新增/編輯表單 Modal */}
      {showForm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}
        onClick={() => resetForm()}
        >
          <div
            style={{
              backgroundColor: '#1a1a2e',
              padding: 24,
              borderRadius: 12,
              width: '90%',
              maxWidth: 500,
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{ margin: '0 0 20px 0', color: '#fff' }}>
              {editingId ? '編輯交易記錄' : '新增交易記錄'}
            </h3>

            <form onSubmit={handleSubmit}>
              {/* 交易類型 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ color: '#888', fontSize: 12 }}>交易類型</label>
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  {TRANSACTION_TYPES.map(type => (
                    <button
                      key={type.type}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, type: type.type }))}
                      style={{
                        flex: 1,
                        padding: '10px 12px',
                        backgroundColor: formData.type === type.type ? type.color : '#2d2d44',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 6,
                        cursor: 'pointer',
                        fontSize: 14,
                      }}
                    >
                      {type.icon} {type.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* 股票代號與名稱 */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                <div>
                  <label style={{ color: '#888', fontSize: 12 }}>股票代號 *</label>
                  <input
                    type="text"
                    value={formData.stock_id}
                    onChange={e => setFormData(prev => ({ ...prev, stock_id: e.target.value }))}
                    placeholder="例：2330"
                    required
                    style={{
                      width: '100%',
                      padding: 10,
                      marginTop: 6,
                      backgroundColor: '#2d2d44',
                      color: '#fff',
                      border: '1px solid #3d3d54',
                      borderRadius: 6,
                    }}
                  />
                </div>
                <div>
                  <label style={{ color: '#888', fontSize: 12 }}>股票名稱</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="例：台積電"
                    style={{
                      width: '100%',
                      padding: 10,
                      marginTop: 6,
                      backgroundColor: '#2d2d44',
                      color: '#fff',
                      border: '1px solid #3d3d54',
                      borderRadius: 6,
                    }}
                  />
                </div>
              </div>

              {/* 股數與價格 */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                <div>
                  <label style={{ color: '#888', fontSize: 12 }}>
                    {formData.type === 'dividend' ? '股利張數' : '股數'} *
                  </label>
                  <input
                    type="number"
                    value={formData.shares}
                    onChange={e => setFormData(prev => ({ ...prev, shares: e.target.value }))}
                    placeholder="1000"
                    required
                    min="0"
                    step="1"
                    style={{
                      width: '100%',
                      padding: 10,
                      marginTop: 6,
                      backgroundColor: '#2d2d44',
                      color: '#fff',
                      border: '1px solid #3d3d54',
                      borderRadius: 6,
                    }}
                  />
                </div>
                <div>
                  <label style={{ color: '#888', fontSize: 12 }}>
                    {formData.type === 'dividend' ? '每股股利' : '成交價'} *
                  </label>
                  <input
                    type="number"
                    value={formData.price}
                    onChange={e => setFormData(prev => ({ ...prev, price: e.target.value }))}
                    placeholder="580"
                    required
                    min="0"
                    step="0.01"
                    style={{
                      width: '100%',
                      padding: 10,
                      marginTop: 6,
                      backgroundColor: '#2d2d44',
                      color: '#fff',
                      border: '1px solid #3d3d54',
                      borderRadius: 6,
                    }}
                  />
                </div>
              </div>

              {/* 手續費與交易稅（非股息時顯示） */}
              {formData.type !== 'dividend' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                  <div>
                    <label style={{ color: '#888', fontSize: 12 }}>手續費</label>
                    <input
                      type="number"
                      value={formData.fee}
                      onChange={e => setFormData(prev => ({ ...prev, fee: e.target.value }))}
                      placeholder="自動計算"
                      min="0"
                      step="1"
                      style={{
                        width: '100%',
                        padding: 10,
                        marginTop: 6,
                        backgroundColor: '#2d2d44',
                        color: '#fff',
                        border: '1px solid #3d3d54',
                        borderRadius: 6,
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ color: '#888', fontSize: 12 }}>交易稅</label>
                    <input
                      type="number"
                      value={formData.tax}
                      onChange={e => setFormData(prev => ({ ...prev, tax: e.target.value }))}
                      placeholder={formData.type === 'sell' ? '自動計算' : '0'}
                      min="0"
                      step="1"
                      style={{
                        width: '100%',
                        padding: 10,
                        marginTop: 6,
                        backgroundColor: '#2d2d44',
                        color: '#fff',
                        border: '1px solid #3d3d54',
                        borderRadius: 6,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* 費用計算提示 */}
              {feeCalc && formData.type !== 'dividend' && (
                <div style={{
                  backgroundColor: '#2d2d44',
                  padding: 12,
                  borderRadius: 6,
                  marginBottom: 16,
                  fontSize: 13,
                }}>
                  <div style={{ color: '#888' }}>費用試算：</div>
                  <div style={{ color: '#fff', marginTop: 4 }}>
                    成交金額 {formatMoney(feeCalc.amount)} |
                    手續費 {formatMoney(feeCalc.fee)} |
                    {formData.type === 'sell' && `交易稅 ${formatMoney(feeCalc.tax)} |`}
                    實際 {formData.type === 'buy' ? '支出' : '收入'} {formatMoney(feeCalc.total_cost)}
                  </div>
                </div>
              )}

              {/* 日期 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ color: '#888', fontSize: 12 }}>交易日期 *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={e => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  required
                  style={{
                    width: '100%',
                    padding: 10,
                    marginTop: 6,
                    backgroundColor: '#2d2d44',
                    color: '#fff',
                    border: '1px solid #3d3d54',
                    borderRadius: 6,
                  }}
                />
              </div>

              {/* 備註 */}
              <div style={{ marginBottom: 20 }}>
                <label style={{ color: '#888', fontSize: 12 }}>備註</label>
                <input
                  type="text"
                  value={formData.note}
                  onChange={e => setFormData(prev => ({ ...prev, note: e.target.value }))}
                  placeholder="例：定期定額、加碼..."
                  style={{
                    width: '100%',
                    padding: 10,
                    marginTop: 6,
                    backgroundColor: '#2d2d44',
                    color: '#fff',
                    border: '1px solid #3d3d54',
                    borderRadius: 6,
                  }}
                />
              </div>

              {/* 按鈕 */}
              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  type="button"
                  onClick={resetForm}
                  style={{
                    flex: 1,
                    padding: 12,
                    backgroundColor: '#3d3d54',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                  }}
                >
                  取消
                </button>
                <button
                  type="submit"
                  style={{
                    flex: 2,
                    padding: 12,
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  {editingId ? '更新' : '新增'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
