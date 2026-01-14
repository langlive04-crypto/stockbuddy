"""
📈 TWSE OpenAPI 整合服務 V10.7.1

🔗 官方 API 端點（不需要 API Key）：
1. OpenAPI: https://openapi.twse.com.tw/v1/
2. 即時報價: https://mis.twse.com.tw/stock/api/getStockInfo.jsp
3. 歷史資料: https://www.twse.com.tw/exchangeReport/

📊 可用資料：
- 本益比/殖利率/淨值比 (BWIBBU_ALL)
- 每日成交資訊 (STOCK_DAY_ALL)
- 大盤指數 (MI_INDEX)
- 三大法人買賣超 (T86)
- 融資融券 (MI_MARGN)
- 即時報價 (getStockInfo)

⚠️ Rate Limit: 每 5 秒最多 3 個 request

🆕 V10.7.1: 整合智能快取（盤中/盤後動態 TTL）
"""

import asyncio
import httpx
import time
import gzip
import zlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import math

# 導入智能快取
from app.services.cache_service import SmartTTL, is_trading_hours


class TWSEOpenAPI:
    """
    TWSE 證交所 OpenAPI 整合服務
    
    使用方式：
        # 取得所有股票的本益比、殖利率
        data = await TWSEOpenAPI.get_per_dividend_all()
        
        # 取得即時報價
        quotes = await TWSEOpenAPI.get_realtime_quotes(["2330", "2454"])
        
        # 取得三大法人買賣超
        inst = await TWSEOpenAPI.get_institutional_trading()
    """
    
    # ============================================================
    # API 端點
    # ============================================================
    
    # OpenAPI（本益比、每日成交等）
    OPENAPI_BASE = "https://openapi.twse.com.tw/v1"
    
    # 即時報價
    REALTIME_API = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    
    # 傳統 API（三大法人、融資融券等）
    TWSE_API = "https://www.twse.com.tw"
    
    # ============================================================
    # 瀏覽器模擬 Headers（繞過 403 限制）
    # ============================================================
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",  # V10.13.1: 移除 br，避免 brotli 解壓問題
        "Connection": "keep-alive",
        "Referer": "https://www.twse.com.tw/",
    }
    
    # ============================================================
    # Rate Limit 設定
    # ============================================================
    
    _last_request_time = 0
    _request_count = 0
    REQUEST_LIMIT = 3
    RATE_LIMIT_WINDOW = 5  # 秒
    
    # ============================================================
    # 快取設定
    # ============================================================
    
    _cache: Dict[str, Any] = {}
    _cache_time: Dict[str, float] = {}
    
    # 🆕 V10.7.1: 使用智能快取，根據盤中/盤後自動調整 TTL
    # 舊的固定 TTL 已棄用，改用 SmartTTL.get_ttl(cache_type)
    # cache_type 對應: per_dividend, daily_trading, market_index, institutional, margin, realtime
    
    # ============================================================
    # 工具方法
    # ============================================================
    
    @classmethod
    async def _rate_limit(cls):
        """確保不超過 rate limit"""
        current_time = time.time()
        
        if current_time - cls._last_request_time < cls.RATE_LIMIT_WINDOW:
            cls._request_count += 1
            if cls._request_count >= cls.REQUEST_LIMIT:
                wait_time = cls.RATE_LIMIT_WINDOW - (current_time - cls._last_request_time) + 0.5
                print(f"⏳ TWSE rate limit，等待 {wait_time:.1f} 秒...")
                await asyncio.sleep(wait_time)
                cls._last_request_time = time.time()
                cls._request_count = 1
        else:
            cls._last_request_time = current_time
            cls._request_count = 1
    
    @classmethod
    def _get_cache(cls, key: str, cache_type: str = "default") -> Optional[Any]:
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            # 🆕 V10.7.1: 使用智能 TTL，盤後自動延長快取時間
            ttl = SmartTTL.get_ttl(cache_type)
            if time.time() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None
    
    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = time.time()
    
    @classmethod
    def clear_cache(cls):
        """🆕 V10.13.4: 清除所有快取"""
        cls._cache.clear()
        cls._cache_time.clear()
        print("🗑️ [TWSE OpenAPI] 所有快取已清除")
    
    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        """安全轉換為浮點數"""
        if val is None:
            return None
        try:
            if isinstance(val, str):
                val = val.replace(",", "").strip()
                if val in ("", "-", "--", "N/A"):
                    return None
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return None
            return round(f, 2)
        except:
            return None
    
    @staticmethod
    def _safe_int(val: Any) -> Optional[int]:
        """安全轉換為整數"""
        if val is None:
            return None
        try:
            if isinstance(val, str):
                val = val.replace(",", "").strip()
                if val in ("", "-", "--", "N/A"):
                    return None
            return int(float(val))
        except:
            return None
    
    @classmethod
    def _parse_response(cls, resp) -> Optional[Dict]:
        """
        V10.13.1: 解析 HTTP 響應，自動處理各種壓縮格式
        
        TWSE API 有時返回壓縮數據但 Content-Encoding 不正確，
        導致 httpx 無法自動解壓。這個方法手動檢測並處理。
        """
        # 方法 1：先嘗試直接 JSON 解析（httpx 已自動解壓）
        try:
            return resp.json()
        except:
            pass
        
        raw_bytes = resp.content
        if not raw_bytes:
            print("⚠️ 響應內容為空")
            return None
        
        # 打印前幾個字節用於調試
        print(f"🔍 響應前 4 bytes: {raw_bytes[:4].hex() if len(raw_bytes) >= 4 else raw_bytes.hex()}")
        
        # 方法 2：嘗試 gzip 解壓（magic: 1f 8b）
        if len(raw_bytes) >= 2 and raw_bytes[0:2] == b'\x1f\x8b':
            try:
                decompressed = gzip.decompress(raw_bytes)
                return json.loads(decompressed.decode('utf-8'))
            except Exception as e:
                print(f"⚠️ gzip 解壓失敗: {e}")
        
        # 方法 3：嘗試 zlib/deflate 解壓
        try:
            # zlib with header
            decompressed = zlib.decompress(raw_bytes)
            return json.loads(decompressed.decode('utf-8'))
        except:
            pass
        
        try:
            # raw deflate (no header)
            decompressed = zlib.decompress(raw_bytes, -zlib.MAX_WBITS)
            return json.loads(decompressed.decode('utf-8'))
        except:
            pass
        
        # 方法 4：直接嘗試 UTF-8 解碼
        try:
            return json.loads(raw_bytes.decode('utf-8'))
        except:
            pass
        
        # 方法 5：嘗試其他編碼
        for encoding in ['big5', 'cp950', 'latin-1']:
            try:
                return json.loads(raw_bytes.decode(encoding))
            except:
                continue
        
        print(f"⚠️ 所有解析方法都失敗，響應長度: {len(raw_bytes)} bytes")
        return None
    
    # ============================================================
    # 1. 本益比 / 殖利率 / 淨值比 API
    # ============================================================
    
    @classmethod
    async def get_per_dividend_all(cls) -> Dict[str, Dict]:
        """
        取得所有上市股票的本益比、殖利率、淨值比
        
        API: https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL
        
        Returns:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "pe_ratio": 23.37,        # 本益比
                    "dividend_yield": 1.19,    # 殖利率 %
                    "pb_ratio": 7.42,          # 淨值比
                    "date": "1141219"
                },
                ...
            }
        """
        cache_key = "per_dividend_all"
        cached = cls._get_cache(cache_key, "per_dividend")
        if cached:
            # V10.13.4: 顯示快取的資料日期
            sample = next(iter(cached.values()), {}) if cached else {}
            sample_date = sample.get("date", "unknown")
            print(f"📦 [TWSE OpenAPI] 使用本益比/殖利率快取 (資料日期: {sample_date})")
            return cached
        
        await cls._rate_limit()
        
        try:
            print("🔍 [TWSE OpenAPI] 取得本益比/殖利率資料...")
            async with httpx.AsyncClient(timeout=30, verify=False, headers=cls.HEADERS) as client:
                resp = await client.get(f"{cls.OPENAPI_BASE}/exchangeReport/BWIBBU_ALL")
                
                if resp.status_code != 200:
                    print(f"⚠️ [TWSE OpenAPI] 本益比 API 失敗: HTTP {resp.status_code}")
                    return {}
                
                data = resp.json()
                
                # V10.13.4: 取得資料日期
                data_date = "unknown"
                if data and len(data) > 0:
                    data_date = data[0].get("Date", "unknown")
                
                result = {}
                for item in data:
                    stock_id = item.get("Code", "")
                    if not stock_id or len(stock_id) != 4:
                        continue
                    
                    result[stock_id] = {
                        "stock_id": stock_id,
                        "name": item.get("Name", stock_id),
                        "pe_ratio": cls._safe_float(item.get("PEratio")),
                        "dividend_yield": cls._safe_float(item.get("DividendYield")),
                        "pb_ratio": cls._safe_float(item.get("PBratio")),
                        "date": item.get("Date", ""),
                    }
                
                if result:
                    cls._set_cache(cache_key, result)
                    print(f"✅ [TWSE OpenAPI] 本益比/殖利率: {len(result)} 檔 (資料日期: {data_date})")
                
                return result
                
        except Exception as e:
            print(f"❌ [TWSE OpenAPI] 本益比 API 錯誤: {e}")
            return {}
    
    # ============================================================
    # 2. 每日成交資訊 API
    # ============================================================
    
    @classmethod
    async def get_daily_trading_all(cls) -> Dict[str, Dict]:
        """
        取得所有上市股票的每日成交資訊
        
        API: https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
        
        Returns:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "trade_volume": 12345678,    # 成交股數
                    "trade_value": 123456789,    # 成交金額
                    "open": 1070.0,              # 開盤價
                    "high": 1085.0,              # 最高價
                    "low": 1068.0,               # 最低價
                    "close": 1080.0,             # 收盤價
                    "change": 5.0,               # 漲跌價差
                    "transaction": 9876,          # 成交筆數
                },
                ...
            }
        """
        cache_key = "daily_trading_all"
        cached = cls._get_cache(cache_key, "daily_trading")
        if cached:
            print("📦 [TWSE OpenAPI] 使用每日成交快取")
            return cached
        
        await cls._rate_limit()
        
        try:
            print("🔍 [TWSE OpenAPI] 取得每日成交資料...")
            async with httpx.AsyncClient(timeout=30, verify=False, headers=cls.HEADERS) as client:
                resp = await client.get(f"{cls.OPENAPI_BASE}/exchangeReport/STOCK_DAY_ALL")
                
                if resp.status_code != 200:
                    print(f"⚠️ [TWSE OpenAPI] 每日成交 API 失敗: HTTP {resp.status_code}")
                    return {}
                
                data = resp.json()
                
                # V10.13.4: 檢查資料日期（從第一筆取得）
                data_date = "unknown"
                if data and len(data) > 0:
                    # 嘗試從資料中找日期欄位
                    first_item = data[0]
                    data_date = first_item.get("Date", first_item.get("date", "unknown"))
                
                result = {}
                for item in data:
                    stock_id = item.get("Code", "")
                    if not stock_id or len(stock_id) != 4:
                        continue
                    
                    close = cls._safe_float(item.get("ClosingPrice"))
                    change = cls._safe_float(item.get("Change"))
                    
                    # 計算漲跌幅
                    change_pct = None
                    if close is not None and change is not None and close != change:
                        yesterday = close - change
                        if yesterday > 0:
                            change_pct = round(change / yesterday * 100, 2)
                    
                    result[stock_id] = {
                        "stock_id": stock_id,
                        "name": item.get("Name", stock_id),
                        "trade_volume": cls._safe_int(item.get("TradeVolume")),
                        "trade_value": cls._safe_int(item.get("TradeValue")),
                        "open": cls._safe_float(item.get("OpeningPrice")),
                        "high": cls._safe_float(item.get("HighestPrice")),
                        "low": cls._safe_float(item.get("LowestPrice")),
                        "close": close,
                        "change": change,
                        "change_percent": change_pct,
                        "transaction": cls._safe_int(item.get("Transaction")),
                    }
                
                if result:
                    cls._set_cache(cache_key, result)
                    # 🆕 V10.13.4: 顯示資料日期
                    print(f"✅ [TWSE OpenAPI] 每日成交: {len(result)} 檔 (資料日期: {data_date})")
                
                return result
                
        except Exception as e:
            print(f"❌ [TWSE OpenAPI] 每日成交 API 錯誤: {e}")
            return {}
    
    # ============================================================
    # 3. 大盤指數 API
    # ============================================================
    
    @classmethod
    async def get_market_index(cls) -> Dict[str, Any]:
        """
        取得大盤指數資訊
        
        API: https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX
        
        Returns:
            {
                "taiex": {
                    "name": "發行量加權股價指數",
                    "value": 23150.5,
                    "change": 85.3,
                    "change_percent": 0.37
                },
                "taiwan50": {...},
                ...
            }
        """
        cache_key = "market_index"
        cached = cls._get_cache(cache_key, "market_index")
        if cached:
            return cached
        
        await cls._rate_limit()
        
        try:
            async with httpx.AsyncClient(timeout=15, verify=False, headers=cls.HEADERS) as client:
                resp = await client.get(f"{cls.OPENAPI_BASE}/exchangeReport/MI_INDEX")
                
                if resp.status_code != 200:
                    return {}
                
                data = resp.json()
                
                result = {}
                index_map = {
                    "發行量加權股價指數": "taiex",
                    "臺灣50指數": "taiwan50",
                    "臺灣中型100指數": "taiwan100",
                    "未含金融指數": "non_finance",
                    "未含電子指數": "non_electronics",
                    "電子類指數": "electronics",
                    "金融保險類指數": "finance",
                }
                
                for item in data:
                    name = item.get("指數", "")
                    key = index_map.get(name)
                    if not key:
                        continue
                    
                    value = cls._safe_float(item.get("收盤指數"))
                    change_str = item.get("漲跌點數", "0")
                    change = cls._safe_float(change_str)
                    change_pct = cls._safe_float(item.get("漲跌百分比"))
                    
                    # 判斷漲跌方向
                    direction = item.get("漲跌", "")
                    if direction == "-" and change:
                        change = -abs(change)
                        if change_pct:
                            change_pct = -abs(change_pct)
                    
                    result[key] = {
                        "name": name,
                        "value": value,
                        "change": change,
                        "change_percent": change_pct,
                    }
                
                if result:
                    cls._set_cache(cache_key, result)
                    print(f"✅ [TWSE OpenAPI] 大盤指數: {len(result)} 項")
                
                return result
                
        except Exception as e:
            print(f"❌ [TWSE OpenAPI] 大盤指數錯誤: {e}")
            return {}
    
    # ============================================================
    # 4. 三大法人買賣超 API
    # ============================================================
    
    @classmethod
    async def get_institutional_trading(cls, date: str = None) -> Dict[str, Dict]:
        """
        取得三大法人買賣超資料
        
        API: https://www.twse.com.tw/rwd/zh/fund/T86
        
        Args:
            date: 日期格式 YYYYMMDD，預設為今天
            
        Returns:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "foreign_buy": 12345,      # 外資買進
                    "foreign_sell": 10000,     # 外資賣出
                    "foreign_net": 2345,       # 外資買賣超
                    "trust_buy": 500,          # 投信買進
                    "trust_sell": 200,         # 投信賣出
                    "trust_net": 300,          # 投信買賣超
                    "dealer_net": 100,         # 自營商買賣超
                    "total_net": 2745,         # 三大法人合計
                },
                ...
            }
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        # V10.13.2: 支持自動回溯交易日（最多嘗試 5 天）
        original_date = date
        max_retry = 5
        
        print(f"📅 [TWSE] 三大法人查詢，起始日期: {original_date}")
        
        for retry in range(max_retry):
            cache_key = f"institutional_{date}"
            cached = cls._get_cache(cache_key, "institutional")
            if cached:
                print(f"📦 [TWSE] 使用三大法人快取 (日期: {date})")
                return cached
            
            if retry > 0:
                await cls._rate_limit()
            else:
                await cls._rate_limit()
            
            try:
                print(f"🔍 [TWSE] 嘗試取得 {date} 三大法人資料 (第 {retry+1} 次)")
                async with httpx.AsyncClient(timeout=30, verify=False, headers=cls.HEADERS) as client:
                    resp = await client.get(
                        f"{cls.TWSE_API}/rwd/zh/fund/T86",
                        params={
                            "date": date,
                            "selectType": "ALLBUT0999",
                            "response": "json"
                        }
                    )
                    
                    if resp.status_code != 200:
                        print(f"⚠️ [TWSE] 三大法人 API 失敗: HTTP {resp.status_code}，日期 {date}")
                        # 嘗試前一天
                        date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                        continue
                    
                    # V10.13.1: 使用 _parse_response 處理壓縮數據
                    data = cls._parse_response(resp)
                    if data is None:
                        print(f"⚠️ [TWSE] 三大法人: 響應解析失敗，日期 {date}")
                        date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                        continue
                    
                    # V10.13.4: 更詳細的日誌
                    stat = data.get("stat", "unknown")
                    print(f"📊 [TWSE] {date} 響應 stat: {stat}")
                    
                    if "data" not in data:
                        if retry < max_retry - 1:
                            print(f"⚠️ [TWSE] 三大法人 {date}: 無資料 (stat={stat})，嘗試前一交易日...")
                            date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                            continue
                        else:
                            print("⚠️ [TWSE] 三大法人: 連續 5 天無資料")
                            return {}
                    
                    result = {}
                    for row in data["data"]:
                        if len(row) < 19:
                            continue
                        
                        stock_id = str(row[0]).strip()
                        if len(stock_id) != 4:
                            continue
                        
                        result[stock_id] = {
                            "stock_id": stock_id,
                            "name": str(row[1]).strip(),
                            "foreign_buy": cls._safe_int(row[2]),
                            "foreign_sell": cls._safe_int(row[3]),
                            "foreign_net": cls._safe_int(row[4]),
                            "trust_buy": cls._safe_int(row[8]),
                            "trust_sell": cls._safe_int(row[9]),
                            "trust_net": cls._safe_int(row[10]),
                            "dealer_net": cls._safe_int(row[17]),
                            "total_net": cls._safe_int(row[18]),
                            "date": date,  # V10.13.4: 記錄資料日期
                        }
                    
                    if result:
                        cls._set_cache(cache_key, result)
                        print(f"✅ [TWSE] 三大法人成功 ({date}): {len(result)} 檔")
                    
                    return result
                    
            except Exception as e:
                print(f"❌ [TWSE] 三大法人錯誤 ({date}): {e}")
                date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                continue
        
        return {}
    
    # ============================================================
    # 5. 融資融券 API
    # ============================================================
    
    @classmethod
    async def get_margin_trading(cls, date: str = None) -> Dict[str, Dict]:
        """
        取得融資融券資料
        
        API: https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN
        
        Returns:
            {
                "2330": {
                    "stock_id": "2330",
                    "margin_buy": 100,         # 融資買進
                    "margin_sell": 50,         # 融資賣出
                    "margin_balance": 5000,    # 融資餘額
                    "short_buy": 10,           # 融券買進
                    "short_sell": 20,          # 融券賣出
                    "short_balance": 500,      # 融券餘額
                },
                ...
            }
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        # V10.13.2: 支持自動回溯交易日（最多嘗試 5 天）
        original_date = date
        max_retry = 5
        
        for retry in range(max_retry):
            cache_key = f"margin_{date}"
            cached = cls._get_cache(cache_key, "margin")
            if cached:
                print("📦 [TWSE] 使用融資融券快取")
                return cached
            
            if retry > 0:
                await cls._rate_limit()
            else:
                await cls._rate_limit()
            
            try:
                async with httpx.AsyncClient(timeout=30, verify=False, headers=cls.HEADERS) as client:
                    resp = await client.get(
                        f"{cls.TWSE_API}/rwd/zh/marginTrading/MI_MARGN",
                        params={
                            "date": date,
                            "selectType": "STOCK",
                            "response": "json"
                        }
                    )
                    
                    if resp.status_code != 200:
                        date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                        continue
                    
                    # V10.13.1: 使用 _parse_response 處理壓縮數據
                    data = cls._parse_response(resp)
                    if data is None:
                        print("⚠️ [TWSE] 融資融券: 響應解析失敗")
                        date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                        continue
                    
                    # 融資融券資料在 tables[1] 中
                    if "tables" not in data or len(data["tables"]) < 2:
                        if retry < max_retry - 1:
                            print(f"⚠️ [TWSE] 融資融券 {date}: 無資料，嘗試前一交易日...")
                            date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                            continue
                        else:
                            print("⚠️ [TWSE] 融資融券: 連續 5 天無資料")
                            return {}
                    
                    table = data["tables"][1]
                    if "data" not in table:
                        date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                        continue
                    
                    result = {}
                    for row in table["data"]:
                        if len(row) < 13:
                            continue
                        
                        stock_id = str(row[0]).strip()
                        if len(stock_id) != 4:
                            continue
                        
                        result[stock_id] = {
                            "stock_id": stock_id,
                            "name": str(row[1]).strip() if len(row) > 1 else stock_id,
                            "margin_buy": cls._safe_int(row[2]),
                            "margin_sell": cls._safe_int(row[3]),
                            "margin_balance": cls._safe_int(row[6]),
                            "short_buy": cls._safe_int(row[8]),
                            "short_sell": cls._safe_int(row[9]),
                            "short_balance": cls._safe_int(row[12]),
                        }
                    
                    if result:
                        cls._set_cache(cache_key, result)
                        if date != original_date:
                            print(f"✅ [TWSE] 融資融券 ({date}): {len(result)} 檔")
                        else:
                            print(f"✅ [TWSE] 融資融券: {len(result)} 檔")
                    
                    return result
                    
            except Exception as e:
                print(f"❌ [TWSE] 融資融券錯誤: {e}")
                date = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                continue
        
        return {}
    
    # ============================================================
    # 6. 即時報價 API
    # ============================================================
    
    @classmethod
    async def get_realtime_quotes(cls, stock_ids: List[str]) -> Dict[str, Dict]:
        """
        取得即時報價（支援批量查詢）
        
        API: https://mis.twse.com.tw/stock/api/getStockInfo.jsp
        
        Args:
            stock_ids: 股票代號列表，例如 ["2330", "2317", "2454"]
            
        Returns:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "price": 1080.0,
                    "open": 1075.0,
                    "high": 1085.0,
                    "low": 1070.0,
                    "yesterday": 1075.0,
                    "volume": 12345,
                    "change": 5.0,
                    "change_percent": 0.47,
                    "time": "13:30:00",
                },
                ...
            }
        """
        if not stock_ids:
            return {}
        
        # 檢查快取（只取前 10 個代號作為 key）
        cache_key = f"realtime_{'_'.join(sorted(stock_ids[:10]))}"
        cached = cls._get_cache(cache_key, "realtime")
        if cached:
            # 只回傳請求的股票
            return {k: v for k, v in cached.items() if k in stock_ids}
        
        await cls._rate_limit()
        
        # 建立查詢字串
        ex_ch_list = []
        for sid in stock_ids:
            # 簡單判斷上市/上櫃（更準確的判斷需要參考完整清單）
            # 一般來說：1xxx-2xxx 上市，3xxx-8xxx 部分上櫃
            if sid.startswith(('3', '4', '5', '6', '8')):
                # 可能是上櫃，先試 tse，失敗再試 otc
                ex_ch_list.append(f"tse_{sid}.tw")
            else:
                ex_ch_list.append(f"tse_{sid}.tw")
        
        ex_ch = "|".join(ex_ch_list)
        
        try:
            async with httpx.AsyncClient(timeout=10, verify=False, headers=cls.HEADERS) as client:
                resp = await client.get(
                    cls.REALTIME_API,
                    params={"ex_ch": ex_ch, "json": "1", "delay": "0"}
                )
                
                if resp.status_code != 200:
                    print(f"⚠️ [TWSE] 即時報價失敗: HTTP {resp.status_code}")
                    return {}
                
                data = resp.json()
                
                if "msgArray" not in data:
                    return {}
                
                result = {}
                for item in data["msgArray"]:
                    stock_id = item.get("c", "")
                    if not stock_id:
                        continue
                    
                    price = cls._safe_float(item.get("z"))
                    yesterday = cls._safe_float(item.get("y"))
                    
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
                        "open": cls._safe_float(item.get("o")),
                        "high": cls._safe_float(item.get("h")),
                        "low": cls._safe_float(item.get("l")),
                        "yesterday": yesterday,
                        "volume": cls._safe_int(item.get("v")),
                        "trade_volume": cls._safe_int(item.get("tv")),
                        "change": change,
                        "change_percent": change_pct,
                        "time": item.get("t", ""),
                    }
                
                if result:
                    cls._set_cache(cache_key, result)
                    print(f"✅ [TWSE] 即時報價: {len(result)} 檔")
                
                return result
                
        except Exception as e:
            print(f"❌ [TWSE] 即時報價錯誤: {e}")
            return {}
    
    @classmethod
    async def get_realtime_quote(cls, stock_id: str) -> Optional[Dict]:
        """取得單一股票即時報價"""
        result = await cls.get_realtime_quotes([stock_id])
        return result.get(stock_id)
    
    # ============================================================
    # 7. 綜合查詢（一次取得多種資料）
    # ============================================================
    
    @classmethod
    async def get_stock_full_info(cls, stock_id: str) -> Dict[str, Any]:
        """
        取得單一股票的完整資訊（整合多個 API）
        
        Returns:
            {
                "stock_id": "2330",
                "name": "台積電",
                "price": 1080.0,
                "change": 5.0,
                "change_percent": 0.47,
                "pe_ratio": 23.37,
                "dividend_yield": 1.19,
                "pb_ratio": 7.42,
                "foreign_net": 2345,
                "trust_net": 300,
                "total_net": 2745,
                ...
            }
        """
        result = {"stock_id": stock_id}
        
        # 並行取得所有資料
        per_task = cls.get_per_dividend_all()
        daily_task = cls.get_daily_trading_all()
        inst_task = cls.get_institutional_trading()
        
        per_data, daily_data, inst_data = await asyncio.gather(
            per_task, daily_task, inst_task,
            return_exceptions=True
        )
        
        # 合併本益比/殖利率
        if isinstance(per_data, dict) and stock_id in per_data:
            result.update(per_data[stock_id])
        
        # 合併每日成交
        if isinstance(daily_data, dict) and stock_id in daily_data:
            daily = daily_data[stock_id]
            result["price"] = daily.get("close")
            result["open"] = daily.get("open")
            result["high"] = daily.get("high")
            result["low"] = daily.get("low")
            result["change"] = daily.get("change")
            result["change_percent"] = daily.get("change_percent")
            result["volume"] = daily.get("trade_volume")
        
        # 合併三大法人
        if isinstance(inst_data, dict) and stock_id in inst_data:
            inst = inst_data[stock_id]
            result["foreign_net"] = inst.get("foreign_net")
            result["trust_net"] = inst.get("trust_net")
            result["dealer_net"] = inst.get("dealer_net")
            result["total_net"] = inst.get("total_net")
        
        return result
    
    @classmethod
    async def get_all_stocks_summary(cls) -> Dict[str, Dict]:
        """
        取得所有股票的摘要資訊（整合本益比 + 每日成交）
        
        這是最常用的 API，一次取得所有股票的基本資訊
        """
        # 並行取得資料
        per_task = cls.get_per_dividend_all()
        daily_task = cls.get_daily_trading_all()
        
        per_data, daily_data = await asyncio.gather(
            per_task, daily_task,
            return_exceptions=True
        )
        
        # 以每日成交為基礎合併
        if not isinstance(daily_data, dict):
            daily_data = {}
        if not isinstance(per_data, dict):
            per_data = {}
        
        result = {}
        
        # 🆕 V10.13.5: 取得資料日期（從本益比資料）
        data_date = None
        if per_data:
            sample = next(iter(per_data.values()), {})
            data_date = sample.get("date")
        
        # 先加入所有每日成交的股票
        for stock_id, daily in daily_data.items():
            result[stock_id] = {
                "stock_id": stock_id,
                "name": daily.get("name", stock_id),
                "price": daily.get("close"),
                "open": daily.get("open"),
                "high": daily.get("high"),
                "low": daily.get("low"),
                "change": daily.get("change"),
                "change_percent": daily.get("change_percent"),
                "volume": daily.get("trade_volume"),
                "pe_ratio": None,
                "dividend_yield": None,
                "pb_ratio": None,
                "date": data_date,  # 🆕 V10.13.5: 資料日期
            }
            
            # 合併本益比資料
            if stock_id in per_data:
                per = per_data[stock_id]
                result[stock_id]["pe_ratio"] = per.get("pe_ratio")
                result[stock_id]["dividend_yield"] = per.get("dividend_yield")
                result[stock_id]["pb_ratio"] = per.get("pb_ratio")
                result[stock_id]["date"] = per.get("date")  # 使用本益比資料的日期
        
        print(f"✅ [TWSE OpenAPI] 股票摘要: {len(result)} 檔")
        return result


