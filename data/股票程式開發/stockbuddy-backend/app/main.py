"""
StockBuddy API 主程式
V10.15 - 新增擴展 API（匯出、績效分析、櫃買股票）
V10.37 - 安全性修復：CORS、環境變數、日誌系統、速率限制
V10.38 - 新增 SQLite 資料庫支援、JWT 認證、錯誤監控
"""

import os
import logging
from fastapi import FastAPI, Request

# V10.38: Sentry 錯誤監控
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    SENTRY_ENABLED = True
except ImportError:
    SENTRY_ENABLED = False
    sentry_sdk = None
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# V10.38: 初始化 Sentry 錯誤監控
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_ENABLED and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.1")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_RATE", "0.1")),
        environment=os.getenv("ENVIRONMENT", "development"),
        release=f"stockbuddy@10.38.0",
    )

# V10.37: 速率限制
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMIT_ENABLED = True
except ImportError:
    RATE_LIMIT_ENABLED = False
    Limiter = None

from .routers import stocks
from .routers import extended_api  # V10.15 新增
# V10.37: 拆分路由
from .routers import risk_routes
from .routers import ml_routes
from .routers import performance_routes
from .routers import us_stock_routes
# V10.38: 身份驗證路由
from .routers import auth_routes
# V10.38: 優化服務路由
from .routers import optimization_routes
# V10.38: API 版本控制
from .routers import api_v1
from .services.twse_api import get_twse_service

# V10.38: 資料庫支援
try:
    from .database import init_db, check_db_status
    DATABASE_ENABLED = True
except ImportError as e:
    DATABASE_ENABLED = False
    logger_msg = f"⚠️ 資料庫模組載入失敗: {e}"

# 設定日誌系統
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stockbuddy.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    logger.info("🚀 StockBuddy API V10.38 啟動中...")
    logger.info("📊 功能：股票資料、AI 推薦、績效分析、匯出、風險管理、ML 預測")

    # V10.38: 初始化資料庫
    if DATABASE_ENABLED:
        try:
            init_db()
            logger.info("✅ SQLite 資料庫初始化完成")
        except Exception as e:
            logger.error(f"❌ 資料庫初始化失敗: {e}")
    else:
        logger.warning("⚠️ 資料庫模組未啟用")

    # V10.38: Sentry 狀態
    if SENTRY_ENABLED and SENTRY_DSN:
        logger.info("✅ Sentry 錯誤監控已啟用")
    else:
        logger.info("⚠️ Sentry 未設定 (設定 SENTRY_DSN 環境變數以啟用)")

    yield
    # 關閉時
    twse = await get_twse_service()
    await twse.close()
    logger.info("👋 StockBuddy API 已關閉")


app = FastAPI(
    title="StockBuddy API",
    description="智能選股助手 API - 提供台股資料、技術分析、AI 推薦、績效分析、匯出功能",
    version="10.38.0",
    lifespan=lifespan,
)

# V10.37: 從環境變數讀取允許的來源，移除 "*" 安全漏洞
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# CORS 設定（僅允許特定前端來源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# V10.37: 速率限制（防止 API 濫用）
if RATE_LIMIT_ENABLED and Limiter:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ 速率限制已啟用 (100 requests/minute)")
else:
    logger.warning("⚠️ 速率限制未啟用 (請安裝 slowapi)")

# 註冊路由
app.include_router(stocks.router)
app.include_router(extended_api.router)  # V10.15 擴展 API
# V10.37: 拆分路由（提高可維護性）
app.include_router(risk_routes.router)
app.include_router(ml_routes.router)
app.include_router(performance_routes.router)
app.include_router(us_stock_routes.router)
# V10.38: 身份驗證路由
app.include_router(auth_routes.router)
# V10.38: 優化服務路由
app.include_router(optimization_routes.router)
# V10.38: API 版本控制
app.include_router(api_v1.router)


@app.get("/")
async def root():
    """API 首頁"""
    return {
        "name": "StockBuddy API",
        "version": "10.38.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "基本功能": {
                "股票資訊": "/api/stocks/info/{stock_id}",
                "歷史K線": "/api/stocks/history/{stock_id}",
                "技術分析": "/api/stocks/analysis/{stock_id}",
                "三大法人": "/api/stocks/institutional",
                "個股法人": "/api/stocks/institutional/{stock_id}",
                "大盤概況": "/api/stocks/market",
                "AI推薦": "/api/stocks/recommend",
                "搜尋股票": "/api/stocks/search?q=台積",
            },
            "V10.15 新增": {
                "績效分析": "/api/stocks/performance/{stock_id}",
                "月報酬熱力圖": "/api/stocks/performance/{stock_id}/monthly-heatmap",
                "風險指標": "/api/stocks/performance/{stock_id}/risk-metrics",
                "匯出CSV": "/api/stocks/export/recommendations/csv",
                "匯出Excel": "/api/stocks/export/recommendations/excel",
                "上櫃股票": "/api/stocks/otc/all",
                "資料狀態": "/api/stocks/data-status",
                "法人追蹤": "/api/stocks/institutional-tracking/{stock_id}",
            }
        }
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy"}


@app.get("/db-status")
async def database_status():
    """V10.38: 資料庫狀態檢查"""
    if DATABASE_ENABLED:
        return check_db_status()
    else:
        return {"status": "disabled", "message": "資料庫模組未啟用"}


@app.get("/sentry-status")
async def sentry_status():
    """V10.38: Sentry 狀態檢查"""
    return {
        "enabled": SENTRY_ENABLED and bool(SENTRY_DSN),
        "sdk_installed": SENTRY_ENABLED,
        "dsn_configured": bool(SENTRY_DSN),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@app.get("/sentry-test")
async def sentry_test_error():
    """V10.38: Sentry 測試端點 (僅開發環境)"""
    if os.getenv("ENVIRONMENT", "development") != "development":
        return {"error": "只能在開發環境使用此端點"}

    if SENTRY_ENABLED and SENTRY_DSN:
        try:
            # 觸發測試錯誤
            raise ValueError("Sentry 測試錯誤 - 此為正常測試")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return {"status": "error_captured", "message": "測試錯誤已發送到 Sentry"}

    return {"status": "sentry_not_enabled", "message": "Sentry 未啟用"}


# 開發用：直接執行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
