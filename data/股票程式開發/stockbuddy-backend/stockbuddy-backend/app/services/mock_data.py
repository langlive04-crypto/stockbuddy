"""
Mock 股票資料服務
用於開發測試和展示，不依賴外部 API
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import random
import math


class MockStockDataService:
    """Mock 股票資料服務（開發展示用）"""
    
    # 台股常用股票
    STOCKS_DATA = {
        "2330": {"name": "台積電", "base_price": 580, "volatility": 0.02},
        "2317": {"name": "鴻海", "base_price": 168, "volatility": 0.025},
        "2454": {"name": "聯發科", "base_price": 720, "volatility": 0.03},
        "2308": {"name": "台達電", "base_price": 380, "volatility": 0.02},
        "2881": {"name": "富邦金", "base_price": 85, "volatility": 0.015},
        "2882": {"name": "國泰金", "base_price": 62, "volatility": 0.015},
        "2303": {"name": "聯電", "base_price": 52, "volatility": 0.025},
        "2412": {"name": "中華電", "base_price": 125, "volatility": 0.01},
        "2891": {"name": "中信金", "base_price": 32, "volatility": 0.015},
        "2886": {"name": "兆豐金", "base_price": 42, "volatility": 0.012},
        "1301": {"name": "台塑", "base_price": 95, "volatility": 0.018},
        "2002": {"name": "中鋼", "base_price": 26, "volatility": 0.02},
        "2603": {"name": "長榮", "base_price": 178, "volatility": 0.035},
        "3037": {"name": "欣興", "base_price": 168, "volatility": 0.03},
        "2382": {"name": "廣達", "base_price": 285, "volatility": 0.025},
    }

    @classmethod
    def _generate_price_series(cls, base_price: float, volatility: float, days: int) -> List[Dict]:
        """生成模擬價格序列"""
        prices = []
        current_price = base_price * (1 + random.uniform(-0.1, 0.1))  # 起始有些變化
        
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            
            # 跳過週末
            if date.weekday() >= 5:
                continue
            
            # 隨機波動
            change_pct = random.gauss(0.001, volatility)  # 微小正向偏移
            current_price = current_price * (1 + change_pct)
            
            # 計算當日 OHLC
            daily_range = current_price * volatility * 0.5
            open_price = current_price * (1 + random.uniform(-0.005, 0.005))
            high = max(open_price, current_price) + random.uniform(0, daily_range)
            low = min(open_price, current_price) - random.uniform(0, daily_range)
            close = current_price
            
            # 成交量（隨機但合理）
            base_volume = 50000000  # 5000萬股基礎
            volume = int(base_volume * random.uniform(0.5, 2.0))
            
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
                "change": round(close - open_price, 2),
            })
        
        return prices

    @classmethod
    async def get_stock_info(cls, stock_id: str) -> Optional[Dict[str, Any]]:
        """取得個股即時資訊"""
        if stock_id not in cls.STOCKS_DATA:
            return None
        
        stock = cls.STOCKS_DATA[stock_id]
        base = stock["base_price"]
        vol = stock["volatility"]
        
        # 模擬當前價格
        price = base * (1 + random.uniform(-0.05, 0.08))
        change = price * random.uniform(-vol, vol)
        change_pct = (change / (price - change)) * 100
        
        return {
            "stock_id": stock_id,
            "name": stock["name"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "open": round(price - random.uniform(-2, 2), 2),
            "high": round(price + abs(random.uniform(0, price * 0.02)), 2),
            "low": round(price - abs(random.uniform(0, price * 0.02)), 2),
            "close": round(price, 2),
            "volume": random.randint(30000000, 100000000),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
        }

    @classmethod
    async def get_stock_history(cls, stock_id: str, months: int = 3) -> List[Dict[str, Any]]:
        """取得個股歷史K線資料"""
        if stock_id not in cls.STOCKS_DATA:
            return []
        
        stock = cls.STOCKS_DATA[stock_id]
        days = months * 30
        
        return cls._generate_price_series(stock["base_price"], stock["volatility"], days)

    @classmethod
    async def get_market_index(cls) -> Dict[str, Any]:
        """取得大盤指數"""
        base_index = 23000
        change = random.uniform(-200, 250)
        value = base_index + change
        
        return {
            "name": "加權指數",
            "symbol": "^TWII",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "value": round(value, 2),
            "change": round(change, 2),
            "change_percent": round((change / base_index) * 100, 2),
            "volume": random.randint(3000, 5000) * 100000000,  # 億
        }

    @classmethod
    async def get_institutional_data(cls, stock_id: str) -> Dict[str, Any]:
        """取得三大法人買賣超"""
        foreign = random.randint(-15000, 20000)
        investment = random.randint(-3000, 5000)
        dealer = random.randint(-2000, 2000)
        
        return {
            "stock_id": stock_id,
            "foreign_net": foreign,
            "investment_net": investment,
            "dealer_net": dealer,
            "total_net": foreign + investment + dealer,
        }

    @classmethod
    async def get_multiple_stocks(cls, stock_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """批次取得多檔股票"""
        results = {}
        for sid in stock_ids:
            info = await cls.get_stock_info(sid)
            if info:
                results[sid] = info
        return results

    @classmethod
    async def search_stock(cls, query: str) -> List[Dict[str, Any]]:
        """搜尋股票"""
        results = []
        for stock_id, data in cls.STOCKS_DATA.items():
            if query.lower() in stock_id.lower() or query in data["name"]:
                results.append({
                    "stock_id": stock_id,
                    "name": data["name"],
                })
        return results


# 給外部使用的介面 - 可切換 Mock 或真實服務
USE_MOCK = True  # 設為 False 使用真實 API

if USE_MOCK:
    StockDataService = MockStockDataService
else:
    from .stock_data import StockDataService as RealStockDataService
    StockDataService = RealStockDataService
