"""
StockBuddy V10.20 - 交易記錄與持股分析服務
提供完整的交易記錄管理與持股損益分析功能

V1.0 功能：
- 交易記錄（買入/賣出）
- 持股計算（平均成本法）
- 損益分析
- 股息記錄
- 持股報表
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
import json

from app.services.cache_service import SmartTTL
from app.services.twse_openapi import TWSEOpenAPI


class TransactionType(str, Enum):
    """交易類型"""
    BUY = "buy"           # 買入
    SELL = "sell"         # 賣出
    DIVIDEND = "dividend" # 股息


class TransactionService:
    """
    交易記錄與持股分析服務

    注意：此為前端快取版本，交易資料儲存在 localStorage
    後端主要負責提供計算與分析功能
    """

    # 快取
    _cache = {}
    _cache_time = {}

    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            ttl = SmartTTL.get_ttl("analysis")
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()

    @classmethod
    def calculate_holdings(
        cls,
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        計算持股狀況（使用平均成本法）

        Args:
            transactions: 交易記錄列表，每筆包含:
                - stock_id: 股票代號
                - type: 交易類型 (buy/sell/dividend)
                - shares: 股數
                - price: 成交價
                - fee: 手續費（可選）
                - tax: 交易稅（可選，賣出時）
                - date: 交易日期
                - note: 備註（可選）

        Returns:
            {
                "holdings": {stock_id: 持股資訊},
                "summary": 總覽資訊,
                "transactions_count": 交易筆數
            }
        """
        if not transactions:
            return {
                "holdings": {},
                "summary": {
                    "total_stocks": 0,
                    "total_cost": 0,
                    "total_market_value": 0,
                    "total_profit_loss": 0,
                    "total_profit_loss_percent": 0,
                    "total_dividends": 0,
                },
                "transactions_count": 0,
            }

        # 按股票分組計算
        holdings = {}
        dividends_by_stock = {}

        for tx in sorted(transactions, key=lambda x: x.get("date", "")):
            stock_id = tx.get("stock_id")
            tx_type = tx.get("type")
            shares = float(tx.get("shares", 0))
            price = float(tx.get("price", 0))
            fee = float(tx.get("fee", 0))
            tax = float(tx.get("tax", 0))

            if stock_id not in holdings:
                holdings[stock_id] = {
                    "stock_id": stock_id,
                    "name": tx.get("name", stock_id),
                    "shares": 0,
                    "avg_cost": 0,
                    "total_cost": 0,
                    "realized_profit": 0,
                    "total_fee": 0,
                    "total_tax": 0,
                    "buy_count": 0,
                    "sell_count": 0,
                }

            holding = holdings[stock_id]

            if tx_type == TransactionType.BUY.value:
                # 買入：更新平均成本
                new_shares = holding["shares"] + shares
                new_cost = holding["total_cost"] + (shares * price) + fee

                if new_shares > 0:
                    holding["avg_cost"] = new_cost / new_shares
                else:
                    holding["avg_cost"] = 0

                holding["shares"] = new_shares
                holding["total_cost"] = new_cost
                holding["total_fee"] += fee
                holding["buy_count"] += 1

            elif tx_type == TransactionType.SELL.value:
                # 賣出：計算已實現損益
                if holding["shares"] >= shares:
                    sell_value = shares * price - fee - tax
                    cost_basis = shares * holding["avg_cost"]
                    realized = sell_value - cost_basis

                    holding["shares"] -= shares
                    holding["total_cost"] = holding["shares"] * holding["avg_cost"]
                    holding["realized_profit"] += realized
                    holding["total_fee"] += fee
                    holding["total_tax"] += tax
                    holding["sell_count"] += 1

            elif tx_type == TransactionType.DIVIDEND.value:
                # 股息
                if stock_id not in dividends_by_stock:
                    dividends_by_stock[stock_id] = 0
                dividends_by_stock[stock_id] += shares * price  # shares = 股利張數, price = 每股股利

        # 計算總覽
        total_cost = 0
        total_dividends = 0
        stocks_held = 0

        for stock_id, holding in holdings.items():
            if holding["shares"] > 0:
                total_cost += holding["total_cost"]
                stocks_held += 1
            holding["dividends"] = dividends_by_stock.get(stock_id, 0)
            total_dividends += holding["dividends"]

        return {
            "holdings": holdings,
            "summary": {
                "total_stocks": stocks_held,
                "total_cost": round(total_cost, 2),
                "total_dividends": round(total_dividends, 2),
            },
            "transactions_count": len(transactions),
            "calculated_at": datetime.now().isoformat(),
        }

    @classmethod
    async def analyze_holdings(
        cls,
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        分析持股損益（含即時市值）

        Returns:
            {
                "holdings": [持股詳細資訊],
                "summary": 投組總覽,
                "performance": 績效指標
            }
        """
        # 先計算基礎持股
        calc_result = cls.calculate_holdings(transactions)
        holdings = calc_result["holdings"]

        if not holdings:
            return {
                "holdings": [],
                "summary": calc_result["summary"],
                "performance": {
                    "total_return": 0,
                    "total_return_percent": 0,
                    "best_performer": None,
                    "worst_performer": None,
                },
            }

        # 取得即時價格
        stock_ids = [sid for sid, h in holdings.items() if h["shares"] > 0]
        prices = {}

        try:
            all_stocks = await TWSEOpenAPI.get_all_stocks_summary()
            for stock_id in stock_ids:
                if stock_id in all_stocks:
                    prices[stock_id] = all_stocks[stock_id].get("price")
        except Exception as e:
            print(f"取得即時價格失敗: {e}")
            # Fallback: 個別取得
            for stock_id in stock_ids:
                try:
                    info = await TWSEOpenAPI.get_stock_info(stock_id)
                    if info:
                        prices[stock_id] = info.get("price")
                except:
                    pass

        # 計算損益
        holdings_list = []
        total_market_value = 0
        total_cost = 0
        total_unrealized = 0
        total_realized = 0
        best = None
        worst = None

        for stock_id, holding in holdings.items():
            if holding["shares"] <= 0:
                continue

            current_price = prices.get(stock_id)
            market_value = 0
            unrealized_profit = 0
            unrealized_percent = 0

            if current_price:
                market_value = holding["shares"] * current_price
                unrealized_profit = market_value - holding["total_cost"]
                if holding["total_cost"] > 0:
                    unrealized_percent = (unrealized_profit / holding["total_cost"]) * 100

            holding_info = {
                "stock_id": stock_id,
                "name": holding["name"],
                "shares": holding["shares"],
                "avg_cost": round(holding["avg_cost"], 2),
                "current_price": current_price,
                "total_cost": round(holding["total_cost"], 2),
                "market_value": round(market_value, 2),
                "unrealized_profit": round(unrealized_profit, 2),
                "unrealized_percent": round(unrealized_percent, 2),
                "realized_profit": round(holding["realized_profit"], 2),
                "dividends": round(holding.get("dividends", 0), 2),
                "total_return": round(unrealized_profit + holding["realized_profit"] + holding.get("dividends", 0), 2),
                "total_fee": round(holding["total_fee"], 2),
                "total_tax": round(holding["total_tax"], 2),
            }

            holdings_list.append(holding_info)
            total_market_value += market_value
            total_cost += holding["total_cost"]
            total_unrealized += unrealized_profit
            total_realized += holding["realized_profit"]

            # 追蹤最佳/最差
            if current_price:
                if best is None or unrealized_percent > best["percent"]:
                    best = {"stock_id": stock_id, "name": holding["name"], "percent": unrealized_percent}
                if worst is None or unrealized_percent < worst["percent"]:
                    worst = {"stock_id": stock_id, "name": holding["name"], "percent": unrealized_percent}

        # 排序：按市值降序
        holdings_list.sort(key=lambda x: x["market_value"], reverse=True)

        # 計算總報酬率
        total_return = total_unrealized + total_realized + calc_result["summary"]["total_dividends"]
        total_return_percent = 0
        if total_cost > 0:
            total_return_percent = (total_return / total_cost) * 100

        return {
            "holdings": holdings_list,
            "summary": {
                "total_stocks": len(holdings_list),
                "total_cost": round(total_cost, 2),
                "total_market_value": round(total_market_value, 2),
                "unrealized_profit": round(total_unrealized, 2),
                "realized_profit": round(total_realized, 2),
                "total_dividends": round(calc_result["summary"]["total_dividends"], 2),
                "total_return": round(total_return, 2),
                "total_return_percent": round(total_return_percent, 2),
            },
            "performance": {
                "total_return": round(total_return, 2),
                "total_return_percent": round(total_return_percent, 2),
                "best_performer": best,
                "worst_performer": worst,
            },
            "analyzed_at": datetime.now().isoformat(),
        }

    @classmethod
    def calculate_transaction_summary(
        cls,
        transactions: List[Dict[str, Any]],
        stock_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        計算交易摘要

        Args:
            transactions: 交易記錄列表
            stock_id: 指定股票（可選）

        Returns:
            {
                "total_buy": 總買入金額,
                "total_sell": 總賣出金額,
                "total_fee": 總手續費,
                "total_tax": 總交易稅,
                "total_dividends": 總股息,
                "net_investment": 淨投資額,
                "transactions_by_month": 月度統計
            }
        """
        if stock_id:
            transactions = [t for t in transactions if t.get("stock_id") == stock_id]

        total_buy = 0
        total_sell = 0
        total_fee = 0
        total_tax = 0
        total_dividends = 0
        by_month = {}

        for tx in transactions:
            tx_type = tx.get("type")
            shares = float(tx.get("shares", 0))
            price = float(tx.get("price", 0))
            fee = float(tx.get("fee", 0))
            tax = float(tx.get("tax", 0))
            tx_date = tx.get("date", "")

            # 月度統計
            if tx_date:
                month_key = tx_date[:7]  # YYYY-MM
                if month_key not in by_month:
                    by_month[month_key] = {"buy": 0, "sell": 0, "dividends": 0}

            amount = shares * price

            if tx_type == TransactionType.BUY.value:
                total_buy += amount + fee
                total_fee += fee
                if tx_date:
                    by_month[month_key]["buy"] += amount

            elif tx_type == TransactionType.SELL.value:
                total_sell += amount - fee - tax
                total_fee += fee
                total_tax += tax
                if tx_date:
                    by_month[month_key]["sell"] += amount

            elif tx_type == TransactionType.DIVIDEND.value:
                total_dividends += amount
                if tx_date:
                    by_month[month_key]["dividends"] += amount

        return {
            "total_buy": round(total_buy, 2),
            "total_sell": round(total_sell, 2),
            "total_fee": round(total_fee, 2),
            "total_tax": round(total_tax, 2),
            "total_dividends": round(total_dividends, 2),
            "net_investment": round(total_buy - total_sell, 2),
            "transactions_by_month": dict(sorted(by_month.items(), reverse=True)),
            "transactions_count": len(transactions),
        }

    @classmethod
    def get_transaction_types(cls) -> List[Dict[str, str]]:
        """取得所有交易類型"""
        return [
            {
                "type": TransactionType.BUY.value,
                "label": "買入",
                "description": "購買股票",
                "icon": "📈",
            },
            {
                "type": TransactionType.SELL.value,
                "label": "賣出",
                "description": "賣出股票",
                "icon": "📉",
            },
            {
                "type": TransactionType.DIVIDEND.value,
                "label": "股息",
                "description": "收到現金股利",
                "icon": "💰",
            },
        ]

    @classmethod
    def calculate_fee_and_tax(
        cls,
        tx_type: str,
        shares: float,
        price: float,
        fee_rate: float = 0.001425,
        tax_rate: float = 0.003,
        fee_discount: float = 0.6,
    ) -> Dict[str, float]:
        """
        計算手續費與交易稅

        Args:
            tx_type: 交易類型
            shares: 股數
            price: 成交價
            fee_rate: 手續費率（預設 0.1425%）
            tax_rate: 證券交易稅率（預設 0.3%，賣出時）
            fee_discount: 手續費折扣（預設 6 折）

        Returns:
            {"fee": 手續費, "tax": 交易稅, "total_cost": 總成本}
        """
        amount = shares * price

        # 手續費（買賣皆有）
        fee = amount * fee_rate * fee_discount
        fee = max(fee, 20)  # 最低 20 元

        # 交易稅（僅賣出）
        tax = 0
        if tx_type == TransactionType.SELL.value:
            tax = amount * tax_rate

        return {
            "amount": round(amount, 2),
            "fee": round(fee, 2),
            "tax": round(tax, 2),
            "total_cost": round(amount + fee + tax if tx_type == TransactionType.BUY.value else amount - fee - tax, 2),
        }

    @classmethod
    async def get_dividend_history(
        cls,
        stock_id: str,
    ) -> Dict[str, Any]:
        """
        取得股票歷史股利資訊

        Returns:
            {
                "stock_id": 股票代號,
                "dividends": [歷年股利],
                "average_yield": 平均殖利率
            }
        """
        # 這裡可以整合實際的股利資料 API
        # 目前返回模擬資料結構
        return {
            "stock_id": stock_id,
            "dividends": [],
            "average_yield": 0,
            "message": "股利歷史資料需整合外部 API",
        }


# 便捷函數
def calculate_holdings(transactions: List[Dict]):
    return TransactionService.calculate_holdings(transactions)


async def analyze_holdings(transactions: List[Dict]):
    return await TransactionService.analyze_holdings(transactions)


def calculate_transaction_summary(transactions: List[Dict], stock_id: str = None):
    return TransactionService.calculate_transaction_summary(transactions, stock_id)


def get_transaction_types():
    return TransactionService.get_transaction_types()


def calculate_fee_and_tax(tx_type: str, shares: float, price: float):
    return TransactionService.calculate_fee_and_tax(tx_type, shares, price)
