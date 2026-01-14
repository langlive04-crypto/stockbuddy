"""
籌碼面分析服務
- 三大法人買賣超
- 融資融券
- 大戶持股比例
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import math


def safe_float(val) -> Optional[float]:
    """安全轉換為 float"""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 2)
    except:
        return None


def safe_int(val) -> Optional[int]:
    """安全轉換為 int"""
    if val is None:
        return None
    try:
        return int(float(val))
    except:
        return None


class InstitutionalService:
    """籌碼面分析服務 - 三大法人買賣超"""
    
    BASE_URL = "https://www.twse.com.tw"
    
    # 快取
    _cache = {}
    _cache_time = {}
    CACHE_DURATION = 600  # 10 分鐘
    
    @classmethod
    async def get_institutional_data(cls, stock_id: str) -> Dict[str, Any]:
        """
        取得三大法人買賣超資料
        
        Returns:
            {
                "foreign": {"buy": 買張, "sell": 賣張, "net": 買賣超},
                "investment_trust": {"buy": 買張, "sell": 賣張, "net": 買賣超},
                "dealer": {"buy": 買張, "sell": 賣張, "net": 買賣超},
                "total_net": 合計買賣超,
                "comment": 籌碼面評論,
                "trend": "買超" / "賣超" / "中性"
            }
        """
        cache_key = f"inst_{stock_id}"
        
        # 檢查快取
        if cache_key in cls._cache:
            if datetime.now().timestamp() - cls._cache_time.get(cache_key, 0) < cls.CACHE_DURATION:
                return cls._cache[cache_key]
        
        try:
            # 嘗試從 TWSE 取得資料
            data = await cls._fetch_from_twse(stock_id)
            if data:
                cls._cache[cache_key] = data
                cls._cache_time[cache_key] = datetime.now().timestamp()
                return data
        except Exception as e:
            print(f"取得籌碼資料失敗 {stock_id}: {e}")
        
        # 返回模擬資料（基於股票特性）
        return cls._generate_simulated_data(stock_id)
    
    @classmethod
    async def _fetch_from_twse(cls, stock_id: str) -> Optional[Dict]:
        """從 TWSE 取得三大法人買賣超"""
        try:
            # 取得最近交易日
            for days_back in range(5):
                target_date = datetime.now() - timedelta(days=days_back)
                if target_date.weekday() >= 5:  # 跳過週末
                    continue
                    
                date_str = target_date.strftime("%Y%m%d")
                
                # TWSE 三大法人買賣超 API
                url = f"{cls.BASE_URL}/fund/T86?response=json&date={date_str}&selectType=ALLBUT0999"
                
                async with httpx.AsyncClient(timeout=10, verify=False) as client:
                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept-Language": "zh-TW"
                    })
                    
                    if response.status_code != 200:
                        continue
                    
                    data = response.json()
                    
                    if "data" not in data:
                        continue
                    
                    # 找到指定股票
                    for row in data["data"]:
                        if row[0].strip() == stock_id:
                            return cls._parse_twse_row(row)
                
        except Exception as e:
            print(f"TWSE 籌碼 API 錯誤: {e}")
        
        return None
    
    @classmethod
    def _parse_twse_row(cls, row: List) -> Dict:
        """解析 TWSE 資料列"""
        try:
            # TWSE T86 格式：
            # 0: 證券代號, 1: 證券名稱, 2: 外資買, 3: 外資賣, 4: 外資買賣超,
            # 5: 投信買, 6: 投信賣, 7: 投信買賣超, 8: 自營商買, 9: 自營商賣, 10: 自營商買賣超
            # 11: 合計買賣超
            
            def parse_num(val):
                if isinstance(val, str):
                    return int(val.replace(",", "").replace(" ", ""))
                return int(val)
            
            foreign_buy = parse_num(row[2])
            foreign_sell = parse_num(row[3])
            foreign_net = parse_num(row[4])
            
            trust_buy = parse_num(row[5])
            trust_sell = parse_num(row[6])
            trust_net = parse_num(row[7])
            
            dealer_buy = parse_num(row[8]) if len(row) > 8 else 0
            dealer_sell = parse_num(row[9]) if len(row) > 9 else 0
            dealer_net = parse_num(row[10]) if len(row) > 10 else 0
            
            total_net = foreign_net + trust_net + dealer_net
            
            # 評論
            comment = cls._generate_comment(foreign_net, trust_net, dealer_net)
            trend = "買超" if total_net > 0 else "賣超" if total_net < 0 else "中性"
            
            return {
                "foreign": {
                    "buy": foreign_buy,
                    "sell": foreign_sell,
                    "net": foreign_net,
                    "net_display": cls._format_shares(foreign_net),
                },
                "investment_trust": {
                    "buy": trust_buy,
                    "sell": trust_sell,
                    "net": trust_net,
                    "net_display": cls._format_shares(trust_net),
                },
                "dealer": {
                    "buy": dealer_buy,
                    "sell": dealer_sell,
                    "net": dealer_net,
                    "net_display": cls._format_shares(dealer_net),
                },
                "total_net": total_net,
                "total_net_display": cls._format_shares(total_net),
                "comment": comment,
                "trend": trend,
                "data_date": datetime.now().strftime("%Y-%m-%d"),
                "is_real_data": True,
            }
            
        except Exception as e:
            print(f"解析籌碼資料錯誤: {e}")
            return None
    
    @classmethod
    def _format_shares(cls, val: int) -> str:
        """格式化張數"""
        if val >= 0:
            return f"+{val:,} 張"
        else:
            return f"{val:,} 張"
    
    @classmethod
    def _generate_comment(cls, foreign: int, trust: int, dealer: int) -> str:
        """生成籌碼評論"""
        comments = []
        
        if foreign > 1000:
            comments.append("外資大買")
        elif foreign > 0:
            comments.append("外資買超")
        elif foreign < -1000:
            comments.append("外資大賣")
        elif foreign < 0:
            comments.append("外資賣超")
        
        if trust > 500:
            comments.append("投信加碼")
        elif trust < -500:
            comments.append("投信減碼")
        
        total = foreign + trust + dealer
        if total > 2000:
            return "法人積極買進，" + "、".join(comments[:2])
        elif total > 0:
            return "法人小幅買超，" + "、".join(comments[:2])
        elif total < -2000:
            return "法人積極賣出，" + "、".join(comments[:2])
        elif total < 0:
            return "法人小幅賣超，" + "、".join(comments[:2])
        else:
            return "法人觀望，籌碼中性"
    
    @classmethod
    def _generate_simulated_data(cls, stock_id: str) -> Dict:
        """生成模擬資料（當 API 失敗時）"""
        import random
        
        # 根據股票代號生成一致的隨機種子
        random.seed(hash(stock_id + datetime.now().strftime("%Y%m%d")))
        
        # 大型股傾向有外資買超
        is_large_cap = stock_id in ["2330", "2454", "2317", "2308", "2881", "2882"]
        
        if is_large_cap:
            foreign_net = random.randint(-2000, 5000)
            trust_net = random.randint(-500, 1500)
        else:
            foreign_net = random.randint(-1000, 1000)
            trust_net = random.randint(-300, 500)
        
        dealer_net = random.randint(-500, 500)
        total_net = foreign_net + trust_net + dealer_net
        
        comment = cls._generate_comment(foreign_net, trust_net, dealer_net)
        trend = "買超" if total_net > 0 else "賣超" if total_net < 0 else "中性"
        
        return {
            "foreign": {
                "buy": abs(foreign_net) + random.randint(100, 500) if foreign_net >= 0 else random.randint(100, 500),
                "sell": random.randint(100, 500) if foreign_net >= 0 else abs(foreign_net) + random.randint(100, 500),
                "net": foreign_net,
                "net_display": cls._format_shares(foreign_net),
            },
            "investment_trust": {
                "buy": abs(trust_net) + random.randint(50, 200) if trust_net >= 0 else random.randint(50, 200),
                "sell": random.randint(50, 200) if trust_net >= 0 else abs(trust_net) + random.randint(50, 200),
                "net": trust_net,
                "net_display": cls._format_shares(trust_net),
            },
            "dealer": {
                "buy": abs(dealer_net) + random.randint(20, 100) if dealer_net >= 0 else random.randint(20, 100),
                "sell": random.randint(20, 100) if dealer_net >= 0 else abs(dealer_net) + random.randint(20, 100),
                "net": dealer_net,
                "net_display": cls._format_shares(dealer_net),
            },
            "total_net": total_net,
            "total_net_display": cls._format_shares(total_net),
            "comment": comment,
            "trend": trend,
            "data_date": datetime.now().strftime("%Y-%m-%d"),
            "is_real_data": False,  # 標記為模擬資料
        }


class MarginService:
    """融資融券服務"""
    
    @classmethod
    async def get_margin_data(cls, stock_id: str) -> Dict[str, Any]:
        """取得融資融券資料"""
        # TODO: 實作真實 API 串接
        # 目前返回模擬資料
        import random
        random.seed(hash(stock_id))
        
        margin_buy = random.randint(1000, 10000)
        margin_sell = random.randint(1000, 10000)
        margin_balance = random.randint(50000, 200000)
        
        short_buy = random.randint(100, 2000)
        short_sell = random.randint(100, 2000)
        short_balance = random.randint(5000, 50000)
        
        # 券資比
        margin_short_ratio = round(short_balance / margin_balance * 100, 2) if margin_balance > 0 else 0
        
        return {
            "margin": {
                "buy": margin_buy,
                "sell": margin_sell,
                "balance": margin_balance,
                "change": margin_buy - margin_sell,
            },
            "short": {
                "buy": short_buy,
                "sell": short_sell,
                "balance": short_balance,
                "change": short_sell - short_buy,
            },
            "margin_short_ratio": margin_short_ratio,
            "comment": cls._get_margin_comment(margin_short_ratio),
            "is_real_data": False,
        }
    
    @classmethod
    def _get_margin_comment(cls, ratio: float) -> str:
        """融資融券評論"""
        if ratio > 30:
            return "券資比偏高，空方壓力大"
        elif ratio > 20:
            return "券資比適中"
        elif ratio > 10:
            return "融資偏多，多方信心強"
        else:
            return "融資主導，看多氣氛濃"
