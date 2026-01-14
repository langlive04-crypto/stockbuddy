/**
 * Prediction Explainer Panel V10.41
 *
 * 整合 SHAP 解釋 + FinBERT 情緒 + TFT 預測的完整面板
 *
 * 安裝位置: stockbuddy-frontend/src/components/PredictionExplainer.jsx
 *
 * 使用方式:
 * <PredictionExplainer stockId="2330" stockName="台積電" />
 */

import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

/**
 * API 呼叫函數
 */
async function fetchPrediction(stockId) {
  const response = await fetch(`${API_BASE}/api/stocks/ml/predict/${stockId}`);
  if (!response.ok) throw new Error('Failed to fetch prediction');
  return response.json();
}

async function fetchExplanation(stockId) {
  const response = await fetch(`${API_BASE}/api/stocks/ml/explain/${stockId}`);
  if (!response.ok) throw new Error('Failed to fetch explanation');
  return response.json();
}

async function fetchSentiment(stockId) {
  const response = await fetch(`${API_BASE}/api/stocks/sentiment/${stockId}`);
  if (!response.ok) throw new Error('Failed to fetch sentiment');
  return response.json();
}

async function fetchForecast(stockId) {
  const response = await fetch(`${API_BASE}/api/stocks/forecast/${stockId}`);
  if (!response.ok) throw new Error('Failed to fetch forecast');
  return response.json();
}

/**
 * 預測解釋面板
 */
export default function PredictionExplainer({ stockId, stockName }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [data, setData] = useState({
    prediction: null,
    explanation: null,
    sentiment: null,
    forecast: null
  });
  const [loading, setLoading] = useState({
    prediction: true,
    explanation: true,
    sentiment: true,
    forecast: true
  });
  const [errors, setErrors] = useState({});

  // 載入資料
  useEffect(() => {
    if (!stockId) return;

    // 並行載入所有資料
    const loadData = async () => {
      // Prediction
      fetchPrediction(stockId)
        .then(result => {
          setData(prev => ({ ...prev, prediction: result }));
          setLoading(prev => ({ ...prev, prediction: false }));
        })
        .catch(err => {
          setErrors(prev => ({ ...prev, prediction: err.message }));
          setLoading(prev => ({ ...prev, prediction: false }));
        });

      // Explanation
      fetchExplanation(stockId)
        .then(result => {
          setData(prev => ({ ...prev, explanation: result }));
          setLoading(prev => ({ ...prev, explanation: false }));
        })
        .catch(err => {
          setErrors(prev => ({ ...prev, explanation: err.message }));
          setLoading(prev => ({ ...prev, explanation: false }));
        });

      // Sentiment
      fetchSentiment(stockId)
        .then(result => {
          setData(prev => ({ ...prev, sentiment: result }));
          setLoading(prev => ({ ...prev, sentiment: false }));
        })
        .catch(err => {
          setErrors(prev => ({ ...prev, sentiment: err.message }));
          setLoading(prev => ({ ...prev, sentiment: false }));
        });

      // Forecast
      fetchForecast(stockId)
        .then(result => {
          setData(prev => ({ ...prev, forecast: result }));
          setLoading(prev => ({ ...prev, forecast: false }));
        })
        .catch(err => {
          setErrors(prev => ({ ...prev, forecast: err.message }));
          setLoading(prev => ({ ...prev, forecast: false }));
        });
    };

    loadData();
  }, [stockId]);

  const isLoading = Object.values(loading).some(v => v);

  return (
    <div className="prediction-explainer">
      {/* 標題 */}
      <div className="header">
        <h2>
          {stockName || stockId} AI 分析報告
        </h2>
        <div className="model-badge">
          V10.41 AI
        </div>
      </div>

      {/* 分頁選單 */}
      <div className="tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          總覽
        </button>
        <button
          className={activeTab === 'explanation' ? 'active' : ''}
          onClick={() => setActiveTab('explanation')}
        >
          SHAP 解釋
        </button>
        <button
          className={activeTab === 'sentiment' ? 'active' : ''}
          onClick={() => setActiveTab('sentiment')}
        >
          FinBERT 情緒
        </button>
        <button
          className={activeTab === 'forecast' ? 'active' : ''}
          onClick={() => setActiveTab('forecast')}
        >
          TFT 預測
        </button>
      </div>

      {/* 內容區 */}
      <div className="content">
        {activeTab === 'overview' && (
          <OverviewTab
            prediction={data.prediction}
            explanation={data.explanation}
            sentiment={data.sentiment}
            forecast={data.forecast}
            loading={isLoading}
          />
        )}
        {activeTab === 'explanation' && (
          <ExplanationTab
            data={data.explanation}
            loading={loading.explanation}
            error={errors.explanation}
          />
        )}
        {activeTab === 'sentiment' && (
          <SentimentTab
            data={data.sentiment}
            loading={loading.sentiment}
            error={errors.sentiment}
          />
        )}
        {activeTab === 'forecast' && (
          <ForecastTab
            data={data.forecast}
            loading={loading.forecast}
            error={errors.forecast}
          />
        )}
      </div>

      {/* 樣式 */}
      <style jsx>{`
        .prediction-explainer {
          background: #1a1a2e;
          border-radius: 16px;
          overflow: hidden;
          color: #fff;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 24px;
          background: linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%);
          border-bottom: 1px solid #333;
        }

        .header h2 {
          margin: 0;
          font-size: 20px;
        }

        .model-badge {
          background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: bold;
        }

        .tabs {
          display: flex;
          background: #2d2d44;
          padding: 4px;
          margin: 16px 24px;
          border-radius: 10px;
        }

        .tabs button {
          flex: 1;
          padding: 10px 16px;
          background: transparent;
          border: none;
          color: #888;
          font-size: 14px;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.2s;
        }

        .tabs button:hover {
          color: #fff;
        }

        .tabs button.active {
          background: #1a1a2e;
          color: #22c55e;
        }

        .content {
          padding: 0 24px 24px;
        }
      `}</style>
    </div>
  );
}

