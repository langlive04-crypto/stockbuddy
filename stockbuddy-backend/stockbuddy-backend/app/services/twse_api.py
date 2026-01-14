"""
台灣證交所 (TWSE) API 串接服務
提供台股即時/歷史資料
"""

import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from cachetools import TTLCache
import asyncio

# 快取設定（避免頻繁請求被擋）
_cache = TTLCache(maxsize=100, ttl=300)  # 5分鐘快取


class TWSEService:
    """台灣證交所資料服務"""
    
    BASE_URL = "https://www.twse.com.tw"
    
    # 常用股票對照表
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
    }

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            }
        )

    async def close(self):
        await self.client.aclose()

    async def get_stock_info(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """
        取得個股即時/盤後資訊
        """
        cache_key = f"stock_info_{stock_id}"
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            # 取得當日行情
            today = datetime.now().strftime("%Y%m%d")
            url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY"
            params = {
                "response": "json",
                "date": today,
                "stockNo": stock_id,
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("stat") != "OK" or not data.get("data"):
                # 嘗試取得前一個交易日
                return await self._get_latest_stock_data(stock_id)
            
            # 取最後一筆（最新）
            latest = data["data"][-1]
            
            result = {
                "stock_id": stock_id,
                "name": self.POPULAR_STOCKS.get(stock_id, data.get("title", "").split()[1] if data.get("title") else stock_id),
                "date": latest[0],  # 日期
                "volume": self._parse_number(latest[1]),  # 成交股數
                "turnover": self._parse_number(latest[2]),  # 成交金額
                "open": self._parse_float(latest[3]),  # 開盤價
                "high": self._parse_float(latest[4]),  # 最高價
                "low": self._parse_float(latest[5]),  # 最低價
                "close": self._parse_float(latest[6]),  # 收盤價
                "change": self._parse_float(latest[7]),  # 漲跌價差
                "transactions": self._parse_number(latest[8]),  # 成交筆數
            }
            
            # 計算漲跌幅
            if result["close"] and result["change"]:
                prev_close = result["close"] - result["change"]
                if prev_close > 0:
                    result["change_percent"] = round((result["change"] / prev_close) * 100, 2)
                else:
                    result["change_percent"] = 0
            else:
                result["change_percent"] = 0

            _cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching stock info for {stock_id}: {e}")
            return None

    async def _get_latest_stock_data(self, stock_id: str) -> Optional[Dict[str, Any]]:
        """取得最近交易日資料（往回找）"""
        for days_back in range(1, 10):
            try:
                date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
                url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY"
                params = {"response": "json", "date": date, "stockNo": stock_id}
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if data.get("stat") == "OK" and data.get("data"):
                    latest = data["data"][-1]
                    return {
                        "stock_id": stock_id,
                        "name": self.POPULAR_STOCKS.get(stock_id, stock_id),
                        "date": latest[0],
                        "volume": self._parse_number(latest[1]),
                        "turnover": self._parse_number(latest[2]),
                        "open": self._parse_float(latest[3]),
                        "high": self._parse_float(latest[4]),
                        "low": self._parse_float(latest[5]),
                        "close": self._parse_float(latest[6]),
                        "change": self._parse_float(latest[7]),
                        "change_percent": 0,
                        "transactions": self._parse_number(latest[8]),
                    }
            except:
                continue
        return None

    async def get_stock_history(self, stock_id: str, months: int = 3) -> List[Dict[str, Any]]:
        """
        取得個股歷史K線資料
        """
        cache_key = f"stock_history_{stock_id}_{months}"
        if cache_key in _cache:
            return _cache[cache_key]

        all_data = []
        current_date = datetime.now()

        for i in range(months):
            target_date = current_date - timedelta(days=30 * i)
            date_str = target_date.strftime("%Y%m%d")
            
            try:
                url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY"
                params = {"response": "json", "date": date_str, "stockNo": stock_id}
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if data.get("stat") == "OK" and data.get("data"):
                    for row in data["data"]:
                        all_data.append({
                            "date": row[0],
                            "volume": self._parse_number(row[1]),
                            "turnover": self._parse_number(row[2]),
                            "open": self._parse_float(row[3]),
                            "high": self._parse_float(row[4]),
                            "low": self._parse_float(row[5]),
                            "close": self._parse_float(row[6]),
                            "change": self._parse_float(row[7]),
                            "transactions": self._parse_number(row[8]),
                        })
                
                # 避免請求過快
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error fetching history for {stock_id} at {date_str}: {e}")
                continue

        # 去重並排序
        seen_dates = set()
        unique_data = []
        for item in all_data:
            if item["date"] not in seen_dates:
                seen_dates.add(item["date"])
                unique_data.append(item)
        
        unique_data.sort(key=lambda x: x["date"])
        
        _cache[cache_key] = unique_data
        return unique_data

    async def get_institutional_investors(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        取得三大法人買賣超資料
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        
        cache_key = f"institutional_{date}"
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            url = f"{self.BASE_URL}/fund/T86"
            params = {
                "response": "json",
                "date": date,
                "selectType": "ALLBUT0999",  # 全部（不含權證等）
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("stat") != "OK" or not data.get("data"):
                # 嘗試前一天
                yesterday = (datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
                params["date"] = yesterday
                response = await self.client.get(url, params=params)
                data = response.json()
            
            if data.get("stat") != "OK" or not data.get("data"):
                return []

            results = []
            for row in data["data"]:
                stock_id = row[0].strip()
                if not stock_id.isdigit():
                    continue
                    
                results.append({
                    "stock_id": stock_id,
                    "name": row[1].strip(),
                    "foreign_buy": self._parse_number(row[2]),  # 外資買
                    "foreign_sell": self._parse_number(row[3]),  # 外資賣
                    "foreign_net": self._parse_number(row[4]),  # 外資淨買賣
                    "investment_buy": self._parse_number(row[5]),  # 投信買
                    "investment_sell": self._parse_number(row[6]),  # 投信賣
                    "investment_net": self._parse_number(row[7]),  # 投信淨買賣
                    "dealer_net": self._parse_number(row[8]),  # 自營商淨買賣
                    "total_net": self._parse_number(row[-1]),  # 三大法人合計
                })
            
            _cache[cache_key] = results
            return results

        except Exception as e:
            print(f"Error fetching institutional data: {e}")
            return []

    async def get_market_summary(self) -> Optional[Dict[str, Any]]:
        """
        取得大盤指數資訊
        """
        cache_key = "market_summary"
        if cache_key in _cache:
            return _cache[cache_key]

        try:
            today = datetime.now().strftime("%Y%m%d")
            url = f"{self.BASE_URL}/exchangeReport/MI_INDEX"
            params = {"response": "json", "date": today}
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data.get("stat") != "OK":
                return None

            # 找到加權指數
            taiex = None
            if "data8" in data:  # 大盤統計資訊
                for row in data["data8"]:
                    if "加權" in row[0]:
                        taiex = {
                            "name": row[0],
                            "value": self._parse_float(row[1].replace(",", "")),
                            "change": self._parse_float(row[2].replace(",", "")),
                        }
                        break

            # 取得成交資訊
            volume_data = None
            if "data5" in data:
                for row in data["data5"]:
                    if "成交金額" in str(row):
                        volume_data = row
                        break

            result = {
                "date": today,
                "taiex": taiex,
                "volume": volume_data,
            }
            
            _cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching market summary: {e}")
            return None

    @staticmethod
    def _parse_number(value: str) -> int:
        """解析數字字串（移除逗號）"""
        try:
            return int(str(value).replace(",", "").replace("--", "0"))
        except:
            return 0

    @staticmethod
    def _parse_float(value: str) -> float:
        """解析浮點數字串"""
        try:
            cleaned = str(value).replace(",", "").replace("--", "0").replace("X", "")
            if cleaned.startswith("+"):
                cleaned = cleaned[1:]
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0


# 單例模式
_twse_service: Optional[TWSEService] = None

async def get_twse_service() -> TWSEService:
    global _twse_service
    if _twse_service is None:
        _twse_service = TWSEService()
    return _twse_service
