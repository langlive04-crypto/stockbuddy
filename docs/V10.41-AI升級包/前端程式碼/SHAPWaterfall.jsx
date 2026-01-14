/**
 * SHAP Waterfall Chart Component V10.41
 *
 * 顯示 AI 預測的特徵貢獻瀑布圖
 *
 * 安裝位置: stockbuddy-frontend/src/components/SHAPWaterfall.jsx
 *
 * 使用方式:
 * <SHAPWaterfall stockId="2330" />
 */

import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  Tooltip,
  ReferenceLine
} from 'recharts';

// API 基礎路徑
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * 取得特徵解釋資料
 */
async function fetchExplanation(stockId) {
  const response = await fetch(`${API_BASE}/api/stocks/ml/explain/${stockId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch explanation');
  }
  return response.json();
}

/**
 * 特徵名稱中文對照
 */
const FEATURE_LABELS = {
  rsi_14: 'RSI (14日)',
  macd_signal: 'MACD 信號',
  foreign_net_ratio: '外資買賣超比',
  trust_net_ratio: '投信買賣超比',
  volume_ratio: '成交量比',
  price_vs_ma20: '股價vs均線20',
  price_vs_ma60: '股價vs均線60',
  volatility_20d: '波動率 (20日)',
  momentum_5d: '動能 (5日)',
  bb_position: '布林通道位置',
  industry_rank: '產業排名',
  news_sentiment: '新聞情緒',
  // 更多特徵...
};

/**
 * 格式化特徵名稱
 */
function formatFeatureName(name) {
  return FEATURE_LABELS[name] || name.replace(/_/g, ' ');
}

/**
 * 格式化數值
 */
function formatValue(value) {
  if (typeof value === 'number') {
    return value.toFixed(2);
  }
  return value;
}

/**
 * SHAP 瀑布圖元件
 */
export default function SHAPWaterfall({ stockId, height = 400 }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!stockId) return;

    setLoading(true);
    setError(null);

    fetchExplanation(stockId)
      .then(result => {
        setData(result);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [stockId]);

  if (loading) {
    return (
      <div className="shap-waterfall loading">
        <div className="spinner"></div>
        <p>載入中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="shap-waterfall error">
        <p>載入失敗: {error}</p>
      </div>
    );
  }

  if (!data || !data.explanation) {
    return (
      <div className="shap-waterfall empty">
        <p>無解釋資料</p>
      </div>
    );
  }

  const { explanation, prediction } = data;
  const { top_features, base_value } = explanation;

  // 準備圖表資料
  const chartData = top_features.map(item => ({
    name: formatFeatureName(item.feature),
    value: item.contribution,
    originalValue: item.value,
    fill: item.contribution >= 0 ? '#22c55e' : '#ef4444'
  }));

  return (
    <div className="shap-waterfall">
      {/* 標題區 */}
      <div className="shap-header">
        <h3>AI 預測解釋</h3>
        <div className="prediction-badge">
          預測: <span className={prediction >= 0.5 ? 'positive' : 'negative'}>
            {prediction >= 0.5 ? '看漲' : '看跌'}
          </span>
          <span className="confidence">
            ({(Math.abs(prediction - 0.5) * 200).toFixed(0)}% 信心)
          </span>
        </div>
      </div>

      {/* 基準值說明 */}
      <div className="base-value-info">
        <span>基準值: {(base_value * 100).toFixed(1)}%</span>
        <span className="arrow">→</span>
        <span>最終預測: {(prediction * 100).toFixed(1)}%</span>
      </div>

      {/* 瀑布圖 */}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
        >
          <XAxis
            type="number"
            domain={['auto', 'auto']}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={90}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload || !payload[0]) return null;
              const item = payload[0].payload;
              return (
                <div className="shap-tooltip">
                  <p className="feature-name">{item.name}</p>
                  <p>原始值: {formatValue(item.originalValue)}</p>
                  <p className={item.value >= 0 ? 'positive' : 'negative'}>
                    貢獻: {item.value >= 0 ? '+' : ''}{(item.value * 100).toFixed(1)}%
                  </p>
                </div>
              );
            }}
          />
          <ReferenceLine x={0} stroke="#666" />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* 特徵列表 */}
      <div className="feature-list">
        <h4>關鍵因素</h4>
        <ul>
          {top_features.slice(0, 5).map((item, index) => (
            <li key={index} className={item.contribution >= 0 ? 'positive' : 'negative'}>
              <span className="feature-name">{formatFeatureName(item.feature)}</span>
              <span className="feature-value">{formatValue(item.value)}</span>
              <span className="contribution">
                {item.contribution >= 0 ? '+' : ''}{(item.contribution * 100).toFixed(1)}%
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* 樣式 */}
      <style jsx>{`
        .shap-waterfall {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
          color: #fff;
        }

        .shap-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .shap-header h3 {
          margin: 0;
          font-size: 18px;
        }

        .prediction-badge {
          background: #2d2d44;
          padding: 8px 16px;
          border-radius: 8px;
        }

        .prediction-badge .positive {
          color: #22c55e;
          font-weight: bold;
        }

        .prediction-badge .negative {
          color: #ef4444;
          font-weight: bold;
        }

        .confidence {
          color: #888;
          font-size: 12px;
          margin-left: 4px;
        }

        .base-value-info {
          text-align: center;
          color: #888;
          font-size: 13px;
          margin-bottom: 16px;
        }

        .base-value-info .arrow {
          margin: 0 8px;
        }

        .feature-list {
          margin-top: 20px;
          border-top: 1px solid #333;
          padding-top: 16px;
        }

        .feature-list h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: #888;
        }

        .feature-list ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .feature-list li {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          border-radius: 6px;
          margin-bottom: 4px;
        }

        .feature-list li.positive {
          background: rgba(34, 197, 94, 0.1);
        }

        .feature-list li.negative {
          background: rgba(239, 68, 68, 0.1);
        }

        .feature-list .feature-name {
          flex: 1;
        }

        .feature-list .feature-value {
          color: #888;
          margin-right: 16px;
        }

        .feature-list .contribution {
          font-weight: bold;
          min-width: 60px;
          text-align: right;
        }

        .feature-list li.positive .contribution {
          color: #22c55e;
        }

        .feature-list li.negative .contribution {
          color: #ef4444;
        }

        .shap-tooltip {
          background: #2d2d44;
          padding: 12px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .shap-tooltip .feature-name {
          font-weight: bold;
          margin-bottom: 8px;
        }

        .shap-tooltip .positive {
          color: #22c55e;
        }

        .shap-tooltip .negative {
          color: #ef4444;
        }

        .loading, .error, .empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 200px;
          color: #888;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #333;
          border-top-color: #22c55e;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
