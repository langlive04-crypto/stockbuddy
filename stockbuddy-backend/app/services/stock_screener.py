"""
StockBuddy V10.17 - 選股篩選器服務
提供多條件組合篩選功能，幫助投資者快速找到符合條件的股票

V1.0 功能：
- 基本面篩選（本益比、股價淨值比、殖利率、ROE）
- 技術面篩選（RSI、均線多頭排列、布林通道位置）
- 籌碼面篩選（三大法人買賣超）
- 市值篩選（大型股、中型股、小型股）
- 預設篩選策略（價值投資、成長股、高殖利率、動能股）
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import asyncio

from app.services.cache_service import SmartTTL, StockCache
from app.services.twse_openapi import TWSEOpenAPI
from app.services.fundamental_service import FundamentalService
from app.services.scoring_service import ScoringService
from app.services.portfolio_service import get_stock_name  # V10.17: 股票名稱對照


class ScreenerPreset(str, Enum):
    """預設篩選策略"""
    VALUE = "value"              # 價值投資
    GROWTH = "growth"            # 成長股
    HIGH_DIVIDEND = "dividend"   # 高殖利率
    MOMENTUM = "momentum"        # 動能股
    DEFENSIVE = "defensive"      # 防禦型
    SMALL_CAP = "small_cap"      # 小型成長股
    BLUE_CHIP = "blue_chip"      # 績優藍籌


class MarketCapSize(str, Enum):
    """市值規模"""
    LARGE = "large"     # 大型股 > 500億
    MID = "mid"         # 中型股 50-500億
    SMALL = "small"     # 小型股 < 50億
    ALL = "all"         # 不限


class StockScreener:
    """
    選股篩選器服務

    支援多條件組合篩選，包含：
    - 基本面條件
    - 技術面條件
    - 籌碼面條件
    - 市值規模
    - 產業類別
    """

    # 快取
    _cache = {}
    _cache_time = {}

    # 熱門股票池（用於快速篩選）
    STOCK_POOL = [
        # 電子權值股
        "2330", "2317", "2454", "2308", "2382", "2303", "2412", "3711", "2379", "3008",
        # 金融股
        "2881", "2882", "2891", "2886", "2884", "2885", "2892", "5880", "2887", "2883",
        # 傳產績優
        "1301", "1303", "1326", "2002", "2207", "1101", "1102", "1216", "2912", "9910",
        # 熱門中小型股
        "2603", "2609", "3037", "2357", "3045", "2049", "6505", "3034", "2327", "2408",
        # 生技醫療
        "4904", "6446", "1707", "1760", "6472", "4174", "4743", "6669", "1734", "4147",
        # AI/半導體
        "3661", "2449", "3443", "6770", "3529", "2376", "3533", "6488", "2363", "2344",
        # ETF 除外的其他熱門股
        "2301", "2395", "9904", "2377", "1402", "6176", "3231", "5871", "2474", "2345",
    ]

    # 預設篩選條件
    PRESET_FILTERS = {
        ScreenerPreset.VALUE: {
            "name": "價值投資",
            "description": "本益比合理、股價低於淨值、穩定配息",
            "pe_max": 15,
            "pb_max": 1.5,
            "dividend_yield_min": 3.0,
            "roe_min": 8,
        },
        ScreenerPreset.GROWTH: {
            "name": "成長股",
            "description": "高ROE、營收成長、本益比可接受較高",
            "pe_max": 30,
            "roe_min": 15,
            "revenue_growth_min": 10,
        },
        ScreenerPreset.HIGH_DIVIDEND: {
            "name": "高殖利率",
            "description": "殖利率 > 5%，穩定配息",
            "dividend_yield_min": 5.0,
            "pe_max": 20,
        },
        ScreenerPreset.MOMENTUM: {
            "name": "動能股",
            "description": "技術面強勢、法人買超",
            "technical_score_min": 70,
            "foreign_net_min": 1000,
        },
        ScreenerPreset.DEFENSIVE: {
            "name": "防禦型",
            "description": "低波動、穩定配息、財務穩健",
            "dividend_yield_min": 3.0,
            "debt_ratio_max": 50,
            "market_cap_size": MarketCapSize.LARGE,
        },
        ScreenerPreset.SMALL_CAP: {
            "name": "小型成長股",
            "description": "市值小但成長潛力大",
            "market_cap_size": MarketCapSize.SMALL,
            "roe_min": 12,
            "revenue_growth_min": 15,
        },
        ScreenerPreset.BLUE_CHIP: {
            "name": "績優藍籌",
            "description": "大型權值股，穩定獲利",
            "market_cap_size": MarketCapSize.LARGE,
            "roe_min": 10,
            "pe_max": 25,
        },
    }

    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            ttl = SmartTTL.get_ttl("recommend")
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()

    @classmethod
    async def screen_stocks(
        cls,
        # 基本面篩選
        pe_min: Optional[float] = None,
        pe_max: Optional[float] = None,
        pb_min: Optional[float] = None,
        pb_max: Optional[float] = None,
        dividend_yield_min: Optional[float] = None,
        dividend_yield_max: Optional[float] = None,
        roe_min: Optional[float] = None,
        roe_max: Optional[float] = None,
        # 技術面篩選
        rsi_min: Optional[float] = None,
        rsi_max: Optional[float] = None,
        technical_score_min: Optional[int] = None,
        ma_trend: Optional[str] = None,  # "bullish", "bearish", "neutral"
        # 籌碼面篩選
        foreign_net_min: Optional[float] = None,
        trust_net_min: Optional[float] = None,
        # 市值篩選
        market_cap_size: Optional[MarketCapSize] = None,
        market_cap_min: Optional[float] = None,
        market_cap_max: Optional[float] = None,
        # 其他
        industries: Optional[List[str]] = None,
        exclude_stocks: Optional[List[str]] = None,
        stock_pool: Optional[List[str]] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        執行選股篩選

        Returns:
            {
                "total_scanned": 篩選的股票數量,
                "matched_count": 符合條件的數量,
                "stocks": [符合條件的股票列表],
                "filters_applied": 套用的篩選條件,
                "execution_time": 執行時間
            }
        """
        start_time = datetime.now()

        # 建立篩選條件摘要
        filters_applied = cls._build_filters_summary(
            pe_min=pe_min, pe_max=pe_max,
            pb_min=pb_min, pb_max=pb_max,
            dividend_yield_min=dividend_yield_min,
            roe_min=roe_min,
            technical_score_min=technical_score_min,
            foreign_net_min=foreign_net_min,
            market_cap_size=market_cap_size,
        )

        # 決定要篩選的股票池
        pool = stock_pool or cls.STOCK_POOL
        if exclude_stocks:
            pool = [s for s in pool if s not in exclude_stocks]

        # 執行篩選
        matched_stocks = []

        for stock_id in pool:
            try:
                # 取得基本面資料
                fundamental = await FundamentalService.get_fundamental_data(stock_id)

                # 套用篩選條件
                if not cls._apply_filters(
                    fundamental=fundamental,
                    pe_min=pe_min, pe_max=pe_max,
                    pb_min=pb_min, pb_max=pb_max,
                    dividend_yield_min=dividend_yield_min,
                    dividend_yield_max=dividend_yield_max,
                    roe_min=roe_min, roe_max=roe_max,
                    market_cap_size=market_cap_size,
                    market_cap_min=market_cap_min,
                    market_cap_max=market_cap_max,
                ):
                    continue

                # V10.17: 通過篩選，加入結果（包含股票名稱）
                matched_stocks.append({
                    "stock_id": stock_id,
                    "name": get_stock_name(stock_id),  # V10.17: 加入股票名稱
                    "stock_name": get_stock_name(stock_id),  # 同時提供 stock_name
                    "pe_ratio": fundamental.get("pe_ratio"),
                    "pb_ratio": fundamental.get("pb_ratio"),
                    "dividend_yield": fundamental.get("dividend_yield_percent"),
                    "roe": fundamental.get("roe"),
                    "market_cap": fundamental.get("market_cap"),
                    "market_cap_display": fundamental.get("market_cap_display"),
                    "valuation_comment": fundamental.get("valuation_comment"),
                    "growth_comment": fundamental.get("growth_comment"),
                    "sector": fundamental.get("sector"),
                    "industry": fundamental.get("industry"),
                })

                if len(matched_stocks) >= limit:
                    break

            except Exception as e:
                print(f"篩選 {stock_id} 時發生錯誤: {e}")
                continue

        # 依殖利率排序（如果有）
        if dividend_yield_min:
            matched_stocks.sort(
                key=lambda x: x.get("dividend_yield") or 0,
                reverse=True
            )
        # 依本益比排序（如果有 PE 條件）
        elif pe_max:
            matched_stocks.sort(
                key=lambda x: x.get("pe_ratio") or 999,
                reverse=False
            )

        execution_time = (datetime.now() - start_time).total_seconds()

        return {
            "total_scanned": len(pool),
            "matched_count": len(matched_stocks),
            "stocks": matched_stocks[:limit],
            "filters_applied": filters_applied,
            "execution_time": round(execution_time, 2),
            "timestamp": datetime.now().isoformat(),
        }

    @classmethod
    async def screen_by_preset(
        cls,
        preset: ScreenerPreset,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        使用預設策略進行篩選

        Args:
            preset: 預設策略類型
            limit: 最大返回數量

        Returns:
            篩選結果（含預設策略資訊）
        """
        # 檢查快取
        cache_key = f"screener_preset_{preset.value}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached

        # 取得預設條件
        preset_config = cls.PRESET_FILTERS.get(preset, {})

        # 執行篩選
        result = await cls.screen_stocks(
            pe_min=preset_config.get("pe_min"),
            pe_max=preset_config.get("pe_max"),
            pb_min=preset_config.get("pb_min"),
            pb_max=preset_config.get("pb_max"),
            dividend_yield_min=preset_config.get("dividend_yield_min"),
            dividend_yield_max=preset_config.get("dividend_yield_max"),
            roe_min=preset_config.get("roe_min"),
            roe_max=preset_config.get("roe_max"),
            technical_score_min=preset_config.get("technical_score_min"),
            foreign_net_min=preset_config.get("foreign_net_min"),
            market_cap_size=preset_config.get("market_cap_size"),
            limit=limit,
        )

        # 加入預設資訊
        result["preset"] = {
            "id": preset.value,
            "name": preset_config.get("name", preset.value),
            "description": preset_config.get("description", ""),
        }

        # 快取結果
        cls._set_cache(cache_key, result)

        return result

    @classmethod
    def get_available_presets(cls) -> List[Dict[str, Any]]:
        """取得所有可用的預設策略"""
        return [
            {
                "id": preset.value,
                "name": config.get("name", preset.value),
                "description": config.get("description", ""),
                "filters": {k: v for k, v in config.items() if k not in ["name", "description"]},
            }
            for preset, config in cls.PRESET_FILTERS.items()
        ]

    @classmethod
    def _apply_filters(
        cls,
        fundamental: Dict[str, Any],
        pe_min: Optional[float] = None,
        pe_max: Optional[float] = None,
        pb_min: Optional[float] = None,
        pb_max: Optional[float] = None,
        dividend_yield_min: Optional[float] = None,
        dividend_yield_max: Optional[float] = None,
        roe_min: Optional[float] = None,
        roe_max: Optional[float] = None,
        market_cap_size: Optional[MarketCapSize] = None,
        market_cap_min: Optional[float] = None,
        market_cap_max: Optional[float] = None,
    ) -> bool:
        """
        套用篩選條件，返回是否通過
        """
        # 本益比篩選
        pe = fundamental.get("pe_ratio")
        if pe is not None:
            if pe_min is not None and pe < pe_min:
                return False
            if pe_max is not None and pe > pe_max:
                return False
        elif pe_max is not None:
            # 如果要求有本益比上限但無資料，跳過
            return False

        # 股價淨值比篩選
        pb = fundamental.get("pb_ratio")
        if pb is not None:
            if pb_min is not None and pb < pb_min:
                return False
            if pb_max is not None and pb > pb_max:
                return False
        elif pb_max is not None:
            return False

        # 殖利率篩選
        dividend = fundamental.get("dividend_yield_percent")
        if dividend is not None:
            if dividend_yield_min is not None and dividend < dividend_yield_min:
                return False
            if dividend_yield_max is not None and dividend > dividend_yield_max:
                return False
        elif dividend_yield_min is not None:
            return False

        # ROE 篩選
        roe = fundamental.get("roe")
        if roe is not None:
            if roe_min is not None and roe < roe_min:
                return False
            if roe_max is not None and roe > roe_max:
                return False
        elif roe_min is not None:
            return False

        # 市值篩選
        market_cap = fundamental.get("market_cap")
        if market_cap is not None:
            cap_billion = market_cap / 1e8  # 轉換為億元

            if market_cap_size:
                if market_cap_size == MarketCapSize.LARGE and cap_billion < 500:
                    return False
                elif market_cap_size == MarketCapSize.MID and (cap_billion < 50 or cap_billion > 500):
                    return False
                elif market_cap_size == MarketCapSize.SMALL and cap_billion > 50:
                    return False

            if market_cap_min is not None and cap_billion < market_cap_min:
                return False
            if market_cap_max is not None and cap_billion > market_cap_max:
                return False

        return True

    @classmethod
    def _build_filters_summary(cls, **kwargs) -> List[Dict[str, Any]]:
        """建立篩選條件摘要"""
        filters = []

        if kwargs.get("pe_max"):
            filters.append({
                "field": "pe_ratio",
                "label": "本益比",
                "condition": f"≤ {kwargs['pe_max']}",
            })
        if kwargs.get("pe_min"):
            filters.append({
                "field": "pe_ratio",
                "label": "本益比",
                "condition": f"≥ {kwargs['pe_min']}",
            })
        if kwargs.get("pb_max"):
            filters.append({
                "field": "pb_ratio",
                "label": "股價淨值比",
                "condition": f"≤ {kwargs['pb_max']}",
            })
        if kwargs.get("dividend_yield_min"):
            filters.append({
                "field": "dividend_yield",
                "label": "殖利率",
                "condition": f"≥ {kwargs['dividend_yield_min']}%",
            })
        if kwargs.get("roe_min"):
            filters.append({
                "field": "roe",
                "label": "ROE",
                "condition": f"≥ {kwargs['roe_min']}%",
            })
        if kwargs.get("technical_score_min"):
            filters.append({
                "field": "technical_score",
                "label": "技術評分",
                "condition": f"≥ {kwargs['technical_score_min']}",
            })
        if kwargs.get("foreign_net_min"):
            filters.append({
                "field": "foreign_net",
                "label": "外資買超",
                "condition": f"≥ {kwargs['foreign_net_min']} 張",
            })
        if kwargs.get("market_cap_size"):
            size_labels = {
                MarketCapSize.LARGE: "大型股 (>500億)",
                MarketCapSize.MID: "中型股 (50-500億)",
                MarketCapSize.SMALL: "小型股 (<50億)",
            }
            filters.append({
                "field": "market_cap",
                "label": "市值規模",
                "condition": size_labels.get(kwargs['market_cap_size'], "不限"),
            })

        return filters

    @classmethod
    async def get_screener_stats(cls) -> Dict[str, Any]:
        """取得篩選器統計資訊"""
        return {
            "stock_pool_size": len(cls.STOCK_POOL),
            "available_presets": len(cls.PRESET_FILTERS),
            "preset_list": [p.value for p in ScreenerPreset],
            "supported_filters": [
                "pe_ratio", "pb_ratio", "dividend_yield", "roe",
                "market_cap", "market_cap_size",
                "technical_score", "rsi",
                "foreign_net", "trust_net",
            ],
            "cache_status": {
                "total_keys": len(cls._cache),
                "is_trading_hours": SmartTTL.get_ttl_info("recommend").get("is_trading_hours"),
            },
        }


# 便捷函數
async def screen_stocks(**kwargs):
    return await StockScreener.screen_stocks(**kwargs)

async def screen_by_preset(preset: ScreenerPreset, limit: int = 20):
    return await StockScreener.screen_by_preset(preset, limit)

def get_available_presets():
    return StockScreener.get_available_presets()
