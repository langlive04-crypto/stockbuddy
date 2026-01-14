/**
 * StockCard.jsx - 股票卡片組件
 * V10.37 從 App.jsx 拆分出來
 * V10.17: 優化後的股票卡片
 */

import React from 'react';
import PortfolioManager from '../../services/portfolioManager';
import ScoreRing from './ScoreRing';
import ScoreBar from './ScoreBar';
import TermTooltip from './TermTooltip';

const StockCard = ({ stock, onClick, isSelected, onAddToPortfolio, showAddButton = true }) => {
  const isUp = (stock.change_percent || 0) >= 0;
  const breakdown = stock.score_breakdown || {};

  const handleAddToPortfolio = (e) => {
    e.stopPropagation();
    const result = PortfolioManager.addToPortfolio(stock);
    alert(result.message);
    if (result.success && onAddToPortfolio) {
      onAddToPortfolio(stock, result);
    }
  };

  // 生成白話文建議
  const getSimpleAdvice = () => {
    const score = stock.confidence || 0;
    if (score >= 80) return '這檔股票各方面表現優秀，可考慮買進';
    if (score >= 70) return '整體表現良好，可留意進場機會';
    if (score >= 60) return '表現中等，建議觀望或持有';
    if (score >= 50) return '需謹慎評估，暫時觀望為佳';
    return '目前不建議介入，請等待更好時機';
  };

  return (
    <div
      onClick={() => onClick(stock)}
      className={`p-4 rounded-xl cursor-pointer transition-all duration-200 ${
        isSelected
          ? 'bg-gradient-to-r from-blue-600/30 to-purple-600/30 border border-blue-500/50 shadow-lg shadow-blue-500/20'
          : 'bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50'
      }`}
    >
      {/* 標題區 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-white font-semibold">{stock.name}</span>
            <span className="text-slate-500 text-sm">{stock.stock_id}</span>
            {PortfolioManager.isInPortfolio(stock.stock_id) && (
              <span className="text-xs px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">追蹤中</span>
            )}
          </div>
          {/* 價格區 */}
          <div className="flex items-center gap-3 mt-1">
            <span className="text-white text-xl font-bold">${stock.price?.toLocaleString()}</span>
            <span className={`text-sm font-bold px-2 py-0.5 rounded ${isUp ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
              {isUp ? '▲' : '▼'} {Math.abs(stock.change_percent || 0).toFixed(2)}%
            </span>
          </div>
        </div>
        <ScoreRing score={stock.confidence} size={55} />
      </div>

      {/* V10.17: 四維評分進度條（更直覺的視覺化） */}
      {breakdown.technical && (
        <div className="space-y-1.5 mb-3 bg-slate-900/30 rounded-lg p-2">
          <ScoreBar label="技術面" score={breakdown.technical} color="red" />
          <ScoreBar label="基本面" score={breakdown.fundamental} color="green" />
          <ScoreBar label="籌碼面" score={breakdown.chip} color="blue" />
          <ScoreBar label="新聞面" score={breakdown.news || 50} color="purple" />
          {breakdown.industry_bonus !== 0 && breakdown.industry_bonus && (
            <TermTooltip term="產業熱度">
              <div className="flex items-center justify-between text-xs mt-1 pt-1 border-t border-slate-700">
                <span className="text-slate-400">產業熱度</span>
                <span className={breakdown.industry_bonus > 0 ? 'text-amber-400' : 'text-slate-500'}>
                  {breakdown.industry_bonus > 0 ? '+' : ''}{breakdown.industry_bonus}
                </span>
              </div>
            </TermTooltip>
          )}
        </div>
      )}

      {/* 基本面快速指標 */}
      <div className="flex items-center gap-4 mb-3 text-xs">
        {stock.pe_ratio && (
          <TermTooltip term="P/E">
            <span className={`${stock.pe_ratio < 15 ? 'text-emerald-400' : stock.pe_ratio > 30 ? 'text-red-400' : 'text-slate-400'}`}>
              P/E {stock.pe_ratio.toFixed(1)}
            </span>
          </TermTooltip>
        )}
        {stock.dividend_yield > 0 && (
          <TermTooltip term="殖利率">
            <span className={`${stock.dividend_yield >= 4 ? 'text-yellow-400' : 'text-slate-400'}`}>
              殖利率 {stock.dividend_yield.toFixed(1)}%
            </span>
          </TermTooltip>
        )}
      </div>

      {/* 產業標籤 */}
      {(stock.industry || stock.tags?.length > 0) && (
        <div className="flex flex-wrap gap-1 mb-3">
          {stock.industry && (
            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full">{stock.industry}</span>
          )}
          {stock.tags?.slice(0, 2).map((tag, i) => (
            <span key={i} className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded-full">{tag}</span>
          ))}
        </div>
      )}

      {/* 訊號與白話建議 */}
      <div className="bg-slate-900/50 rounded-lg p-2 mb-3">
        <div className="flex items-center gap-2 mb-1">
          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
            stock.signal === '強力買進' ? 'bg-red-500 text-white' :
            stock.signal === '買進' ? 'bg-orange-500 text-white' :
            stock.signal === '持有' ? 'bg-yellow-500 text-black' :
            'bg-slate-600 text-slate-300'
          }`}>
            {stock.signal}
          </span>
        </div>
        <p className="text-slate-400 text-xs">{stock.reason || getSimpleAdvice()}</p>
      </div>

      {/* V10.17: 交易建議區（更清晰的呈現） */}
      {stock.price && (
        <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
          <TermTooltip term="止損">
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2 text-center">
              <div className="text-slate-400 mb-0.5">止損價位</div>
              <div className="text-emerald-400 font-bold text-sm">${(stock.price * 0.95).toFixed(0)}</div>
              <div className="text-emerald-400/60 text-[10px]">-5%</div>
            </div>
          </TermTooltip>
          <TermTooltip term="目標價">
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2 text-center">
              <div className="text-slate-400 mb-0.5">目標價位</div>
              <div className="text-red-400 font-bold text-sm">${(stock.price * 1.10).toFixed(0)}</div>
              <div className="text-red-400/60 text-[10px]">+10%</div>
            </div>
          </TermTooltip>
        </div>
      )}

      {/* 追蹤按鈕 */}
      {showAddButton && (
        <button
          onClick={handleAddToPortfolio}
          className={`w-full py-2 text-xs rounded-lg font-medium transition-colors ${
            PortfolioManager.isInPortfolio(stock.stock_id)
              ? 'bg-slate-600/30 text-slate-400 border border-slate-600/50 hover:bg-slate-600/50'
              : 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-400 hover:to-orange-400'
          }`}
        >
          {PortfolioManager.isInPortfolio(stock.stock_id) ? '✓ 已加入追蹤' : '⭐ 加入追蹤清單'}
        </button>
      )}
    </div>
  );
};

export default StockCard;
