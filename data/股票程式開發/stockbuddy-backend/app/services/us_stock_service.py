"""
美股資料服務 - US Stock Data Service
V10.24 新增

功能：
- 美股即時報價和歷史資料
- 支援主要美股指數（道瓊、S&P 500、納斯達克）
- 熱門美股對照表
- 美股技術分析
- 美股基本面資料
"""

import warnings
import logging

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

# 快取設定（美股快取時間較長，因為盤後不變）
_us_cache = TTLCache(maxsize=500, ttl=300)  # 5分鐘快取

# 執行緒池
_us_executor = ThreadPoolExecutor(max_workers=6)


class USStockService:
    """美股資料服務"""

    # 熱門美股對照表
    POPULAR_US_STOCKS = {
        # 科技巨頭
        "AAPL": "蘋果 Apple",
        "MSFT": "微軟 Microsoft",
        "GOOGL": "Google (Alphabet)",
        "AMZN": "亞馬遜 Amazon",
        "META": "Meta (Facebook)",
        "NVDA": "輝達 NVIDIA",
        "TSLA": "特斯拉 Tesla",
        "AMD": "超微 AMD",
        "INTC": "英特爾 Intel",
        "AVGO": "博通 Broadcom",
        # 半導體
        "TSM": "台積電 ADR",
        "ASML": "艾司摩爾 ASML",
        "QCOM": "高通 Qualcomm",
        "MU": "美光 Micron",
        "LRCX": "科林研發 Lam Research",
        # 金融
        "JPM": "摩根大通 JPMorgan",
        "BAC": "美國銀行 Bank of America",
        "WFC": "富國銀行 Wells Fargo",
        "GS": "高盛 Goldman Sachs",
        "MS": "摩根士丹利 Morgan Stanley",
        # 消費
        "WMT": "沃爾瑪 Walmart",
        "COST": "好市多 Costco",
        "HD": "家得寶 Home Depot",
        "NKE": "耐吉 Nike",
        "SBUX": "星巴克 Starbucks",
        # 醫療
        "JNJ": "嬌生 Johnson & Johnson",
        "UNH": "聯合健康 UnitedHealth",
        "PFE": "輝瑞 Pfizer",
        "ABBV": "艾伯維 AbbVie",
        "MRK": "默克 Merck",
        # 通訊
        "VZ": "威訊 Verizon",
        "T": "AT&T",
        "NFLX": "網飛 Netflix",
        "DIS": "迪士尼 Disney",
        "CMCSA": "康卡斯特 Comcast",
        # 能源
        "XOM": "艾克森美孚 Exxon Mobil",
        "CVX": "雪佛龍 Chevron",
        # AI 概念股
        "PLTR": "Palantir",
        "AI": "C3.ai",
        "SNOW": "Snowflake",
        "CRM": "Salesforce",
    }

    # 美股主要指數
    MARKET_INDICES = {
        "^DJI": "道瓊工業指數",
        "^GSPC": "S&P 500",
        "^IXIC": "納斯達克綜合指數",
        "^SOX": "費城半導體指數",
        "^VIX": "VIX 恐慌指數",
    }

    # 產業分類
    SECTORS = {
        "technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "AVGO"],
        "semiconductor": ["TSM", "NVDA", "AMD", "ASML", "QCOM", "MU", "LRCX", "INTC"],
        "finance": ["JPM", "BAC", "WFC", "GS", "MS"],
        "consumer": ["WMT", "COST", "HD", "NKE", "SBUX", "AMZN"],
        "healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
        "communication": ["VZ", "T", "NFLX", "DIS", "CMCSA", "GOOGL", "META"],
        "energy": ["XOM", "CVX"],
        "ai_concept": ["NVDA", "MSFT", "GOOGL", "PLTR", "AI", "SNOW", "CRM"],
    }

    @classmethod
    def is_market_open(cls) -> Dict[str, Any]:
        """
        檢查美股市場是否開盤
        美東時間 9:30 AM - 4:00 PM
        """
        from datetime import timezone
        import pytz

        try:
            et_tz = pytz.timezone('US/Eastern')
            now_et = datetime.now(et_tz)

            # 週末不開盤
            if now_et.weekday() >= 5:
                return {
                    "is_open": False,
                    "status": "weekend",
                    "message": "美股週末休市",
                    "local_time": now_et.strftime("%Y-%m-%d %H:%M:%S ET")
                }

            market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

            if market_open <= now_et <= market_close:
                return {
                    "is_open": True,
                    "status": "open",
                    "message": "美股交易中",
                    "local_time": now_et.strftime("%Y-%m-%d %H:%M:%S ET")
                }
            elif now_et < market_open:
                return {
                    "is_open": False,
                    "status": "pre_market",
                    "message": "美股盤前",
                    "local_time": now_et.strftime("%Y-%m-%d %H:%M:%S ET")
                }
            else:
                return {
                    "is_open": False,
                    "status": "after_hours",
                    "message": "美股盤後",
                    "local_time": now_et.strftime("%Y-%m-%d %H:%M:%S ET")
                }
        except Exception:
            return {
                "is_open": False,
                "status": "unknown",
                "message": "無法判斷市場狀態",
                "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    @classmethod
    async def get_stock_info(cls, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得美股即時資訊
        """
        symbol = symbol.upper()
        cache_key = f"us_stock_info_{symbol}"

        if cache_key in _us_cache:
            return _us_cache[cache_key]

        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(_us_executor, lambda: yf.Ticker(symbol))

            # 取得歷史資料
            hist = await loop.run_in_executor(
                _us_executor,
                lambda: ticker.history(period="5d")
            )

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest

            change = latest['Close'] - prev['Close']
            change_percent = (change / prev['Close'] * 100) if prev['Close'] > 0 else 0

            # 取得更多資訊
            info = await loop.run_in_executor(_us_executor, lambda: ticker.info)

            result = {
                "symbol": symbol,
                "stock_id": symbol,  # 相容台股介面
                "name": cls.POPULAR_US_STOCKS.get(symbol, info.get('shortName', symbol)),
                "name_en": info.get('shortName', symbol),
                "market": "US",
                "currency": "USD",
                "date": latest.name.strftime("%Y-%m-%d"),
                "open": round(latest['Open'], 2),
                "high": round(latest['High'], 2),
                "low": round(latest['Low'], 2),
                "close": round(latest['Close'], 2),
                "volume": int(latest['Volume']),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                # 額外資訊
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "dividend_yield": info.get('dividendYield'),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
                "avg_volume": info.get('averageVolume'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
            }

            _us_cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching US stock info for {symbol}: {e}")
            return None

    @classmethod
    async def get_stock_history(cls, symbol: str, months: int = 3) -> List[Dict[str, Any]]:
        """
        取得美股歷史K線資料
        """
        symbol = symbol.upper()
        cache_key = f"us_stock_history_{symbol}_{months}"

        if cache_key in _us_cache:
            return _us_cache[cache_key]

        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(_us_executor, lambda: yf.Ticker(symbol))

            period = f"{months}mo"
            hist = await loop.run_in_executor(
                _us_executor,
                lambda: ticker.history(period=period)
            )

            if hist.empty:
                return []

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

            _us_cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching US stock history for {symbol}: {e}")
            return []

    @classmethod
    async def get_market_indices(cls) -> Dict[str, Dict[str, Any]]:
        """
        取得美股主要指數
        """
        cache_key = "us_market_indices"

        if cache_key in _us_cache:
            return _us_cache[cache_key]

        results = {}

        try:
            loop = asyncio.get_event_loop()

            for index_symbol, index_name in cls.MARKET_INDICES.items():
                try:
                    ticker = await loop.run_in_executor(_us_executor, lambda s=index_symbol: yf.Ticker(s))
                    hist = await loop.run_in_executor(
                        _us_executor,
                        lambda t=ticker: t.history(period="5d")
                    )

                    if not hist.empty:
                        latest = hist.iloc[-1]
                        prev = hist.iloc[-2] if len(hist) > 1 else latest

                        change = latest['Close'] - prev['Close']
                        change_percent = (change / prev['Close'] * 100) if prev['Close'] > 0 else 0

                        results[index_symbol] = {
                            "symbol": index_symbol,
                            "name": index_name,
                            "value": round(latest['Close'], 2),
                            "change": round(change, 2),
                            "change_percent": round(change_percent, 2),
                            "date": latest.name.strftime("%Y-%m-%d"),
                        }
                except Exception as e:
                    print(f"Error fetching index {index_symbol}: {e}")
                    continue

            _us_cache[cache_key] = results
            return results

        except Exception as e:
            print(f"Error fetching market indices: {e}")
            return results

    @classmethod
    async def get_sector_stocks(cls, sector: str) -> List[Dict[str, Any]]:
        """
        取得特定產業的股票清單
        """
        sector = sector.lower()
        if sector not in cls.SECTORS:
            return []

        symbols = cls.SECTORS[sector]
        results = []

        for symbol in symbols:
            info = await cls.get_stock_info(symbol)
            if info:
                results.append(info)

        # 依漲跌幅排序
        results.sort(key=lambda x: x.get('change_percent', 0), reverse=True)
        return results

    @classmethod
    async def get_multiple_stocks(cls, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批次取得多檔美股資訊
        """
        results = {}

        tasks = [cls.get_stock_info(symbol) for symbol in symbols]
        infos = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, info in zip(symbols, infos):
            if isinstance(info, dict):
                results[symbol] = info

        return results

    @classmethod
    async def search_stock(cls, query: str) -> List[Dict[str, Any]]:
        """
        搜尋美股
        """
        query = query.upper()
        results = []

        for symbol, name in cls.POPULAR_US_STOCKS.items():
            if query in symbol or query.lower() in name.lower():
                results.append({
                    "symbol": symbol,
                    "stock_id": symbol,  # 相容性
                    "name": name,
                    "market": "US"
                })

        return results[:20]  # 限制結果數量

    @classmethod
    async def get_company_profile(cls, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得公司詳細資料
        """
        symbol = symbol.upper()
        cache_key = f"us_company_profile_{symbol}"

        if cache_key in _us_cache:
            return _us_cache[cache_key]

        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(_us_executor, lambda: yf.Ticker(symbol))
            info = await loop.run_in_executor(_us_executor, lambda: ticker.info)

            result = {
                "symbol": symbol,
                "name": info.get('shortName', symbol),
                "long_name": info.get('longName'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "country": info.get('country'),
                "website": info.get('website'),
                "description": info.get('longBusinessSummary'),
                "employees": info.get('fullTimeEmployees'),
                "market_cap": info.get('marketCap'),
                "enterprise_value": info.get('enterpriseValue'),
                # 財務指標
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "peg_ratio": info.get('pegRatio'),
                "price_to_book": info.get('priceToBook'),
                "price_to_sales": info.get('priceToSalesTrailing12Months'),
                "profit_margin": info.get('profitMargins'),
                "operating_margin": info.get('operatingMargins'),
                "roe": info.get('returnOnEquity'),
                "roa": info.get('returnOnAssets'),
                "revenue": info.get('totalRevenue'),
                "revenue_growth": info.get('revenueGrowth'),
                "earnings_growth": info.get('earningsGrowth'),
                "dividend_yield": info.get('dividendYield'),
                "dividend_rate": info.get('dividendRate'),
                "payout_ratio": info.get('payoutRatio'),
                "beta": info.get('beta'),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
                "fifty_day_average": info.get('fiftyDayAverage'),
                "two_hundred_day_average": info.get('twoHundredDayAverage'),
            }

            _us_cache[cache_key] = result
            return result

        except Exception as e:
            print(f"Error fetching company profile for {symbol}: {e}")
            return None

    @classmethod
    async def get_hot_stocks(cls) -> List[Dict[str, Any]]:
        """
        取得熱門美股（成交量較大的）
        """
        # 先取所有熱門股票資訊
        all_stocks = await cls.get_multiple_stocks(list(cls.POPULAR_US_STOCKS.keys())[:20])

        # 依成交量排序
        stocks_list = list(all_stocks.values())
        stocks_list.sort(key=lambda x: x.get('volume', 0), reverse=True)

        return stocks_list[:10]

    @classmethod
    async def get_top_movers(cls) -> Dict[str, List[Dict[str, Any]]]:
        """
        取得漲跌幅排行
        """
        all_stocks = await cls.get_multiple_stocks(list(cls.POPULAR_US_STOCKS.keys()))
        stocks_list = list(all_stocks.values())

        # 依漲跌幅排序
        sorted_by_change = sorted(stocks_list, key=lambda x: x.get('change_percent', 0), reverse=True)

        return {
            "gainers": sorted_by_change[:5],  # 漲幅前5
            "losers": sorted_by_change[-5:][::-1],  # 跌幅前5
        }


# 建立全域服務實例
us_stock_service = USStockService()
