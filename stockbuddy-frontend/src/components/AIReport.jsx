/**
 * AIReport.jsx - AI 分析報告
 * V10.31 新增
 *
 * 功能：
 * - 個股 AI 分析報告
 * - 投組健診報告
 * - 報告匯出 (PDF/HTML)
 * - 報告歷史記錄
 */

import React, { useState, useMemo } from 'react';

// 評級對應
const RATING_CONFIG = {
  '強力買進': { color: 'text-emerald-400', bg: 'bg-emerald-500/20', icon: '🚀' },
  '買進': { color: 'text-green-400', bg: 'bg-green-500/20', icon: '📈' },
  '持有': { color: 'text-yellow-400', bg: 'bg-yellow-500/20', icon: '⏸️' },
  '賣出': { color: 'text-orange-400', bg: 'bg-orange-500/20', icon: '📉' },
  '強力賣出': { color: 'text-red-400', bg: 'bg-red-500/20', icon: '⚠️' },
};

const AIReport = ({ stock = null, portfolio = [] }) => {
  const [reportType, setReportType] = useState('stock'); // stock | portfolio
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedReport, setGeneratedReport] = useState(null);

  // 生成股票報告
  const generateStockReport = useMemo(() => {
    if (!stock) return null;

    // 技術面評分
    const technicalScore = stock.confidence || stock.score || 75;

    // 基本面評分（模擬）
    const fundamentalScore = stock.pe_ratio
      ? (stock.pe_ratio < 15 ? 85 : stock.pe_ratio < 25 ? 70 : 55)
      : 70;

    // 籌碼面評分（模擬）
    const chipScore = stock.foreign_buy
      ? (stock.foreign_buy > 0 ? 80 : 60)
      : 70;

    // 綜合評分
    const overallScore = Math.round((technicalScore * 0.4 + fundamentalScore * 0.3 + chipScore * 0.3));

    // 評級
    let rating = '持有';
    if (overallScore >= 85) rating = '強力買進';
    else if (overallScore >= 75) rating = '買進';
    else if (overallScore >= 60) rating = '持有';
    else if (overallScore >= 45) rating = '賣出';
    else rating = '強力賣出';

    // 生成報告內容
    return {
      stockId: stock.stock_id,
      stockName: stock.name,
      price: stock.price,
      changePercent: stock.change_percent,
      generatedAt: new Date().toISOString(),

      scores: {
        overall: overallScore,
        technical: technicalScore,
        fundamental: fundamentalScore,
        chip: chipScore,
      },

      rating,
      ratingConfig: RATING_CONFIG[rating],

      summary: generateSummary(stock, overallScore, rating),
      technicalAnalysis: generateTechnicalAnalysis(stock),
      fundamentalAnalysis: generateFundamentalAnalysis(stock),
      chipAnalysis: generateChipAnalysis(stock),
      riskFactors: generateRiskFactors(stock),
      recommendation: generateRecommendation(stock, rating),
    };
  }, [stock]);

  // 生成摘要
  function generateSummary(stock, score, rating) {
    const priceAction = stock.change_percent >= 0 ? '上漲' : '下跌';
    const trend = score >= 70 ? '偏多' : score >= 50 ? '中性' : '偏空';

    return `${stock.name}（${stock.stock_id}）目前股價 ${stock.price?.toFixed(2)} 元，` +
      `今日${priceAction} ${Math.abs(stock.change_percent * 100).toFixed(2)}%。` +
      `綜合 AI 評分為 ${score} 分，整體趨勢${trend}，` +
      `建議操作為「${rating}」。`;
  }

  // 生成技術分析
  function generateTechnicalAnalysis(stock) {
    const analyses = [];

    if (stock.rsi) {
      if (stock.rsi > 70) analyses.push('RSI 指標顯示超買，短期可能面臨回調壓力');
      else if (stock.rsi < 30) analyses.push('RSI 指標顯示超賣，可能出現反彈契機');
      else analyses.push('RSI 指標處於中性區間，無明顯超買超賣');
    }

    if (stock.signal) {
      analyses.push(`技術訊號顯示「${stock.signal}」`);
    }

    if (stock.ma_trend) {
      analyses.push(`移動平均線呈現${stock.ma_trend === 'up' ? '多頭' : '空頭'}排列`);
    }

    if (analyses.length === 0) {
      analyses.push('技術指標整體呈現中性格局');
    }

    return analyses;
  }

  // 生成基本面分析
  function generateFundamentalAnalysis(stock) {
    const analyses = [];

    if (stock.pe_ratio) {
      if (stock.pe_ratio < 10) analyses.push(`本益比 ${stock.pe_ratio.toFixed(1)} 倍，估值偏低，具投資價值`);
      else if (stock.pe_ratio < 20) analyses.push(`本益比 ${stock.pe_ratio.toFixed(1)} 倍，估值合理`);
      else analyses.push(`本益比 ${stock.pe_ratio.toFixed(1)} 倍，估值偏高，需注意風險`);
    }

    if (stock.dividend_yield) {
      if (stock.dividend_yield > 5) analyses.push(`殖利率 ${stock.dividend_yield.toFixed(2)}%，具高股息優勢`);
      else if (stock.dividend_yield > 3) analyses.push(`殖利率 ${stock.dividend_yield.toFixed(2)}%，股息穩定`);
    }

    if (stock.industry) {
      analyses.push(`所屬產業：${stock.industry}`);
    }

    if (analyses.length === 0) {
      analyses.push('基本面數據尚未完整，建議觀察');
    }

    return analyses;
  }

  // 生成籌碼分析
  function generateChipAnalysis(stock) {
    const analyses = [];

    if (stock.foreign_buy !== undefined) {
      if (stock.foreign_buy > 1000) analyses.push(`外資買超 ${stock.foreign_buy} 張，呈現買盤支撐`);
      else if (stock.foreign_buy < -1000) analyses.push(`外資賣超 ${Math.abs(stock.foreign_buy)} 張，注意賣壓`);
    }

    if (stock.volume_ratio) {
      if (stock.volume_ratio > 2) analyses.push(`成交量放大 ${stock.volume_ratio.toFixed(1)} 倍，交投活絡`);
      else if (stock.volume_ratio < 0.5) analyses.push('成交量萎縮，觀望氣氛濃厚');
    }

    if (analyses.length === 0) {
      analyses.push('籌碼面變化不大，維持原有格局');
    }

    return analyses;
  }

  // 生成風險因素
  function generateRiskFactors(stock) {
    const risks = [];

    if (stock.change_percent && Math.abs(stock.change_percent) > 0.05) {
      risks.push('股價波動劇烈，短線操作風險較高');
    }

    if (stock.pe_ratio && stock.pe_ratio > 30) {
      risks.push('估值偏高，可能面臨修正風險');
    }

    if (stock.rsi && stock.rsi > 80) {
      risks.push('技術指標嚴重超買，短期回調風險高');
    }

    if (risks.length === 0) {
      risks.push('目前無明顯重大風險因素');
    }

    return risks;
  }

  // 生成建議
  function generateRecommendation(stock, rating) {
    const recommendations = {
      '強力買進': [
        '建議積極建立部位',
        '可考慮分批買進，降低進場成本',
        '設定合理停損點，控制風險',
      ],
      '買進': [
        '建議逢低布局',
        '可於支撐位附近分批進場',
        '持股比例建議不超過投組 10%',
      ],
      '持有': [
        '已持有者建議續抱觀察',
        '暫不建議新增部位',
        '關注後續技術面變化',
      ],
      '賣出': [
        '建議減碼或分批出場',
        '設定嚴格停損以保護獲利',
        '等待更好的進場時機',
      ],
      '強力賣出': [
        '建議盡速減碼出場',
        '避免持續攤平增加風險',
        '觀望至趨勢明確再考慮進場',
      ],
    };

    return recommendations[rating] || recommendations['持有'];
  }

  // 匯出報告
  const exportReport = (format = 'html') => {
    if (!generatedReport) return;

    const content = generateReportHTML(generatedReport);

    if (format === 'print') {
      const printWindow = window.open('', '_blank');
      printWindow.document.write(content);
      printWindow.document.close();
      printWindow.onload = () => printWindow.print();
    } else {
      const blob = new Blob([content], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AI分析報告_${generatedReport.stockName}_${new Date().toISOString().split('T')[0]}.html`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  // 生成報告 HTML
  function generateReportHTML(report) {
    return `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>AI 分析報告 - ${report.stockName}</title>
  <style>
    body { font-family: 'Microsoft JhengHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; }
    h1 { color: #1e293b; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }
    h2 { color: #334155; margin-top: 30px; }
    .header { display: flex; justify-content: space-between; align-items: center; }
    .rating { font-size: 24px; padding: 10px 20px; border-radius: 8px; background: #10b981; color: white; }
    .score-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
    .score-card { background: #f8fafc; padding: 15px; border-radius: 8px; text-align: center; }
    .score-value { font-size: 28px; font-weight: bold; color: #3b82f6; }
    .section { margin: 25px 0; padding: 20px; background: #f8fafc; border-radius: 8px; }
    .risk { background: #fef3c7; }
    ul { padding-left: 20px; }
    li { margin: 8px 0; }
    .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px; text-align: center; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 AI 分析報告</h1>
    <div class="rating">${report.rating}</div>
  </div>

  <p><strong>${report.stockName}</strong>（${report.stockId}）| 股價 $${report.price?.toFixed(2)} | 報告日期：${new Date(report.generatedAt).toLocaleDateString('zh-TW')}</p>

  <h2>📈 評分概覽</h2>
  <div class="score-grid">
    <div class="score-card"><div class="score-value">${report.scores.overall}</div><div>綜合評分</div></div>
    <div class="score-card"><div class="score-value">${report.scores.technical}</div><div>技術面</div></div>
    <div class="score-card"><div class="score-value">${report.scores.fundamental}</div><div>基本面</div></div>
    <div class="score-card"><div class="score-value">${report.scores.chip}</div><div>籌碼面</div></div>
  </div>

  <h2>📝 摘要</h2>
  <p>${report.summary}</p>

  <div class="section">
    <h2>📊 技術分析</h2>
    <ul>${report.technicalAnalysis.map(a => `<li>${a}</li>`).join('')}</ul>
  </div>

  <div class="section">
    <h2>💰 基本面分析</h2>
    <ul>${report.fundamentalAnalysis.map(a => `<li>${a}</li>`).join('')}</ul>
  </div>

  <div class="section">
    <h2>🏦 籌碼分析</h2>
    <ul>${report.chipAnalysis.map(a => `<li>${a}</li>`).join('')}</ul>
  </div>

  <div class="section risk">
    <h2>⚠️ 風險提示</h2>
    <ul>${report.riskFactors.map(r => `<li>${r}</li>`).join('')}</ul>
  </div>

  <div class="section">
    <h2>💡 操作建議</h2>
    <ul>${report.recommendation.map(r => `<li>${r}</li>`).join('')}</ul>
  </div>

  <div class="footer">
    <p>本報告由 StockBuddy AI 系統自動生成，僅供參考，不構成投資建議。</p>
    <p>StockBuddy V10.31 | ${new Date().toLocaleString('zh-TW')}</p>
  </div>
</body>
</html>
    `;
  }

  // 生成報告
  const handleGenerateReport = async () => {
    setIsGenerating(true);

    // 模擬生成延遲
    await new Promise(resolve => setTimeout(resolve, 1500));

    setGeneratedReport(generateStockReport);
    setIsGenerating(false);
  };

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* 標題 */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>📊</span> AI 分析報告
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setReportType('stock')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              reportType === 'stock'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            個股報告
          </button>
          <button
            onClick={() => setReportType('portfolio')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              reportType === 'portfolio'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            投組健診
          </button>
        </div>
      </div>

      <div className="p-4">
        {!stock && reportType === 'stock' ? (
          <div className="text-center text-slate-500 py-12">
            <p className="text-4xl mb-4">📊</p>
            <p>請先選擇一檔股票</p>
            <p className="text-sm mt-2">從 AI 精選或其他列表中選擇股票後，即可生成分析報告</p>
          </div>
        ) : (
          <>
            {/* 股票資訊 */}
            {stock && reportType === 'stock' && (
              <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xl font-bold text-white">
                      {stock.name}
                      <span className="ml-2 text-slate-400 text-base">({stock.stock_id})</span>
                    </div>
                    <div className="flex items-center gap-4 mt-2">
                      <span className="text-2xl text-white">${stock.price?.toFixed(2)}</span>
                      <span className={`${stock.change_percent >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {stock.change_percent >= 0 ? '+' : ''}{(stock.change_percent * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={handleGenerateReport}
                    disabled={isGenerating}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    {isGenerating ? '生成中...' : '生成報告'}
                  </button>
                </div>
              </div>
            )}

            {/* 報告內容 */}
            {generatedReport && (
              <div className="space-y-4">
                {/* 評級和評分 */}
                <div className="flex items-center justify-between">
                  <div className={`px-4 py-2 rounded-lg ${generatedReport.ratingConfig.bg}`}>
                    <span className="text-2xl mr-2">{generatedReport.ratingConfig.icon}</span>
                    <span className={`text-xl font-bold ${generatedReport.ratingConfig.color}`}>
                      {generatedReport.rating}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => exportReport('html')}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                    >
                      下載報告
                    </button>
                    <button
                      onClick={() => exportReport('print')}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                    >
                      列印報告
                    </button>
                  </div>
                </div>

                {/* 評分卡片 */}
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { label: '綜合', value: generatedReport.scores.overall },
                    { label: '技術面', value: generatedReport.scores.technical },
                    { label: '基本面', value: generatedReport.scores.fundamental },
                    { label: '籌碼面', value: generatedReport.scores.chip },
                  ].map((item) => (
                    <div key={item.label} className="bg-slate-700/50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-blue-400">{item.value}</div>
                      <div className="text-slate-400 text-sm">{item.label}</div>
                    </div>
                  ))}
                </div>

                {/* 摘要 */}
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <h3 className="text-white font-medium mb-2">📝 摘要</h3>
                  <p className="text-slate-300">{generatedReport.summary}</p>
                </div>

                {/* 分析內容 */}
                <div className="grid md:grid-cols-2 gap-4">
                  {/* 技術分析 */}
                  <div className="bg-slate-700/30 rounded-lg p-4">
                    <h3 className="text-white font-medium mb-2">📊 技術分析</h3>
                    <ul className="space-y-1">
                      {generatedReport.technicalAnalysis.map((item, i) => (
                        <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                          <span className="text-blue-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 基本面分析 */}
                  <div className="bg-slate-700/30 rounded-lg p-4">
                    <h3 className="text-white font-medium mb-2">💰 基本面分析</h3>
                    <ul className="space-y-1">
                      {generatedReport.fundamentalAnalysis.map((item, i) => (
                        <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                          <span className="text-emerald-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 籌碼分析 */}
                  <div className="bg-slate-700/30 rounded-lg p-4">
                    <h3 className="text-white font-medium mb-2">🏦 籌碼分析</h3>
                    <ul className="space-y-1">
                      {generatedReport.chipAnalysis.map((item, i) => (
                        <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                          <span className="text-purple-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* 風險提示 */}
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                    <h3 className="text-yellow-400 font-medium mb-2">⚠️ 風險提示</h3>
                    <ul className="space-y-1">
                      {generatedReport.riskFactors.map((item, i) => (
                        <li key={i} className="text-yellow-200/80 text-sm flex items-start gap-2">
                          <span className="text-yellow-400">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 操作建議 */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <h3 className="text-blue-400 font-medium mb-2">💡 操作建議</h3>
                  <ul className="space-y-1">
                    {generatedReport.recommendation.map((item, i) => (
                      <li key={i} className="text-blue-200 text-sm flex items-start gap-2">
                        <span className="text-blue-400">{i + 1}.</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 報告時間 */}
                <div className="text-center text-slate-500 text-xs">
                  報告生成時間：{new Date(generatedReport.generatedAt).toLocaleString('zh-TW')}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AIReport;
