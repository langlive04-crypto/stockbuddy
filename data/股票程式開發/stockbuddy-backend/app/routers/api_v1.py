"""
api_v1.py - API 版本 1 路由聚合
V10.38: API 版本控制

將所有 v1 版本的路由聚合到 /api/v1 前綴下
"""

from fastapi import APIRouter

# 創建 v1 版本路由
router = APIRouter(prefix="/api/v1", tags=["API v1"])

# 這裡可以導入其他路由並添加版本前綴
# 例如：
# from . import stocks
# router.include_router(stocks.router, prefix="/stocks")

# 版本資訊端點
@router.get("/")
async def api_v1_info():
    """API v1 版本資訊"""
    return {
        "version": "1.0",
        "status": "stable",
        "deprecation_date": None,
        "endpoints": {
            "stocks": "/api/v1/stocks/*",
            "auth": "/api/v1/auth/*",
            "optimization": "/api/v1/optimization/*",
        }
    }


@router.get("/version")
async def get_api_version():
    """取得 API 版本詳情"""
    return {
        "api_version": "1.0",
        "app_version": "10.38.0",
        "features": [
            "股票資料查詢",
            "AI 推薦系統",
            "績效追蹤",
            "風險管理",
            "ML 預測",
            "身份驗證",
            "權重優化",
        ],
        "changelog": [
            {"version": "1.0", "date": "2026-01-13", "changes": ["初始 v1 版本"]},
        ]
    }
