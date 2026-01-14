"""
擴展 API 路由 V10.21
新增功能：匯出、績效分析、櫃買股票、策略、篩選、比較、警示、交易、分類

端點：
- /api/stocks/export/* - 匯出功能
- /api/stocks/performance/* - 績效分析
- /api/stocks/otc/* - 櫃買股票
- /api/stocks/strategy/* - 綜合投資策略 (V10.16)
- /api/stocks/screener/* - 選股篩選器 (V10.17)
- /api/stocks/compare/* - 股票比較 (V10.18)
- /api/stocks/alerts/* - 價格警示 (V10.19)
- /api/stocks/transactions/* - 交易記錄 (V10.20)
- /api/stocks/categories/* - 自選股分類 (V10.21)
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import io

router = APIRouter(prefix="/api/stocks", tags=["extended"])


# ============================================================
# 匯出功能 API
# ============================================================

@router.get("/export/recommendations/csv")
async def export_recommendations_csv():
    """
    匯出 AI 推薦股票清單為 CSV
    """
    try:
        from app.services.ai_stock_picker import get_ai_top_picks
        from app.services.export_service import ExportService

        # 取得推薦清單
        recommendations = await get_ai_top_picks(limit=50)

        if not recommendations:
            raise HTTPException(status_code=404, detail="無推薦資料")

        # 匯出 CSV
        csv_content = ExportService.export_recommendations_csv(recommendations)

        # 設定檔名
        filename = f"stockbuddy_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            content=csv_content.encode('utf-8-sig'),  # BOM for Excel
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


@router.get("/export/recommendations/excel")
async def export_recommendations_excel():
    """
    匯出 AI 推薦股票清單為 Excel
    """
    try:
        from app.services.ai_stock_picker import get_ai_top_picks
        from app.services.export_service import ExportService

        recommendations = await get_ai_top_picks(limit=50)

        if not recommendations:
            raise HTTPException(status_code=404, detail="無推薦資料")

        excel_content = ExportService.export_recommendations_excel(recommendations)
        filename = f"stockbuddy_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


@router.get("/export/portfolio/csv")
async def export_portfolio_csv():
    """
    匯出投資組合為 CSV
    """
    try:
        from app.services.portfolio_service import PortfolioService
        from app.services.export_service import ExportService

        portfolio = PortfolioService()
        holdings = portfolio.get_all_holdings()
        summary = portfolio.get_summary()

        csv_content = ExportService.export_portfolio_csv(holdings, summary)
        filename = f"stockbuddy_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            content=csv_content.encode('utf-8-sig'),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


@router.get("/export/portfolio/excel")
async def export_portfolio_excel():
    """
    匯出投資組合為 Excel
    """
    try:
        from app.services.portfolio_service import PortfolioService
        from app.services.export_service import ExportService

        portfolio = PortfolioService()
        holdings = portfolio.get_all_holdings()
        summary = portfolio.get_summary()

        excel_content = ExportService.export_portfolio_excel(holdings, summary)
        filename = f"stockbuddy_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


@router.get("/export/backtest/{stock_id}/excel")
async def export_backtest_excel(
    stock_id: str,
    strategy: str = Query(default="combined", description="策略名稱"),
    months: int = Query(default=6, ge=1, le=24, description="回測月數")
):
    """
    匯出回測結果為 Excel
    """
    try:
        from app.services.backtest_engine import run_backtest
        from app.services.export_service import ExportService

        # 計算日期範圍
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")

        # 執行回測
        result = await run_backtest(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        excel_content = ExportService.export_backtest_excel(result)
        filename = f"backtest_{stock_id}_{strategy}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


# ============================================================
# 績效分析 API
# ============================================================

@router.get("/performance/{stock_id}")
async def get_stock_performance(
    stock_id: str,
    months: int = Query(default=12, ge=1, le=60, description="分析月數")
):
    """
    取得股票進階績效分析

    包含：Alpha/Beta、夏普比率、Sortino、最大回撤、VaR 等
    """
    try:
        from app.services.github_data import SmartStockService
        from app.services.performance_analytics import PerformanceAnalytics

        # 取得股票歷史資料
        stock_history = await SmartStockService.get_stock_history(stock_id, months=months)

        if not stock_history or len(stock_history) < 20:
            raise HTTPException(status_code=400, detail="股票歷史資料不足")

        # 取得大盤歷史（用於計算 Alpha/Beta）
        market_history = await SmartStockService.get_stock_history("0050", months=months)

        # 執行分析
        performance = PerformanceAnalytics.full_performance_analysis(
            stock_history=stock_history,
            market_history=market_history
        )

        return {
            "success": True,
            "stock_id": stock_id,
            "analysis_period": f"{months} 個月",
            "performance": performance
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"績效分析失敗: {str(e)}")


@router.get("/performance/{stock_id}/monthly-heatmap")
async def get_monthly_heatmap(
    stock_id: str,
    years: int = Query(default=3, ge=1, le=10, description="分析年數")
):
    """
    取得月報酬熱力圖數據
    """
    try:
        from app.services.github_data import SmartStockService
        from app.services.performance_analytics import PerformanceAnalytics

        stock_history = await SmartStockService.get_stock_history(stock_id, months=years * 12)

        if not stock_history:
            raise HTTPException(status_code=400, detail="無法取得歷史資料")

        monthly_returns = PerformanceAnalytics.calculate_monthly_returns(stock_history)
        yearly_stats = PerformanceAnalytics.calculate_yearly_stats(stock_history)

        # 計算月平均報酬和月勝率
        all_returns = []
        for year_data in monthly_returns.values():
            all_returns.extend(year_data.values())

        avg_monthly_return = sum(all_returns) / len(all_returns) if all_returns else 0
        positive_months = sum(1 for r in all_returns if r > 0)
        monthly_win_rate = (positive_months / len(all_returns) * 100) if all_returns else 0

        return {
            "success": True,
            "stock_id": stock_id,
            "monthly_returns": monthly_returns,
            "yearly_stats": yearly_stats,
            "summary": {
                "avg_monthly_return": round(avg_monthly_return, 2),
                "monthly_win_rate": round(monthly_win_rate, 1),
                "total_months": len(all_returns),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得月報酬失敗: {str(e)}")


@router.get("/performance/{stock_id}/risk-metrics")
async def get_risk_metrics(
    stock_id: str,
    months: int = Query(default=12, ge=1, le=36, description="分析月數")
):
    """
    取得風險指標詳情

    包含：VaR、CVaR、最大回撤、波動率等
    """
    try:
        from app.services.github_data import SmartStockService
        from app.services.performance_analytics import PerformanceAnalytics

        stock_history = await SmartStockService.get_stock_history(stock_id, months=months)

        if not stock_history or len(stock_history) < 20:
            raise HTTPException(status_code=400, detail="歷史資料不足")

        prices = [h["close"] for h in stock_history]
        returns = PerformanceAnalytics.calculate_returns(prices)

        # 計算各種風險指標
        max_dd = PerformanceAnalytics.calculate_max_drawdown(prices)
        var_95 = PerformanceAnalytics.calculate_var(returns, 0.95)
        var_99 = PerformanceAnalytics.calculate_var(returns, 0.99)
        cvar_95 = PerformanceAnalytics.calculate_cvar(returns, 0.95)

        import numpy as np
        volatility_daily = np.std(returns) * 100
        volatility_annual = volatility_daily * np.sqrt(252)

        return {
            "success": True,
            "stock_id": stock_id,
            "period": f"{months} 個月",
            "risk_metrics": {
                "max_drawdown_pct": max_dd["max_drawdown_pct"],
                "var_95": var_95,
                "var_99": var_99,
                "cvar_95": cvar_95,
                "volatility_daily": round(volatility_daily, 2),
                "volatility_annual": round(volatility_annual, 2),
            },
            "drawdown_info": {
                "max_drawdown": max_dd["max_drawdown"],
                "peak_idx": max_dd.get("peak_idx"),
                "trough_idx": max_dd.get("trough_idx"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得風險指標失敗: {str(e)}")


# ============================================================
# 櫃買股票 API
# ============================================================

@router.get("/otc/all")
async def get_all_otc_stocks():
    """
    取得所有上櫃股票資料
    """
    try:
        from app.services.tpex_openapi import TPExOpenAPI

        data = await TPExOpenAPI.get_all_otc_data()

        return {
            "success": True,
            "count": len(data),
            "market": "OTC",
            "stocks": list(data.values())[:100],  # 限制返回數量
            "data_time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得上櫃資料失敗: {str(e)}")


@router.get("/otc/info/{stock_id}")
async def get_otc_stock_info(stock_id: str):
    """
    取得單一上櫃股票資訊
    """
    try:
        from app.services.tpex_openapi import TPExOpenAPI

        data = await TPExOpenAPI.get_all_otc_data()

        if stock_id not in data:
            raise HTTPException(status_code=404, detail=f"找不到上櫃股票 {stock_id}")

        return {
            "success": True,
            "stock": data[stock_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得資料失敗: {str(e)}")


@router.get("/otc/institutional")
async def get_otc_institutional():
    """
    取得上櫃三大法人買賣超
    """
    try:
        from app.services.tpex_openapi import TPExOpenAPI

        data = await TPExOpenAPI.get_otc_institutional()

        # 排序：依買超金額排序
        sorted_data = sorted(
            data.values(),
            key=lambda x: x.get("total_net", 0),
            reverse=True
        )

        return {
            "success": True,
            "count": len(sorted_data),
            "data": sorted_data[:50],  # Top 50
            "data_time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得法人資料失敗: {str(e)}")


@router.get("/market-type/{stock_id}")
async def check_market_type(stock_id: str):
    """
    判斷股票屬於上市或上櫃
    """
    from app.services.tpex_openapi import TPExOpenAPI

    is_otc = TPExOpenAPI.is_otc_stock(stock_id)

    return {
        "stock_id": stock_id,
        "market": "OTC" if is_otc else "TWSE",
        "market_name": "上櫃" if is_otc else "上市",
        "is_otc": is_otc
    }


# ============================================================
# 資料日期與狀態 API
# ============================================================

@router.get("/data-status")
async def get_data_status():
    """
    取得資料更新狀態與日期

    用於前端顯示資料新鮮度警告
    """
    try:
        from app.services.twse_openapi import TWSEOpenAPI
        from datetime import datetime

        # 取得 TWSE 資料更新時間
        twse_data = await TWSEOpenAPI.get_all_stocks_summary()
        twse_date = None
        if twse_data:
            # 從任一股票取得日期
            for stock_id, data in twse_data.items():
                if data.get("date"):
                    twse_date = data.get("date")
                    break

        # 判斷資料是否過期（超過 1 天）
        today = datetime.now().strftime("%Y-%m-%d")
        is_stale = twse_date != today if twse_date else True

        # 判斷是否為交易時間
        now = datetime.now()
        is_trading_hours = (
            now.weekday() < 5 and  # 週一到週五
            9 <= now.hour < 14     # 9:00 - 14:00
        )

        return {
            "success": True,
            "data_date": twse_date,
            "current_date": today,
            "is_stale": is_stale,
            "is_trading_hours": is_trading_hours,
            "message": "資料已過期，請清除快取更新" if is_stale else "資料為最新",
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "is_stale": True
        }


# ============================================================
# 三大法人追蹤 API
# ============================================================

@router.get("/institutional-tracking/{stock_id}")
async def get_institutional_tracking(
    stock_id: str,
    days: int = Query(default=20, ge=5, le=60, description="追蹤天數")
):
    """
    取得三大法人持股追蹤資料（用於圖表）
    """
    try:
        from app.services.finmind_service import FinMindService
        from datetime import datetime, timedelta

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 10)).strftime("%Y-%m-%d")

        # 嘗試取得多日法人資料
        history = await FinMindService.get_institutional_history(stock_id, start_date, end_date)

        if not history:
            # Fallback: 只返回最新一天
            latest = await FinMindService.get_latest_institutional(stock_id)
            if latest:
                history = [latest]
            else:
                return {
                    "success": False,
                    "error": "無法取得法人資料",
                    "stock_id": stock_id
                }

        return {
            "success": True,
            "stock_id": stock_id,
            "days": len(history),
            "tracking_data": history[-days:] if len(history) > days else history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得法人追蹤資料失敗: {str(e)}")


# ============================================================
# 綜合投資策略 API (V10.16)
# ============================================================

@router.get("/strategy/{stock_id}")
async def get_investment_strategy(stock_id: str):
    """
    取得股票的綜合投資策略分析

    包含：
    - 投資建議等級 (Strong Buy/Buy/Hold/Reduce/Sell)
    - 完整交易策略 (進場、加碼、止損、獲利了結)
    - 多維度分析 (技術/基本/籌碼/產業)
    - 風險評估
    - 投資論點與關鍵因素
    """
    try:
        from app.services.investment_strategy import InvestmentStrategyService

        strategy = await InvestmentStrategyService.get_comprehensive_strategy(stock_id)

        if "error" in strategy:
            raise HTTPException(status_code=400, detail=strategy["error"])

        return {
            "success": True,
            "stock_id": stock_id,
            "strategy": strategy
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得投資策略失敗: {str(e)}")


@router.get("/strategy-picks")
async def get_strategy_picks(
    top_n: int = Query(default=10, ge=1, le=30, description="精選數量")
):
    """
    取得綜合投資策略精選股票

    結合 AI 分析和多維度指標，提供專業的投顧級建議

    Returns:
        - market_overview: 市場概覽
        - strategy_picks: 策略精選清單
        - portfolio_allocation: 投資組合配置建議
        - is_fallback: 是否使用備用方案（可選）
    """
    try:
        from app.services.investment_strategy import InvestmentStrategyService

        result = await InvestmentStrategyService.get_strategy_picks(top_n)

        # 只有當沒有任何策略精選且有錯誤時才返回錯誤
        if "error" in result and not result.get("strategy_picks"):
            raise HTTPException(status_code=400, detail=result["error"])

        # 正常返回（包含備用方案的結果）
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得策略精選失敗: {str(e)}")


@router.get("/strategy/{stock_id}/trading-plan")
async def get_trading_plan(stock_id: str):
    """
    取得股票的詳細交易計劃

    提供：
    - 進場策略與時機
    - 加碼計劃
    - 止損策略
    - 分批獲利了結計劃
    - 資金配置建議
    """
    try:
        from app.services.investment_strategy import InvestmentStrategyService

        strategy = await InvestmentStrategyService.get_comprehensive_strategy(stock_id)

        if "error" in strategy:
            raise HTTPException(status_code=400, detail=strategy["error"])

        trading_strategy = strategy.get("trading_strategy", {})
        risk_assessment = strategy.get("risk_assessment", {})

        return {
            "success": True,
            "stock_id": stock_id,
            "stock_name": strategy.get("stock_name"),
            "current_price": strategy.get("current_price"),
            "rating": strategy.get("rating"),
            "trading_plan": trading_strategy,
            "risk_assessment": risk_assessment,
            "analysis_time": strategy.get("analysis_time")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得交易計劃失敗: {str(e)}")


@router.get("/strategy/{stock_id}/risk")
async def get_risk_assessment(stock_id: str):
    """
    取得股票的風險評估報告

    包含：
    - 整體風險等級
    - 各類風險分析 (市場/流動性/波動/基本面)
    - 風險因素列表
    - 風險緩解策略
    """
    try:
        from app.services.investment_strategy import InvestmentStrategyService

        strategy = await InvestmentStrategyService.get_comprehensive_strategy(stock_id)

        if "error" in strategy:
            raise HTTPException(status_code=400, detail=strategy["error"])

        return {
            "success": True,
            "stock_id": stock_id,
            "stock_name": strategy.get("stock_name"),
            "risk_assessment": strategy.get("risk_assessment"),
            "key_risks": strategy.get("key_risks"),
            "investment_horizon": strategy.get("investment_horizon"),
            "suitable_investor": strategy.get("suitable_investor")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得風險評估失敗: {str(e)}")


@router.get("/portfolio-recommendation")
async def get_portfolio_recommendation(
    budget: float = Query(default=100000, ge=10000, description="投資預算（台幣）"),
    risk_tolerance: str = Query(default="medium", description="風險承受度: low/medium/high")
):
    """
    取得投資組合建議

    依據投資預算和風險承受度，提供最佳配置建議

    Args:
        budget: 投資預算
        risk_tolerance: 風險承受度

    Returns:
        - recommended_stocks: 推薦股票清單
        - allocation: 配置比例
        - expected_metrics: 預期指標
    """
    try:
        from app.services.investment_strategy import InvestmentStrategyService

        # 取得策略精選
        picks_count = 5 if risk_tolerance == "low" else 10 if risk_tolerance == "medium" else 15
        result = await InvestmentStrategyService.get_strategy_picks(picks_count)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # 依風險承受度調整配置
        picks = result.get("strategy_picks", [])
        allocation = result.get("portfolio_allocation", {})

        # 計算每檔股票的建議金額
        allocations = allocation.get("allocations", [])
        for item in allocations:
            weight = item.get("weight_percent", 0)
            item["suggested_amount"] = round(budget * weight / 100, 0)
            item["suggested_shares"] = 0

            # 找到對應的股票資訊計算股數
            for pick in picks:
                if pick.get("stock_id") == item.get("stock_id"):
                    price = pick.get("current_price", 0)
                    if price > 0:
                        # 計算可買股數（以張為單位）
                        shares = int(item["suggested_amount"] / (price * 1000)) * 1000
                        item["suggested_shares"] = shares
                        item["actual_amount"] = shares * price
                    break

        return {
            "success": True,
            "budget": budget,
            "risk_tolerance": risk_tolerance,
            "recommended_count": len(picks),
            "portfolio_allocation": allocations,
            "strategy_summary": allocation.get("strategy"),
            "market_overview": result.get("market_overview"),
            "analysis_time": result.get("updated_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得投資組合建議失敗: {str(e)}")


# ============================================================
# 選股篩選器 API (V10.17)
# ============================================================

@router.get("/screener/screen")
async def screen_stocks(
    pe_min: Optional[float] = Query(default=None, description="本益比下限"),
    pe_max: Optional[float] = Query(default=None, description="本益比上限"),
    pb_min: Optional[float] = Query(default=None, description="股價淨值比下限"),
    pb_max: Optional[float] = Query(default=None, description="股價淨值比上限"),
    dividend_yield_min: Optional[float] = Query(default=None, description="殖利率下限 (%)"),
    dividend_yield_max: Optional[float] = Query(default=None, description="殖利率上限 (%)"),
    roe_min: Optional[float] = Query(default=None, description="ROE 下限 (%)"),
    roe_max: Optional[float] = Query(default=None, description="ROE 上限 (%)"),
    market_cap_size: Optional[str] = Query(default=None, description="市值規模: large/mid/small"),
    limit: int = Query(default=20, ge=1, le=50, description="最大返回數量")
):
    """
    執行選股篩選

    支援多條件組合篩選：
    - 基本面篩選（本益比、股價淨值比、殖利率、ROE）
    - 市值規模篩選（大型股/中型股/小型股）

    Example:
        - 價值型：/screener/screen?pe_max=15&dividend_yield_min=3
        - 成長型：/screener/screen?roe_min=15&pe_max=30
    """
    try:
        from app.services.stock_screener import StockScreener, MarketCapSize

        # 轉換市值規模
        cap_size = None
        if market_cap_size:
            cap_size = MarketCapSize(market_cap_size) if market_cap_size in ["large", "mid", "small"] else None

        result = await StockScreener.screen_stocks(
            pe_min=pe_min,
            pe_max=pe_max,
            pb_min=pb_min,
            pb_max=pb_max,
            dividend_yield_min=dividend_yield_min,
            dividend_yield_max=dividend_yield_max,
            roe_min=roe_min,
            roe_max=roe_max,
            market_cap_size=cap_size,
            limit=limit,
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"篩選失敗: {str(e)}")


@router.get("/screener/preset/{preset_name}")
async def screen_by_preset(
    preset_name: str,
    limit: int = Query(default=20, ge=1, le=50, description="最大返回數量")
):
    """
    使用預設策略進行篩選

    可用策略：
    - value: 價值投資（低本益比、高殖利率）
    - growth: 成長股（高 ROE、營收成長）
    - dividend: 高殖利率（殖利率 > 5%）
    - momentum: 動能股（技術面強勢）
    - defensive: 防禦型（低波動、穩定配息）
    - small_cap: 小型成長股
    - blue_chip: 績優藍籌
    """
    try:
        from app.services.stock_screener import StockScreener, ScreenerPreset

        # 驗證預設策略名稱
        try:
            preset = ScreenerPreset(preset_name)
        except ValueError:
            available = [p.value for p in ScreenerPreset]
            raise HTTPException(
                status_code=400,
                detail=f"無效的預設策略: {preset_name}。可用策略: {available}"
            )

        result = await StockScreener.screen_by_preset(preset, limit)

        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"篩選失敗: {str(e)}")


@router.get("/screener/presets")
async def get_screener_presets():
    """
    取得所有可用的預設篩選策略

    返回每個策略的名稱、描述和篩選條件
    """
    try:
        from app.services.stock_screener import StockScreener

        presets = StockScreener.get_available_presets()

        return {
            "success": True,
            "count": len(presets),
            "presets": presets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得預設策略失敗: {str(e)}")


@router.get("/screener/stats")
async def get_screener_stats():
    """
    取得篩選器統計資訊

    包含股票池大小、可用篩選條件、快取狀態等
    """
    try:
        from app.services.stock_screener import StockScreener

        stats = await StockScreener.get_screener_stats()

        return {
            "success": True,
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得統計失敗: {str(e)}")


# ============================================================
# 股票比較 API (V10.18)
# ============================================================

@router.get("/compare")
async def compare_stocks(
    stocks: str = Query(..., description="股票代號（逗號分隔，最多 5 檔）"),
    metrics_type: str = Query(default="fundamental", description="比較類型: fundamental/valuation/growth/dividend")
):
    """
    比較多檔股票

    支援最多 5 檔股票的並排比較，提供：
    - 基本面指標比較表格
    - 雷達圖數據
    - 各指標最佳股票標記

    Example:
        - /compare?stocks=2330,2317,2454&metrics_type=fundamental
    """
    try:
        from app.services.stock_comparison import StockComparison

        # 解析股票代號
        stock_ids = [s.strip() for s in stocks.split(",") if s.strip()]

        if len(stock_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要 2 檔股票進行比較")
        if len(stock_ids) > 5:
            raise HTTPException(status_code=400, detail="最多比較 5 檔股票")

        result = await StockComparison.compare_stocks(stock_ids, metrics_type)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比較失敗: {str(e)}")


@router.get("/compare/quick")
async def quick_compare_stocks(
    stocks: str = Query(..., description="股票代號（逗號分隔，最多 5 檔）")
):
    """
    快速比較（簡化版本）

    返回關鍵指標的快速對比，適合卡片式顯示

    Example:
        - /compare/quick?stocks=2330,2317
    """
    try:
        from app.services.stock_comparison import StockComparison

        stock_ids = [s.strip() for s in stocks.split(",") if s.strip()]

        if len(stock_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要 2 檔股票進行比較")
        if len(stock_ids) > 5:
            raise HTTPException(status_code=400, detail="最多比較 5 檔股票")

        result = await StockComparison.get_quick_comparison(stock_ids)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比較失敗: {str(e)}")


@router.get("/compare/metrics")
async def get_comparison_metrics():
    """
    取得可用的比較指標配置

    返回各種比較類型的指標列表
    """
    try:
        from app.services.stock_comparison import StockComparison

        return {
            "success": True,
            "metrics_types": list(StockComparison.COMPARISON_METRICS.keys()),
            "metrics": StockComparison.COMPARISON_METRICS,
            "radar_dimensions": StockComparison.RADAR_DIMENSIONS,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得指標配置失敗: {str(e)}")


# ============================================================
# 價格警示 API (V10.19)
# ============================================================

@router.post("/alerts/check")
async def check_price_alerts(
    alerts: List[Dict] = []
):
    """
    檢查價格警示觸發狀態

    Body 參數:
    ```json
    [
        {
            "id": "alert_1",
            "stock_id": "2330",
            "alert_type": "above",  // above, below, percent_up, percent_down
            "target_price": 600,    // 價格類型用
            "target_percent": 5,    // 百分比類型用
            "base_price": 550       // 百分比類型的基準價
        }
    ]
    ```

    Returns:
        - checked_count: 檢查的警示數量
        - triggered_count: 已觸發數量
        - triggered: 已觸發的警示列表
        - results: 所有警示的檢查結果
    """
    try:
        from app.services.price_alert import PriceAlertService

        result = await PriceAlertService.check_alerts(alerts)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檢查警示失敗: {str(e)}")


@router.get("/alerts/price/{stock_id}")
async def get_stock_price(stock_id: str):
    """
    取得股票即時價格

    用於設定警示時取得當前價格作為參考
    """
    try:
        from app.services.price_alert import PriceAlertService

        result = await PriceAlertService.get_current_price(stock_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得價格失敗: {str(e)}")


@router.get("/alerts/prices")
async def get_batch_prices(
    stocks: str = Query(..., description="股票代號（逗號分隔）")
):
    """
    批次取得多檔股票即時價格

    Example:
        - /alerts/prices?stocks=2330,2317,2454
    """
    try:
        from app.services.price_alert import PriceAlertService

        stock_ids = [s.strip() for s in stocks.split(",") if s.strip()]

        if not stock_ids:
            raise HTTPException(status_code=400, detail="請提供股票代號")

        result = await PriceAlertService.get_batch_prices(stock_ids)

        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批次取得價格失敗: {str(e)}")


@router.get("/alerts/types")
async def get_alert_types():
    """
    取得所有警示類型

    返回可用的警示類型列表及其說明
    """
    try:
        from app.services.price_alert import PriceAlertService

        types = PriceAlertService.get_alert_types()

        return {
            "success": True,
            "types": types,
            "count": len(types),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得警示類型失敗: {str(e)}")


# ============================================================
# 交易記錄與持股分析 API (V10.20)
# ============================================================

from pydantic import BaseModel
from typing import Dict


class TransactionRequest(BaseModel):
    """交易記錄請求模型"""
    transactions: List[Dict]


@router.post("/transactions/calculate-holdings")
async def calculate_holdings(request: TransactionRequest):
    """
    計算持股狀況（使用平均成本法）

    Body 參數:
    ```json
    {
        "transactions": [
            {
                "stock_id": "2330",
                "name": "台積電",
                "type": "buy",        // buy, sell, dividend
                "shares": 1000,       // 股數
                "price": 580,         // 成交價
                "fee": 82,            // 手續費
                "tax": 0,             // 交易稅（賣出時）
                "date": "2026-01-09", // 交易日期
                "note": "定期定額"    // 備註（選填）
            }
        ]
    }
    ```

    Returns:
        - holdings: 各股持股資訊
        - summary: 持股總覽
    """
    try:
        from app.services.transaction_service import TransactionService

        result = TransactionService.calculate_holdings(request.transactions)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算持股失敗: {str(e)}")


@router.post("/transactions/analyze")
async def analyze_holdings(request: TransactionRequest):
    """
    分析持股損益（含即時市值）

    根據交易記錄計算持股狀況，並取得即時價格計算損益

    Returns:
        - holdings: 持股詳細資訊（含損益）
        - summary: 投組總覽（總成本、總市值、總損益）
        - performance: 績效指標（總報酬率、最佳/最差持股）
    """
    try:
        from app.services.transaction_service import TransactionService

        result = await TransactionService.analyze_holdings(request.transactions)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析持股失敗: {str(e)}")


@router.post("/transactions/summary")
async def get_transaction_summary(
    request: TransactionRequest,
    stock_id: Optional[str] = Query(default=None, description="指定股票代號（可選）")
):
    """
    計算交易摘要

    提供買入/賣出總額、手續費/稅金統計、月度交易統計

    Returns:
        - total_buy: 總買入金額
        - total_sell: 總賣出金額
        - total_fee: 總手續費
        - total_tax: 總交易稅
        - total_dividends: 總股息
        - net_investment: 淨投資額
        - transactions_by_month: 月度交易統計
    """
    try:
        from app.services.transaction_service import TransactionService

        result = TransactionService.calculate_transaction_summary(
            request.transactions,
            stock_id
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算交易摘要失敗: {str(e)}")


@router.get("/transactions/types")
async def get_transaction_types():
    """
    取得所有交易類型

    Returns:
        - types: 交易類型列表（buy/sell/dividend）
    """
    try:
        from app.services.transaction_service import TransactionService

        types = TransactionService.get_transaction_types()

        return {
            "success": True,
            "types": types,
            "count": len(types),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得交易類型失敗: {str(e)}")


@router.get("/transactions/calculate-fee")
async def calculate_fee_and_tax(
    tx_type: str = Query(..., description="交易類型: buy/sell"),
    shares: float = Query(..., ge=0, description="股數"),
    price: float = Query(..., ge=0, description="成交價"),
    fee_discount: float = Query(default=0.6, ge=0, le=1, description="手續費折扣（0.6 = 6折）")
):
    """
    計算手續費與交易稅

    手續費率：0.1425%（依折扣調整）
    證券交易稅：0.3%（僅賣出時）

    Example:
        - /transactions/calculate-fee?tx_type=buy&shares=1000&price=580
        - /transactions/calculate-fee?tx_type=sell&shares=1000&price=600&fee_discount=0.5
    """
    try:
        from app.services.transaction_service import TransactionService

        result = TransactionService.calculate_fee_and_tax(
            tx_type=tx_type,
            shares=shares,
            price=price,
            fee_discount=fee_discount,
        )

        return {
            "success": True,
            "tx_type": tx_type,
            "shares": shares,
            "price": price,
            "fee_discount": fee_discount,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"計算費用失敗: {str(e)}")


# ============================================================
# 自選股分類群組 API (V10.21)
# ============================================================

class CategoryAnalyzeRequest(BaseModel):
    """分類分析請求模型"""
    categories: List[Dict]
    stocks_by_category: Dict[str, List[Dict]]


@router.get("/categories/defaults")
async def get_default_categories():
    """
    取得預設分類模板

    返回系統預設的分類模板，可直接使用或作為建立自訂分類的參考

    Returns:
        - categories: 預設分類列表
    """
    try:
        from app.services.watchlist_category import WatchlistCategoryService

        categories = WatchlistCategoryService.get_default_categories()

        return {
            "success": True,
            "count": len(categories),
            "categories": categories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得預設分類失敗: {str(e)}")


@router.get("/categories/colors")
async def get_available_colors():
    """
    取得可用顏色列表

    返回所有可用於分類的顏色配置

    Returns:
        - colors: 顏色列表（含色碼）
    """
    try:
        from app.services.watchlist_category import WatchlistCategoryService

        colors = WatchlistCategoryService.get_available_colors()

        return {
            "success": True,
            "count": len(colors),
            "colors": colors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得顏色列表失敗: {str(e)}")


@router.get("/categories/icons")
async def get_available_icons():
    """
    取得可用圖示列表

    返回所有可用於分類的圖示

    Returns:
        - icons: 圖示列表
    """
    try:
        from app.services.watchlist_category import WatchlistCategoryService

        icons = WatchlistCategoryService.get_available_icons()

        return {
            "success": True,
            "count": len(icons),
            "icons": icons,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得圖示列表失敗: {str(e)}")


@router.post("/categories/validate")
async def validate_category(category: Dict):
    """
    驗證分類資料

    Body 參數:
    ```json
    {
        "name": "分類名稱",
        "description": "描述",
        "color": "blue",
        "icon": "📈"
    }
    ```

    Returns:
        - valid: 是否有效
        - errors: 錯誤訊息（如有）
    """
    try:
        from app.services.watchlist_category import WatchlistCategoryService

        result = WatchlistCategoryService.validate_category(category)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"驗證失敗: {str(e)}")


@router.post("/categories/analyze")
async def analyze_categories(request: CategoryAnalyzeRequest):
    """
    分析分類統計

    Body 參數:
    ```json
    {
        "categories": [{"id": "cat1", "name": "分類1", ...}],
        "stocks_by_category": {
            "cat1": [{"stock_id": "2330"}, {"stock_id": "2317"}]
        }
    }
    ```

    Returns:
        - total_categories: 分類數量
        - total_stocks: 股票總數
        - category_stats: 各分類統計
        - distribution: 分佈比例
    """
    try:
        from app.services.watchlist_category import WatchlistCategoryService

        result = WatchlistCategoryService.analyze_categories(
            request.categories,
            request.stocks_by_category
        )

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.post("/categories/suggest")
async def suggest_category(stock_info: Dict):
    """
    根據股票資訊建議分類

    Body 參數:
    ```json
    {
        "stock_id": "2330",
        "dividend_yield": 2.5,
        "pe_ratio": 15,
        "technical_score": 72
    }
    ```

    Returns:
        - suggested_category: 建議分類 ID
        - reason: 建議原因
    """
    try:
        from app.services.watchlist_category import WatchlistCategoryService

        result = WatchlistCategoryService.suggest_category(stock_info)

        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建議失敗: {str(e)}")
