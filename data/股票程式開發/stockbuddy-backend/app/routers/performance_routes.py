"""
V10.37: 績效追蹤 API 路由
從 stocks.py 拆分出來，提高可維護性
"""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/stocks/performance-tracker", tags=["performance"])


def get_tracker():
    """取得績效追蹤器實例"""
    from app.services.performance_tracker import get_performance_tracker
    return get_performance_tracker()


# =============================================================================
# V10.23: 基本績效追蹤 API
# =============================================================================

@router.post("/record")
async def record_recommendation(
    stock_id: str,
    name: str,
    price: float,
    signal: str,
    confidence: int,
    reason: str = None
):
    """
    V10.23: 記錄一次推薦

    用於追蹤 AI 推薦的後續表現
    """
    tracker = get_tracker()
    result = tracker.record_recommendation(
        stock_id=stock_id,
        name=name,
        price=price,
        signal=signal,
        confidence=confidence,
        reason=reason
    )
    return result


@router.post("/update-price/{stock_id}")
async def update_stock_price(stock_id: str, current_price: float):
    """
    V10.23: 更新股票當前價格
    """
    tracker = get_tracker()
    result = tracker.update_price(stock_id, current_price)
    return result


@router.post("/close/{stock_id}")
async def close_recommendation(
    stock_id: str,
    exit_price: float,
    reason: str = "手動關閉"
):
    """
    V10.23: 關閉推薦追蹤
    """
    tracker = get_tracker()
    result = tracker.close_position(stock_id, exit_price, reason)
    return result


@router.get("/active")
async def get_active_recommendations():
    """
    V10.23: 取得所有進行中的推薦
    """
    tracker = get_tracker()
    return {
        "success": True,
        "recommendations": tracker.get_active_recommendations()
    }


@router.get("/closed")
async def get_closed_recommendations(limit: int = Query(50, description="數量限制")):
    """
    V10.23: 取得已關閉的推薦
    """
    tracker = get_tracker()
    return {
        "success": True,
        "recommendations": tracker.get_closed_recommendations(limit)
    }


@router.get("/statistics")
async def get_performance_statistics():
    """
    V10.23: 取得績效統計
    """
    tracker = get_tracker()
    return {
        "success": True,
        "statistics": tracker.get_statistics()
    }


@router.get("/history/{stock_id}")
async def get_stock_recommendation_history(stock_id: str):
    """
    V10.23: 取得特定股票的推薦歷史
    """
    tracker = get_tracker()
    return {
        "success": True,
        "history": tracker.get_recommendation_history(stock_id)
    }


@router.get("/daily")
async def get_daily_performance(days: int = Query(30, description="天數")):
    """
    V10.23: 取得每日績效摘要
    """
    tracker = get_tracker()
    return {
        "success": True,
        "daily_performance": tracker.get_daily_performance(days)
    }


@router.get("/report")
async def get_performance_report():
    """
    V10.23: 匯出完整績效報告
    """
    tracker = get_tracker()
    return {
        "success": True,
        "report": tracker.export_report()
    }


@router.post("/cleanup")
async def cleanup_expired_recommendations(max_days: int = Query(90, description="最大保留天數")):
    """
    V10.23: 清理過期的推薦記錄
    """
    tracker = get_tracker()
    tracker.cleanup_expired(max_days)
    return {
        "success": True,
        "message": f"已清理超過 {max_days} 天的過期記錄"
    }


# =============================================================================
# V10.36: 進階績效統計 API
# =============================================================================

@router.get("/stats-by-period")
async def get_performance_stats_by_period():
    """
    V10.36: 按追蹤週期取得績效統計 (7/30/90天)
    """
    try:
        tracker = get_tracker()
        result = tracker.get_stats_by_period([7, 30, 90])
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/stats-by-signal")
async def get_performance_stats_by_signal():
    """
    V10.36: 按訊號類型取得績效統計
    """
    try:
        tracker = get_tracker()
        result = tracker.get_stats_by_signal()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/stats-by-score")
async def get_performance_stats_by_score():
    """
    V10.36: 按評分區間取得績效統計
    """
    try:
        tracker = get_tracker()
        result = tracker.get_stats_by_score_range()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/comprehensive")
async def get_comprehensive_performance_stats():
    """
    V10.36: 取得綜合績效統計報告
    """
    try:
        tracker = get_tracker()
        result = tracker.get_comprehensive_stats()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}