/**
 * 總覽分頁
 */
function OverviewTab({ prediction, explanation, sentiment, forecast, loading }) {
  if (loading) {
    return <LoadingState message="載入分析資料中..." />;
  }

  const aiScore = prediction?.ai_score || 50;
  const sentimentScore = sentiment?.score || 50;
  const forecastTrend = forecast?.predictions?.day_5?.return || 0;

  // 綜合評分
  const overallScore = Math.round(
    aiScore * 0.4 + sentimentScore * 0.3 + (50 + forecastTrend * 10) * 0.3
  );

  const getSignalText = (score) => {
    if (score >= 70) return { text: '強力買進', color: '#22c55e' };
    if (score >= 60) return { text: '買進', color: '#86efac' };
    if (score >= 40) return { text: '持有', color: '#fbbf24' };
    if (score >= 30) return { text: '減碼', color: '#fb923c' };
    return { text: '賣出', color: '#ef4444' };
  };

  const signal = getSignalText(overallScore);

  return (
    <div className="overview-tab">
      {/* 綜合評分 */}
      <div className="overall-score">
        <div className="score-circle" style={{ borderColor: signal.color }}>
          <span className="score-value">{overallScore}</span>
          <span className="score-label">綜合評分</span>
        </div>
        <div className="signal" style={{ color: signal.color }}>
          {signal.text}
        </div>
      </div>

      {/* 三大指標 */}
      <div className="metrics">
        <MetricCard
          title="XGBoost + SHAP"
          value={aiScore}
          icon="robot"
          description={explanation?.explanation?.top_features?.[0]?.feature
            ? `主要因素: ${explanation.explanation.top_features[0].feature}`
            : '特徵分析中...'
          }
        />
        <MetricCard
          title="FinBERT 情緒"
          value={sentimentScore}
          icon="news"
          description={sentiment?.label
            ? `情緒: ${sentiment.label}`
            : '情緒分析中...'
          }
        />
        <MetricCard
          title="TFT 5日預測"
          value={50 + forecastTrend * 10}
          icon="chart"
          description={`預期報酬: ${forecastTrend >= 0 ? '+' : ''}${forecastTrend.toFixed(1)}%`}
        />
      </div>

      <style jsx>{`
        .overview-tab {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .overall-score {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 24px;
        }

        .score-circle {
          width: 120px;
          height: 120px;
          border-radius: 50%;
          border: 4px solid;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background: #2d2d44;
        }

        .score-value {
          font-size: 40px;
          font-weight: bold;
        }

        .score-label {
          font-size: 12px;
          color: #888;
        }

        .signal {
          font-size: 24px;
          font-weight: bold;
          margin-top: 12px;
        }

        .metrics {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
        }

        @media (max-width: 768px) {
          .metrics {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

/**
 * 指標卡片
 */
function MetricCard({ title, value, icon, description }) {
  const getColor = (v) => {
    if (v >= 60) return '#22c55e';
    if (v >= 40) return '#fbbf24';
    return '#ef4444';
  };

  const getIcon = (type) => {
    switch(type) {
      case 'robot': return 'AI';
      case 'news': return 'NLP';
      case 'chart': return 'TFT';
      default: return '';
    }
  };

  return (
    <div className="metric-card">
      <div className="metric-header">
        <span className="icon">{getIcon(icon)}</span>
        <span className="title">{title}</span>
      </div>
      <div className="metric-value" style={{ color: getColor(value) }}>
        {value}
      </div>
      <div className="metric-description">{description}</div>

      <style jsx>{`
        .metric-card {
          background: #2d2d44;
          border-radius: 12px;
          padding: 16px;
        }

        .metric-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }

        .icon {
          font-size: 14px;
          background: #1a1a2e;
          padding: 4px 8px;
          border-radius: 4px;
          color: #22c55e;
        }

        .title {
          font-size: 14px;
          color: #888;
        }

        .metric-value {
          font-size: 32px;
          font-weight: bold;
          margin-bottom: 8px;
        }

        .metric-description {
          font-size: 12px;
          color: #666;
        }
      `}</style>
    </div>
  );
}

/**
 * SHAP 解釋分頁
 */
function ExplanationTab({ data, loading, error }) {
  if (loading) return <LoadingState message="載入 SHAP 解釋..." />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState message="無解釋資料" />;

  const { explanation, prediction } = data;
  const features = explanation?.top_features || [];

  return (
    <div className="explanation-tab">
      <div className="prediction-summary">
        <span>預測結果:</span>
        <span className={prediction >= 0.5 ? 'positive' : 'negative'}>
          {prediction >= 0.5 ? '看漲' : '看跌'} ({(prediction * 100).toFixed(1)}%)
        </span>
      </div>

      <div className="feature-contributions">
        <h3>特徵貢獻度 (Top 10)</h3>
        {features.map((item, index) => (
          <div key={index} className="feature-row">
            <span className="feature-name">{item.feature}</span>
            <div className="feature-bar-container">
              <div
                className={`feature-bar ${item.contribution >= 0 ? 'positive' : 'negative'}`}
                style={{
                  width: `${Math.abs(item.contribution) * 500}%`,
                  maxWidth: '100%'
                }}
              />
            </div>
            <span className={`contribution ${item.contribution >= 0 ? 'positive' : 'negative'}`}>
              {item.contribution >= 0 ? '+' : ''}{(item.contribution * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      <style jsx>{`
        .explanation-tab h3 {
          font-size: 16px;
          margin-bottom: 16px;
          color: #888;
        }

        .prediction-summary {
          background: #2d2d44;
          padding: 16px;
          border-radius: 10px;
          margin-bottom: 20px;
          display: flex;
          justify-content: space-between;
        }

        .prediction-summary .positive { color: #22c55e; font-weight: bold; }
        .prediction-summary .negative { color: #ef4444; font-weight: bold; }

        .feature-row {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
        }

        .feature-name {
          width: 150px;
          font-size: 13px;
        }

        .feature-bar-container {
          flex: 1;
          height: 20px;
          background: #2d2d44;
          border-radius: 4px;
          margin: 0 12px;
          overflow: hidden;
        }

        .feature-bar {
          height: 100%;
          border-radius: 4px;
        }

        .feature-bar.positive { background: #22c55e; }
        .feature-bar.negative { background: #ef4444; }

        .contribution {
          width: 60px;
          text-align: right;
          font-size: 13px;
        }

        .contribution.positive { color: #22c55e; }
        .contribution.negative { color: #ef4444; }
      `}</style>
    </div>
  );
}

/**
 * 情緒分析分頁
 */
function SentimentTab({ data, loading, error }) {
  if (loading) return <LoadingState message="載入 FinBERT 情緒分析..." />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState message="無情緒資料" />;

  const { label, score, probabilities, recent_news } = data;

  const labelColors = {
    positive: '#22c55e',
    neutral: '#fbbf24',
    negative: '#ef4444'
  };

  return (
    <div className="sentiment-tab">
      <div className="sentiment-summary">
        <div className="sentiment-label" style={{ color: labelColors[label] }}>
          {label === 'positive' ? '正面' : label === 'negative' ? '負面' : '中性'}
        </div>
        <div className="sentiment-score">
          信心度: {(score * 100).toFixed(0)}%
        </div>
      </div>

      <div className="probability-bars">
        <h3>情緒機率分佈</h3>
        {['positive', 'neutral', 'negative'].map(key => (
          <div key={key} className="prob-row">
            <span className="prob-label">
              {key === 'positive' ? '正面' : key === 'negative' ? '負面' : '中性'}
            </span>
            <div className="prob-bar-container">
              <div
                className="prob-bar"
                style={{
                  width: `${(probabilities?.[key] || 0) * 100}%`,
                  backgroundColor: labelColors[key]
                }}
              />
            </div>
            <span className="prob-value">
              {((probabilities?.[key] || 0) * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      {recent_news && recent_news.length > 0 && (
        <div className="recent-news">
          <h3>近期新聞情緒</h3>
          {recent_news.slice(0, 5).map((news, index) => (
            <div key={index} className="news-item">
              <span className="news-title">{news.title}</span>
              <span
                className="news-sentiment"
                style={{ color: labelColors[news.sentiment] }}
              >
                {news.sentiment}
              </span>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .sentiment-tab h3 {
          font-size: 14px;
          color: #888;
          margin-bottom: 12px;
        }

        .sentiment-summary {
          text-align: center;
          padding: 24px;
          background: #2d2d44;
          border-radius: 12px;
          margin-bottom: 20px;
        }

        .sentiment-label {
          font-size: 32px;
          font-weight: bold;
        }

        .sentiment-score {
          color: #888;
          margin-top: 8px;
        }

        .probability-bars {
          margin-bottom: 20px;
        }

        .prob-row {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
        }

        .prob-label {
          width: 60px;
          font-size: 13px;
        }

        .prob-bar-container {
          flex: 1;
          height: 24px;
          background: #2d2d44;
          border-radius: 4px;
          margin: 0 12px;
          overflow: hidden;
        }

        .prob-bar {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }

        .prob-value {
          width: 50px;
          text-align: right;
          font-size: 13px;
        }

        .recent-news {
          background: #2d2d44;
          border-radius: 12px;
          padding: 16px;
        }

        .news-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #333;
        }

        .news-item:last-child {
          border-bottom: none;
        }

        .news-title {
          font-size: 13px;
          flex: 1;
          margin-right: 12px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .news-sentiment {
          font-size: 12px;
          font-weight: bold;
        }
      `}</style>
    </div>
  );
}

/**
 * TFT 預測分頁
 */
function ForecastTab({ data, loading, error }) {
  if (loading) return <LoadingState message="載入 TFT 預測..." />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState message="無預測資料" />;

  const { predictions, model_version, attention } = data;

  const days = Object.keys(predictions || {}).sort();

  return (
    <div className="forecast-tab">
      <div className="model-info">
        <span>模型版本: {model_version}</span>
        {attention?.method && <span>方法: {attention.method}</span>}
      </div>

      <div className="forecast-table">
        <h3>未來 5 日報酬預測</h3>
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>預測報酬</th>
              <th>信賴區間</th>
            </tr>
          </thead>
          <tbody>
            {days.map(day => {
              const pred = predictions[day];
              const returnValue = pred?.return || 0;
              return (
                <tr key={day}>
                  <td>{day.replace('day_', '第 ') + ' 日'}</td>
                  <td className={returnValue >= 0 ? 'positive' : 'negative'}>
                    {returnValue >= 0 ? '+' : ''}{returnValue.toFixed(2)}%
                  </td>
                  <td className="interval">
                    [{pred?.lower?.toFixed(2)}%, {pred?.upper?.toFixed(2)}%]
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <style jsx>{`
        .forecast-tab h3 {
          font-size: 14px;
          color: #888;
          margin-bottom: 12px;
        }

        .model-info {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #666;
          margin-bottom: 16px;
        }

        .forecast-table {
          background: #2d2d44;
          border-radius: 12px;
          padding: 16px;
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th, td {
          padding: 12px;
          text-align: left;
        }

        th {
          color: #888;
          font-size: 13px;
          border-bottom: 1px solid #333;
        }

        td {
          font-size: 14px;
        }

        td.positive { color: #22c55e; font-weight: bold; }
        td.negative { color: #ef4444; font-weight: bold; }
        td.interval { color: #888; font-size: 12px; }

        tr:not(:last-child) td {
          border-bottom: 1px solid #333;
        }
      `}</style>
    </div>
  );
}

/**
 * 狀態元件
 */
function LoadingState({ message }) {
  return (
    <div className="state loading">
      <div className="spinner" />
      <p>{message}</p>
      <style jsx>{`
        .state { display: flex; flex-direction: column; align-items: center; padding: 40px; color: #888; }
        .spinner { width: 40px; height: 40px; border: 3px solid #333; border-top-color: #22c55e; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

function ErrorState({ message }) {
  return (
    <div className="state error">
      <span>Error</span>
      <p>{message}</p>
      <style jsx>{`
        .state { display: flex; flex-direction: column; align-items: center; padding: 40px; color: #ef4444; }
      `}</style>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="state empty">
      <p>{message}</p>
      <style jsx>{`
        .state { display: flex; flex-direction: column; align-items: center; padding: 40px; color: #888; }
      `}</style>
    </div>
  );
}
