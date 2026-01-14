"""
V10.37: 風險管理 API 路由
從 stocks.py 拆分出來，提高可維護性
"""

from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter(prefix="/api/stocks/risk", tags=["risk"])


@router.get("/stop-loss/{stock_id}")
async def get_risk_stop_loss(
    stock_id: str,
    entry_price: Optional[float] = Query(None, description="進場價格，若無則使用當前價")
):
    """
    V10.36: 取得止損止盈建議

    基於 ATR 計算止損價位和三階段獲利目標
    """
    try:
        from app.services.risk_calculator import get_stop_loss_target

        # 如果沒有提供進場價格，嘗試取得當前價格
        atr = None
        if entry_price is None:
            try:
                import yfinance as yf
                ticker = yf.Ticker(f"{stock_id}.TW")
                hist = ticker.history(period="5d")
                if not hist.empty:
                    entry_price = float(hist['Close'].iloc[-1])

                    # 計算 ATR
                    if len(hist) >= 5:
                        high = hist['High']
                        low = hist['Low']
                        close = hist['Close']
                        tr = []
                        for i in range(1, len(hist)):
                            tr.append(max(
                                high.iloc[i] - low.iloc[i],
                                abs(high.iloc[i] - close.iloc[i-1]),
                                abs(low.iloc[i] - close.iloc[i-1])
                            ))
                        atr = sum(tr) / len(tr) if tr else None
                else:
                    return {"success": False, "error": f"無法取得 {stock_id} 價格資料"}
            except Exception as e:
                return {"success": False, "error": f"取得價格失敗: {str(e)}"}

        result = get_stop_loss_target(stock_id, entry_price, atr=atr)
        return {"success": True, **result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/position-size")
async def get_risk_position_size(
    win_rate: float = Query(0.5, ge=0, le=1, description="勝率 (0-1)"),
    avg_win: float = Query(10.0, ge=0, description="平均獲利 (%)"),
    avg_loss: float = Query(5.0, ge=0, description="平均虧損 (%)"),
    capital: float = Query(1000000, ge=0, description="當前資金"),
    risk_tolerance: str = Query("moderate", description="風險偏好: conservative/moderate/aggressive")
):
    """
    V10.36: 計算建議倉位

    使用凱利公式計算最佳倉位比例
    """
    try:
        from app.services.risk_calculator import get_position_size

        result = get_position_size(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            capital=capital,
            risk_tolerance=risk_tolerance
        )
        return {"success": True, **result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/portfolio-assessment")
async def assess_portfolio_risk(holdings: List[dict]):
    """
    V10.36: 評估投資組合風險

    分析產業集中度、分散度、風險警告

    Request Body 範例:
    [
        {"stock_id": "2330", "stock_name": "台積電", "market_value": 500000, "industry": "半導體"},
        {"stock_id": "2317", "stock_name": "鴻海", "market_value": 200000, "industry": "電子"}
    ]
    """
    try:
        from app.services.risk_calculator import assess_portfolio

        result = assess_portfolio(holdings)
        return {"success": True, **result}

    except Exception as e:
        return {"success": False, "error": str(e)}
