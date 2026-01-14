/**
 * EnhancedAIPanel.jsx - 增強版 AI 分析面板
 * V10.25 新增
 * V10.35.1 更新：相關股票添加中文名稱和連結功能
 *
 * 功能：
 * - 顯示增強版情緒分析結果
 * - 顯示產業連動分析
 * - 顯示相關股票（含中文名稱和連結）
 * - 顯示供應鏈影響
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getStockName } from '../services/stockNames';
import { API_STOCKS_BASE } from '../config';

const API_BASE = API_STOCKS_BASE;

const EnhancedAIPanel = ({ stockId, stockName, onSelectStock }) => {
  const [industryAnalysis, setIndustryAnalysis] = useState(null);
  const [relatedStocks, setRelatedStocks] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 取得產業分析
  const fetchIndustryAnalysis = useCallback(async () => {
    if (!stockId) return;

    setLoading(true);
    setError(null);

    try {
      const [industryRes, relatedRes] = await Promise.all([
        fetch(`${API_BASE}/enhanced-ai/industry/${stockId}`),
        fetch(`${API_BASE}/enhanced-ai/related-stocks/${stockId}`),
      ]);

      const industryData = await industryRes.json();
      const relatedData = await relatedRes.json();

      if (industryData.success) {
        setIndustryAnalysis(industryData.data);
      }

      if (relatedData.success) {
        setRelatedStocks(relatedData.data);
      }
    } catch (e) {
      setError('載入失敗');
    } finally {
      setLoading(false);
    }
  }, [stockId]);

  useEffect(() => {
    fetchIndustryAnalysis();
  }, [fetchIndustryAnalysis]);

  // 取得輪動訊號顏色
  const getRotationColor = (signal) => {
    switch (signal) {
      case '強勢輪入':
        return 'text-emerald-400';
      case '輪入':
        return 'text-green-400';
      case '強勢輪出':
        return 'text-red-400';
      case '輪出':
        return 'text-orange-400';
      default:
        return 'text-slate-400';
    }
  };

  // 取得供應鏈影響顏色
  const getSupplyChainColor = (impact) => {
    switch (impact) {
      case '關鍵上游':
        return 'text-purple-400';
      case '重要下游':
        return 'text-blue-400';
      case '有連動':
        return 'text-cyan-400';
      default:
        return 'text-slate-400';
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-700/30 rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-slate-600 rounded w-1/3 mb-3"></div>
        <div className="h-20 bg-slate-600 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
        {error}
      </div>
    );
  }

  if (!industryAnalysis) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* 產業資訊 */}
      <div className="bg-slate-700/30 rounded-lg p-4">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <span>🏭</span> 產業連動分析
        </h4>

        <div className="grid grid-cols-2 gap-3 mb-3">
          {/* 所屬產業 */}
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-400 text-xs mb-1">所屬產業</div>
            <div className="text-white font-medium">
              {industryAnalysis.industry}
            </div>
          </div>

          {/* 產業連動分數 */}
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-400 text-xs mb-1">產業連動</div>
            <div className={`font-bold ${
              industryAnalysis.correlation_score >= 70 ? 'text-emerald-400' :
              industryAnalysis.correlation_score >= 50 ? 'text-yellow-400' :
              'text-red-400'
            }`}>
              {industryAnalysis.correlation_score}分
            </div>
          </div>

          {/* 輪動訊號 */}
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-400 text-xs mb-1">輪動訊號</div>
            <div className={`font-medium ${getRotationColor(industryAnalysis.rotation_signal)}`}>
              {industryAnalysis.rotation_signal}
            </div>
          </div>

          {/* 供應鏈影響 */}
          <div className="bg-slate-800/50 rounded p-2">
            <div className="text-slate-400 text-xs mb-1">供應鏈</div>
            <div className={`font-medium ${getSupplyChainColor(industryAnalysis.supply_chain_impact)}`}>
              {industryAnalysis.supply_chain_impact}
            </div>
          </div>
        </div>

        {/* 產業動能 */}
        {industryAnalysis.details?.industry_momentum !== undefined && (
          <div className="bg-slate-800/50 rounded p-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-xs">產業動能</span>
              <span className={`text-sm font-medium ${
                industryAnalysis.details.industry_momentum > 0 ? 'text-emerald-400' :
                industryAnalysis.details.industry_momentum < 0 ? 'text-red-400' :
                'text-slate-400'
              }`}>
                {industryAnalysis.details.industry_momentum > 0 ? '+' : ''}
                {industryAnalysis.details.industry_momentum?.toFixed(2)}%
              </span>
            </div>
            <div className="mt-2 h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  industryAnalysis.details.industry_momentum > 0 ? 'bg-emerald-500' : 'bg-red-500'
                }`}
                style={{
                  width: `${Math.min(100, Math.abs(industryAnalysis.details.industry_momentum) * 10 + 50)}%`,
                  marginLeft: industryAnalysis.details.industry_momentum < 0 ? 'auto' : 0,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 相關股票 */}
      {relatedStocks && (relatedStocks.same_industry?.length > 0 || relatedStocks.supply_chain?.length > 0) && (
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h4 className="text-white font-medium mb-3 flex items-center gap-2">
            <span>🔗</span> 相關股票
          </h4>

          {/* 同產業 */}
          {relatedStocks.same_industry?.length > 0 && (
            <div className="mb-3">
              <div className="text-slate-400 text-xs mb-2">同產業股票</div>
              <div className="flex flex-wrap gap-2">
                {relatedStocks.same_industry.map((id) => (
                  <button
                    key={id}
                    onClick={() => onSelectStock?.(id)}
                    className="px-2 py-1 bg-blue-500/20 text-blue-400 text-sm rounded hover:bg-blue-500/30 transition-colors cursor-pointer"
                    title={`查看 ${getStockName(id)}`}
                  >
                    {id} {getStockName(id)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 供應鏈 */}
          {relatedStocks.supply_chain?.length > 0 && (
            <div>
              <div className="text-slate-400 text-xs mb-2">供應鏈相關</div>
              <div className="flex flex-wrap gap-2">
                {relatedStocks.supply_chain.map((id) => (
                  <button
                    key={id}
                    onClick={() => onSelectStock?.(id)}
                    className="px-2 py-1 bg-purple-500/20 text-purple-400 text-sm rounded hover:bg-purple-500/30 transition-colors cursor-pointer"
                    title={`查看 ${getStockName(id)}`}
                  >
                    {id} {getStockName(id)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI 分析說明 */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <span className="text-lg">💡</span>
          <div className="text-sm text-slate-300">
            <strong className="text-white">增強版 AI 分析</strong>
            <p className="mt-1 text-slate-400">
              結合產業連動、供應鏈分析和輪動訊號，提供更全面的投資參考。
              {industryAnalysis.rotation_signal === '強勢輪入' && (
                <span className="text-emerald-400 ml-1">產業正處於資金輪入階段。</span>
              )}
              {industryAnalysis.rotation_signal === '強勢輪出' && (
                <span className="text-red-400 ml-1">產業正處於資金輪出階段，宜謹慎。</span>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedAIPanel;
