"""
optimization_routes.py - 優化服務 API 路由
V10.38: 權重優化、閾值分析、動態產業熱度

端點：
- GET /api/optimization/weights/analyze - 分析當前權重績效
- POST /api/optimization/weights/optimize - 執行權重優化
- GET /api/optimization/threshold/analyze - 分析分數閾值
- GET /api/optimization/market-condition - 市場狀況分析
- GET /api/optimization/industry-heat - 動態產業熱度
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List

from ..services.weight_optimizer import get_weight_optimizer

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])


# ===== 權重優化 API =====

@router.get("/weights/analyze")
async def analyze_current_weights():
    """
    分析當前權重配置的績效

    Returns:
        當前權重的績效分析報告
    """
    optimizer = get_weight_optimizer()
    result = optimizer.analyze_current_performance()

    if "error" in result:
        return {
            "status": "insufficient_data",
            "message": result["error"],
            "data": result
        }

    return {
        "status": "success",
        "data": result
    }


@router.post("/weights/optimize")
async def optimize_weights(min_samples: int = Query(default=30, ge=10, le=500)):
    """
    執行權重優化

    使用 Grid Search 尋找最佳權重組合

    Args:
        min_samples: 最少樣本數 (預設 30)

    Returns:
        優化結果，包含最佳權重和改善建議
    """
    optimizer = get_weight_optimizer()
    result = optimizer.optimize_weights(min_samples=min_samples)

    if "error" in result:
        return {
            "status": "insufficient_data",
            "message": result["error"],
            "data": result
        }

    return {
        "status": "success",
        "data": result
    }


@router.get("/threshold/analyze")
async def analyze_score_threshold():
    """
    分析最佳分數閾值

    找出買進訊號的最佳信心分數閾值

    Returns:
        閾值分析結果和建議
    """
    optimizer = get_weight_optimizer()
    result = optimizer.get_score_threshold_analysis()

    if "error" in result:
        return {
            "status": "insufficient_data",
            "message": result["error"],
            "data": result
        }

    return {
        "status": "success",
        "data": result
    }


@router.get("/market-condition")
async def analyze_market_condition():
    """
    根據市場狀況分析最適權重

    分析不同市場環境下（多頭/空頭/盤整）的最佳權重配置

    Returns:
        市場狀況分析和權重建議
    """
    optimizer = get_weight_optimizer()
    result = optimizer.get_weight_analysis_by_market_condition()

    if "error" in result:
        return {
            "status": "insufficient_data",
            "message": result["error"],
            "data": result
        }

    return {
        "status": "success",
        "data": result
    }


# ===== 動態產業熱度 API =====

# 產業基礎熱度 (可被動態調整)
INDUSTRY_BASE_HEAT = {
    # AI 相關
    "AI": 12,
    "AI伺服器": 12,
    "GB200": 10,
    "HBM": 10,
    "CoWoS": 10,
    "先進製程": 8,
    "先進封裝": 8,

    # 半導體
    "半導體": 6,
    "IC設計": 5,
    "封測": 4,

    # 新能源
    "電動車": 5,
    "充電樁": 4,
    "太陽能": 3,
    "儲能": 4,

    # 通訊
    "5G": 4,
    "低軌衛星": 4,

    # 傳產
    "航運": 2,
    "鋼鐵": 1,
    "金融": 2,
    "營建": 1,

    # 防禦性
    "生技": 3,
    "食品": 0,
    "電信": -1,
}


def calculate_dynamic_industry_heat(
    base_industry: str,
    market_trend: float = 0,  # 大盤趨勢 (-10 ~ +10)
    sector_momentum: float = 0,  # 產業動能 (-5 ~ +5)
    news_sentiment: float = 0,  # 新聞情緒 (-3 ~ +3)
) -> Dict[str, Any]:
    """
    計算動態產業熱度

    Args:
        base_industry: 產業名稱
        market_trend: 大盤趨勢
        sector_momentum: 產業動能
        news_sentiment: 新聞情緒

    Returns:
        動態熱度計算結果
    """
    base_heat = INDUSTRY_BASE_HEAT.get(base_industry, 0)

    # 動態調整因子
    trend_factor = market_trend * 0.3  # 大盤影響 30%
    momentum_factor = sector_momentum * 0.5  # 產業動能影響 50%
    sentiment_factor = news_sentiment * 0.2  # 新聞情緒影響 20%

    # 計算動態熱度
    dynamic_adjustment = trend_factor + momentum_factor + sentiment_factor
    final_heat = base_heat + dynamic_adjustment

    # 限制範圍
    final_heat = max(-10, min(15, final_heat))

    return {
        "industry": base_industry,
        "base_heat": base_heat,
        "adjustments": {
            "market_trend": round(trend_factor, 2),
            "sector_momentum": round(momentum_factor, 2),
            "news_sentiment": round(sentiment_factor, 2),
        },
        "dynamic_adjustment": round(dynamic_adjustment, 2),
        "final_heat": round(final_heat, 1),
        "heat_level": _get_heat_level(final_heat),
    }


def _get_heat_level(heat: float) -> str:
    """取得熱度等級描述"""
    if heat >= 10:
        return "極熱門"
    elif heat >= 6:
        return "熱門"
    elif heat >= 3:
        return "溫和"
    elif heat >= 0:
        return "中性"
    elif heat >= -3:
        return "冷門"
    else:
        return "極冷門"


@router.get("/industry-heat")
async def get_industry_heat(industry: str = Query(default=None)):
    """
    V10.38: 取得動態產業熱度

    使用 IndustryHeatService 從市場數據計算產業熱度

    Args:
        industry: 產業名稱 (可選，不指定則返回所有產業)

    Returns:
        產業熱度資料
    """
    try:
        from ..services.industry_heat_service import IndustryHeatService
        from dataclasses import asdict

        if industry:
            # V10.38: 使用新的動態計算服務
            heat = await IndustryHeatService.get_industry_heat(industry)
            return {
                "status": "success",
                "data": {
                    "industry": heat.industry,
                    "heat_score": heat.heat_score,
                    "heat_level": _get_heat_level(heat.heat_score),
                    "details": {
                        "avg_return_5d": heat.avg_return_5d,
                        "avg_return_20d": heat.avg_return_20d,
                        "foreign_net_ratio": heat.foreign_net_ratio,
                        "volume_trend": heat.volume_trend,
                        "momentum_score": heat.momentum_score,
                    },
                    "stock_count": heat.stock_count,
                    "data_source": heat.data_source,
                    "updated_at": heat.updated_at,
                }
            }

        # V10.38: 取得所有產業的動態熱度
        all_heat = await IndustryHeatService.get_all_industry_heat()
        industries = []
        for heat in all_heat:
            industries.append({
                "industry": heat.industry,
                "heat_score": heat.heat_score,
                "heat_level": _get_heat_level(heat.heat_score),
                "stock_count": heat.stock_count,
                "data_source": heat.data_source,
            })

        return {
            "status": "success",
            "count": len(industries),
            "data": industries,
            "note": "V10.38: 動態計算產業熱度"
        }

    except Exception as e:
        # 降級到舊版靜態熱度
        if industry:
            result = calculate_dynamic_industry_heat(
                base_industry=industry,
                market_trend=0,
                sector_momentum=0,
                news_sentiment=0,
            )
            result["data_source"] = "legacy"
            return {
                "status": "success",
                "data": result
            }

        industries = []
        for ind, heat in INDUSTRY_BASE_HEAT.items():
            industries.append({
                "industry": ind,
                "heat_score": heat,
                "heat_level": _get_heat_level(heat),
                "data_source": "legacy",
            })

        industries.sort(key=lambda x: x["heat_score"], reverse=True)

        return {
            "status": "success",
            "count": len(industries),
            "data": industries,
            "note": "Using legacy static heat values"
        }


@router.put("/industry-heat/{industry}")
async def update_industry_heat(
    industry: str,
    heat: int = Query(..., ge=-10, le=15, description="熱度值 (-10 ~ 15)")
):
    """
    更新產業熱度 (管理功能)

    Args:
        industry: 產業名稱
        heat: 新的熱度值

    Returns:
        更新結果
    """
    old_heat = INDUSTRY_BASE_HEAT.get(industry, 0)
    INDUSTRY_BASE_HEAT[industry] = heat

    return {
        "status": "success",
        "industry": industry,
        "old_heat": old_heat,
        "new_heat": heat,
        "message": f"產業 '{industry}' 熱度已從 {old_heat} 更新為 {heat}"
    }


@router.post("/industry-heat/batch")
async def batch_update_industry_heat(updates: Dict[str, int]):
    """
    批次更新產業熱度

    Args:
        updates: 產業名稱 -> 熱度值 的字典

    Returns:
        更新結果
    """
    results = []
    for industry, heat in updates.items():
        if -10 <= heat <= 15:
            old_heat = INDUSTRY_BASE_HEAT.get(industry, 0)
            INDUSTRY_BASE_HEAT[industry] = heat
            results.append({
                "industry": industry,
                "old_heat": old_heat,
                "new_heat": heat,
            })

    return {
        "status": "success",
        "updated_count": len(results),
        "data": results
    }
