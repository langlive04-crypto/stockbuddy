"""
TWSE 批量資料服務
一次取得所有上市股票的當日行情，避免 API 限流
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from cachetools import TTLCache

# 快取：全市場資料快取 10 分鐘
_market_cache = TTLCache(maxsize=10, ttl=600)
# 個股歷史快取 30 分鐘
_history_cache = TTLCache(maxsize=500, ttl=1800)


class TWSEBulkService:
    """TWSE 批量資料服務 - 一次取得全市場資料"""
    
    BASE_URL = "https://www.twse.com.tw"
    
    # 完整股票名稱對照表
    STOCK_NAMES = {}  # 會從 API 動態填充
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0,
            verify=False,  # 禁用 SSL 驗證（TWSE 證書有時有問題）
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            }
        )
    
    async def get_all_stocks_daily(self) -> Dict[str, Dict[str, Any]]:
        """
        取得所有上市股票的當日行情
        回傳格式: {股票代號: {資料...}, ...}
        """
        cache_key = "all_stocks_daily"
        if cache_key in _market_cache:
            return _market_cache[cache_key]
        
        # 嘗試取得今天或最近交易日的資料
        for days_back in range(5):
            target_date = datetime.now() - timedelta(days=days_back)
            date_str = target_date.strftime("%Y%m%d")
            
            result = await self._fetch_daily_data(date_str)
            if result:
                _market_cache[cache_key] = result
                print(f"✅ 成功取得 {len(result)} 檔股票的行情資料 (日期: {date_str})")
                return result
        
        print("❌ 無法取得市場資料")
        return {}
    
    async def _fetch_daily_data(self, date_str: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """從 TWSE 取得指定日期的全市場資料"""
        try:
            # MI_INDEX 可以取得當日所有股票行情
            url = f"{self.BASE_URL}/exchangeReport/MI_INDEX"
            params = {
                "response": "json",
                "date": date_str,
                "type": "ALL"
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("stat") != "OK":
                return None
            
            # 解析 data9: 每日收盤行情
            stocks_data = data.get("data9") or data.get("data8") or []
            if not stocks_data:
                return None
            
            result = {}
            for row in stocks_data:
                try:
                    stock_id = row[0].strip()
                    
                    # 只要純數字的股票代號（過濾權證等）
                    if not stock_id.isdigit() or len(stock_id) > 4:
                        continue
                    
                    name = row[1].strip()
                    
                    # 儲存名稱
                    self.STOCK_NAMES[stock_id] = name
                    
                    # 解析數據
                    volume = self._parse_int(row[2])  # 成交股數
                    transactions = self._parse_int(row[3])  # 成交筆數
                    turnover = self._parse_int(row[4])  # 成交金額
                    open_price = self._parse_float(row[5])
                    high = self._parse_float(row[6])
                    low = self._parse_float(row[7])
                    close = self._parse_float(row[8])
                    
                    # 漲跌
                    direction = row[9] if len(row) > 9 else ""
                    change_str = row[10] if len(row) > 10 else "0"
                    change = self._parse_float(change_str)
                    if "-" in str(direction) or "green" in str(direction).lower():
                        change = -abs(change)
                    
                    # 計算漲跌幅
                    if close and change:
                        prev_close = close - change
                        change_percent = round((change / prev_close) * 100, 2) if prev_close > 0 else 0
                    else:
                        change_percent = 0
                    
                    result[stock_id] = {
                        "stock_id": stock_id,
                        "name": name,
                        "date": date_str,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                        "turnover": turnover,
                        "transactions": transactions,
                        "change": change,
                        "change_percent": change_percent,
                    }
                except Exception as e:
                    continue
            
            return result if result else None
            
        except Exception as e:
            print(f"Error fetching TWSE data for {date_str}: {e}")
            return None
    
    async def get_stock_history_yf(self, stock_id: str, months: int = 2) -> List[Dict[str, Any]]:
        """
        使用 yfinance 取得個股歷史資料
        （技術分析需要歷史資料，TWSE 批量 API 只有當日）
        """
        cache_key = f"history_{stock_id}_{months}"
        if cache_key in _history_cache:
            return _history_cache[cache_key]
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(f"{stock_id}.TW")
            period = f"{months}mo"
            
            df = ticker.history(period=period)
            
            if df.empty:
                # 嘗試上櫃
                ticker = yf.Ticker(f"{stock_id}.TWO")
                df = ticker.history(period=period)
            
            if df.empty:
                return []
            
            history = []
            for date, row in df.iterrows():
                history.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                })
            
            _history_cache[cache_key] = history
            return history
            
        except Exception as e:
            print(f"yfinance 歷史資料失敗 {stock_id}: {e}")
            return []
    
    async def get_market_index(self) -> Optional[Dict[str, Any]]:
        """取得大盤指數"""
        try:
            import yfinance as yf
            ticker = yf.Ticker("^TWII")
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty:
                return None
            
            current = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
            change = current - prev
            change_pct = round((change / prev) * 100, 2) if prev else 0
            
            return {
                "name": "加權指數",
                "value": round(current, 2),
                "change": round(change, 2),
                "change_percent": change_pct,
            }
        except Exception as e:
            print(f"Error fetching market index: {e}")
            return None
    
    @staticmethod
    def _parse_int(value) -> int:
        try:
            return int(str(value).replace(",", "").replace("--", "0").strip())
        except:
            return 0
    
    @staticmethod
    def _parse_float(value) -> float:
        try:
            cleaned = str(value).replace(",", "").replace("--", "0").replace("X", "").strip()
            if cleaned.startswith("+"):
                cleaned = cleaned[1:]
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0


# 全域實例
_bulk_service: Optional[TWSEBulkService] = None

def get_bulk_service() -> TWSEBulkService:
    global _bulk_service
    if _bulk_service is None:
        _bulk_service = TWSEBulkService()
    return _bulk_service
