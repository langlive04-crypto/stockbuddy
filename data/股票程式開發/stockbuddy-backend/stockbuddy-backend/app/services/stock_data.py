"""
股票資料服務 - 使用 yfinance
穩定取得台股資料
"""

import warnings
import logging

# 抑制 yfinance 的警告輸出
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*possibly delisted.*')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from cachetools import TTLCache
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 快取設定
_cache = TTLCache(maxsize=200, ttl=300)  # 5分鐘快取

# 執行緒池（yfinance 是同步的）
_executor = ThreadPoolExecutor(max_workers=4)


class StockDataService:
    """股票資料服務（使用 Yahoo Finance）"""
    
    # 台股常用股票對照表
    POPULAR_STOCKS = {
        "2330": "台積電",
        "2317": "鴻海",
        "2454": "聯發科",
        "2308": "台達電",
        "2881": "富邦金",
        "2882": "國泰金",
        "2303": "聯電",
        "2412": "中華電",
        "2891": "中信金",
        "3711": "日月光投控",
        "2886": "兆豐金",
        "1301": "台塑",
        "1303": "南亞",
        "2002": "中鋼",
        "2603": "長榮",
        "2609": "陽明",
        "3037": "欣興",
        "2382": "廣達",
        "2357": "華碩",
        "6505": "台塑化",
    }

    @staticmethod
    def _to_tw_symbol(stock_id: str) -> str:
        """轉換為 Yahoo Finance 台股代號格式"""
        if not stock_id.endswith(".TW") and not stock_id.endswith(".TWO"):
            return f"{stock_id}.TW"
        return stock_id

    @classmethod
    async def get_stock_info(cls, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        取得個股即時資訊
        """
        cache_key = f"stock_info_{stock_id}"
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            symbol = cls._to_tw_symbol(stock_id)
            
            # 在執行緒池中執行同步的 yfinance 呼叫
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(_executor, lambda: yf.Ticker(symbol))
            
            # 取得歷史資料（最近 5 天）
            hist = await loop.run_in_executor(
                _executor, 
                lambda: ticker.history(period="5d")
            )
            
            if hist.empty:
                return None
            
            # 取最新一筆
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            change = latest['Close'] - prev['Close']
            change_percent = (change / prev['Close'] * 100) if prev['Close'] > 0 else 0
            
            result = {
                "stock_id": stock_id,
                "name": cls.POPULAR_STOCKS.get(stock_id, stock_id),
                "date": latest.name.strftime("%Y-%m-%d"),
                "open": round(latest['Open'], 2),
                "high": round(latest['High'], 2),
                "low": round(latest['Low'], 2),
                "close": round(latest['Close'], 2),
                "volume": int(latest['Volume']),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
            }
            
            _cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching stock info for {stock_id}: {e}")
            return None

    @classmethod
    async def get_stock_history(cls, stock_id: str, months: int = 3) -> List[Dict[str, Any]]:
        """
        取得個股歷史K線資料
        """
        cache_key = f"stock_history_{stock_id}_{months}"
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            symbol = cls._to_tw_symbol(stock_id)
            
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(_executor, lambda: yf.Ticker(symbol))
            
            # 計算期間
            period = f"{months}mo"
            
            hist = await loop.run_in_executor(
                _executor,
                lambda: ticker.history(period=period)
            )
            
            if hist.empty:
                return []
            
            # 轉換格式
            result = []
            prev_close = None
            
            for idx, row in hist.iterrows():
                change = row['Close'] - prev_close if prev_close else 0
                
                result.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(row['Open'], 2),
                    "high": round(row['High'], 2),
                    "low": round(row['Low'], 2),
                    "close": round(row['Close'], 2),
                    "volume": int(row['Volume']),
                    "change": round(change, 2),
                })
                
                prev_close = row['Close']
            
            _cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching history for {stock_id}: {e}")
            return []

    @classmethod
    async def get_multiple_stocks(cls, stock_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批次取得多檔股票資訊
        """
        results = {}
        
        # 並行取得
        tasks = [cls.get_stock_info(sid) for sid in stock_ids]
        infos = await asyncio.gather(*tasks, return_exceptions=True)
        
        for sid, info in zip(stock_ids, infos):
            if isinstance(info, dict):
                results[sid] = info
        
        return results

    @classmethod
    async def get_market_index(cls) -> Optional[Dict[str, Any]]:
        """
        取得大盤指數（台灣加權指數）
        """
        cache_key = "market_index"
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(_executor, lambda: yf.Ticker("^TWII"))
            
            hist = await loop.run_in_executor(
                _executor,
                lambda: ticker.history(period="5d")
            )
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            change = latest['Close'] - prev['Close']
            change_percent = (change / prev['Close'] * 100) if prev['Close'] > 0 else 0
            
            result = {
                "name": "加權指數",
                "symbol": "^TWII",
                "date": latest.name.strftime("%Y-%m-%d"),
                "value": round(latest['Close'], 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": int(latest['Volume']),
            }
            
            _cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching market index: {e}")
            return None

    @classmethod
    async def search_stock(cls, query: str) -> List[Dict[str, Any]]:
        """
        搜尋股票
        """
        results = []
        
        for stock_id, name in cls.POPULAR_STOCKS.items():
            if query.lower() in stock_id.lower() or query in name:
                results.append({
                    "stock_id": stock_id,
                    "name": name,
                })
        
        return results


# 建立全域服務實例
stock_service = StockDataService()
