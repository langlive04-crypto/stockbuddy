"""
投資組合 / 自選股服務
- 使用本地儲存（JSON 檔案）
- 未來可擴展為資料庫
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class WatchlistService:
    """自選股服務"""
    
    # 儲存路徑
    DATA_FILE = "watchlist.json"
    
    def __init__(self):
        self._data = self._load_data()
    
    def _load_data(self) -> Dict:
        """載入資料"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"watchlist": [], "portfolios": []}
    
    def _save_data(self):
        """儲存資料"""
        with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
    
    # ===== 自選股 =====
    
    def get_watchlist(self) -> List[Dict]:
        """取得自選股清單"""
        return self._data.get("watchlist", [])
    
    def add_to_watchlist(self, stock_id: str, name: str = "", note: str = "") -> Dict:
        """加入自選股"""
        # 檢查是否已存在
        existing = [s for s in self._data["watchlist"] if s["stock_id"] == stock_id]
        if existing:
            return {"success": False, "message": "股票已在自選清單中"}
        
        item = {
            "stock_id": stock_id,
            "name": name,
            "note": note,
            "added_at": datetime.now().isoformat(),
        }
        self._data["watchlist"].append(item)
        self._save_data()
        
        return {"success": True, "message": "已加入自選股", "item": item}
    
    def remove_from_watchlist(self, stock_id: str) -> Dict:
        """移除自選股"""
        original_len = len(self._data["watchlist"])
        self._data["watchlist"] = [s for s in self._data["watchlist"] if s["stock_id"] != stock_id]
        
        if len(self._data["watchlist"]) < original_len:
            self._save_data()
            return {"success": True, "message": "已從自選股移除"}
        else:
            return {"success": False, "message": "找不到該股票"}
    
    def update_watchlist_note(self, stock_id: str, note: str) -> Dict:
        """更新自選股備註"""
        for item in self._data["watchlist"]:
            if item["stock_id"] == stock_id:
                item["note"] = note
                self._save_data()
                return {"success": True, "message": "已更新備註"}
        
        return {"success": False, "message": "找不到該股票"}
    
    def is_in_watchlist(self, stock_id: str) -> bool:
        """檢查是否在自選股中"""
        return any(s["stock_id"] == stock_id for s in self._data["watchlist"])
    
    # ===== 投資組合 =====
    
    def get_portfolios(self) -> List[Dict]:
        """取得投資組合清單"""
        return self._data.get("portfolios", [])
    
    def add_portfolio(self, name: str) -> Dict:
        """新增投資組合"""
        portfolio = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "name": name,
            "stocks": [],
            "created_at": datetime.now().isoformat(),
        }
        self._data.setdefault("portfolios", []).append(portfolio)
        self._save_data()
        
        return {"success": True, "portfolio": portfolio}
    
    def add_stock_to_portfolio(self, portfolio_id: str, stock_id: str, 
                                shares: int = 0, cost: float = 0) -> Dict:
        """將股票加入投資組合"""
        for portfolio in self._data.get("portfolios", []):
            if portfolio["id"] == portfolio_id:
                # 檢查是否已存在
                existing = [s for s in portfolio["stocks"] if s["stock_id"] == stock_id]
                if existing:
                    return {"success": False, "message": "股票已在組合中"}
                
                portfolio["stocks"].append({
                    "stock_id": stock_id,
                    "shares": shares,
                    "cost": cost,
                    "added_at": datetime.now().isoformat(),
                })
                self._save_data()
                return {"success": True, "message": "已加入組合"}
        
        return {"success": False, "message": "找不到該組合"}
    
    def remove_stock_from_portfolio(self, portfolio_id: str, stock_id: str) -> Dict:
        """從投資組合移除股票"""
        for portfolio in self._data.get("portfolios", []):
            if portfolio["id"] == portfolio_id:
                original_len = len(portfolio["stocks"])
                portfolio["stocks"] = [s for s in portfolio["stocks"] if s["stock_id"] != stock_id]
                
                if len(portfolio["stocks"]) < original_len:
                    self._save_data()
                    return {"success": True, "message": "已從組合移除"}
                else:
                    return {"success": False, "message": "找不到該股票"}
        
        return {"success": False, "message": "找不到該組合"}


# 單例
_watchlist_service = None

def get_watchlist_service() -> WatchlistService:
    global _watchlist_service
    if _watchlist_service is None:
        _watchlist_service = WatchlistService()
    return _watchlist_service
