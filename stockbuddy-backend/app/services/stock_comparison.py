"""
StockBuddy V10.18 - 股票比較服務
提供多檔股票並排比較功能，幫助投資者快速比較不同股票的各項指標

V1.0 功能：
- 基本面指標比較（PE、PB、ROE、殖利率）
- 技術面指標比較（RSI、MACD、布林位置）
- 籌碼面比較（法人買賣超）
- 股價表現比較（漲跌幅、波動度）
- 雷達圖數據生成
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from app.services.cache_service import SmartTTL, StockCache
from app.services.fundamental_service import FundamentalService
from app.services.scoring_service import ScoringService


class StockComparison:
    """
    股票比較服務

    支援最多 5 檔股票的並排比較
    """

    # 快取
    _cache = {}
    _cache_time = {}

    # 比較指標配置
    COMPARISON_METRICS = {
        "fundamental": [
            {"key": "pe_ratio", "label": "本益比", "format": "number", "lower_better": True},
            {"key": "pb_ratio", "label": "股價淨值比", "format": "number", "lower_better": True},
            {"key": "dividend_yield_percent", "label": "殖利率 (%)", "format": "percent", "lower_better": False},
            {"key": "roe", "label": "ROE (%)", "format": "percent", "lower_better": False},
            {"key": "eps", "label": "每股盈餘", "format": "currency", "lower_better": False},
            {"key": "profit_margin", "label": "淨利率 (%)", "format": "percent", "lower_better": False},
            {"key": "debt_to_equity", "label": "負債比", "format": "number", "lower_better": True},
        ],
        "valuation": [
            {"key": "pe_ratio", "label": "本益比", "format": "number", "lower_better": True},
            {"key": "pb_ratio", "label": "P/B", "format": "number", "lower_better": True},
            {"key": "market_cap_display", "label": "市值", "format": "text", "lower_better": None},
        ],
        "growth": [
            {"key": "revenue_growth", "label": "營收成長率 (%)", "format": "percent", "lower_better": False},
            {"key": "earnings_growth", "label": "獲利成長率 (%)", "format": "percent", "lower_better": False},
            {"key": "roe", "label": "ROE (%)", "format": "percent", "lower_better": False},
        ],
        "dividend": [
            {"key": "dividend_yield_percent", "label": "現金殖利率 (%)", "format": "percent", "lower_better": False},
            {"key": "dividend_rate", "label": "每股股利", "format": "currency", "lower_better": False},
            {"key": "payout_ratio", "label": "配息率 (%)", "format": "percent", "lower_better": None},
        ],
    }

    # 雷達圖維度配置
    RADAR_DIMENSIONS = [
        {"key": "value_score", "label": "價值", "max": 100},
        {"key": "growth_score", "label": "成長", "max": 100},
        {"key": "dividend_score", "label": "股利", "max": 100},
        {"key": "safety_score", "label": "安全", "max": 100},
        {"key": "momentum_score", "label": "動能", "max": 100},
    ]

    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            ttl = SmartTTL.get_ttl("fundamental")
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()

    @classmethod
    async def compare_stocks(
        cls,
        stock_ids: List[str],
        metrics_type: str = "fundamental",
    ) -> Dict[str, Any]:
        """
        比較多檔股票

        Args:
            stock_ids: 股票代號列表（最多 5 檔）
            metrics_type: 比較類型 (fundamental/valuation/growth/dividend)

        Returns:
            {
                "stocks": [股票資料列表],
                "metrics": [比較指標配置],
                "comparison_table": [比較表格數據],
                "radar_data": [雷達圖數據],
                "best_picks": {各指標最佳股票}
            }
        """
        # 限制比較數量
        stock_ids = stock_ids[:5]

        if len(stock_ids) < 2:
            return {"error": "至少需要 2 檔股票進行比較"}

        # 檢查快取
        cache_key = f"comparison_{'-'.join(sorted(stock_ids))}_{metrics_type}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached

        # 取得所有股票的基本面資料
        stocks_data = []
        for stock_id in stock_ids:
            try:
                fundamental = await FundamentalService.get_fundamental_data(stock_id)
                stocks_data.append({
                    "stock_id": stock_id,
                    "fundamental": fundamental,
                })
            except Exception as e:
                print(f"取得 {stock_id} 資料失敗: {e}")
                stocks_data.append({
                    "stock_id": stock_id,
                    "fundamental": {},
                    "error": str(e),
                })

        # 取得比較指標配置
        metrics = cls.COMPARISON_METRICS.get(metrics_type, cls.COMPARISON_METRICS["fundamental"])

        # 建立比較表格
        comparison_table = cls._build_comparison_table(stocks_data, metrics)

        # 計算雷達圖數據
        radar_data = cls._calculate_radar_data(stocks_data)

        # 找出各指標最佳股票
        best_picks = cls._find_best_picks(stocks_data, metrics)

        result = {
            "stocks": [
                {
                    "stock_id": s["stock_id"],
                    "sector": s["fundamental"].get("sector"),
                    "industry": s["fundamental"].get("industry"),
                    "market_cap_display": s["fundamental"].get("market_cap_display"),
                }
                for s in stocks_data
            ],
            "metrics_type": metrics_type,
            "metrics": metrics,
            "comparison_table": comparison_table,
            "radar_data": radar_data,
            "radar_dimensions": cls.RADAR_DIMENSIONS,
            "best_picks": best_picks,
            "timestamp": datetime.now().isoformat(),
        }

        # 快取結果
        cls._set_cache(cache_key, result)

        return result

    @classmethod
    def _build_comparison_table(
        cls,
        stocks_data: List[Dict],
        metrics: List[Dict],
    ) -> List[Dict[str, Any]]:
        """建立比較表格數據"""
        table = []

        for metric in metrics:
            row = {
                "metric_key": metric["key"],
                "metric_label": metric["label"],
                "format": metric.get("format", "number"),
                "lower_better": metric.get("lower_better"),
                "values": [],
            }

            values = []
            for stock in stocks_data:
                value = stock["fundamental"].get(metric["key"])
                values.append({
                    "stock_id": stock["stock_id"],
                    "value": value,
                    "display": cls._format_value(value, metric.get("format", "number")),
                })

            # 標記最佳值
            valid_values = [v["value"] for v in values if v["value"] is not None]
            if valid_values:
                if metric.get("lower_better") is True:
                    best_value = min(valid_values)
                elif metric.get("lower_better") is False:
                    best_value = max(valid_values)
                else:
                    best_value = None

                for v in values:
                    v["is_best"] = (v["value"] == best_value) if best_value is not None else False

            row["values"] = values
            table.append(row)

        return table

    @classmethod
    def _calculate_radar_data(cls, stocks_data: List[Dict]) -> List[Dict[str, Any]]:
        """計算雷達圖數據"""
        radar_data = []

        for stock in stocks_data:
            f = stock["fundamental"]

            # 計算各維度分數 (0-100)
            scores = {
                "stock_id": stock["stock_id"],
                "value_score": cls._calculate_value_score(f),
                "growth_score": cls._calculate_growth_score(f),
                "dividend_score": cls._calculate_dividend_score(f),
                "safety_score": cls._calculate_safety_score(f),
                "momentum_score": 50,  # 需要技術分析數據，暫時使用固定值
            }

            radar_data.append(scores)

        return radar_data

    @classmethod
    def _calculate_value_score(cls, f: Dict) -> int:
        """計算價值分數"""
        score = 50
        pe = f.get("pe_ratio")
        pb = f.get("pb_ratio")

        if pe is not None and pe > 0:
            if pe < 10:
                score += 30
            elif pe < 15:
                score += 20
            elif pe < 25:
                score += 5
            elif pe > 40:
                score -= 20

        if pb is not None and pb > 0:
            if pb < 1:
                score += 20
            elif pb < 1.5:
                score += 10
            elif pb > 3:
                score -= 15

        return max(0, min(100, score))

    @classmethod
    def _calculate_growth_score(cls, f: Dict) -> int:
        """計算成長分數"""
        score = 50
        roe = f.get("roe")
        rev_growth = f.get("revenue_growth")
        earn_growth = f.get("earnings_growth")

        if roe is not None:
            if roe > 20:
                score += 25
            elif roe > 15:
                score += 15
            elif roe > 10:
                score += 5
            elif roe < 5:
                score -= 15

        if rev_growth is not None:
            if rev_growth > 20:
                score += 15
            elif rev_growth > 10:
                score += 10
            elif rev_growth < -10:
                score -= 15

        if earn_growth is not None:
            if earn_growth > 30:
                score += 10
            elif earn_growth > 15:
                score += 5

        return max(0, min(100, score))

    @classmethod
    def _calculate_dividend_score(cls, f: Dict) -> int:
        """計算股利分數"""
        score = 50
        div_yield = f.get("dividend_yield_percent")
        payout = f.get("payout_ratio")

        if div_yield is not None:
            if div_yield > 7:
                score += 35
            elif div_yield > 5:
                score += 25
            elif div_yield > 3:
                score += 15
            elif div_yield > 1:
                score += 5
            else:
                score -= 10

        if payout is not None:
            if 30 <= payout <= 70:
                score += 15  # 配息率適中
            elif payout > 90:
                score -= 10  # 配息率過高

        return max(0, min(100, score))

    @classmethod
    def _calculate_safety_score(cls, f: Dict) -> int:
        """計算安全分數"""
        score = 50
        debt_equity = f.get("debt_to_equity")
        current_ratio = f.get("current_ratio")

        if debt_equity is not None:
            if debt_equity < 30:
                score += 25
            elif debt_equity < 50:
                score += 15
            elif debt_equity < 100:
                score += 5
            elif debt_equity > 150:
                score -= 20

        if current_ratio is not None:
            if current_ratio > 2:
                score += 20
            elif current_ratio > 1.5:
                score += 10
            elif current_ratio < 1:
                score -= 15

        return max(0, min(100, score))

    @classmethod
    def _find_best_picks(
        cls,
        stocks_data: List[Dict],
        metrics: List[Dict],
    ) -> Dict[str, str]:
        """找出各指標最佳股票"""
        best_picks = {}

        for metric in metrics:
            key = metric["key"]
            lower_better = metric.get("lower_better")

            if lower_better is None:
                continue

            values = []
            for stock in stocks_data:
                value = stock["fundamental"].get(key)
                if value is not None:
                    values.append((stock["stock_id"], value))

            if values:
                if lower_better:
                    best = min(values, key=lambda x: x[1])
                else:
                    best = max(values, key=lambda x: x[1])
                best_picks[key] = best[0]

        return best_picks

    @classmethod
    def _format_value(cls, value: Any, format_type: str) -> str:
        """格式化數值"""
        if value is None:
            return "N/A"

        try:
            if format_type == "number":
                return f"{value:.2f}"
            elif format_type == "percent":
                return f"{value:.2f}%"
            elif format_type == "currency":
                return f"${value:.2f}"
            else:
                return str(value)
        except:
            return str(value)

    @classmethod
    async def get_quick_comparison(
        cls,
        stock_ids: List[str],
    ) -> Dict[str, Any]:
        """
        快速比較（簡化版本）

        返回關鍵指標的快速對比
        """
        stock_ids = stock_ids[:5]

        if len(stock_ids) < 2:
            return {"error": "至少需要 2 檔股票進行比較"}

        quick_data = []
        for stock_id in stock_ids:
            try:
                fundamental = await FundamentalService.get_fundamental_data(stock_id)
                quick_data.append({
                    "stock_id": stock_id,
                    "pe_ratio": fundamental.get("pe_ratio"),
                    "pb_ratio": fundamental.get("pb_ratio"),
                    "dividend_yield": fundamental.get("dividend_yield_percent"),
                    "roe": fundamental.get("roe"),
                    "market_cap_display": fundamental.get("market_cap_display"),
                    "valuation_comment": fundamental.get("valuation_comment"),
                })
            except Exception as e:
                quick_data.append({
                    "stock_id": stock_id,
                    "error": str(e),
                })

        return {
            "stocks": quick_data,
            "count": len(quick_data),
            "timestamp": datetime.now().isoformat(),
        }


# 便捷函數
async def compare_stocks(stock_ids: List[str], metrics_type: str = "fundamental"):
    return await StockComparison.compare_stocks(stock_ids, metrics_type)

async def get_quick_comparison(stock_ids: List[str]):
    return await StockComparison.get_quick_comparison(stock_ids)
