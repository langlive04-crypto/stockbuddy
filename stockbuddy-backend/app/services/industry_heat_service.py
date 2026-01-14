"""
V10.38: 動態產業熱度計算服務

取代硬編碼的 HOT_INDUSTRIES，基於市場數據自動評估產業熱度

計算邏輯：
1. 取得產業內股票近期報酬表現
2. 計算產業外資淨買超趨勢
3. 計算成交量變化趨勢
4. 綜合評分 (-10 ~ +10)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class IndustryHeat:
    """產業熱度數據"""
    industry: str
    heat_score: int              # -10 ~ +10 的熱度分數
    avg_return_5d: float         # 5 日平均報酬 (%)
    avg_return_20d: float        # 20 日平均報酬 (%)
    foreign_net_ratio: float     # 外資淨買超比例 (-1 ~ +1)
    volume_trend: float          # 成交量趨勢 (-1 ~ +1)
    momentum_score: float        # 動能分數 (-1 ~ +1)
    stock_count: int             # 產業內股票數量
    updated_at: str
    data_source: str             # "calculated" or "fallback"


class IndustryHeatService:
    """
    動態產業熱度服務

    計算邏輯：
    1. 取得產業內所有股票 20 天報酬
    2. 計算產業外資淨買超趨勢
    3. 計算成交量變化
    4. 綜合評分 (-10 ~ +10)

    使用方式：
    ```python
    score = await IndustryHeatService.get_industry_score("AI")
    heat = await IndustryHeatService.get_industry_heat("半導體")
    ```
    """

    # 快取設定
    _cache: Dict[str, IndustryHeat] = {}
    _cache_ttl = 3600  # 1 小時快取
    _last_update: Dict[str, float] = {}
    _industry_stocks_cache: Dict[str, List[str]] = {}

    # 備用硬編碼分數（當 API 失敗時使用）
    # 這些值仍保留但僅作為 fallback
    FALLBACK_SCORES = {
        # 熱門題材
        "AI": 10, "AI伺服器": 10, "HBM": 8, "GB200": 8,
        "半導體": 6, "IC設計": 5, "先進製程": 7, "先進封裝": 6,
        "封測": 4, "載板": 4, "矽智財": 5,
        # 成長型
        "電動車": 5, "充電樁": 4, "綠能": 3, "儲能": 3,
        "5G": 2, "網通": 2, "電信": 1,
        # 穩健型
        "金融": 0, "金控": 0, "銀行": 0,
        "ETF": 0, "高股息": 1,
        # 防禦型
        "食品": -1, "民生消費": 0,
        # 傳產
        "傳產": -2, "塑膠": -3, "石化": -2, "水泥": -3,
        "鋼鐵": -2, "紡織": -2, "造紙": -2,
        # 景氣循環
        "航運": -1, "散裝": -1, "貨櫃": 0,
        "觀光": 1, "零售": 0,
    }

    @classmethod
    def _build_industry_stocks_map(cls) -> Dict[str, List[str]]:
        """從 themes.py 建立產業-股票對照表"""
        if cls._industry_stocks_cache:
            return cls._industry_stocks_cache

        try:
            from .themes import INDUSTRY_MAP

            industry_stocks = {}
            for stock_id, info in INDUSTRY_MAP.items():
                industry = info.get("industry", "")
                if industry:
                    if industry not in industry_stocks:
                        industry_stocks[industry] = []
                    industry_stocks[industry].append(stock_id)

                # 也將 tags 視為產業分類
                for tag in info.get("tags", []):
                    if tag not in industry_stocks:
                        industry_stocks[tag] = []
                    if stock_id not in industry_stocks[tag]:
                        industry_stocks[tag].append(stock_id)

            cls._industry_stocks_cache = industry_stocks
            logger.info(f"[IndustryHeat] 建立產業對照表: {len(industry_stocks)} 個產業")
            return industry_stocks

        except Exception as e:
            logger.error(f"[IndustryHeat] 建立產業對照表失敗: {e}")
            return {}

    @classmethod
    def _get_industry_stocks(cls, industry: str) -> List[str]:
        """取得產業內的股票清單"""
        industry_map = cls._build_industry_stocks_map()
        return industry_map.get(industry, [])

    @classmethod
    def _is_cache_valid(cls, key: str) -> bool:
        """檢查快取是否有效"""
        if key not in cls._cache:
            return False
        last = cls._last_update.get(key, 0)
        return (datetime.now().timestamp() - last) < cls._cache_ttl

    @classmethod
    async def get_industry_heat(cls, industry: str) -> IndustryHeat:
        """
        取得產業熱度數據

        Args:
            industry: 產業名稱（如 "AI", "半導體", "金融"）

        Returns:
            IndustryHeat 數據物件
        """
        # 檢查快取
        if cls._is_cache_valid(industry):
            return cls._cache[industry]

        try:
            # 計算動態熱度
            heat = await cls._calculate_heat(industry)
            cls._cache[industry] = heat
            cls._last_update[industry] = datetime.now().timestamp()
            return heat

        except Exception as e:
            logger.warning(f"[IndustryHeat] 計算失敗 {industry}: {e}")
            return cls._get_fallback(industry)

    @classmethod
    async def get_industry_score(cls, industry: str) -> int:
        """
        快速取得產業熱度分數 (-10 ~ +10)

        這是主要的對外介面，用於取代原本的 HOT_INDUSTRIES 字典
        """
        heat = await cls.get_industry_heat(industry)
        return heat.heat_score

    @classmethod
    async def _calculate_heat(cls, industry: str) -> IndustryHeat:
        """計算產業熱度"""
        stocks = cls._get_industry_stocks(industry)

        if not stocks:
            logger.debug(f"[IndustryHeat] 產業 {industry} 無對應股票，使用 fallback")
            return cls._get_fallback(industry)

        # 計算各項指標
        avg_return_5d = await cls._calc_avg_return(stocks, days=5)
        avg_return_20d = await cls._calc_avg_return(stocks, days=20)
        foreign_ratio = await cls._calc_foreign_ratio(stocks)
        volume_trend = await cls._calc_volume_trend(stocks)
        momentum = await cls._calc_momentum(stocks)

        # 綜合評分
        # 權重：20日報酬 35% + 5日報酬 20% + 外資 25% + 成交量 10% + 動能 10%
        raw_score = (
            avg_return_20d * 0.35 +
            avg_return_5d * 0.20 +
            foreign_ratio * 10 * 0.25 +  # 放大到 -10 ~ +10 範圍
            volume_trend * 5 * 0.10 +
            momentum * 5 * 0.10
        )

        # 標準化到 -10 ~ +10 並取整
        heat_score = max(-10, min(10, int(round(raw_score))))

        return IndustryHeat(
            industry=industry,
            heat_score=heat_score,
            avg_return_5d=round(avg_return_5d, 2),
            avg_return_20d=round(avg_return_20d, 2),
            foreign_net_ratio=round(foreign_ratio, 3),
            volume_trend=round(volume_trend, 3),
            momentum_score=round(momentum, 3),
            stock_count=len(stocks),
            updated_at=datetime.now().isoformat(),
            data_source="calculated"
        )

    @classmethod
    async def _calc_avg_return(cls, stocks: List[str], days: int) -> float:
        """
        計算產業平均報酬率

        Returns:
            報酬率百分比 (-20 ~ +20 範圍)
        """
        try:
            from .twse_api import get_twse_service
            twse = await get_twse_service()

            returns = []
            sample_count = min(len(stocks), 20)  # 最多取 20 檔代表性股票

            for stock_id in stocks[:sample_count]:
                try:
                    # 取得歷史數據
                    history = await twse.get_history(stock_id, days=days + 5)
                    if history and len(history) >= days:
                        closes = [h.get("close", 0) for h in history if h.get("close")]
                        if len(closes) >= days:
                            ret = (closes[-1] - closes[-days]) / closes[-days] * 100
                            returns.append(ret)
                except Exception:
                    continue

            if returns:
                return sum(returns) / len(returns)
            return 0

        except Exception as e:
            logger.debug(f"[IndustryHeat] 計算報酬失敗: {e}")
            return 0

    @classmethod
    async def _calc_foreign_ratio(cls, stocks: List[str]) -> float:
        """
        計算外資淨買超比例

        Returns:
            -1 ~ +1 的標準化分數
        """
        try:
            from .twse_api import get_twse_service
            twse = await get_twse_service()

            buy_count = 0
            sell_count = 0
            sample_count = min(len(stocks), 15)

            for stock_id in stocks[:sample_count]:
                try:
                    institutional = await twse.get_institutional(stock_id)
                    if institutional:
                        foreign_net = institutional.get("foreign_net", 0)
                        if foreign_net > 0:
                            buy_count += 1
                        elif foreign_net < 0:
                            sell_count += 1
                except Exception:
                    continue

            total = buy_count + sell_count
            if total > 0:
                return (buy_count - sell_count) / total
            return 0

        except Exception as e:
            logger.debug(f"[IndustryHeat] 計算外資比例失敗: {e}")
            return 0

    @classmethod
    async def _calc_volume_trend(cls, stocks: List[str]) -> float:
        """
        計算成交量趨勢

        Returns:
            -1 ~ +1 的標準化分數
        """
        try:
            from .twse_api import get_twse_service
            twse = await get_twse_service()

            volume_ratios = []
            sample_count = min(len(stocks), 15)

            for stock_id in stocks[:sample_count]:
                try:
                    history = await twse.get_history(stock_id, days=25)
                    if history and len(history) >= 20:
                        volumes = [h.get("volume", 0) for h in history if h.get("volume")]
                        if len(volumes) >= 20:
                            recent_vol = sum(volumes[-5:]) / 5
                            avg_vol = sum(volumes[-20:]) / 20
                            if avg_vol > 0:
                                ratio = recent_vol / avg_vol
                                volume_ratios.append(ratio)
                except Exception:
                    continue

            if volume_ratios:
                avg_ratio = sum(volume_ratios) / len(volume_ratios)
                # 標準化: 1.0 = 0, 1.5 = +1, 0.5 = -1
                return max(-1, min(1, (avg_ratio - 1) * 2))
            return 0

        except Exception as e:
            logger.debug(f"[IndustryHeat] 計算成交量趨勢失敗: {e}")
            return 0

    @classmethod
    async def _calc_momentum(cls, stocks: List[str]) -> float:
        """
        計算動能分數

        Returns:
            -1 ~ +1 的標準化分數
        """
        try:
            from .twse_api import get_twse_service
            twse = await get_twse_service()

            momentum_scores = []
            sample_count = min(len(stocks), 15)

            for stock_id in stocks[:sample_count]:
                try:
                    history = await twse.get_history(stock_id, days=15)
                    if history and len(history) >= 10:
                        closes = [h.get("close", 0) for h in history if h.get("close")]
                        if len(closes) >= 10:
                            # 短期動能: 5日報酬 vs 10日報酬
                            ret_5d = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] else 0
                            ret_10d = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] else 0

                            # 動能加速中 = 正向
                            if ret_5d > ret_10d / 2:
                                momentum_scores.append(0.5)
                            elif ret_5d < ret_10d / 2:
                                momentum_scores.append(-0.5)
                            else:
                                momentum_scores.append(0)
                except Exception:
                    continue

            if momentum_scores:
                return sum(momentum_scores) / len(momentum_scores)
            return 0

        except Exception as e:
            logger.debug(f"[IndustryHeat] 計算動能失敗: {e}")
            return 0

    @classmethod
    def _get_fallback(cls, industry: str) -> IndustryHeat:
        """取得備用熱度分數"""
        score = cls.FALLBACK_SCORES.get(industry, 0)
        return IndustryHeat(
            industry=industry,
            heat_score=score,
            avg_return_5d=0,
            avg_return_20d=0,
            foreign_net_ratio=0,
            volume_trend=0,
            momentum_score=0,
            stock_count=0,
            updated_at=datetime.now().isoformat(),
            data_source="fallback"
        )

    @classmethod
    async def get_all_industry_heat(cls) -> List[IndustryHeat]:
        """
        取得所有產業的熱度排行

        Returns:
            按熱度分數排序的產業列表
        """
        industry_map = cls._build_industry_stocks_map()
        results = []

        for industry in industry_map.keys():
            try:
                heat = await cls.get_industry_heat(industry)
                results.append(heat)
            except Exception as e:
                logger.debug(f"[IndustryHeat] 取得 {industry} 失敗: {e}")
                results.append(cls._get_fallback(industry))

        # 按熱度分數排序（高到低）
        results.sort(key=lambda x: x.heat_score, reverse=True)
        return results

    @classmethod
    def clear_cache(cls):
        """清除快取"""
        cls._cache.clear()
        cls._last_update.clear()
        logger.info("[IndustryHeat] 快取已清除")


# 便捷函數
async def get_industry_score(industry: str) -> int:
    """
    快速取得產業熱度分數 (-10 ~ +10)

    這是用來取代硬編碼 HOT_INDUSTRIES 的主要函數

    Usage:
        score = await get_industry_score("AI")  # 返回 -10 ~ +10
    """
    return await IndustryHeatService.get_industry_score(industry)


async def get_industry_heat(industry: str) -> dict:
    """取得完整的產業熱度資訊"""
    heat = await IndustryHeatService.get_industry_heat(industry)
    return asdict(heat)
