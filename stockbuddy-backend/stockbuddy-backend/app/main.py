"""
StockBuddy API 主程式
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import stocks
from .services.twse_api import get_twse_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    print("🚀 StockBuddy API 啟動中...")
    yield
    # 關閉時
    twse = await get_twse_service()
    await twse.close()
    print("👋 StockBuddy API 已關閉")


app = FastAPI(
    title="StockBuddy API",
    description="智能選股助手 API - 提供台股資料、技術分析、AI 推薦",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 設定（允許前端跨域請求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 開發伺服器
        "http://localhost:5173",  # Vite 開發伺服器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(stocks.router)


@app.get("/")
async def root():
    """API 首頁"""
    return {
        "name": "StockBuddy API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "股票資訊": "/api/stocks/info/{stock_id}",
            "歷史K線": "/api/stocks/history/{stock_id}",
            "技術分析": "/api/stocks/analysis/{stock_id}",
            "三大法人": "/api/stocks/institutional",
            "個股法人": "/api/stocks/institutional/{stock_id}",
            "大盤概況": "/api/stocks/market",
            "AI推薦": "/api/stocks/recommend",
            "搜尋股票": "/api/stocks/search?q=台積",
        }
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy"}


# 開發用：直接執行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
