"""
📈 TWSE 證交所 API 服務

官方 API 端點：
1. 即時報價: mis.twse.com.tw/stock/api/getStockInfo.jsp
2. 歷史資料: www.twse.com.tw/exchangeReport/STOCK_DAY
3. OpenAPI: openapi.twse.com.tw

⚠️ 重要：TWSE 有 rate limit - 每 5 秒最多 3 個 request！
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time


class TWSEService:
    """TWSE 證交所 API 服務"""
    
    # API 端點
    REALTIME_API = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    HISTORY_API = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
    ALL_STOCKS_API = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL"
    OPENAPI_BASE = "https://openapi.twse.com.tw/v1"
    
    # Rate limit: 每 5 秒最多 3 個 request
    _last_request_time = 0
    _request_count = 0
    REQUEST_LIMIT = 3
    RATE_LIMIT_WINDOW = 5  # 秒
    
    # 快取
    _cache = {}
    _cache_time = {}
    CACHE_TTL = 60  # 1 分鐘快取
    
    @classmethod
    async def _rate_limit(cls):
        """確保不超過 rate limit"""
        current_time = time.time()
        
        # 如果在同一個時間窗口內
        if current_time - cls._last_request_time < cls.RATE_LIMIT_WINDOW:
            cls._request_count += 1
            if cls._request_count >= cls.REQUEST_LIMIT:
                # 等待到下一個時間窗口
                wait_time = cls.RATE_LIMIT_WINDOW - (current_time - cls._last_request_time) + 0.5
                print(f"⏳ TWSE rate limit，等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)
                cls._last_request_time = time.time()
                cls._request_count = 1
        else:
            # 新的時間窗口
            cls._last_request_time = current_time
            cls._request_count = 1
    
    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取"""
        if key in cls._cache:
            if time.time() - cls._cache_time.get(key, 0) < cls.CACHE_TTL:
                return cls._cache[key]
        return None
    
    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = time.time()
    
    # ============================================================
    # 即時報價 API（推薦用於即時資料）
    # ============================================================
    
    @classmethod
    async def get_realtime_quotes(cls, stock_ids: List[str]) -> Dict[str, Dict]:
        """
        取得即時報價（支援批量查詢）
        
        Args:
            stock_ids: 股票代號列表，例如 ["2330", "2317", "2454"]
            
        Returns:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "price": 1080.0,
                    ...
                },
                ...
            }
        """
        # 檢查快取
        cache_key = f"realtime_{'_'.join(sorted(stock_ids[:10]))}"
        cached = cls._get_cache(cache_key)
        if cached:
            print("📦 使用 TWSE 即時報價快取")
            return cached
        
        await cls._rate_limit()
        
        # 建立查詢字串（上市用 tse_，上櫃用 otc_）
        ex_ch_list = []
        for sid in stock_ids:
            # 判斷上市或上櫃
            if sid.startswith('6') or sid.startswith('3') or sid.startswith('4') or sid.startswith('8'):
                ex_ch_list.append(f"otc_{sid}.tw")
            else:
                ex_ch_list.append(f"tse_{sid}.tw")
        
        ex_ch = "|".join(ex_ch_list)
        
        try:
            # ⚠️ 關鍵：verify=False 解決 SSL 問題
            async with httpx.AsyncClient(timeout=10, verify=False) as client:
                resp = await client.get(
                    cls.REALTIME_API,
                    params={"ex_ch": ex_ch, "json": "1", "delay": "0"}
                )
                
                if resp.status_code != 200:
                    print(f"⚠️ TWSE 即時報價失敗: HTTP {resp.status_code}")
                    return {}
                
                data = resp.json()
                
                if "msgArray" not in data:
                    return {}
                
                result = {}
                for item in data["msgArray"]:
                    stock_id = item.get("c", "")
                    if not stock_id:
                        continue
                    
                    # 解析價格（可能是 "-" 表示無交易）
                    def parse_price(val):
                        try:
                            return float(val) if val and val != "-" else None
                        except:
                            return None
                    
                    price = parse_price(item.get("z"))
                    yesterday = parse_price(item.get("y"))
                    
                    # 計算漲跌
                    change = None
                    change_pct = None
                    if price and yesterday:
                        change = round(price - yesterday, 2)
                        change_pct = round(change / yesterday * 100, 2)
                    
                    result[stock_id] = {
                        "stock_id": stock_id,
                        "name": item.get("n", stock_id),
                        "price": price,
                        "open": parse_price(item.get("o")),
                        "high": parse_price(item.get("h")),
                        "low": parse_price(item.get("l")),
                        "yesterday": yesterday,
                        "volume": int(item.get("v", 0) or 0),
                        "trade_volume": int(item.get("tv", 0) or 0),
                        "change": change,
                        "change_percent": change_pct,
                        "time": item.get("t", ""),
                    }
                
                if result:
                    cls._set_cache(cache_key, result)
                    print(f"✅ TWSE 即時報價: {len(result)} 檔")
                return result
                
        except Exception as e:
            print(f"❌ TWSE 即時報價錯誤: {e}")
            return {}
    
    @classmethod
    async def get_realtime_quote(cls, stock_id: str) -> Optional[Dict]:
        """取得單一股票即時報價"""
        result = await cls.get_realtime_quotes([stock_id])
        return result.get(stock_id)
    
    # ============================================================
    # 全市場資料（每日成交）
    # ============================================================
    
    @classmethod
    async def get_all_stocks_daily(cls) -> Dict[str, Dict]:
        """
        取得全市場當日成交資訊
        """
        cache_key = "all_stocks_daily"
        cached = cls._get_cache(cache_key)
        if cached:
            print("📦 使用 TWSE 全市場快取")
            return cached
        
        await cls._rate_limit()
        
        try:
            # ⚠️ 關鍵：verify=False 解決 SSL 問題
            async with httpx.AsyncClient(timeout=30, verify=False) as client:
                today = datetime.now().strftime("%Y%m%d")
                resp = await client.get(
                    cls.ALL_STOCKS_API,
                    params={"response": "json", "date": today}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    if "data" not in data:
                        print("⚠️ TWSE 全市場: 無資料")
                        return {}
                    
                    result = {}
                    for row in data["data"]:
                        if len(row) < 9:
                            continue
                        
                        stock_id = row[0]
                        if len(stock_id) != 4:
                            continue
                        
                        try:
                            close = float(row[6].replace(",", ""))
                            change = float(row[7].replace(",", "").replace("X", "0"))
                            volume = int(row[2].replace(",", ""))
                            
                            result[stock_id] = {
                                "stock_id": stock_id,
                                "name": row[1],
                                "price": close,
                                "change": change,
                                "change_percent": round(change / (close - change) * 100, 2) if close != change else 0,
                                "volume": volume,
                            }
                        except:
                            pass
                    
                    if result:
                        cls._set_cache(cache_key, result)
                        print(f"✅ TWSE 全市場: {len(result)} 檔")
                        return result
                        
        except Exception as e:
            print(f"⚠️ TWSE 全市場失敗: {e}")
        
        return {}


# ============================================================
# 便捷函數
# ============================================================

async def get_twse_realtime(stock_ids: List[str]) -> Dict[str, Dict]:
    """取得 TWSE 即時報價"""
    return await TWSEService.get_realtime_quotes(stock_ids)

async def get_twse_all_stocks() -> Dict[str, Dict]:
    """取得 TWSE 全市場資料"""
    return await TWSEService.get_all_stocks_daily()
