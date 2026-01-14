"""
TPEx OpenAPI 服務 - 櫃買中心資料 API
V10.15 新增：支援上櫃股票資料

提供功能：
1. 上櫃股票每日成交資訊
2. 上櫃股票本益比/殖利率/淨值比
3. 上櫃三大法人買賣超
4. 上櫃融資融券
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cachetools import TTLCache
import time
import json

class TPExOpenAPI:
    """櫃買中心 OpenAPI 服務"""

    BASE_URL = "https://www.tpex.org.tw/openapi/v1"

    # 快取設定
    _cache = TTLCache(maxsize=100, ttl=300)  # 5 分鐘
    _daily_cache = TTLCache(maxsize=50, ttl=60)  # 1 分鐘
    _last_request_time = 0
    _request_interval = 1.5  # 每次請求間隔 1.5 秒

    @classmethod
    async def _rate_limited_request(cls, url: str, params: dict = None) -> Optional[Any]:
        """限速請求"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - cls._last_request_time
        if time_since_last < cls._request_interval:
            await asyncio.sleep(cls._request_interval - time_since_last)

        cls._last_request_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                # 嘗試解析 JSON
                try:
                    return response.json()
                except:
                    return None
        except Exception as e:
            print(f"[TPEx] 請求失敗: {url}, 錯誤: {e}")
            return None

    @classmethod
    async def get_otc_stock_summary(cls) -> Dict[str, Dict]:
        """
        取得上櫃股票每日成交資訊

        Returns:
            Dict[stock_id, {name, price, change, change_percent, volume, ...}]
        """
        cache_key = "otc_stock_summary"
        if cache_key in cls._daily_cache:
            return cls._daily_cache[cache_key]

        url = f"{cls.BASE_URL}/tpex_mainboard_quotes"
        data = await cls._rate_limited_request(url)

        if not data:
            return {}

        result = {}
        for item in data:
            try:
                stock_id = item.get("SecuritiesCompanyCode", "")
                if not stock_id or not stock_id.isdigit():
                    continue

                # 解析價格和成交量
                close_price = cls._parse_number(item.get("Close", 0))
                open_price = cls._parse_number(item.get("Open", 0))
                high_price = cls._parse_number(item.get("High", 0))
                low_price = cls._parse_number(item.get("Low", 0))
                prev_close = cls._parse_number(item.get("PreviousClose", 0))
                volume = cls._parse_number(item.get("TradingShares", 0))

                # 計算漲跌
                change = close_price - prev_close if prev_close else 0
                change_percent = (change / prev_close * 100) if prev_close else 0

                result[stock_id] = {
                    "stock_id": stock_id,
                    "name": item.get("CompanyName", stock_id),
                    "price": close_price,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "prev_close": prev_close,
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "volume": int(volume / 1000) if volume > 0 else 0,  # 轉換為張
                    "market": "OTC",
                    "source": "TPEx",
                }
            except Exception as e:
                continue

        if result:
            cls._daily_cache[cache_key] = result
            print(f"[TPEx] 取得 {len(result)} 檔上櫃股票資料")

        return result

    @classmethod
    async def get_otc_pe_ratio(cls) -> Dict[str, Dict]:
        """
        取得上櫃股票本益比/殖利率/淨值比

        Returns:
            Dict[stock_id, {pe_ratio, pb_ratio, dividend_yield}]
        """
        cache_key = "otc_pe_ratio"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        url = f"{cls.BASE_URL}/tpex_mainboard_peratio"
        data = await cls._rate_limited_request(url)

        if not data:
            return {}

        result = {}
        for item in data:
            try:
                stock_id = item.get("SecuritiesCompanyCode", "")
                if not stock_id or not stock_id.isdigit():
                    continue

                pe_ratio = cls._parse_number(item.get("PriceEarningRatio", 0))
                pb_ratio = cls._parse_number(item.get("PriceBookRatio", 0))
                dividend_yield = cls._parse_number(item.get("DividendYield", 0))

                result[stock_id] = {
                    "stock_id": stock_id,
                    "name": item.get("CompanyName", stock_id),
                    "pe_ratio": pe_ratio if pe_ratio > 0 else None,
                    "pb_ratio": pb_ratio if pb_ratio > 0 else None,
                    "dividend_yield": dividend_yield if dividend_yield > 0 else None,
                }
            except:
                continue

        if result:
            cls._cache[cache_key] = result
            print(f"[TPEx] 取得 {len(result)} 檔上櫃股票本益比資料")

        return result

    @classmethod
    async def get_otc_institutional(cls) -> Dict[str, Dict]:
        """
        取得上櫃三大法人買賣超

        Returns:
            Dict[stock_id, {foreign_net, trust_net, dealer_net, total_net}]
        """
        cache_key = "otc_institutional"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        url = f"{cls.BASE_URL}/tpex_mainboard_fund"
        data = await cls._rate_limited_request(url)

        if not data:
            return {}

        result = {}
        for item in data:
            try:
                stock_id = item.get("SecuritiesCompanyCode", "")
                if not stock_id or not stock_id.isdigit():
                    continue

                foreign_net = cls._parse_number(item.get("ForeignNetBuySellShares", 0))
                trust_net = cls._parse_number(item.get("InvestmentTrustNetBuySellShares", 0))
                dealer_net = cls._parse_number(item.get("DealerNetBuySellShares", 0))
                total_net = foreign_net + trust_net + dealer_net

                result[stock_id] = {
                    "stock_id": stock_id,
                    "name": item.get("CompanyName", stock_id),
                    "foreign_net": int(foreign_net / 1000),  # 轉換為張
                    "trust_net": int(trust_net / 1000),
                    "dealer_net": int(dealer_net / 1000),
                    "total_net": int(total_net / 1000),
                    "source": "TPEx",
                }
            except:
                continue

        if result:
            cls._cache[cache_key] = result
            print(f"[TPEx] 取得 {len(result)} 檔上櫃法人資料")

        return result

    @classmethod
    async def get_otc_margin(cls) -> Dict[str, Dict]:
        """
        取得上櫃融資融券資料

        Returns:
            Dict[stock_id, {margin_balance, margin_change, short_balance, short_change}]
        """
        cache_key = "otc_margin"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        url = f"{cls.BASE_URL}/tpex_mainboard_margin"
        data = await cls._rate_limited_request(url)

        if not data:
            return {}

        result = {}
        for item in data:
            try:
                stock_id = item.get("SecuritiesCompanyCode", "")
                if not stock_id or not stock_id.isdigit():
                    continue

                margin_buy = cls._parse_number(item.get("MarginPurchaseShares", 0))
                margin_sell = cls._parse_number(item.get("MarginSaleShares", 0))
                margin_balance = cls._parse_number(item.get("MarginBalanceShares", 0))

                short_sell = cls._parse_number(item.get("ShortSaleShares", 0))
                short_cover = cls._parse_number(item.get("ShortCoveringShares", 0))
                short_balance = cls._parse_number(item.get("ShortBalanceShares", 0))

                result[stock_id] = {
                    "stock_id": stock_id,
                    "margin_balance": int(margin_balance / 1000),  # 轉換為張
                    "margin_change": int((margin_buy - margin_sell) / 1000),
                    "short_balance": int(short_balance / 1000),
                    "short_change": int((short_sell - short_cover) / 1000),
                    "source": "TPEx",
                }
            except:
                continue

        if result:
            cls._cache[cache_key] = result
            print(f"[TPEx] 取得 {len(result)} 檔上櫃融資融券資料")

        return result

    @classmethod
    async def get_all_otc_data(cls) -> Dict[str, Dict]:
        """
        取得所有上櫃股票整合資料

        Returns:
            Dict[stock_id, {完整股票資料}]
        """
        # 並行取得所有資料
        summary_task = cls.get_otc_stock_summary()
        pe_task = cls.get_otc_pe_ratio()
        inst_task = cls.get_otc_institutional()
        margin_task = cls.get_otc_margin()

        summary, pe_data, inst_data, margin_data = await asyncio.gather(
            summary_task, pe_task, inst_task, margin_task
        )

        # 整合資料
        result = {}
        for stock_id, data in summary.items():
            merged = {**data}

            # 合併本益比資料
            if stock_id in pe_data:
                merged.update({
                    "pe_ratio": pe_data[stock_id].get("pe_ratio"),
                    "pb_ratio": pe_data[stock_id].get("pb_ratio"),
                    "dividend_yield": pe_data[stock_id].get("dividend_yield"),
                })

            # 合併法人資料
            if stock_id in inst_data:
                merged.update({
                    "foreign_net": inst_data[stock_id].get("foreign_net"),
                    "trust_net": inst_data[stock_id].get("trust_net"),
                    "dealer_net": inst_data[stock_id].get("dealer_net"),
                    "total_net": inst_data[stock_id].get("total_net"),
                })

            # 合併融資融券資料
            if stock_id in margin_data:
                merged.update({
                    "margin_balance": margin_data[stock_id].get("margin_balance"),
                    "short_balance": margin_data[stock_id].get("short_balance"),
                })

            result[stock_id] = merged

        print(f"[TPEx] 整合完成: {len(result)} 檔上櫃股票")
        return result

    @classmethod
    def is_otc_stock(cls, stock_id: str) -> bool:
        """
        判斷是否為上櫃股票

        上櫃股票代號通常為 4 碼數字，開頭為 3, 4, 5, 6, 8
        """
        if not stock_id or not stock_id.isdigit():
            return False
        if len(stock_id) != 4:
            return False
        first_digit = stock_id[0]
        return first_digit in ['3', '4', '5', '6', '8']

    @classmethod
    def _parse_number(cls, value: Any) -> float:
        """解析數字（處理各種格式）"""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # 移除逗號和空白
            value = value.replace(",", "").replace(" ", "").strip()
            if value == "" or value == "-" or value == "--":
                return 0
            try:
                return float(value)
            except:
                return 0
        return 0

    @classmethod
    def clear_cache(cls):
        """清除所有快取"""
        cls._cache.clear()
        cls._daily_cache.clear()
        print("[TPEx] 快取已清除")


# 便捷函數
async def get_otc_stocks():
    """取得所有上櫃股票資料"""
    return await TPExOpenAPI.get_all_otc_data()

async def get_otc_institutional():
    """取得上櫃法人資料"""
    return await TPExOpenAPI.get_otc_institutional()

def is_otc_stock(stock_id: str) -> bool:
    """判斷是否為上櫃股票"""
    return TPExOpenAPI.is_otc_stock(stock_id)
