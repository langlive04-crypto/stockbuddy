"""
V10.37: 美股 API 路由
從 stocks.py 拆分出來，提高可維護性
"""

import asyncio
from datetime import datetime
from fastapi import APIRouter
from typing import List

from app.services.us_stock_service import USStockService
from app.services.us_technical_analysis import USTechnicalAnalysis

router = APIRouter(prefix="/api/stocks/us", tags=["us-stocks"])


# =============================================================================
# V10.24: 美股基本 API
# =============================================================================

@router.get("/market-status")
async def get_us_market_status():
    """
    V10.24: 取得美股市場狀態
    """
    return USStockService.is_market_open()


@router.get("/indices")
async def get_us_market_indices():
    """
    V10.24: 取得美股主要指數
    """
    try:
        indices = await USStockService.get_market_indices()
        return {
            "success": True,
            "data": indices,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/stock/{symbol}")
async def get_us_stock_info(symbol: str):
    """
    V10.24: 取得美股個股資訊
    """
    try:
        info = await USStockService.get_stock_info(symbol)
        if info:
            return {"success": True, "data": info}
        return {"success": False, "error": f"找不到股票 {symbol}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/stock/{symbol}/history")
async def get_us_stock_history(symbol: str, months: int = 3):
    """
    V10.24: 取得美股歷史K線資料
    """
    try:
        history = await USStockService.get_stock_history(symbol, months)
        return {
            "success": True,
            "data": history,
            "count": len(history)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/stock/{symbol}/profile")
async def get_us_company_profile(symbol: str):
    """
    V10.24: 取得美股公司詳細資料
    """
    try:
        profile = await USStockService.get_company_profile(symbol)
        if profile:
            return {"success": True, "data": profile}
        return {"success": False, "error": f"找不到公司資料 {symbol}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/search")
async def search_us_stocks(q: str):
    """
    V10.24: 搜尋美股
    """
    try:
        results = await USStockService.search_stock(q)
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/hot")
async def get_us_hot_stocks():
    """
    V10.24: 取得熱門美股
    """
    try:
        stocks = await USStockService.get_hot_stocks()
        return {
            "success": True,
            "data": stocks,
            "count": len(stocks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/movers")
async def get_us_top_movers():
    """
    V10.24: 取得美股漲跌幅排行
    """
    try:
        movers = await USStockService.get_top_movers()
        return {
            "success": True,
            "data": movers
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/sector/{sector}")
async def get_us_sector_stocks(sector: str):
    """
    V10.24: 取得特定產業的美股
    可用產業: technology, semiconductor, finance, consumer, healthcare, communication, energy, ai_concept
    """
    try:
        stocks = await USStockService.get_sector_stocks(sector)
        return {
            "success": True,
            "data": stocks,
            "sector": sector,
            "count": len(stocks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/batch")
async def get_us_batch_stocks(symbols: List[str]):
    """
    V10.24: 批次取得多檔美股資訊
    """
    try:
        stocks = await USStockService.get_multiple_stocks(symbols)
        return {
            "success": True,
            "data": stocks,
            "count": len(stocks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/popular-list")
async def get_us_popular_list():
    """
    V10.24: 取得熱門美股清單（僅代號和名稱）
    """
    return {
        "success": True,
        "data": [
            {"symbol": symbol, "name": name}
            for symbol, name in USStockService.POPULAR_US_STOCKS.items()
        ],
        "sectors": list(USStockService.SECTORS.keys())
    }


# =============================================================================
# V10.27: 美股技術分析 API
# =============================================================================

@router.get("/stock/{symbol}/technical")
async def get_us_technical_analysis(symbol: str):
    """
    V10.27: 取得美股技術分析
    包含: RSI, MACD, KD, 移動平均線, 布林通道, 支撐/壓力位
    """
    try:
        analysis = await USTechnicalAnalysis.analyze(symbol)
        if analysis:
            return {
                "success": True,
                "data": {
                    "symbol": analysis.symbol,
                    "date": analysis.date,
                    "rsi": {
                        "value": analysis.rsi,
                        "signal": analysis.rsi_signal
                    },
                    "macd": {
                        "macd": analysis.macd,
                        "signal": analysis.macd_signal,
                        "histogram": analysis.macd_histogram,
                        "cross": analysis.macd_cross
                    },
                    "kd": {
                        "k": analysis.k,
                        "d": analysis.d,
                        "signal": analysis.kd_signal
                    },
                    "ma": {
                        "ma5": analysis.ma5,
                        "ma10": analysis.ma10,
                        "ma20": analysis.ma20,
                        "ma60": analysis.ma60,
                        "trend": analysis.ma_trend
                    },
                    "bollinger": {
                        "upper": analysis.bb_upper,
                        "middle": analysis.bb_middle,
                        "lower": analysis.bb_lower,
                        "position": analysis.bb_position
                    },
                    "support_resistance": {
                        "support": analysis.support,
                        "resistance": analysis.resistance
                    },
                    "summary": {
                        "score": analysis.technical_score,
                        "recommendation": analysis.recommendation
                    }
                }
            }
        return {"success": False, "error": f"無法取得 {symbol} 技術分析資料，請確認股票代號正確且有足夠歷史資料"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/technical/batch")
async def get_us_batch_technical(symbols: List[str]):
    """
    V10.27: 批次取得多檔美股技術分析
    """
    try:
        # 並行分析多檔股票
        tasks = [USTechnicalAnalysis.analyze(symbol) for symbol in symbols[:10]]  # 限制最多10檔
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = []
        for symbol, result in zip(symbols[:10], results):
            if isinstance(result, Exception):
                data.append({"symbol": symbol, "error": str(result)})
            elif result:
                data.append({
                    "symbol": result.symbol,
                    "score": result.technical_score,
                    "recommendation": result.recommendation,
                    "rsi": result.rsi,
                    "macd_cross": result.macd_cross,
                    "ma_trend": result.ma_trend
                })
            else:
                data.append({"symbol": symbol, "error": "資料不足"})

        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
