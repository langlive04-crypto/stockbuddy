"""
基本面分析服務
- 本益比 (P/E)
- 股價淨值比 (P/B)
- 市值
- 股息殖利率
- 營收資料
"""

import yfinance as yf
from typing import Dict, Optional, Any
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
        return int(val)
    except:
        return None


class FundamentalService:
    """基本面分析服務"""
    
    @classmethod
    async def get_fundamental_data(cls, stock_id: str) -> Dict[str, Any]:
        """
        取得個股基本面資料
        
        Returns:
            {
                "pe_ratio": 本益比,
                "pb_ratio": 股價淨值比,
                "market_cap": 市值,
                "dividend_yield": 股息殖利率,
                "revenue_growth": 營收成長率,
                "profit_margin": 淨利率,
                "gross_margin": 毛利率,
                "debt_ratio": 負債比,
                "eps": 每股盈餘,
                "roe": 股東權益報酬率,
                ...
            }
        """
        try:
            ticker = yf.Ticker(f"{stock_id}.TW")
            info = ticker.info
            
            if not info or info.get("regularMarketPrice") is None:
                # 嘗試 .TWO (上櫃)
                ticker = yf.Ticker(f"{stock_id}.TWO")
                info = ticker.info
            
            if not info:
                return cls._empty_fundamental()
            
            # 提取基本面資料
            result = {
                # 估值指標
                "pe_ratio": safe_float(info.get("trailingPE") or info.get("forwardPE")),
                "pb_ratio": safe_float(info.get("priceToBook")),
                "ps_ratio": safe_float(info.get("priceToSalesTrailing12Months")),
                "peg_ratio": safe_float(info.get("pegRatio")),
                
                # 市值相關
                "market_cap": safe_int(info.get("marketCap")),
                "market_cap_display": cls._format_market_cap(info.get("marketCap")),
                "enterprise_value": safe_int(info.get("enterpriseValue")),
                
                # 股息
                "dividend_yield": safe_float(info.get("dividendYield")),
                "dividend_yield_percent": cls._to_percent(info.get("dividendYield")),
                "dividend_rate": safe_float(info.get("dividendRate")),
                "payout_ratio": cls._to_percent(info.get("payoutRatio")),
                
                # 獲利能力
                "profit_margin": cls._to_percent(info.get("profitMargins")),
                "gross_margin": cls._to_percent(info.get("grossMargins")),
                "operating_margin": cls._to_percent(info.get("operatingMargins")),
                "ebitda_margin": cls._to_percent(info.get("ebitdaMargins")),
                
                # 成長性
                "revenue_growth": cls._to_percent(info.get("revenueGrowth")),
                "earnings_growth": cls._to_percent(info.get("earningsGrowth")),
                "earnings_quarterly_growth": cls._to_percent(info.get("earningsQuarterlyGrowth")),
                
                # 每股數據
                "eps": safe_float(info.get("trailingEps")),
                "eps_forward": safe_float(info.get("forwardEps")),
                "book_value": safe_float(info.get("bookValue")),
                "revenue_per_share": safe_float(info.get("revenuePerShare")),
                
                # 財務健康
                "debt_to_equity": safe_float(info.get("debtToEquity")),
                "current_ratio": safe_float(info.get("currentRatio")),
                "quick_ratio": safe_float(info.get("quickRatio")),
                "total_debt": safe_int(info.get("totalDebt")),
                "total_cash": safe_int(info.get("totalCash")),
                
                # 報酬率
                "roe": cls._to_percent(info.get("returnOnEquity")),
                "roa": cls._to_percent(info.get("returnOnAssets")),
                
                # 其他
                "beta": safe_float(info.get("beta")),
                "52_week_high": safe_float(info.get("fiftyTwoWeekHigh")),
                "52_week_low": safe_float(info.get("fiftyTwoWeekLow")),
                "50_day_avg": safe_float(info.get("fiftyDayAverage")),
                "200_day_avg": safe_float(info.get("twoHundredDayAverage")),
                
                # 目標價
                "target_high": safe_float(info.get("targetHighPrice")),
                "target_low": safe_float(info.get("targetLowPrice")),
                "target_mean": safe_float(info.get("targetMeanPrice")),
                "recommendation": info.get("recommendationKey"),
                
                # 公司資訊
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "employees": safe_int(info.get("fullTimeEmployees")),
            }
            
            # 計算評估
            result["valuation_comment"] = cls._get_valuation_comment(result)
            result["growth_comment"] = cls._get_growth_comment(result)
            result["health_comment"] = cls._get_health_comment(result)
            
            return result
            
        except Exception as e:
            print(f"取得基本面資料失敗 {stock_id}: {e}")
            return cls._empty_fundamental()
    
    @classmethod
    def _to_percent(cls, val) -> Optional[float]:
        """轉換為百分比"""
        if val is None:
            return None
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return None
            return round(f * 100, 2)
        except:
            return None
    
    @classmethod
    def _format_market_cap(cls, val) -> str:
        """格式化市值"""
        if val is None:
            return "N/A"
        try:
            v = float(val)
            if v >= 1e12:
                return f"{v/1e12:.1f}兆"
            elif v >= 1e8:
                return f"{v/1e8:.0f}億"
            elif v >= 1e4:
                return f"{v/1e4:.0f}萬"
            else:
                return str(int(v))
        except:
            return "N/A"
    
    @classmethod
    def _get_valuation_comment(cls, data: Dict) -> str:
        """估值評論"""
        pe = data.get("pe_ratio")
        pb = data.get("pb_ratio")
        
        if pe is None and pb is None:
            return "資料不足"
        
        comments = []
        
        if pe is not None:
            if pe < 0:
                comments.append("虧損中")
            elif pe < 10:
                comments.append("本益比偏低")
            elif pe < 20:
                comments.append("本益比合理")
            elif pe < 30:
                comments.append("本益比偏高")
            else:
                comments.append("本益比過高")
        
        if pb is not None:
            if pb < 1:
                comments.append("股價低於淨值")
            elif pb < 2:
                comments.append("淨值比合理")
            else:
                comments.append("淨值比偏高")
        
        return "，".join(comments) if comments else "中性"
    
    @classmethod
    def _get_growth_comment(cls, data: Dict) -> str:
        """成長性評論"""
        rev_growth = data.get("revenue_growth")
        earn_growth = data.get("earnings_growth")
        
        if rev_growth is None and earn_growth is None:
            return "資料不足"
        
        growth = rev_growth or earn_growth or 0
        
        if growth > 30:
            return "高速成長"
        elif growth > 10:
            return "穩定成長"
        elif growth > 0:
            return "緩步成長"
        elif growth > -10:
            return "小幅衰退"
        else:
            return "衰退中"
    
    @classmethod
    def _get_health_comment(cls, data: Dict) -> str:
        """財務健康評論"""
        debt_equity = data.get("debt_to_equity")
        current = data.get("current_ratio")
        
        if debt_equity is None and current is None:
            return "資料不足"
        
        comments = []
        
        if debt_equity is not None:
            if debt_equity < 50:
                comments.append("負債低")
            elif debt_equity < 100:
                comments.append("負債適中")
            else:
                comments.append("負債偏高")
        
        if current is not None:
            if current > 2:
                comments.append("流動性佳")
            elif current > 1:
                comments.append("流動性適中")
            else:
                comments.append("流動性緊張")
        
        return "，".join(comments) if comments else "中性"
    
    @classmethod
    def _empty_fundamental(cls) -> Dict:
        """空的基本面資料"""
        return {
            "pe_ratio": None,
            "pb_ratio": None,
            "market_cap": None,
            "market_cap_display": "N/A",
            "dividend_yield_percent": None,
            "profit_margin": None,
            "gross_margin": None,
            "revenue_growth": None,
            "eps": None,
            "roe": None,
            "debt_to_equity": None,
            "valuation_comment": "資料不足",
            "growth_comment": "資料不足",
            "health_comment": "資料不足",
        }
