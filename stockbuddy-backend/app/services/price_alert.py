"""
StockBuddy V10.19 - 價格警示服務
提供股票價格警示功能，當股價達到設定目標時發出通知

V1.0 功能：
- 設定價格警示（突破/跌破）
- 檢查警示觸發狀態
- 警示歷史記錄
- 支援多種警示類型
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json

from app.services.cache_service import SmartTTL
from app.services.twse_openapi import TWSEOpenAPI


class AlertType(str, Enum):
    """警示類型"""
    ABOVE = "above"          # 股價突破
    BELOW = "below"          # 股價跌破
    PERCENT_UP = "percent_up"    # 漲幅達到
    PERCENT_DOWN = "percent_down"  # 跌幅達到


class AlertStatus(str, Enum):
    """警示狀態"""
    ACTIVE = "active"        # 活躍中
    TRIGGERED = "triggered"  # 已觸發
    EXPIRED = "expired"      # 已過期
    CANCELED = "canceled"    # 已取消


class PriceAlertService:
    """
    價格警示服務

    注意：此為前端快取版本，警示資料儲存在 localStorage
    後端主要負責提供即時價格檢查功能
    """

    # 快取
    _cache = {}
    _cache_time = {}

    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            ttl = SmartTTL.get_ttl("realtime")
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()

    @classmethod
    async def check_alerts(
        cls,
        alerts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        檢查多個警示的觸發狀態

        Args:
            alerts: 警示列表，每個警示包含:
                - stock_id: 股票代號
                - alert_type: 警示類型
                - target_price: 目標價格（price 類型）
                - target_percent: 目標百分比（percent 類型）
                - base_price: 基準價格（percent 類型用）

        Returns:
            {
                "checked_count": 檢查的警示數量,
                "triggered": [已觸發的警示],
                "results": [所有警示的檢查結果]
            }
        """
        if not alerts:
            return {
                "checked_count": 0,
                "triggered": [],
                "results": [],
            }

        # 收集需要查詢的股票
        stock_ids = list(set(a.get("stock_id") for a in alerts if a.get("stock_id")))

        # 批次取得股票即時價格
        prices = {}
        try:
            all_stocks = await TWSEOpenAPI.get_all_stocks_summary()
            for stock_id in stock_ids:
                if stock_id in all_stocks:
                    prices[stock_id] = all_stocks[stock_id].get("price")
        except Exception as e:
            print(f"取得即時價格失敗: {e}")
            # 嘗試單獨取得
            for stock_id in stock_ids:
                try:
                    info = await TWSEOpenAPI.get_stock_info(stock_id)
                    if info:
                        prices[stock_id] = info.get("price")
                except:
                    pass

        # 檢查每個警示
        results = []
        triggered = []

        for alert in alerts:
            stock_id = alert.get("stock_id")
            alert_type = alert.get("alert_type")
            target_price = alert.get("target_price")
            target_percent = alert.get("target_percent")
            base_price = alert.get("base_price")

            current_price = prices.get(stock_id)

            result = {
                "alert_id": alert.get("id"),
                "stock_id": stock_id,
                "alert_type": alert_type,
                "current_price": current_price,
                "target_price": target_price,
                "target_percent": target_percent,
                "is_triggered": False,
                "message": None,
            }

            if current_price is None:
                result["message"] = "無法取得即時價格"
                results.append(result)
                continue

            # 檢查觸發條件
            is_triggered = False
            message = None

            if alert_type == AlertType.ABOVE.value:
                if target_price and current_price >= target_price:
                    is_triggered = True
                    message = f"{stock_id} 股價 ${current_price} 已突破 ${target_price}"

            elif alert_type == AlertType.BELOW.value:
                if target_price and current_price <= target_price:
                    is_triggered = True
                    message = f"{stock_id} 股價 ${current_price} 已跌破 ${target_price}"

            elif alert_type == AlertType.PERCENT_UP.value:
                if target_percent and base_price:
                    change_pct = ((current_price - base_price) / base_price) * 100
                    if change_pct >= target_percent:
                        is_triggered = True
                        message = f"{stock_id} 漲幅 {change_pct:.2f}% 已達 {target_percent}%"

            elif alert_type == AlertType.PERCENT_DOWN.value:
                if target_percent and base_price:
                    change_pct = ((base_price - current_price) / base_price) * 100
                    if change_pct >= target_percent:
                        is_triggered = True
                        message = f"{stock_id} 跌幅 {change_pct:.2f}% 已達 {target_percent}%"

            result["is_triggered"] = is_triggered
            result["message"] = message
            results.append(result)

            if is_triggered:
                triggered.append(result)

        return {
            "checked_count": len(alerts),
            "triggered_count": len(triggered),
            "triggered": triggered,
            "results": results,
            "checked_at": datetime.now().isoformat(),
        }

    @classmethod
    async def get_current_price(cls, stock_id: str) -> Dict[str, Any]:
        """
        取得股票即時價格

        Returns:
            {
                "stock_id": 股票代號,
                "price": 即時價格,
                "change": 漲跌,
                "change_percent": 漲跌幅
            }
        """
        cache_key = f"price_{stock_id}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached

        try:
            info = await TWSEOpenAPI.get_stock_info(stock_id)

            if not info:
                return {"stock_id": stock_id, "error": "無法取得價格"}

            result = {
                "stock_id": stock_id,
                "name": info.get("name"),
                "price": info.get("price"),
                "change": info.get("change"),
                "change_percent": info.get("change_percent"),
                "open": info.get("open"),
                "high": info.get("high"),
                "low": info.get("low"),
                "volume": info.get("volume"),
                "timestamp": datetime.now().isoformat(),
            }

            cls._set_cache(cache_key, result)
            return result

        except Exception as e:
            return {"stock_id": stock_id, "error": str(e)}

    @classmethod
    async def get_batch_prices(cls, stock_ids: List[str]) -> Dict[str, Any]:
        """
        批次取得多檔股票即時價格

        Returns:
            {
                "prices": {stock_id: price_info},
                "count": 數量
            }
        """
        prices = {}

        try:
            all_stocks = await TWSEOpenAPI.get_all_stocks_summary()

            for stock_id in stock_ids:
                if stock_id in all_stocks:
                    data = all_stocks[stock_id]
                    prices[stock_id] = {
                        "stock_id": stock_id,
                        "name": data.get("name"),
                        "price": data.get("price"),
                        "change": data.get("change"),
                        "change_percent": data.get("change_percent"),
                    }
                else:
                    prices[stock_id] = {"stock_id": stock_id, "error": "找不到股票"}

        except Exception as e:
            print(f"批次取得價格失敗: {e}")
            # Fallback: 個別取得
            for stock_id in stock_ids:
                prices[stock_id] = await cls.get_current_price(stock_id)

        return {
            "prices": prices,
            "count": len(prices),
            "timestamp": datetime.now().isoformat(),
        }

    @classmethod
    def get_alert_types(cls) -> List[Dict[str, str]]:
        """取得所有警示類型"""
        return [
            {
                "type": AlertType.ABOVE.value,
                "label": "突破價格",
                "description": "當股價上漲到目標價位時通知",
                "icon": "📈",
            },
            {
                "type": AlertType.BELOW.value,
                "label": "跌破價格",
                "description": "當股價下跌到目標價位時通知",
                "icon": "📉",
            },
            {
                "type": AlertType.PERCENT_UP.value,
                "label": "漲幅達標",
                "description": "當漲幅達到目標百分比時通知",
                "icon": "🚀",
            },
            {
                "type": AlertType.PERCENT_DOWN.value,
                "label": "跌幅達標",
                "description": "當跌幅達到目標百分比時通知",
                "icon": "⚠️",
            },
        ]


# 便捷函數
async def check_alerts(alerts: List[Dict]):
    return await PriceAlertService.check_alerts(alerts)

async def get_current_price(stock_id: str):
    return await PriceAlertService.get_current_price(stock_id)

async def get_batch_prices(stock_ids: List[str]):
    return await PriceAlertService.get_batch_prices(stock_ids)

def get_alert_types():
    return PriceAlertService.get_alert_types()