# ============================================================
    # 6. 注意股票 API (V10.11 新增)
    # ============================================================
    
    @classmethod
    async def get_attention_stocks(cls) -> Dict[str, Dict]:
        """
        取得當日注意股票
        
        API: https://openapi.twse.com.tw/v1/announcement/notice
        
        回傳:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "attention_date": "2024/12/22",
                    "attention_reason": "近期股價異常波動",
                    "is_attention": True
                }
            }
        """
        cache_key = "attention_stocks"
        cached = cls._get_cache(cache_key, "institutional")
        if cached:
            print("📦 [TWSE] 使用注意股票快取")
            return cached
        
        await cls._rate_limit()
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
                response = await client.get(
                    f"{cls.OPENAPI_BASE}/announcement/notice",
                    headers=cls.HEADERS
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {}
                    
                    for item in data:
                        stock_id = item.get("Code", "")
                        if stock_id and len(stock_id) == 4:
                            result[stock_id] = {
                                "stock_id": stock_id,
                                "name": item.get("Name", ""),
                                "attention_date": item.get("Date", ""),
                                "attention_reason": item.get("Reason", "注意股票"),
                                "is_attention": True
                            }
                    
                    if result:
                        print(f"✅ [TWSE] 注意股票: {len(result)} 檔")
                        cls._set_cache(cache_key, result, "institutional")
                    
                    return result
                    
        except Exception as e:
            print(f"❌ [TWSE] 注意股票錯誤: {e}")
        
        return {}
    
    # ============================================================
    # 7. 每月營收 API (V10.11 新增)
    # ============================================================
    
    @classmethod
    async def get_monthly_revenue(cls) -> Dict[str, Dict]:
        """
        取得上市公司每月營業收入
        
        API: https://openapi.twse.com.tw/v1/opendata/t187ap05_L
        
        回傳:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "revenue": 236020000,      # 當月營收（千元）
                    "revenue_mom": 5.2,        # 月增率 %
                    "revenue_yoy": 12.8,       # 年增率 %
                    "revenue_date": "113年11月"
                }
            }
        """
        cache_key = "monthly_revenue"
        cached = cls._get_cache(cache_key, "per")  # 較長快取
        if cached:
            print("📦 [TWSE] 使用營收快取")
            return cached
        
        await cls._rate_limit()
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
                response = await client.get(
                    f"{cls.OPENAPI_BASE}/opendata/t187ap05_L",
                    headers=cls.HEADERS
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {}
                    
                    for item in data:
                        stock_id = item.get("公司代號", "")
                        if stock_id and len(stock_id) == 4:
                            # 解析營收數據
                            revenue = cls._safe_float(item.get("當月營收", 0))
                            revenue_mom = cls._safe_float(item.get("上月比較增減(%)", 0))
                            revenue_yoy = cls._safe_float(item.get("去年同月增減(%)", 0))
                            
                            result[stock_id] = {
                                "stock_id": stock_id,
                                "name": item.get("公司名稱", ""),
                                "revenue": revenue,
                                "revenue_mom": revenue_mom,
                                "revenue_yoy": revenue_yoy,
                                "revenue_date": item.get("資料年月", "")
                            }
                    
                    if result:
                        print(f"✅ [TWSE] 每月營收: {len(result)} 檔")
                        cls._set_cache(cache_key, result, "per")
                    
                    return result
                    
        except Exception as e:
            print(f"❌ [TWSE] 每月營收錯誤: {e}")
        
        return {}
    
    # ============================================================
    # 8. 除權息預告 API (V10.11 新增)
    # ============================================================
    
    @classmethod
    async def get_dividend_schedule(cls) -> Dict[str, Dict]:
        """
        取得除權除息預告表
        
        API: https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL
        
        回傳:
            {
                "2330": {
                    "stock_id": "2330",
                    "name": "台積電",
                    "ex_date": "2024/12/25",
                    "cash_dividend": 3.5,
                    "stock_dividend": 0
                }
            }
        """
        cache_key = "dividend_schedule"
        cached = cls._get_cache(cache_key, "per")
        if cached:
            print("📦 [TWSE] 使用除權息快取")
            return cached
        
        await cls._rate_limit()
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
                response = await client.get(
                    f"{cls.OPENAPI_BASE}/exchangeReport/TWT48U_ALL",
                    headers=cls.HEADERS
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = {}
                    
                    for item in data:
                        stock_id = item.get("Code", "")
                        if stock_id and len(stock_id) == 4:
                            result[stock_id] = {
                                "stock_id": stock_id,
                                "name": item.get("Name", ""),
                                "ex_date": item.get("ExDividendDate", ""),
                                "ex_reason": item.get("ExDividendReason", ""),
                                "cash_dividend": cls._safe_float(item.get("CashDividend", 0)),
                                "stock_dividend": cls._safe_float(item.get("StockDividendShares", 0))
                            }
                    
                    if result:
                        print(f"✅ [TWSE] 除權息預告: {len(result)} 檔")
                        cls._set_cache(cache_key, result, "per")
                    
                    return result
                    
        except Exception as e:
            print(f"❌ [TWSE] 除權息預告錯誤: {e}")
        
        return {}


# ============================================================
# 便捷函數（向後相容）
# ============================================================

async def get_twse_per_dividend() -> Dict[str, Dict]:
    """取得所有股票本益比/殖利率"""
    return await TWSEOpenAPI.get_per_dividend_all()

async def get_twse_daily_trading() -> Dict[str, Dict]:
    """取得所有股票每日成交"""
    return await TWSEOpenAPI.get_daily_trading_all()

async def get_twse_market_index() -> Dict[str, Any]:
    """取得大盤指數"""
    return await TWSEOpenAPI.get_market_index()

async def get_twse_institutional() -> Dict[str, Dict]:
    """取得三大法人買賣超"""
    return await TWSEOpenAPI.get_institutional_trading()

async def get_twse_margin() -> Dict[str, Dict]:
    """取得融資融券"""
    return await TWSEOpenAPI.get_margin_trading()

async def get_twse_realtime(stock_ids: List[str]) -> Dict[str, Dict]:
    """取得即時報價"""
    return await TWSEOpenAPI.get_realtime_quotes(stock_ids)

async def get_twse_all_summary() -> Dict[str, Dict]:
    """取得所有股票摘要"""
    return await TWSEOpenAPI.get_all_stocks_summary()

async def get_twse_attention() -> Dict[str, Dict]:
    """取得注意股票"""
    return await TWSEOpenAPI.get_attention_stocks()

async def get_twse_revenue() -> Dict[str, Dict]:
    """取得每月營收"""
    return await TWSEOpenAPI.get_monthly_revenue()

async def get_twse_dividend() -> Dict[str, Dict]:
    """取得除權息預告"""
    return await TWSEOpenAPI.get_dividend_schedule()
