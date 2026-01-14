"""
快取服務模組 V2.0
- 智能快取：根據盤中/盤後自動調整 TTL
- 減少 API 請求次數
- 加快回應速度

台股交易時間：週一至週五 09:00-13:30
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Tuple
import json


def is_trading_hours() -> bool:
    """
    判斷目前是否為台股交易時段

    交易時間：週一至週五 09:00-13:30
    """
    now = datetime.now()

    # 週末不交易
    if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False

    # 檢查時間範圍
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)

    return market_open <= now <= market_close


def get_next_market_open() -> datetime:
    """取得下一個開盤時間"""
    now = datetime.now()
    next_open = now.replace(hour=9, minute=0, second=0, microsecond=0)

    # 如果今天已經過了開盤時間，設定為明天
    if now.hour >= 9:
        next_open += timedelta(days=1)

    # 跳過週末
    while next_open.weekday() >= 5:
        next_open += timedelta(days=1)

    return next_open


class SmartTTL:
    """
    智能 TTL 管理器

    根據盤中/盤後自動調整快取時間：
    - 盤中：較短的 TTL，確保資料即時性
    - 盤後：較長的 TTL，減少不必要的 API 請求
    """

    # 盤中 TTL（秒）
    TRADING_HOURS = {
        "realtime": 30,           # 即時報價：30 秒
        "daily_trading": 60,      # 每日成交：1 分鐘
        "analysis": 300,          # 技術分析：5 分鐘
        "fundamental": 600,       # 基本面：10 分鐘
        "institutional": 600,     # 三大法人：10 分鐘
        "margin": 600,            # 融資融券：10 分鐘
        "per_dividend": 600,      # 本益比/殖利率：10 分鐘
        "news": 300,              # 新聞：5 分鐘
        "recommend": 600,         # AI 推薦：10 分鐘
        "strategy": 900,          # 策略分析：15 分鐘
        "score": 600,             # 評分：10 分鐘
        "history": 3600,          # 歷史資料：1 小時
        "market_index": 60,       # 大盤指數：1 分鐘
    }

    # 盤後 TTL（秒）
    AFTER_HOURS = {
        "realtime": 3600,         # 即時報價：1 小時
        "daily_trading": 7200,    # 每日成交：2 小時
        "analysis": 7200,         # 技術分析：2 小時
        "fundamental": 14400,     # 基本面：4 小時
        "institutional": 14400,   # 三大法人：4 小時（盤後15:00更新一次）
        "margin": 14400,          # 融資融券：4 小時
        "per_dividend": 14400,    # 本益比/殖利率：4 小時
        "news": 1800,             # 新聞：30 分鐘（新聞仍會更新）
        "recommend": 14400,       # AI 推薦：4 小時
        "strategy": 14400,        # 策略分析：4 小時
        "score": 14400,           # 評分：4 小時
        "history": 43200,         # 歷史資料：12 小時
        "market_index": 3600,     # 大盤指數：1 小時
    }

    @classmethod
    def get_ttl(cls, data_type: str) -> int:
        """
        取得智能 TTL

        Args:
            data_type: 資料類型（realtime, analysis, etc.）

        Returns:
            TTL 秒數
        """
        if is_trading_hours():
            return cls.TRADING_HOURS.get(data_type, 300)
        else:
            return cls.AFTER_HOURS.get(data_type, 3600)

    @classmethod
    def get_ttl_info(cls, data_type: str) -> Dict:
        """取得 TTL 詳細資訊"""
        trading = is_trading_hours()
        ttl = cls.get_ttl(data_type)

        return {
            "data_type": data_type,
            "ttl_seconds": ttl,
            "ttl_display": f"{ttl // 60} 分鐘" if ttl < 3600 else f"{ttl // 3600} 小時",
            "is_trading_hours": trading,
            "market_status": "盤中" if trading else "盤後",
        }


class CacheService:
    """通用快取服務"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl: Dict[str, int] = {}  # 秒
        self._data_types: Dict[str, str] = {}  # 記錄資料類型供智能 TTL 使用

    def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        if key not in self._cache:
            return None

        # 檢查是否過期（支援智能 TTL）
        if self._is_expired(key):
            self.delete(key)
            return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl: int = 300, data_type: str = None) -> None:
        """設定快取值

        Args:
            key: 快取鍵
            value: 快取值
            ttl: 存活時間（秒），預設 5 分鐘
            data_type: 資料類型（用於智能 TTL）
        """
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

        # 如果指定了資料類型，使用智能 TTL
        if data_type:
            self._data_types[key] = data_type
            self._ttl[key] = SmartTTL.get_ttl(data_type)
        else:
            self._ttl[key] = ttl

    def set_smart(self, key: str, value: Any, data_type: str) -> None:
        """使用智能 TTL 設定快取

        Args:
            key: 快取鍵
            value: 快取值
            data_type: 資料類型
        """
        self.set(key, value, data_type=data_type)

    def delete(self, key: str) -> None:
        """刪除快取"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._ttl.pop(key, None)
        self._data_types.pop(key, None)

    def clear(self) -> None:
        """清除所有快取"""
        self._cache.clear()
        self._timestamps.clear()
        self._ttl.clear()
        self._data_types.clear()

    def _is_expired(self, key: str) -> bool:
        """檢查是否過期"""
        if key not in self._timestamps:
            return True

        # 如果有資料類型，重新計算智能 TTL（因為可能從盤中變盤後）
        if key in self._data_types:
            current_ttl = SmartTTL.get_ttl(self._data_types[key])
        else:
            current_ttl = self._ttl.get(key, 300)

        elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
        return elapsed > current_ttl

    def get_stats(self) -> Dict:
        """取得快取統計"""
        valid_count = sum(1 for k in self._cache if not self._is_expired(k))
        return {
            "total_keys": len(self._cache),
            "valid_keys": valid_count,
            "expired_keys": len(self._cache) - valid_count,
            "is_trading_hours": is_trading_hours(),
            "market_status": "盤中" if is_trading_hours() else "盤後",
        }


# 專用快取實例
class StockCache:
    """股票資料快取（支援智能 TTL）"""

    _instance = None
    _cache = None

    @classmethod
    def get_instance(cls) -> CacheService:
        """取得快取實例（單例）"""
        if cls._cache is None:
            cls._cache = CacheService()
        return cls._cache

    @classmethod
    def get_stock_info(cls, stock_id: str) -> Optional[Dict]:
        """取得股票即時資訊快取"""
        return cls.get_instance().get(f"info:{stock_id}")

    @classmethod
    def set_stock_info(cls, stock_id: str, data: Dict) -> None:
        """設定股票即時資訊快取（智能 TTL）"""
        cls.get_instance().set_smart(f"info:{stock_id}", data, "realtime")

    @classmethod
    def get_stock_history(cls, stock_id: str, months: int) -> Optional[list]:
        """取得股票歷史資料快取"""
        return cls.get_instance().get(f"history:{stock_id}:{months}")

    @classmethod
    def set_stock_history(cls, stock_id: str, months: int, data: list) -> None:
        """設定股票歷史資料快取（智能 TTL）"""
        cls.get_instance().set_smart(f"history:{stock_id}:{months}", data, "history")

    @classmethod
    def get_analysis(cls, stock_id: str) -> Optional[Dict]:
        """取得技術分析快取"""
        return cls.get_instance().get(f"analysis:{stock_id}")

    @classmethod
    def set_analysis(cls, stock_id: str, data: Dict) -> None:
        """設定技術分析快取（智能 TTL）"""
        cls.get_instance().set_smart(f"analysis:{stock_id}", data, "analysis")

    @classmethod
    def get_recommendations(cls) -> Optional[Dict]:
        """取得推薦結果快取"""
        return cls.get_instance().get("recommendations")

    @classmethod
    def set_recommendations(cls, data: Dict) -> None:
        """設定推薦結果快取（智能 TTL）"""
        cls.get_instance().set_smart("recommendations", data, "recommend")

    @classmethod
    def get_score(cls, stock_id: str) -> Optional[Dict]:
        """取得評分快取"""
        return cls.get_instance().get(f"score:{stock_id}")

    @classmethod
    def set_score(cls, stock_id: str, data: Dict) -> None:
        """設定評分快取（智能 TTL）"""
        cls.get_instance().set_smart(f"score:{stock_id}", data, "score")

    @classmethod
    def get_fundamental(cls, stock_id: str) -> Optional[Dict]:
        """取得基本面快取"""
        return cls.get_instance().get(f"fundamental:{stock_id}")

    @classmethod
    def set_fundamental(cls, stock_id: str, data: Dict) -> None:
        """設定基本面快取（智能 TTL）"""
        cls.get_instance().set_smart(f"fundamental:{stock_id}", data, "fundamental")

    @classmethod
    def get_strategy(cls, stock_id: str) -> Optional[Dict]:
        """取得策略分析快取"""
        return cls.get_instance().get(f"strategy:{stock_id}")

    @classmethod
    def set_strategy(cls, stock_id: str, data: Dict) -> None:
        """設定策略分析快取（智能 TTL）"""
        cls.get_instance().set_smart(f"strategy:{stock_id}", data, "strategy")

    @classmethod
    def clear_all(cls) -> None:
        """清除所有快取"""
        cls.get_instance().clear()

    @classmethod
    def get_stats(cls) -> Dict:
        """取得快取統計"""
        return cls.get_instance().get_stats()


# 快取裝飾器（支援智能 TTL）
def cached(ttl: int = 300, key_prefix: str = "", data_type: str = None):
    """快取裝飾器

    Args:
        ttl: 存活時間（秒），若指定 data_type 則忽略
        key_prefix: 快取鍵前綴
        data_type: 資料類型（用於智能 TTL）
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 嘗試從快取取得
            cache = StockCache.get_instance()
            cached_value = cache.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 執行函數
            result = await func(*args, **kwargs)

            # 存入快取
            if result is not None:
                if data_type:
                    cache.set_smart(cache_key, result, data_type)
                else:
                    cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def smart_cached(data_type: str, key_prefix: str = ""):
    """智能快取裝飾器

    自動根據盤中/盤後調整 TTL

    Args:
        data_type: 資料類型
        key_prefix: 快取鍵前綴
    """
    return cached(data_type=data_type, key_prefix=key_prefix)
