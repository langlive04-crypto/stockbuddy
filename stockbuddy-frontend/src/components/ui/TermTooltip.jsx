/**
 * TermTooltip.jsx - 專有名詞解釋 Tooltip
 * V10.37 從 App.jsx 拆分出來
 * V10.17: 新增專有名詞解釋功能
 */

import React, { useState } from 'react';

const TermTooltip = ({ term, children }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const termExplanations = {
    '技術面': '根據股價走勢和成交量分析，判斷買賣時機',
    '基本面': '分析公司財務狀況，評估股票是否值得投資',
    '籌碼面': '觀察大戶和法人的買賣動向',
    '新聞面': '從近期新聞評估市場對股票的看法',
    'P/E': '本益比：股價除以每股盈餘，數字越低表示股票越便宜',
    '殖利率': '股息報酬率：每年能拿到的股息佔股價的比例',
    '止損': '設定一個價格，跌到這個價位就賣出，避免虧更多',
    '目標價': '預期股價可能漲到的價格',
    '產業熱度': '這個產業目前是否受到市場關注',
    // V10.23: 新增技術指標解釋
    'RSI': '相對強弱指標：超過70為超買（可能下跌），低於30為超賣（可能上漲）',
    'MACD': '趨勢指標：金叉表示買進訊號，死叉表示賣出訊號',
    'KD': '隨機指標：K>80超買可能下跌，K<20超賣可能上漲，黃金交叉為買進訊號',
    '威廉指標': '動量指標：大於-20為超買，小於-80為超賣',
    '風險評估': '根據股價波動性評估投資風險，波動越大風險越高',
    '均線': '過去N天的平均價格，股價在均線上方表示趨勢偏多',
    '成交量': '股票交易的數量，放量上漲通常代表趨勢確立',
  };

  const explanation = termExplanations[term];
  if (!explanation) return children;

  return (
    <span
      className="relative cursor-help"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-xs text-slate-300 whitespace-nowrap z-50 shadow-lg">
          <div className="text-white font-medium mb-1">{term}</div>
          <div className="text-slate-400">{explanation}</div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-slate-900"></div>
        </div>
      )}
    </span>
  );
};

export default TermTooltip;
