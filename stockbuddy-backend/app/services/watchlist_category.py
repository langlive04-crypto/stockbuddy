"""
StockBuddy V10.21 - 自選股分類群組服務
提供自選股分類管理功能

V1.0 功能：
- 建立/編輯/刪除分類群組
- 股票加入/移除群組
- 群組統計分析
- 預設分類模板
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class CategoryColor(str, Enum):
    """分類顏色"""
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    TEAL = "teal"
    BLUE = "blue"
    INDIGO = "indigo"
    PURPLE = "purple"
    PINK = "pink"
    GRAY = "gray"


# 預設分類模板
DEFAULT_CATEGORIES = [
    {
        "id": "dividend",
        "name": "存股標的",
        "description": "長期持有、穩定配息的股票",
        "color": CategoryColor.GREEN.value,
        "icon": "💰",
    },
    {
        "id": "growth",
        "name": "成長觀察",
        "description": "具成長潛力的觀察標的",
        "color": CategoryColor.BLUE.value,
        "icon": "📈",
    },
    {
        "id": "short_term",
        "name": "短線操作",
        "description": "短期交易標的",
        "color": CategoryColor.ORANGE.value,
        "icon": "⚡",
    },
    {
        "id": "etf",
        "name": "ETF",
        "description": "指數股票型基金",
        "color": CategoryColor.TEAL.value,
        "icon": "🏦",
    },
    {
        "id": "pending",
        "name": "待研究",
        "description": "需要進一步研究的標的",
        "color": CategoryColor.GRAY.value,
        "icon": "🔍",
    },
]

# 顏色配置
COLOR_PALETTE = {
    CategoryColor.RED.value: {"bg": "#fef2f2", "border": "#fecaca", "text": "#ef4444"},
    CategoryColor.ORANGE.value: {"bg": "#fff7ed", "border": "#fed7aa", "text": "#f97316"},
    CategoryColor.YELLOW.value: {"bg": "#fefce8", "border": "#fef08a", "text": "#eab308"},
    CategoryColor.GREEN.value: {"bg": "#f0fdf4", "border": "#bbf7d0", "text": "#22c55e"},
    CategoryColor.TEAL.value: {"bg": "#f0fdfa", "border": "#99f6e4", "text": "#14b8a6"},
    CategoryColor.BLUE.value: {"bg": "#eff6ff", "border": "#bfdbfe", "text": "#3b82f6"},
    CategoryColor.INDIGO.value: {"bg": "#eef2ff", "border": "#c7d2fe", "text": "#6366f1"},
    CategoryColor.PURPLE.value: {"bg": "#faf5ff", "border": "#e9d5ff", "text": "#a855f7"},
    CategoryColor.PINK.value: {"bg": "#fdf2f8", "border": "#fbcfe8", "text": "#ec4899"},
    CategoryColor.GRAY.value: {"bg": "#f9fafb", "border": "#e5e7eb", "text": "#6b7280"},
}


class WatchlistCategoryService:
    """
    自選股分類群組服務

    注意：此為前端快取版本，分類資料儲存在 localStorage
    後端主要負責提供分類模板和統計分析功能
    """

    @classmethod
    def get_default_categories(cls) -> List[Dict[str, Any]]:
        """取得預設分類模板"""
        return DEFAULT_CATEGORIES

    @classmethod
    def get_color_palette(cls) -> Dict[str, Dict[str, str]]:
        """取得顏色配置"""
        return COLOR_PALETTE

    @classmethod
    def get_available_colors(cls) -> List[Dict[str, Any]]:
        """取得可用顏色列表"""
        return [
            {
                "value": color.value,
                "label": {
                    "red": "紅色",
                    "orange": "橙色",
                    "yellow": "黃色",
                    "green": "綠色",
                    "teal": "青色",
                    "blue": "藍色",
                    "indigo": "靛色",
                    "purple": "紫色",
                    "pink": "粉色",
                    "gray": "灰色",
                }.get(color.value, color.value),
                **COLOR_PALETTE.get(color.value, {}),
            }
            for color in CategoryColor
        ]

    @classmethod
    def get_available_icons(cls) -> List[Dict[str, str]]:
        """取得可用圖示列表"""
        return [
            {"value": "💰", "label": "錢袋"},
            {"value": "📈", "label": "上漲"},
            {"value": "📉", "label": "下跌"},
            {"value": "⚡", "label": "閃電"},
            {"value": "🏦", "label": "銀行"},
            {"value": "🔍", "label": "搜尋"},
            {"value": "⭐", "label": "星星"},
            {"value": "🎯", "label": "目標"},
            {"value": "🚀", "label": "火箭"},
            {"value": "💎", "label": "鑽石"},
            {"value": "🔥", "label": "火焰"},
            {"value": "💡", "label": "燈泡"},
            {"value": "🏠", "label": "房子"},
            {"value": "🚗", "label": "汽車"},
            {"value": "📱", "label": "手機"},
            {"value": "💻", "label": "電腦"},
        ]

    @classmethod
    def validate_category(cls, category: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證分類資料

        Args:
            category: 分類資料

        Returns:
            {
                "valid": 是否有效,
                "errors": 錯誤訊息列表
            }
        """
        errors = []

        # 檢查必填欄位
        if not category.get("name"):
            errors.append("分類名稱為必填")

        if len(category.get("name", "")) > 20:
            errors.append("分類名稱不得超過 20 字")

        if len(category.get("description", "")) > 100:
            errors.append("描述不得超過 100 字")

        # 檢查顏色是否有效
        color = category.get("color")
        if color and color not in [c.value for c in CategoryColor]:
            errors.append(f"無效的顏色: {color}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @classmethod
    def analyze_categories(
        cls,
        categories: List[Dict[str, Any]],
        stocks_by_category: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        分析分類統計

        Args:
            categories: 分類列表
            stocks_by_category: 各分類的股票列表 {category_id: [stocks]}

        Returns:
            {
                "total_categories": 分類數量,
                "total_stocks": 股票總數,
                "category_stats": 各分類統計,
                "distribution": 分佈統計
            }
        """
        total_stocks = 0
        category_stats = []

        for cat in categories:
            cat_id = cat.get("id")
            stocks = stocks_by_category.get(cat_id, [])
            stock_count = len(stocks)
            total_stocks += stock_count

            category_stats.append({
                "id": cat_id,
                "name": cat.get("name"),
                "color": cat.get("color"),
                "icon": cat.get("icon"),
                "stock_count": stock_count,
                "stocks": [s.get("stock_id") for s in stocks[:5]],  # 只取前 5 檔
            })

        # 計算分佈
        distribution = []
        for stat in category_stats:
            if total_stocks > 0:
                percentage = (stat["stock_count"] / total_stocks) * 100
            else:
                percentage = 0
            distribution.append({
                "name": stat["name"],
                "count": stat["stock_count"],
                "percentage": round(percentage, 1),
                "color": stat["color"],
            })

        return {
            "total_categories": len(categories),
            "total_stocks": total_stocks,
            "category_stats": category_stats,
            "distribution": distribution,
        }

    @classmethod
    def suggest_category(cls, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據股票資訊建議分類

        Args:
            stock_info: 股票資訊（含殖利率、PE、技術分數等）

        Returns:
            {
                "suggested_category": 建議分類 ID,
                "reason": 建議原因
            }
        """
        dividend_yield = stock_info.get("dividend_yield", 0)
        pe_ratio = stock_info.get("pe_ratio", 0)
        technical_score = stock_info.get("technical_score", 0)
        stock_id = stock_info.get("stock_id", "")

        # ETF 判斷
        if stock_id.startswith("00"):
            return {
                "suggested_category": "etf",
                "reason": "股票代號以 00 開頭，判斷為 ETF",
            }

        # 高殖利率 → 存股標的
        if dividend_yield and dividend_yield >= 4:
            return {
                "suggested_category": "dividend",
                "reason": f"殖利率 {dividend_yield}% 達存股標準",
            }

        # 高技術分數 → 短線操作
        if technical_score and technical_score >= 75:
            return {
                "suggested_category": "short_term",
                "reason": f"技術分數 {technical_score} 具短線機會",
            }

        # 低 PE + 成長性 → 成長觀察
        if pe_ratio and pe_ratio <= 15:
            return {
                "suggested_category": "growth",
                "reason": f"PE {pe_ratio} 估值合理，具成長潛力",
            }

        # 預設 → 待研究
        return {
            "suggested_category": "pending",
            "reason": "需進一步分析後再分類",
        }


# 便捷函數
def get_default_categories():
    return WatchlistCategoryService.get_default_categories()


def get_color_palette():
    return WatchlistCategoryService.get_color_palette()


def get_available_colors():
    return WatchlistCategoryService.get_available_colors()


def get_available_icons():
    return WatchlistCategoryService.get_available_icons()


def validate_category(category: Dict):
    return WatchlistCategoryService.validate_category(category)


def analyze_categories(categories: List[Dict], stocks_by_category: Dict):
    return WatchlistCategoryService.analyze_categories(categories, stocks_by_category)


def suggest_category(stock_info: Dict):
    return WatchlistCategoryService.suggest_category(stock_info)
