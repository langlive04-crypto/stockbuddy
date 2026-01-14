"""
V10.40: 歷史數據補齊服務

為 ML 訓練補齊 55 特徵所需的所有數據源：
- 價格/動能/成交量/波動率: Yahoo Finance OHLCV
- 籌碼面: Yahoo Finance institutional holders + 估算
- 基本面: Yahoo Finance ticker.info
- 市場環境: ^TWII 大盤指數
- 評分: 訓練時使用中性值

目標: 將特徵完整度從 49% 提升到 90%+
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class HistoricalDataEnricher:
    """
    歷史數據補齊器

    為 ML 訓練準備完整的 55 維特徵所需數據
    """

    def __init__(self):
        self._market_cache = {}  # 大盤數據快取
        self._fundamental_cache = {}  # 基本面數據快取

    def get_market_data(self, period: str = "1y"):
        """
        獲取大盤指數數據 (^TWII)

        Returns:
            DataFrame with market index data
        """
        import yfinance as yf

        cache_key = f"market_{period}"
        if cache_key in self._market_cache:
            return self._market_cache[cache_key]

        try:
            twii = yf.Ticker("^TWII")
            market_hist = twii.history(period=period)

            if not market_hist.empty:
                # 計算大盤技術指標
                market_hist['Market_MA5'] = market_hist['Close'].rolling(5).mean()
                market_hist['Market_MA20'] = market_hist['Close'].rolling(20).mean()
                market_hist['Market_Change'] = market_hist['Close'].pct_change() * 100
                market_hist['Market_Volatility'] = market_hist['Close'].rolling(20).std() / market_hist['Close'].rolling(20).mean() * 100

                # 大盤趨勢 (1=多頭, -1=空頭, 0=盤整)
                market_hist['Market_Trend'] = np.where(
                    market_hist['Market_MA5'] > market_hist['Market_MA20'], 1,
                    np.where(market_hist['Market_MA5'] < market_hist['Market_MA20'], -1, 0)
                )

                self._market_cache[cache_key] = market_hist
                logger.info(f"[DataEnricher] 大盤數據載入成功: {len(market_hist)} 筆")
                return market_hist
        except Exception as e:
            logger.warning(f"[DataEnricher] 大盤數據載入失敗: {e}")

        return None

    def get_fundamental_data(self, stock_id: str) -> Dict[str, Any]:
        """
        獲取股票基本面數據

        使用 yfinance ticker.info 獲取:
        - PE ratio
        - PB ratio
        - Dividend yield
        - Profit margins
        - ROE
        - Debt ratio
        """
        import yfinance as yf

        if stock_id in self._fundamental_cache:
            return self._fundamental_cache[stock_id]

        try:
            ticker = yf.Ticker(f"{stock_id}.TW")
            info = ticker.info

            fundamental = {
                # PE 相關
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "forward_pe": info.get("forwardPE"),

                # PB 相關
                "pb_ratio": info.get("priceToBook"),

                # 殖利率
                "dividend_yield": info.get("dividendYield", 0) or 0,
                "dividend_rate": info.get("dividendRate", 0) or 0,

                # 獲利能力
                "profit_margin": info.get("profitMargins", 0) or 0,
                "gross_margin": info.get("grossMargins", 0) or 0,
                "operating_margin": info.get("operatingMargins", 0) or 0,

                # 成長性
                "revenue_growth": info.get("revenueGrowth", 0) or 0,
                "earnings_growth": info.get("earningsGrowth", 0) or 0,

                # 效率指標
                "roe": info.get("returnOnEquity", 0) or 0,
                "roa": info.get("returnOnAssets", 0) or 0,

                # 財務結構
                "debt_to_equity": info.get("debtToEquity", 0) or 0,
                "current_ratio": info.get("currentRatio", 0) or 0,

                # 其他
                "market_cap": info.get("marketCap", 0) or 0,
                "beta": info.get("beta", 1) or 1,
            }

            self._fundamental_cache[stock_id] = fundamental
            return fundamental

        except Exception as e:
            logger.debug(f"[DataEnricher] {stock_id} 基本面數據獲取失敗: {e}")
            return self._get_default_fundamental()

    def _get_default_fundamental(self) -> Dict[str, Any]:
        """返回預設基本面數據 (產業平均值)"""
        return {
            "pe_ratio": 15.0,  # 台股平均
            "forward_pe": 15.0,
            "pb_ratio": 1.5,
            "dividend_yield": 0.03,  # 3%
            "dividend_rate": 0,
            "profit_margin": 0.1,  # 10%
            "gross_margin": 0.25,  # 25%
            "operating_margin": 0.1,
            "revenue_growth": 0.05,  # 5%
            "earnings_growth": 0.05,
            "roe": 0.1,  # 10%
            "roa": 0.05,
            "debt_to_equity": 0.5,
            "current_ratio": 1.5,
            "market_cap": 0,
            "beta": 1.0,
        }

    def enrich_stock_data(
        self,
        stock_id: str,
        hist_row,  # pandas Series (當天數據)
        hist_df,   # pandas DataFrame (完整歷史)
        row_index: int,
        market_hist=None,
        fundamental: Dict = None,
    ) -> Dict[str, Any]:
        """
        補齊單筆股票數據，準備萃取 55 特徵

        Args:
            stock_id: 股票代碼
            hist_row: 當天 K 線數據
            hist_df: 完整歷史 DataFrame
            row_index: 當前索引
            market_hist: 大盤數據 (可選)
            fundamental: 基本面數據 (可選)

        Returns:
            完整的 stock_data dict，可傳入 ml_feature_engine
        """

        # 基本 OHLCV
        stock_data = {
            "stock_id": stock_id,
            "close": float(hist_row['Close']),
            "open": float(hist_row['Open']),
            "high": float(hist_row['High']),
            "low": float(hist_row['Low']),
            "volume": float(hist_row['Volume']),
        }

        # 前一日收盤
        if row_index > 0:
            stock_data["prev_close"] = float(hist_df.iloc[row_index - 1]['Close'])

        # 均線 (如果有計算)
        for col in ['MA5', 'MA20', 'MA60', 'Volume_MA20', 'RSI', 'Volatility']:
            if col in hist_df.columns and not np.isnan(hist_row.get(col, np.nan)):
                key = col.lower().replace('volume_ma20', 'volume_ma20')
                if col == 'MA5':
                    stock_data['ma5'] = float(hist_row[col])
                elif col == 'MA20':
                    stock_data['ma20'] = float(hist_row[col])
                elif col == 'MA60':
                    stock_data['ma60'] = float(hist_row[col])
                elif col == 'Volume_MA20':
                    stock_data['volume_ma20'] = float(hist_row[col])
                elif col == 'RSI':
                    stock_data['rsi'] = float(hist_row[col])
                elif col == 'Volatility':
                    stock_data['volatility'] = float(hist_row[col])

        # 補齊籌碼面數據 (使用估算)
        stock_data.update(self._estimate_chip_data(hist_df, row_index))

        # 補齊基本面數據
        if fundamental:
            stock_data.update(self._format_fundamental_data(fundamental))

        # 補齊市場環境數據
        if market_hist is not None:
            stock_data.update(self._get_market_context(market_hist, hist_row.name))

        # 補齊評分 (訓練時使用中性值)
        stock_data["ai_score"] = 50.0  # 中性評分
        stock_data["confidence"] = 0.5  # 中性信心

        return stock_data

    def _estimate_chip_data(self, hist_df, row_index: int) -> Dict[str, float]:
        """
        估算籌碼面數據

        由於歷史籌碼數據難以獲取，使用技術指標估算法人動向：
        - 量價齊揚 + 價格上漲 → 可能有法人買盤
        - 量縮價跌 → 可能有法人賣盤
        """
        chip_data = {
            "foreign_net_ratio": 0.0,
            "foreign_net_5d": 0.0,
            "foreign_trend": 0,
            "trust_net_ratio": 0.0,
            "trust_net_5d": 0.0,
            "dealer_net_ratio": 0.0,
            "institutional_score": 0.0,
            "institutional_consensus": 0.0,
        }

        try:
            # 使用量價關係估算法人動向
            if row_index >= 5:
                recent = hist_df.iloc[row_index-4:row_index+1]

                # 計算量價趨勢
                price_change = (recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0]
                volume_avg = recent['Volume'].mean()
                current_volume = recent['Volume'].iloc[-1]
                volume_ratio = current_volume / volume_avg if volume_avg > 0 else 1

                # 估算法人動向 (-1 到 1)
                # 量增價漲 → 正向，量縮價跌 → 負向
                estimated_flow = price_change * 10 * (volume_ratio - 1)
                estimated_flow = np.clip(estimated_flow, -1, 1)

                chip_data["foreign_net_ratio"] = estimated_flow * 0.5  # 外資占一半
                chip_data["trust_net_ratio"] = estimated_flow * 0.3   # 投信占30%
                chip_data["dealer_net_ratio"] = estimated_flow * 0.2  # 自營占20%

                # 5日累計
                chip_data["foreign_net_5d"] = estimated_flow * 5
                chip_data["trust_net_5d"] = estimated_flow * 3

                # 趨勢 (連續方向)
                trend = 0
                for i in range(1, min(5, row_index + 1)):
                    if hist_df.iloc[row_index - i + 1]['Close'] > hist_df.iloc[row_index - i]['Close']:
                        trend += 1
                    else:
                        trend -= 1
                chip_data["foreign_trend"] = np.sign(trend)

                # 綜合評分
                chip_data["institutional_score"] = estimated_flow * 50  # -50 到 50
                chip_data["institutional_consensus"] = abs(estimated_flow)  # 共識度 0-1

        except Exception as e:
            logger.debug(f"[DataEnricher] 籌碼估算失敗: {e}")

        return chip_data

    def _format_fundamental_data(self, fundamental: Dict) -> Dict[str, float]:
        """格式化基本面數據"""
        return {
            # PE 標準化 (假設合理範圍 5-50)
            "pe_normalized": np.clip((fundamental.get("pe_ratio", 15) - 5) / 45, 0, 1),

            # PB 標準化 (假設合理範圍 0.5-5)
            "pb_normalized": np.clip((fundamental.get("pb_ratio", 1.5) - 0.5) / 4.5, 0, 1),

            # 殖利率 (直接使用)
            "dividend_yield": fundamental.get("dividend_yield", 0) * 100,  # 轉換為百分比

            # 營收成長率
            "revenue_growth": fundamental.get("revenue_growth", 0) * 100,

            # 毛利率
            "profit_margin": fundamental.get("profit_margin", 0) * 100,

            # ROE
            "roe": fundamental.get("roe", 0) * 100,

            # 負債比
            "debt_ratio": np.clip(fundamental.get("debt_to_equity", 0) / 2, 0, 1),  # 標準化

            # EPS 成長率
            "eps_growth": fundamental.get("earnings_growth", 0) * 100,
        }

    def _get_market_context(self, market_hist, date) -> Dict[str, float]:
        """獲取市場環境數據"""
        market_data = {
            "market_trend": 0,
            "sector_momentum": 0,
            "market_volatility": 0,
            "industry_heat": 0.5,  # 預設中性
        }

        try:
            # 嘗試找到對應日期的大盤數據
            if date in market_hist.index:
                row = market_hist.loc[date]
                market_data["market_trend"] = float(row.get('Market_Trend', 0))
                market_data["market_volatility"] = float(row.get('Market_Volatility', 0)) if not np.isnan(row.get('Market_Volatility', np.nan)) else 0

                # 大盤動能作為產業動能的代理
                market_change = float(row.get('Market_Change', 0)) if not np.isnan(row.get('Market_Change', np.nan)) else 0
                market_data["sector_momentum"] = np.clip(market_change, -5, 5)

                # 產業熱度 (使用大盤量能估算)
                if 'Volume' in market_hist.columns and not np.isnan(row.get('Volume', np.nan)):
                    avg_vol = market_hist['Volume'].rolling(20).mean().loc[date] if date in market_hist.index else 0
                    if avg_vol > 0:
                        market_data["industry_heat"] = np.clip(row['Volume'] / avg_vol, 0.5, 2.0) / 2

        except Exception as e:
            logger.debug(f"[DataEnricher] 市場環境獲取失敗: {e}")

        return market_data

    def prepare_history_for_features(
        self,
        hist_df,
        row_index: int,
        lookback: int = 60
    ) -> List[Dict]:
        """
        準備歷史數據列表 (用於 ml_feature_engine.extract_features)

        Args:
            hist_df: 完整歷史 DataFrame
            row_index: 當前索引
            lookback: 回溯天數

        Returns:
            List of dict, 過去 N 天的數據
        """
        history = []
        start = max(0, row_index - lookback + 1)

        for i in range(start, row_index + 1):
            row = hist_df.iloc[i]
            history.append({
                "close": float(row['Close']) if not np.isnan(row['Close']) else None,
                "open": float(row['Open']) if not np.isnan(row['Open']) else None,
                "high": float(row['High']) if not np.isnan(row['High']) else None,
                "low": float(row['Low']) if not np.isnan(row['Low']) else None,
                "volume": float(row['Volume']) if not np.isnan(row['Volume']) else None,
                "ma5": float(row['MA5']) if 'MA5' in hist_df.columns and not np.isnan(row.get('MA5', np.nan)) else None,
                "ma20": float(row['MA20']) if 'MA20' in hist_df.columns and not np.isnan(row.get('MA20', np.nan)) else None,
            })

        return history


# 單例
_enricher = None


def get_enricher() -> HistoricalDataEnricher:
    """獲取數據補齊器單例"""
    global _enricher
    if _enricher is None:
        _enricher = HistoricalDataEnricher()
    return _enricher
