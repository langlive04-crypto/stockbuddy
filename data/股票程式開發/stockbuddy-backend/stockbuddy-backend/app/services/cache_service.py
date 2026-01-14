"""
快取服務模組
- 減少 API 請求次數
- 加快回應速度
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import json


class CacheService:
    """通用快取服務"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl: Dict[str, int] = {}  # 秒
        
    def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        if key not in self._cache:
            return None
            
        # 檢查是否過期
        if self._is_expired(key):
            self.delete(key)
            return None
            
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """設定快取值
        
        Args:
            key: 快取鍵
            value: 快取值
            ttl: 存活時間（秒），預設 5 分鐘
        """
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        self._ttl[key] = ttl
    
    def delete(self, key: str) -> None:
        """刪除快取"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._ttl.pop(key, None)
    
    def clear(self) -> None:
        """清除所有快取"""
        self._cache.clear()
        self._timestamps.clear()
        self._ttl.clear()
    
    def _is_expired(self, key: str) -> bool:
        """檢查是否過期"""
        if key not in self._timestamps:
            return True
            
        elapsed = (datetime.now() - self._timestamps[key]).total_seconds()
        ttl = self._ttl.get(key, 300)
        return elapsed > ttl
    
    def get_stats(self) -> Dict:
        """取得快取統計"""
        valid_count = sum(1 for k in self._cache if not self._is_expired(k))
        return {
            "total_keys": len(self._cache),
            "valid_keys": valid_count,
            "expired_keys": len(self._cache) - valid_count,
        }


# 專用快取實例
class StockCache:
    """股票資料快取"""
    
    # 快取時間設定（秒）
    TTL_REALTIME = 60       # 即時報價：1 分鐘
    TTL_HISTORY = 3600      # 歷史資料：1 小時
    TTL_ANALYSIS = 300      # 技術分析：5 分鐘
    TTL_NEWS = 300          # 新聞：5 分鐘
    TTL_RECOMMEND = 180     # 推薦結果：3 分鐘
    
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
        """設定股票即時資訊快取"""
        cls.get_instance().set(f"info:{stock_id}", data, cls.TTL_REALTIME)
    
    @classmethod
    def get_stock_history(cls, stock_id: str, months: int) -> Optional[list]:
        """取得股票歷史資料快取"""
        return cls.get_instance().get(f"history:{stock_id}:{months}")
    
    @classmethod
    def set_stock_history(cls, stock_id: str, months: int, data: list) -> None:
        """設定股票歷史資料快取"""
        cls.get_instance().set(f"history:{stock_id}:{months}", data, cls.TTL_HISTORY)
    
    @classmethod
    def get_analysis(cls, stock_id: str) -> Optional[Dict]:
        """取得技術分析快取"""
        return cls.get_instance().get(f"analysis:{stock_id}")
    
    @classmethod
    def set_analysis(cls, stock_id: str, data: Dict) -> None:
        """設定技術分析快取"""
        cls.get_instance().set(f"analysis:{stock_id}", data, cls.TTL_ANALYSIS)
    
    @classmethod
    def get_recommendations(cls) -> Optional[Dict]:
        """取得推薦結果快取"""
        return cls.get_instance().get("recommendations")
    
    @classmethod
    def set_recommendations(cls, data: Dict) -> None:
        """設定推薦結果快取"""
        cls.get_instance().set("recommendations", data, cls.TTL_RECOMMEND)
    
    @classmethod
    def clear_all(cls) -> None:
        """清除所有快取"""
        cls.get_instance().clear()
    
    @classmethod
    def get_stats(cls) -> Dict:
        """取得快取統計"""
        return cls.get_instance().get_stats()


# 快取裝飾器
def cached(ttl: int = 300, key_prefix: str = ""):
    """快取裝飾器
    
    Args:
        ttl: 存活時間（秒）
        key_prefix: 快取鍵前綴
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
                cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
