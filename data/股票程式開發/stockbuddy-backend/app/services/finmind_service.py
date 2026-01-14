"""
FinMind 資料服務
- 台股完整資料源
- 三大法人買賣超
- 融資融券
- 營收資料
- 技術指標

API 文件: https://finmind.github.io/

V10.37 安全性修復: API Token 改從環境變數讀取
"""

import os
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import math

logger = logging.getLogger(__name__)


class FinMindService:
    """FinMind 資料服務"""

    BASE_URL = "https://api.finmindtrade.com/api/v4/data"

    # V10.37: API Token 從環境變數讀取，不再硬編碼
    API_TOKEN = os.getenv("FINMIND_TOKEN", "")
    
    # 快取
    _cache = {}
    _cache_time = {}
    CACHE_DURATION = 600  # 10 分鐘
    
    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取"""
        if key in cls._cache:
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < cls.CACHE_DURATION:
                return cls._cache[key]
        return None
    
    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()
    
    @classmethod
    async def _request(cls, dataset: str, params: Dict) -> Optional[List[Dict]]:
        """發送 API 請求"""
        try:
            params["token"] = cls.API_TOKEN
            params["dataset"] = dataset
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(cls.BASE_URL, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"FinMind API 錯誤: HTTP {response.status_code}")
                    try:
                        error_detail = response.json()
                        logger.warning(f"  錯誤詳情: {error_detail}")
                    except:
                        logger.warning(f"  回應內容: {response.text[:200]}")
                    return None

                data = response.json()

                if data.get("status") != 200:
                    logger.warning(f"FinMind API 回應錯誤: {data.get('msg')}")
                    return None

                return data.get("data", [])

        except Exception as e:
            logger.error(f"FinMind API 請求失敗: {e}")
            return None
    
    # ========== 股價資料 ==========
    
    @classmethod
    async def get_stock_price(cls, stock_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        取得股價資料
        
        Args:
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
        
        Returns:
            [{"date": "2024-12-13", "open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000000}, ...]
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"price_{stock_id}_{start_date}_{end_date}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockPrice", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            result = []
            for row in data:
                result.append({
                    "date": row.get("date"),
                    "open": row.get("open"),
                    "high": row.get("max"),
                    "low": row.get("min"),
                    "close": row.get("close"),
                    "volume": row.get("Trading_Volume"),
                    "turnover": row.get("Trading_money"),
                })
            cls._set_cache(cache_key, result)
            return result
        
        return []
    
    # ========== 三大法人 ==========
    
    @classmethod
    async def get_institutional_investors(cls, stock_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        取得三大法人買賣超
        
        Returns:
            [{"date": "2024-12-13", "foreign_net": 1000, "foreign_buy": 5000, "foreign_sell": 4000, ...}, ...]
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"inst_{stock_id}_{start_date}_{end_date}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockInstitutionalInvestorsBuySell", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            # 整理資料（按日期彙總，包含買賣明細）
            daily_data = {}
            for row in data:
                date = row.get("date")
                if date not in daily_data:
                    daily_data[date] = {
                        "date": date, 
                        "foreign_buy": 0, "foreign_sell": 0, "foreign_net": 0, 
                        "trust_buy": 0, "trust_sell": 0, "trust_net": 0, 
                        "dealer_buy": 0, "dealer_sell": 0, "dealer_net": 0
                    }
                
                inv_type = row.get("name")
                buy = row.get("buy", 0) or 0
                sell = row.get("sell", 0) or 0
                net = buy - sell
                
                if "外資" in inv_type or "Foreign" in inv_type:
                    daily_data[date]["foreign_buy"] += buy
                    daily_data[date]["foreign_sell"] += sell
                    daily_data[date]["foreign_net"] += net
                elif "投信" in inv_type or "Investment" in inv_type:
                    daily_data[date]["trust_buy"] += buy
                    daily_data[date]["trust_sell"] += sell
                    daily_data[date]["trust_net"] += net
                elif "自營" in inv_type or "Dealer" in inv_type:
                    daily_data[date]["dealer_buy"] += buy
                    daily_data[date]["dealer_sell"] += sell
                    daily_data[date]["dealer_net"] += net
            
            result = list(daily_data.values())
            result.sort(key=lambda x: x["date"], reverse=True)
            cls._set_cache(cache_key, result)
            return result
        
        return []
    
    @classmethod
    async def get_institutional_history(
        cls,
        stock_id: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        取得三大法人歷史資料（用於圖表）

        這是 get_institutional_investors 的別名，返回相同格式的資料

        Args:
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            [{"date": "2024-12-13", "foreign_net": 1000, "trust_net": 500, "dealer_net": -200}, ...]
        """
        data = await cls.get_institutional_investors(stock_id, start_date, end_date)
        # 反轉順序讓日期從舊到新（用於圖表繪製）
        if data:
            return list(reversed(data))
        return []

    @classmethod
    async def get_latest_institutional(cls, stock_id: str) -> Dict:
        """取得最新三大法人買賣超（含買賣明細）"""
        data = await cls.get_institutional_investors(stock_id)
        
        if data:
            latest = data[0]
            total = latest["foreign_net"] + latest["trust_net"] + latest["dealer_net"]
            
            return {
                "date": latest["date"],
                "foreign": {
                    "buy": latest["foreign_buy"],
                    "sell": latest["foreign_sell"],
                    "net": latest["foreign_net"],
                    "net_display": f"{'+' if latest['foreign_net'] >= 0 else ''}{latest['foreign_net']:,} 張",
                },
                "investment_trust": {
                    "buy": latest["trust_buy"],
                    "sell": latest["trust_sell"],
                    "net": latest["trust_net"],
                    "net_display": f"{'+' if latest['trust_net'] >= 0 else ''}{latest['trust_net']:,} 張",
                },
                "dealer": {
                    "buy": latest["dealer_buy"],
                    "sell": latest["dealer_sell"],
                    "net": latest["dealer_net"],
                    "net_display": f"{'+' if latest['dealer_net'] >= 0 else ''}{latest['dealer_net']:,} 張",
                },
                "total_net": total,
                "total_net_display": f"{'+' if total >= 0 else ''}{total:,} 張",
                "trend": "買超" if total > 0 else "賣超" if total < 0 else "中性",
                "is_real_data": True,
            }
        
        return {"is_real_data": False}
    
    # ========== 融資融券 ==========
    
    @classmethod
    async def get_margin_trading(cls, stock_id: str, start_date: str = None, end_date: str = None, days: int = None) -> List[Dict]:
        """
        取得融資融券資料
        
        Args:
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            days: 取得最近幾天的資料（會覆蓋 start_date）
        
        Returns:
            [{"date": "2024-12-13", "margin_balance": 10000, "short_balance": 500}, ...]
        """
        if days:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        elif not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"margin_{stock_id}_{start_date}_{end_date}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockMarginPurchaseShortSale", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            result = []
            for row in data:
                result.append({
                    "date": row.get("date"),
                    "margin_buy": row.get("MarginPurchaseBuy", 0),
                    "margin_sell": row.get("MarginPurchaseSell", 0),
                    "margin_balance": row.get("MarginPurchaseTodayBalance", 0),
                    "short_buy": row.get("ShortSaleBuy", 0),
                    "short_sell": row.get("ShortSaleSell", 0),
                    "short_balance": row.get("ShortSaleTodayBalance", 0),
                })
            cls._set_cache(cache_key, result)
            return result
        
        return []
    
    # ========== 營收資料 ==========
    
    @classmethod
    async def get_monthly_revenue(cls, stock_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        取得月營收資料
        
        Returns:
            [{"date": "2024-11", "revenue": 1000000000, "yoy": 15.5, "mom": 2.3}, ...]
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"revenue_{stock_id}_{start_date}_{end_date}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockMonthRevenue", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            result = []
            for row in data:
                result.append({
                    "date": row.get("date"),
                    "revenue": row.get("revenue", 0),
                    "yoy": row.get("revenue_year_growth_rate"),  # 年增率
                    "mom": row.get("revenue_month_growth_rate"),  # 月增率
                })
            cls._set_cache(cache_key, result)
            return result
        
        return []
    
    # ========== 財報資料 ==========
    
    @classmethod
    async def get_financial_statements(cls, stock_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        取得財報資料（季報）
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"financial_{stock_id}_{start_date}_{end_date}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockFinancialStatements", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            cls._set_cache(cache_key, data)
            return data
        
        return []
    
    # ========== 本益比/淨值比 ==========
    
    @classmethod
    async def get_per_pbr(cls, stock_id: str, start_date: str = None, end_date: str = None, days: int = None) -> List[Dict]:
        """
        取得本益比/股價淨值比
        
        Args:
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            days: 取得最近幾天的資料（會覆蓋 start_date）
        """
        if days:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        elif not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = f"per_{stock_id}_{start_date}_{end_date}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockPER", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            result = []
            for row in data:
                result.append({
                    "date": row.get("date"),
                    "pe_ratio": row.get("PER"),
                    "pb_ratio": row.get("PBR"),
                    "dividend_yield": row.get("dividend_yield"),
                })
            cls._set_cache(cache_key, result)
            return result
        
        return []
    
    @classmethod
    async def get_latest_per_pbr(cls, stock_id: str) -> Dict:
        """取得最新本益比/淨值比"""
        data = await cls.get_per_pbr(stock_id)
        
        if data:
            latest = data[-1]  # 最新一筆
            return {
                "date": latest["date"],
                "pe_ratio": latest.get("pe_ratio"),
                "pb_ratio": latest.get("pb_ratio"),
                "dividend_yield": latest.get("dividend_yield"),
                "is_real_data": True,
            }
        
        return {"is_real_data": False}
    
    # ========== 全市場掃描 ==========
    
    @classmethod
    async def get_all_stocks_daily(cls, date: str = None) -> Dict[str, Dict]:
        """
        取得全市場當日行情
        
        注意：FinMind 全市場查詢需要用最近的交易日
        
        Returns:
            {stock_id: {price_data...}, ...}
        """
        # 嘗試最近 5 個交易日（避免週末/假日問題）
        from datetime import timedelta
        
        for days_ago in range(5):
            check_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            cache_key = f"all_daily_{check_date}"
            cached = cls._get_cache(cache_key)
            if cached and len(cached) > 100:
                print(f"📦 FinMind 快取: {len(cached)} 檔")
                return cached
            
            try:
                # FinMind 全市場查詢不需要 data_id
                params = {
                    "token": cls.API_TOKEN,
                    "dataset": "TaiwanStockPrice",
                    "start_date": check_date,
                    "end_date": check_date,
                }
                
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.get(cls.BASE_URL, params=params)
                    
                    if response.status_code != 200:
                        print(f"⚠️ FinMind {check_date}: HTTP {response.status_code}")
                        continue
                    
                    data = response.json()
                    
                    if data.get("status") != 200:
                        print(f"⚠️ FinMind {check_date}: {data.get('msg')}")
                        continue
                    
                    rows = data.get("data", [])
                    if not rows or len(rows) < 100:
                        print(f"⚠️ FinMind {check_date}: 資料不足 ({len(rows)} 筆)")
                        continue
                    
                    # 處理資料
                    result = {}
                    for row in rows:
                        stock_id = row.get("stock_id")
                        if not stock_id:
                            continue
                        
                        # 只要上市櫃股票（排除權證等）
                        if len(stock_id) != 4:
                            continue
                        if not stock_id.isdigit():
                            continue
                        
                        close_price = row.get("close")
                        open_price = row.get("open")
                        spread = row.get("spread", 0) or 0
                        
                        if not close_price or close_price <= 0:
                            continue
                        
                        # 計算漲跌幅
                        prev_close = close_price - spread
                        change_pct = round(spread / prev_close * 100, 2) if prev_close > 0 else 0
                        
                        result[stock_id] = {
                            "stock_id": stock_id,
                            "date": row.get("date"),
                            "open": open_price,
                            "high": row.get("max"),
                            "low": row.get("min"),
                            "close": close_price,
                            "volume": row.get("Trading_Volume", 0) or 0,
                            "change": spread,
                            "change_percent": change_pct,
                        }
                    
                    if len(result) > 100:
                        cls._set_cache(cache_key, result)
                        print(f"✅ FinMind: 取得 {len(result)} 檔股票 ({check_date})")
                        return result
                    
            except Exception as e:
                print(f"⚠️ FinMind {check_date} 錯誤: {e}")
                continue
        
        print("❌ FinMind 全市場查詢失敗")
        return {}
    
    # ========== 股票清單 ==========
    
    @classmethod
    async def get_stock_list(cls) -> List[Dict]:
        """
        取得所有上市櫃股票清單
        """
        cache_key = "stock_list"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        data = await cls._request("TaiwanStockInfo", {})
        
        if data:
            result = []
            for row in data:
                result.append({
                    "stock_id": row.get("stock_id"),
                    "name": row.get("stock_name"),
                    "industry": row.get("industry_category"),
                    "type": row.get("type"),  # 上市/上櫃
                })
            cls._set_cache(cache_key, result)
            return result
        
        return []


# 便捷函數
async def get_finmind_institutional(stock_id: str) -> Dict:
    """取得 FinMind 三大法人資料"""
    return await FinMindService.get_latest_institutional(stock_id)


async def get_finmind_per_pbr(stock_id: str) -> Dict:
    """取得 FinMind 本益比/淨值比"""
    return await FinMindService.get_latest_per_pbr(stock_id)


async def get_finmind_all_stocks() -> Dict:
    """取得全市場股票資料"""
    return await FinMindService.get_all_stocks_daily()


# ============================================================
# 擴展資料集（V9.5+）
# ============================================================

class FinMindExtended:
    """FinMind 擴展資料服務 - 更多免費資料集"""
    
    # ========== 外資持股 ==========
    
    @classmethod
    async def get_foreign_holding(cls, stock_id: str, days: int = 30) -> List[Dict]:
        """
        取得外資持股資料
        
        Returns:
            [{date, stock_id, Foreign_Investor_Shareholding, Foreign_Holding_Percentage, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cache_key = f"foreign_{stock_id}_{days}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockShareholding", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    @classmethod
    async def get_latest_foreign_holding(cls, stock_id: str) -> Dict:
        """取得最新外資持股"""
        data = await cls.get_foreign_holding(stock_id, days=10)
        if data:
            latest = data[-1]
            return {
                "date": latest.get("date"),
                "holding_shares": latest.get("Foreign_Investor_Shareholding", 0),
                "holding_percentage": latest.get("Foreign_Holding_Percentage", 0),
            }
        return {}
    
    # ========== 借券明細 ==========
    
    @classmethod
    async def get_securities_lending(cls, stock_id: str, days: int = 30) -> List[Dict]:
        """
        取得借券成交明細
        
        Returns:
            [{date, stock_id, transaction_type, volume, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cache_key = f"lending_{stock_id}_{days}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockSecuritiesLending", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== 月營收 ==========
    
    @classmethod
    async def get_monthly_revenue(cls, stock_id: str, months: int = 12) -> List[Dict]:
        """
        取得月營收資料
        
        Returns:
            [{date, stock_id, revenue, revenue_month, revenue_year, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=months*35)).strftime("%Y-%m-%d")
        
        cache_key = f"revenue_{stock_id}_{months}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockMonthRevenue", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    @classmethod
    async def get_latest_revenue(cls, stock_id: str) -> Dict:
        """取得最新月營收"""
        data = await cls.get_monthly_revenue(stock_id, months=3)
        if data:
            latest = data[-1]
            # 計算年增率
            yoy = None
            if len(data) >= 2:
                prev_year_data = [d for d in data if d.get("revenue_year") == latest.get("revenue_year") - 1 
                                  and d.get("revenue_month") == latest.get("revenue_month")]
                if prev_year_data:
                    prev_revenue = prev_year_data[0].get("revenue", 0)
                    if prev_revenue > 0:
                        yoy = round((latest.get("revenue", 0) - prev_revenue) / prev_revenue * 100, 2)
            
            return {
                "date": latest.get("date"),
                "revenue": latest.get("revenue"),
                "revenue_month": latest.get("revenue_month"),
                "revenue_year": latest.get("revenue_year"),
                "yoy": yoy,  # 年增率
            }
        return {}
    
    # ========== 財報 - 綜合損益表 ==========
    
    @classmethod
    async def get_income_statement(cls, stock_id: str) -> List[Dict]:
        """
        取得綜合損益表
        
        Returns:
            [{date, stock_id, type, value, origin_name, ...}, ...]
        """
        cache_key = f"income_{stock_id}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        start_date = (datetime.now() - timedelta(days=365*2)).strftime("%Y-%m-%d")
        
        data = await FinMindService._request("TaiwanStockFinancialStatements", {
            "data_id": stock_id,
            "start_date": start_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== 財報 - 資產負債表 ==========
    
    @classmethod
    async def get_balance_sheet(cls, stock_id: str) -> List[Dict]:
        """
        取得資產負債表
        
        Returns:
            [{date, stock_id, type, value, origin_name, ...}, ...]
        """
        cache_key = f"balance_{stock_id}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        start_date = (datetime.now() - timedelta(days=365*2)).strftime("%Y-%m-%d")
        
        data = await FinMindService._request("TaiwanStockBalanceSheet", {
            "data_id": stock_id,
            "start_date": start_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== 財報 - 現金流量表 ==========
    
    @classmethod
    async def get_cash_flow(cls, stock_id: str) -> List[Dict]:
        """
        取得現金流量表
        
        Returns:
            [{date, stock_id, type, value, origin_name, ...}, ...]
        """
        cache_key = f"cashflow_{stock_id}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        start_date = (datetime.now() - timedelta(days=365*2)).strftime("%Y-%m-%d")
        
        data = await FinMindService._request("TaiwanStockCashFlowsStatement", {
            "data_id": stock_id,
            "start_date": start_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== 股利政策 ==========
    
    @classmethod
    async def get_dividend(cls, stock_id: str) -> List[Dict]:
        """
        取得股利政策
        
        Returns:
            [{date, stock_id, CashEarningsDistribution, StockEarningsDistribution, ...}, ...]
        """
        cache_key = f"dividend_{stock_id}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d")
        
        data = await FinMindService._request("TaiwanStockDividend", {
            "data_id": stock_id,
            "start_date": start_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    @classmethod
    async def get_latest_dividend(cls, stock_id: str) -> Dict:
        """取得最新股利資料"""
        data = await cls.get_dividend(stock_id)
        if data:
            latest = data[-1]
            cash = latest.get("CashEarningsDistribution", 0) or 0
            stock = latest.get("StockEarningsDistribution", 0) or 0
            return {
                "year": latest.get("date", "")[:4],
                "cash_dividend": cash,  # 現金股利
                "stock_dividend": stock,  # 股票股利
                "total_dividend": cash + stock,
            }
        return {}
    
    # ========== 股票新聞 ==========
    
    @classmethod
    async def get_stock_news(cls, stock_id: str, days: int = 7) -> List[Dict]:
        """
        取得股票相關新聞
        
        Returns:
            [{date, stock_id, description, link, source, title, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cache_key = f"news_{stock_id}_{days}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockNews", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            # 只保留最新的 10 則
            result = data[-10:] if len(data) > 10 else data
            FinMindService._set_cache(cache_key, result)
            return result
        return []
    
    # ========== 當日沖銷交易 ==========
    
    @classmethod
    async def get_day_trading(cls, stock_id: str, days: int = 30) -> List[Dict]:
        """
        取得當日沖銷交易資料
        
        Returns:
            [{date, stock_id, DayTradingVolume, DayTradingAmount, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cache_key = f"daytrading_{stock_id}_{days}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockDayTrading", {
            "data_id": stock_id,
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== 整體市場三大法人 ==========
    
    @classmethod
    async def get_total_institutional(cls, days: int = 30) -> List[Dict]:
        """
        取得整體市場三大法人買賣
        
        Returns:
            [{date, name, buy, sell, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cache_key = f"total_inst_{days}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockTotalInstitutionalInvestors", {
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== 整體市場融資融券 ==========
    
    @classmethod
    async def get_total_margin(cls, days: int = 30) -> List[Dict]:
        """
        取得整體市場融資融券
        
        Returns:
            [{date, name, buy, sell, TodayBalance, ...}, ...]
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cache_key = f"total_margin_{days}"
        cached = FinMindService._get_cache(cache_key)
        if cached:
            return cached
        
        data = await FinMindService._request("TaiwanStockTotalMarginPurchaseShortSale", {
            "start_date": start_date,
            "end_date": end_date,
        })
        
        if data:
            FinMindService._set_cache(cache_key, data)
            return data
        return []
    
    # ========== PER/PBR（優化版）==========
    
    @classmethod
    async def get_valuation(cls, stock_id: str) -> Dict:
        """
        取得估值資料（PER、PBR、殖利率）
        
        Returns:
            {per, pbr, dividend_yield, date}
        """
        data = await FinMindService.get_per_pbr(stock_id, days=10)
        if data:
            latest = data[-1]
            return {
                "date": latest.get("date"),
                "per": latest.get("PER"),
                "pbr": latest.get("PBR"),
                "dividend_yield": latest.get("dividend_yield"),
            }
        return {}


# 便捷函數 - 擴展
async def get_finmind_news(stock_id: str) -> List[Dict]:
    """取得股票新聞"""
    return await FinMindExtended.get_stock_news(stock_id)


async def get_finmind_revenue(stock_id: str) -> Dict:
    """取得最新營收"""
    return await FinMindExtended.get_latest_revenue(stock_id)


async def get_finmind_dividend(stock_id: str) -> Dict:
    """取得股利資料"""
    return await FinMindExtended.get_latest_dividend(stock_id)


async def get_finmind_foreign(stock_id: str) -> Dict:
    """取得外資持股"""
    return await FinMindExtended.get_latest_foreign_holding(stock_id)
