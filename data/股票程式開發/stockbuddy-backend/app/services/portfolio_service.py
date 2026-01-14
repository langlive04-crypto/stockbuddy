# ============================================================
# 📊 StockBuddy - 投資組合服務
# ============================================================

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf

class PortfolioService:
    """投資組合管理服務"""
    
    # 本地儲存路徑（簡單的 JSON 檔案儲存）
    PORTFOLIO_FILE = "portfolio_data.json"
    
    @classmethod
    def _load_portfolio(cls) -> Dict:
        """載入投資組合資料"""
        if os.path.exists(cls.PORTFOLIO_FILE):
            try:
                with open(cls.PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"holdings": [], "transactions": []}
    
    @classmethod
    def _save_portfolio(cls, data: Dict):
        """儲存投資組合資料"""
        with open(cls.PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_current_price(cls, stock_id: str) -> Optional[float]:
        """取得即時股價"""
        try:
            ticker = yf.Ticker(f"{stock_id}.TW")
            info = ticker.info
            return info.get('regularMarketPrice') or info.get('currentPrice')
        except:
            return None
    
    @classmethod
    async def add_holding(
        cls,
        stock_id: str,
        stock_name: str,
        buy_price: float,
        quantity: int,
        buy_date: str = None,
        note: str = ""
    ) -> Dict:
        """
        新增持股
        
        Args:
            stock_id: 股票代號
            stock_name: 股票名稱
            buy_price: 買入價格
            quantity: 股數
            buy_date: 買入日期 (YYYY-MM-DD)
            note: 備註
        """
        portfolio = cls._load_portfolio()
        
        if not buy_date:
            buy_date = datetime.now().strftime("%Y-%m-%d")
        
        holding = {
            "id": f"{stock_id}_{datetime.now().timestamp()}",
            "stock_id": stock_id,
            "stock_name": stock_name,
            "buy_price": buy_price,
            "quantity": quantity,
            "buy_date": buy_date,
            "note": note,
            "created_at": datetime.now().isoformat()
        }
        
        portfolio["holdings"].append(holding)
        
        # 記錄交易
        portfolio["transactions"].append({
            "type": "BUY",
            "stock_id": stock_id,
            "stock_name": stock_name,
            "price": buy_price,
            "quantity": quantity,
            "date": buy_date,
            "timestamp": datetime.now().isoformat()
        })
        
        cls._save_portfolio(portfolio)
        
        return {"success": True, "holding": holding}
    
    @classmethod
    async def get_holdings(cls) -> List[Dict]:
        """取得所有持股，並計算即時損益"""
        portfolio = cls._load_portfolio()
        holdings = portfolio.get("holdings", [])
        
        result = []
        for holding in holdings:
            stock_id = holding["stock_id"]
            current_price = cls.get_current_price(stock_id)
            
            buy_price = holding["buy_price"]
            quantity = holding["quantity"]
            
            if current_price:
                # 計算損益
                cost = buy_price * quantity
                market_value = current_price * quantity
                profit = market_value - cost
                profit_percent = ((current_price - buy_price) / buy_price) * 100
            else:
                cost = buy_price * quantity
                market_value = None
                profit = None
                profit_percent = None
            
            result.append({
                **holding,
                "current_price": current_price,
                "cost": cost,
                "market_value": market_value,
                "profit": profit,
                "profit_percent": profit_percent
            })
        
        return result
    
    @classmethod
    async def update_holding(
        cls,
        holding_id: str,
        buy_price: float = None,
        quantity: int = None,
        note: str = None
    ) -> Dict:
        """更新持股資訊"""
        portfolio = cls._load_portfolio()
        
        for holding in portfolio["holdings"]:
            if holding["id"] == holding_id:
                if buy_price is not None:
                    holding["buy_price"] = buy_price
                if quantity is not None:
                    holding["quantity"] = quantity
                if note is not None:
                    holding["note"] = note
                holding["updated_at"] = datetime.now().isoformat()
                cls._save_portfolio(portfolio)
                return {"success": True, "holding": holding}
        
        return {"success": False, "error": "找不到該持股"}
    
    @classmethod
    async def delete_holding(cls, holding_id: str) -> Dict:
        """刪除持股"""
        portfolio = cls._load_portfolio()
        
        for i, holding in enumerate(portfolio["holdings"]):
            if holding["id"] == holding_id:
                deleted = portfolio["holdings"].pop(i)
                
                # 記錄交易
                portfolio["transactions"].append({
                    "type": "SELL",
                    "stock_id": deleted["stock_id"],
                    "stock_name": deleted["stock_name"],
                    "price": deleted["buy_price"],  # 實際應該用賣出價
                    "quantity": deleted["quantity"],
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().isoformat()
                })
                
                cls._save_portfolio(portfolio)
                return {"success": True, "deleted": deleted}
        
        return {"success": False, "error": "找不到該持股"}
    
    @classmethod
    async def get_summary(cls) -> Dict:
        """取得投資組合總覽"""
        holdings = await cls.get_holdings()
        
        if not holdings:
            return {
                "total_holdings": 0,
                "total_cost": 0,
                "total_market_value": 0,
                "total_profit": 0,
                "total_profit_percent": 0,
                "holdings_count": 0,
                "profitable_count": 0,
                "loss_count": 0
            }
        
        total_cost = sum(h["cost"] for h in holdings if h["cost"])
        total_market_value = sum(h["market_value"] for h in holdings if h["market_value"])
        
        profitable = [h for h in holdings if h["profit"] and h["profit"] > 0]
        loss = [h for h in holdings if h["profit"] and h["profit"] < 0]
        
        total_profit = total_market_value - total_cost if total_market_value else 0
        profit_percent = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_holdings": len(holdings),
            "total_cost": round(total_cost, 2),
            "total_market_value": round(total_market_value, 2) if total_market_value else None,
            "total_profit": round(total_profit, 2),
            "total_profit_percent": round(profit_percent, 2),
            "holdings_count": len(holdings),
            "profitable_count": len(profitable),
            "loss_count": len(loss),
            "win_rate": round(len(profitable) / len(holdings) * 100, 1) if holdings else 0
        }
    
    @classmethod
    async def get_transactions(cls, limit: int = 20) -> List[Dict]:
        """取得交易紀錄"""
        portfolio = cls._load_portfolio()
        transactions = portfolio.get("transactions", [])
        # 按時間倒序
        transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return transactions[:limit]
    
    @classmethod
    async def sell_holding(
        cls,
        holding_id: str,
        sell_price: float,
        sell_quantity: int = None
    ) -> Dict:
        """賣出持股"""
        portfolio = cls._load_portfolio()
        
        for i, holding in enumerate(portfolio["holdings"]):
            if holding["id"] == holding_id:
                if sell_quantity is None or sell_quantity >= holding["quantity"]:
                    # 全部賣出
                    deleted = portfolio["holdings"].pop(i)
                    actual_quantity = holding["quantity"]
                else:
                    # 部分賣出
                    holding["quantity"] -= sell_quantity
                    actual_quantity = sell_quantity
                    deleted = None
                
                # 記錄交易
                profit = (sell_price - holding["buy_price"]) * actual_quantity
                portfolio["transactions"].append({
                    "type": "SELL",
                    "stock_id": holding["stock_id"],
                    "stock_name": holding["stock_name"],
                    "buy_price": holding["buy_price"],
                    "sell_price": sell_price,
                    "quantity": actual_quantity,
                    "profit": profit,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().isoformat()
                })
                
                cls._save_portfolio(portfolio)
                return {
                    "success": True,
                    "sold_quantity": actual_quantity,
                    "profit": profit,
                    "remaining": None if deleted else holding
                }
        
        return {"success": False, "error": "找不到該持股"}


# 股票名稱對照（常用股票）
STOCK_NAMES = {
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "2881": "富邦金",
    "2882": "國泰金",
    "2891": "中信金",
    "2303": "聯電",
    "2412": "中華電",
    "2886": "兆豐金",
    "1301": "台塑",
    "2002": "中鋼",
    "3008": "大立光",
    "2382": "廣達",
    "2357": "華碩",
    "2609": "陽明",
    "2615": "萬海",
    "2603": "長榮",
    "3711": "日月光投控",
    "2327": "國巨",
    # 可以繼續擴充...
}

def get_stock_name(stock_id: str) -> str:
    """取得股票名稱"""
    return STOCK_NAMES.get(stock_id, stock_id)
