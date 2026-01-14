"""
股票相關 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ..services.github_data import SmartStockService as StockDataService  # 智能選擇資料源
from ..services.technical_analysis import TechnicalAnalysis
from ..services.themes import get_stock_info as get_stock_tags  # 產業標籤（只顯示，不影響評分）
from ..services.news_service import get_news_service  # 新聞服務
from ..services.cache_service import StockCache  # 快取服務
from ..services.fundamental_service import FundamentalService  # 基本面分析
from ..services.institutional_service import InstitutionalService, MarginService  # 籌碼面分析（備用）
from ..services.finmind_service import FinMindService  # FinMind API（主要資料源）
from ..services.ai_stock_picker import AIStockPicker, get_ai_top_picks  # 🤖 AI 選股引擎
from ..services.twse_openapi import TWSEOpenAPI  # 🆕 TWSE OpenAPI（V10.7）
from ..services.scoring_service import ScoringService  # 🆕 V10.9 多維度評分

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

# ============================================================
# 🆕 V10.13.3: 全局籌碼快取（供股票分析 Tab 共用）
# ============================================================
import time

class ChipDataCache:
    """籌碼數據全局快取，讓股票分析 Tab 共用 TWSE 預取數據"""
    _institutional_data: dict = {}  # 三大法人
    _margin_data: dict = {}  # 融資融券
    _last_update: float = 0
    _cache_ttl: int = 600  # 10 分鐘
    
    @classmethod
    def set_institutional(cls, data: dict):
        """設定三大法人快取"""
        cls._institutional_data = data or {}
        cls._last_update = time.time()
        print(f"📦 [ChipCache] 三大法人快取已更新: {len(cls._institutional_data)} 檔")
    
    @classmethod
    def set_margin(cls, data: dict):
        """設定融資融券快取"""
        cls._margin_data = data or {}
        print(f"📦 [ChipCache] 融資融券快取已更新: {len(cls._margin_data)} 檔")
    
    @classmethod
    def get_institutional(cls, stock_id: str) -> dict:
        """取得單檔三大法人數據"""
        if cls._is_expired():
            return None
        return cls._institutional_data.get(stock_id)
    
    @classmethod
    def get_margin(cls, stock_id: str) -> dict:
        """取得單檔融資融券數據"""
        if cls._is_expired():
            return None
        return cls._margin_data.get(stock_id)
    
    @classmethod
    def get_all_institutional(cls) -> dict:
        """取得全部三大法人數據"""
        if cls._is_expired():
            return {}
        return cls._institutional_data
    
    @classmethod
    def get_all_margin(cls) -> dict:
        """取得全部融資融券數據"""
        if cls._is_expired():
            return {}
        return cls._margin_data
    
    @classmethod
    def _is_expired(cls) -> bool:
        """檢查快取是否過期"""
        return time.time() - cls._last_update > cls._cache_ttl
    
    @classmethod
    def clear(cls):
        """🆕 V10.13.4: 強制清除所有快取"""
        cls._institutional_data = {}
        cls._margin_data = {}
        cls._last_update = 0
        print("🗑️ [ChipCache] 所有快取已清除")
    
    @classmethod
    def is_available(cls) -> bool:
        """檢查快取是否可用"""
        return len(cls._institutional_data) > 0 and not cls._is_expired()
# ============================================================


# ============================================================
# 🆕 V10.13.4: 強制清除快取 API
# ============================================================
@router.post("/clear-cache")
async def clear_all_cache():
    """
    強制清除所有快取，重新從 API 獲取最新資料
    """
    import shutil
    import os
    
    cleared_items = []
    
    # 1. 清除 ChipDataCache
    ChipDataCache.clear()
    cleared_items.append("籌碼快取")
    
    # 2. 清除 StockCache（如果有）
    try:
        StockCache.clear_all()
        cleared_items.append("股票快取")
    except:
        pass
    
    # 3. 清除 TWSE OpenAPI 快取
    try:
        TWSEOpenAPI.clear_cache()
        cleared_items.append("TWSE 快取")
    except:
        pass
    
    # 4. 清除 yfinance 快取（本地檔案）
    try:
        yf_cache_path = os.path.expanduser("~/.cache/py-yfinance")
        if os.path.exists(yf_cache_path):
            shutil.rmtree(yf_cache_path)
            cleared_items.append("yfinance 快取")
    except:
        pass
    
    print(f"🗑️ [ClearCache] 已清除: {', '.join(cleared_items)}")
    
    return {
        "success": True,
        "message": f"已清除快取: {', '.join(cleared_items)}",
        "cleared": cleared_items,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/info/{stock_id}")
async def get_stock_info(stock_id: str):
    """
    取得個股即時資訊
    """
    info = await StockDataService.get_stock_info(stock_id)
    
    if not info:
        raise HTTPException(status_code=404, detail=f"找不到股票 {stock_id}")
    
    # 🆕 V10.13.4: 確保返回股票名稱
    if not info.get("name") or info.get("name") == stock_id:
        # 嘗試從 TWSE 或其他來源取得名稱
        try:
            twse_data = await TWSEOpenAPI.get_stock_summary()
            if twse_data and stock_id in twse_data:
                info["name"] = twse_data[stock_id].get("name", stock_id)
        except:
            pass
    
    return info


# ============================================================
# 🆕 V10.13.4: 股票完整評分端點
# ============================================================
@router.get("/score/{stock_id}")
async def get_stock_score(stock_id: str):
    """
    取得股票完整四維評分
    與 AI 精選使用相同的評分邏輯和資料來源
    """
    import asyncio
    from app.services.twse_bulk import get_bulk_service
    
    bulk_service = get_bulk_service()
    
    # 🆕 V10.13.4: 使用和 AI 精選相同的資料來源
    history_task = bulk_service.get_stock_history_yf(stock_id, months=2)
    info_task = StockDataService.get_stock_info(stock_id)
    twse_task = TWSEOpenAPI.get_all_stocks_summary()  # 🆕 V10.13.4: 獲取 TWSE 基本面資料
    
    history, info, twse_data = await asyncio.gather(
        history_task, info_task, twse_task
    )
    
    # 🆕 V10.13.4: 從 TWSE OpenAPI 獲取基本面（和 AI 精選一致）
    twse_stock = twse_data.get(stock_id, {}) if twse_data else {}
    
    # 取得股票名稱（多來源 - V10.13.4 改進）
    stock_name = twse_stock.get("name") or (info.get("name") if info else None)
    
    # 來源 2: 從 ChipDataCache 取得（三大法人資料也有名稱）
    if not stock_name or stock_name == stock_id:
        inst_cache = ChipDataCache.get_institutional(stock_id)
        if inst_cache:
            stock_name = inst_cache.get("name", stock_id)
    
    # 最後 fallback
    if not stock_name:
        stock_name = stock_id
    
    # ===== 1. 技術面分數（V10.13.4 修正：使用和 AI 精選相同的 overall_score）=====
    tech_score = 50
    tech_details = {}
    reason_parts = []
    
    if history and len(history) >= 20:
        analysis = TechnicalAnalysis.full_analysis(history)
        
        # 🆕 V10.13.4: 使用和 AI 精選相同的 overall_score
        tech_score = analysis.get("overall_score", 50)
        
        # 收集技術分析詳情
        rsi = analysis.get("rsi", {})
        rsi_value = rsi.get("value", 50)
        macd = analysis.get("macd", {})
        macd_signal = macd.get("signal", "")
        ma = analysis.get("ma", {})
        ma_trend = ma.get("trend", "")
        volume = analysis.get("volume", {})
        vol_ratio = volume.get("ratio", 1)
        
        # 收集理由說明
        if macd_signal in ["金叉", "多方"]:
            reason_parts.append(f"MACD {macd_signal}")
        elif macd_signal in ["死叉", "空方"]:
            reason_parts.append(f"MACD {macd_signal}")
        
        if rsi_value < 30:
            reason_parts.append("RSI 超賣")
        elif rsi_value > 70:
            reason_parts.append("RSI 超買")
        
        if "多頭" in ma_trend or "強勢" in ma_trend:
            reason_parts.append("均線多頭")
        
        if vol_ratio > 2:
            reason_parts.append("量能放大")
        elif vol_ratio > 1.5:
            reason_parts.append("量增")
        
        tech_details = {
            "rsi": rsi_value,
            "macd": macd_signal,
            "ma_trend": ma_trend,
            "volume_ratio": vol_ratio
        }
    else:
        reason_parts.append("歷史資料不足")
    
    tech_score = max(20, min(90, tech_score))
    
    # ===== 2. 基本面分數（V10.13.4: 使用 TWSE OpenAPI，和 AI 精選一致）=====
    fundamental_score = 50
    if twse_stock:
        fundamental_result = ScoringService.calculate_fundamental_score(
            pe_ratio=twse_stock.get("pe_ratio"),
            pb_ratio=twse_stock.get("pb_ratio"),
            dividend_yield=twse_stock.get("dividend_yield"),
        )
        fundamental_score = fundamental_result["score"]
        fund_summary = fundamental_result.get("summary", "")
        if fund_summary and fund_summary != "基本面中性":
            reason_parts.append(fund_summary)
    
    # ===== 3. 籌碼面分數 =====
    chip_score = 50
    inst_data = ChipDataCache.get_institutional(stock_id)
    
    # 如果快取沒有，嘗試 FinMind fallback
    if not inst_data:
        try:
            finmind_data = await FinMindService.get_latest_institutional(stock_id)
            if finmind_data and finmind_data.get("is_real_data"):
                inst_data = {
                    "foreign_net": finmind_data.get("foreign_net", 0),
                    "trust_net": finmind_data.get("trust_net", 0),
                    "dealer_net": finmind_data.get("dealer_net", 0),
                }
        except:
            pass
    
    if inst_data:
        chip_result = ScoringService.calculate_chip_score(
            foreign_net=inst_data.get("foreign_net"),
            trust_net=inst_data.get("trust_net"),
            dealer_net=inst_data.get("dealer_net"),
        )
        chip_score = chip_result["score"]
        chip_summary = chip_result.get("summary", "")
        if chip_summary and chip_summary != "籌碼中性":
            reason_parts.append(chip_summary)
        
        # 🆕 V10.13.4: 融資融券加分（與 AI 精選一致）
        margin_data = ChipDataCache.get_margin(stock_id)
        if margin_data:
            margin_buy = margin_data.get("margin_buy", 0) or 0
            margin_sell = margin_data.get("margin_sell", 0) or 0
            short_balance = margin_data.get("short_balance", 0) or 0
            margin_balance = margin_data.get("margin_balance", 0) or 0
            
            # 融資減少 = 籌碼沉澱
            if margin_sell > margin_buy + 500:
                chip_score = min(85, chip_score + 6)
                reason_parts.append("融資減少")
            
            # 券資比高 = 軋空潛力
            if margin_balance > 0:
                short_ratio = (short_balance / margin_balance) * 100
                if short_ratio > 30:
                    chip_score = min(85, chip_score + 8)
                    reason_parts.append("高券資比")
                elif short_ratio > 20:
                    chip_score = min(85, chip_score + 4)
    
    # ===== 4. 新聞面分數（V10.13.4: 使用和 AI 精選相同的邏輯）=====
    news_score = 50
    stock_tags = get_stock_tags(stock_id)  # 提前初始化
    try:
        news_service = get_news_service()
        
        news_list = []
        # 方案 1：使用產業新聞（較快，和 AI 精選一致）
        industry = stock_tags.get("industry", "")
        if industry:
            news_list = await news_service.get_industry_news(industry, limit=5)
        
        # 方案 2：如果沒有產業或產業新聞為空，使用股票名稱搜尋
        if not news_list and stock_name and stock_name != stock_id:
            news_list = await news_service.get_stock_news(stock_name, limit=3)
        
        if news_list:
            news_summary = news_service.get_news_summary(news_list)
            news_result = ScoringService.calculate_news_score(
                positive_count=news_summary.get("positive_count", 0),
                negative_count=news_summary.get("negative_count", 0),
                total_count=news_summary.get("total", 0),
                sentiment_trend=news_summary.get("trend", "neutral"),
            )
            news_score = news_result["score"]
    except:
        pass
    
    # ===== 5. 產業熱度（stock_tags 已在新聞分數計算時初始化）=====
    industry_bonus = 0
    try:
        industry_result = ScoringService.calculate_industry_bonus(
            industry=stock_tags.get("industry"),
            tags=stock_tags.get("tags", []),
        )
        industry_bonus = industry_result["bonus"]
        if industry_result.get("summary"):
            reason_parts.append(industry_result["summary"])
    except:
        pass
    
    # ===== 6. 計算最終分數 =====
    scoring_result = ScoringService.calculate_final_score(
        technical_score=tech_score,
        fundamental_score=fundamental_score,
        chip_score=chip_score,
        news_score=news_score,
        industry_bonus=industry_bonus,
    )
    final_score = scoring_result["final_score"]
    signal = scoring_result["signal"]
    
    # 組合理由
    reason = "、".join(reason_parts[:5]) if reason_parts else "資料分析中"
    
    return {
        "stock_id": stock_id,
        "name": stock_name,
        "scores": {
            "technical": tech_score,
            "fundamental": fundamental_score,
            "chip": chip_score,
            "news": news_score,
            "industry_bonus": industry_bonus,
            "total": final_score
        },
        "signal": signal,
        "reason": reason,
        "details": {
            "technical": tech_details,
            "has_chip_data": inst_data is not None,
            "has_fundamental": bool(twse_stock)
        }
    }


@router.get("/history/{stock_id}")
async def get_stock_history(
    stock_id: str,
    months: int = Query(default=3, ge=1, le=12, description="取得幾個月的資料")
):
    """
    取得個股歷史K線資料
    """
    history = await StockDataService.get_stock_history(stock_id, months)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"找不到股票 {stock_id} 的歷史資料")
    
    return {
        "stock_id": stock_id,
        "name": StockDataService.POPULAR_STOCKS.get(stock_id, stock_id),
        "count": len(history),
        "data": history
    }


@router.get("/analysis/{stock_id}")
async def get_stock_analysis(stock_id: str):
    """
    取得個股技術分析
    """
    # 取得歷史資料
    history = await StockDataService.get_stock_history(stock_id, months=3)
    
    if not history or len(history) < 20:
        raise HTTPException(
            status_code=400, 
            detail=f"股票 {stock_id} 歷史資料不足，無法進行技術分析（需要至少20天）"
        )
    
    # 技術分析
    analysis = TechnicalAnalysis.full_analysis(history)
    
    # 取得基本資訊
    info = await StockDataService.get_stock_info(stock_id)
    
    return {
        "stock_id": stock_id,
        "name": info.get("name", stock_id) if info else stock_id,
        "current_price": info.get("close") if info else history[-1]["close"],
        "change_percent": info.get("change_percent", 0) if info else 0,
        "analysis": analysis
    }


@router.get("/fundamental/{stock_id}")
async def get_fundamental_analysis(stock_id: str):
    """
    取得個股基本面分析
    - 本益比 (P/E)
    - 股價淨值比 (P/B)
    - 市值
    - 股息殖利率
    - 營收成長率
    - 毛利率/淨利率
    - ROE/ROA
    """
    data = await FundamentalService.get_fundamental_data(stock_id)
    
    # 取得股票名稱
    info = await StockDataService.get_stock_info(stock_id)
    
    return {
        "stock_id": stock_id,
        "name": info.get("name", stock_id) if info else stock_id,
        "fundamental": data
    }


@router.get("/institutional/{stock_id}")
async def get_institutional_data(stock_id: str):
    """
    取得三大法人買賣超資料
    🆕 V10.13.3: 優先使用 TWSE 全局快取，快取為空時主動預取
    - 外資
    - 投信
    - 自營商
    """
    # 取得股票名稱
    info = await StockDataService.get_stock_info(stock_id)
    stock_name = info.get("name", stock_id) if info else stock_id
    
    # 🆕 V10.13.3: 優先使用全局快取（TWSE 預取數據）
    cached_data = ChipDataCache.get_institutional(stock_id)
    
    # 如果快取為空或過期，主動預取 TWSE 數據
    if not cached_data and not ChipDataCache.is_available():
        print(f"📊 [ChipCache] 快取為空，主動預取 TWSE 三大法人...")
        try:
            all_inst_data = await TWSEOpenAPI.get_institutional_trading() or {}
            if all_inst_data:
                ChipDataCache.set_institutional(all_inst_data)
                cached_data = all_inst_data.get(stock_id)
        except Exception as e:
            print(f"⚠️ TWSE 預取失敗: {e}")
    
    if cached_data:
        print(f"📦 [ChipCache] 三大法人命中: {stock_id}")
        return {
            "stock_id": stock_id,
            "name": stock_name,
            "institutional": {
                "foreign_net": cached_data.get("foreign_net", 0),
                "foreign_net_display": f"{cached_data.get('foreign_net', 0):+,} 張",
                "trust_net": cached_data.get("trust_net", 0),
                "trust_net_display": f"{cached_data.get('trust_net', 0):+,} 張",
                "dealer_net": cached_data.get("dealer_net", 0),
                "dealer_net_display": f"{cached_data.get('dealer_net', 0):+,} 張",
                "total_net": cached_data.get("total_net", 0),
                "total_net_display": f"{cached_data.get('total_net', 0):+,} 張",
                "is_real_data": True,
                "data_source": "TWSE_Cache",
                "date": cached_data.get("date", ""),  # V10.13.4: 加入資料日期
            }
        }
    
    # Fallback: 使用 FinMind API（只在 TWSE 完全失敗時）
    try:
        data = await FinMindService.get_latest_institutional(stock_id)
        if data and data.get("is_real_data"):
            print(f"✅ FinMind 三大法人: {stock_id}")
            return {
                "stock_id": stock_id,
                "name": stock_name,
                "institutional": data
            }
    except Exception as e:
        print(f"⚠️ FinMind 失敗: {e}")
    
    # 最後 Fallback: 舊的服務
    print(f"⚠️ 使用備用籌碼服務: {stock_id}")
    data = await InstitutionalService.get_institutional_data(stock_id)
    
    return {
        "stock_id": stock_id,
        "name": stock_name,
        "institutional": data
    }


@router.get("/margin/{stock_id}")
async def get_margin_data(stock_id: str):
    """
    取得融資融券資料
    🆕 V10.13.3: 優先使用 TWSE 全局快取，快取為空時主動預取
    """
    # 🆕 V10.13.3: 優先使用全局快取
    cached_data = ChipDataCache.get_margin(stock_id)
    
    # 如果快取為空，主動預取 TWSE 數據
    if not cached_data and len(ChipDataCache.get_all_margin()) == 0:
        print(f"📊 [ChipCache] 融資融券快取為空，主動預取 TWSE...")
        try:
            all_margin_data = await TWSEOpenAPI.get_margin_trading() or {}
            if all_margin_data:
                ChipDataCache.set_margin(all_margin_data)
                cached_data = all_margin_data.get(stock_id)
        except Exception as e:
            print(f"⚠️ TWSE 融資融券預取失敗: {e}")
    
    if cached_data:
        print(f"📦 [ChipCache] 融資融券命中: {stock_id}")
        
        margin_balance = cached_data.get("margin_balance", 0) or 1
        short_balance = cached_data.get("short_balance", 0) or 0
        margin_short_ratio = round(short_balance / margin_balance * 100, 2) if margin_balance > 0 else 0
        
        # 計算變動（融資買-賣，融券賣-買）
        margin_change = (cached_data.get("margin_buy", 0) or 0) - (cached_data.get("margin_sell", 0) or 0)
        short_change = (cached_data.get("short_sell", 0) or 0) - (cached_data.get("short_buy", 0) or 0)
        
        result = {
            "date": cached_data.get("date", ""),
            "margin": {
                "buy": cached_data.get("margin_buy", 0),
                "sell": cached_data.get("margin_sell", 0),
                "balance": cached_data.get("margin_balance", 0),
                "change": margin_change,
                "change_display": f"{'+' if margin_change >= 0 else ''}{margin_change:,} 張",
            },
            "short": {
                "buy": cached_data.get("short_buy", 0),
                "sell": cached_data.get("short_sell", 0),
                "balance": cached_data.get("short_balance", 0),
                "change": short_change,
                "change_display": f"{'+' if short_change >= 0 else ''}{short_change:,} 張",
            },
            "margin_short_ratio": margin_short_ratio,
            "comment": _get_margin_comment(margin_short_ratio, margin_change),
            "is_real_data": True,
            "data_source": "TWSE_Cache"
        }
        return {"stock_id": stock_id, "margin_data": result}
    
    # Fallback: 使用 FinMind API
    try:
        data = await FinMindService.get_margin_trading(stock_id)
        if data and len(data) > 0:
            latest = data[0]  # 最新一筆
            margin_change = latest.get("margin_buy", 0) - latest.get("margin_sell", 0)
            short_change = latest.get("short_sell", 0) - latest.get("short_buy", 0)
            
            # 計算券資比
            margin_balance = latest.get("margin_balance", 0) or 1
            short_balance = latest.get("short_balance", 0) or 0
            margin_short_ratio = round(short_balance / margin_balance * 100, 2) if margin_balance > 0 else 0
            
            result = {
                "date": latest.get("date"),
                "margin": {
                    "buy": latest.get("margin_buy", 0),
                    "sell": latest.get("margin_sell", 0),
                    "balance": latest.get("margin_balance", 0),
                    "change": margin_change,
                    "change_display": f"{'+' if margin_change >= 0 else ''}{margin_change:,} 張",
                },
                "short": {
                    "buy": latest.get("short_buy", 0),
                    "sell": latest.get("short_sell", 0),
                    "balance": latest.get("short_balance", 0),
                    "change": short_change,
                    "change_display": f"{'+' if short_change >= 0 else ''}{short_change:,} 張",
                },
                "margin_short_ratio": margin_short_ratio,
                "comment": _get_margin_comment(margin_short_ratio, margin_change),
                "is_real_data": True,
            }
            
            print(f"✅ FinMind 融資融券: {stock_id}")
            return {"stock_id": stock_id, "margin_data": result}
    except Exception as e:
        print(f"⚠️ FinMind 融資融券失敗: {e}")
    
    # 最後 Fallback
    data = await MarginService.get_margin_data(stock_id)
    return {"stock_id": stock_id, "margin_data": data}


def _get_margin_comment(ratio: float, margin_change: int) -> str:
    """融資融券評論"""
    comments = []
    
    if ratio > 30:
        comments.append("券資比偏高，空方壓力大")
    elif ratio > 20:
        comments.append("券資比適中")
    elif ratio > 10:
        comments.append("融資偏多")
    else:
        comments.append("融資主導")
    
    if margin_change > 1000:
        comments.append("融資大增")
    elif margin_change > 0:
        comments.append("融資增加")
    elif margin_change < -1000:
        comments.append("融資大減")
    elif margin_change < 0:
        comments.append("融資減少")
    
    return "，".join(comments)


@router.get("/full-analysis/{stock_id}")
async def get_full_analysis(stock_id: str):
    """
    取得完整分析（技術面 + 基本面 + 籌碼面 + 新聞）
    🆕 V10.13.3: 優先使用 TWSE 全局快取
    """
    import asyncio
    
    # 🆕 V10.13.3: 先檢查全局快取
    cached_inst = ChipDataCache.get_institutional(stock_id)
    
    # 並行取得所有資料
    history_task = StockDataService.get_stock_history(stock_id, months=3)
    info_task = StockDataService.get_stock_info(stock_id)
    fundamental_task = FundamentalService.get_fundamental_data(stock_id)
    
    # 如果快取命中，不需要查詢 FinMind
    if cached_inst:
        print(f"📦 [ChipCache] full-analysis 三大法人命中: {stock_id}")
        history, info, fundamental = await asyncio.gather(
            history_task, info_task, fundamental_task
        )
        institutional = {
            "foreign_net": cached_inst.get("foreign_net", 0),
            "foreign_net_display": f"{cached_inst.get('foreign_net', 0):+,} 張",
            "trust_net": cached_inst.get("trust_net", 0),
            "trust_net_display": f"{cached_inst.get('trust_net', 0):+,} 張",
            "dealer_net": cached_inst.get("dealer_net", 0),
            "dealer_net_display": f"{cached_inst.get('dealer_net', 0):+,} 張",
            "total_net": cached_inst.get("total_net", 0),
            "total_net_display": f"{cached_inst.get('total_net', 0):+,} 張",
            "is_real_data": True,
            "data_source": "TWSE_Cache"
        }
    else:
        # 快取未命中，使用 FinMind
        institutional_task = FinMindService.get_latest_institutional(stock_id)
        history, info, fundamental, institutional = await asyncio.gather(
            history_task, info_task, fundamental_task, institutional_task
        )
        
        # 如果 FinMind 失敗，使用備用
        if not institutional or not institutional.get("is_real_data"):
            institutional = await InstitutionalService.get_institutional_data(stock_id)
    
    # 技術分析
    technical = None
    if history and len(history) >= 20:
        technical = TechnicalAnalysis.full_analysis(history)
    
    # 新聞
    news_service = get_news_service()
    news = await news_service.get_stock_news(stock_id, limit=5)
    news_summary = news_service.get_news_summary(news)
    
    # 產業標籤
    tags = get_stock_tags(stock_id)
    
    return {
        "stock_id": stock_id,
        "name": info.get("name", stock_id) if info else stock_id,
        "price": info.get("close") if info else None,
        "change_percent": info.get("change_percent", 0) if info else 0,
        "industry": tags.get("industry", ""),
        "tags": tags.get("tags", []),
        "technical": technical,
        "fundamental": fundamental,
        "institutional": institutional,
        "news": {
            "items": news,
            "summary": news_summary
        }
    }


@router.get("/market")
async def get_market_summary():
    """
    取得大盤概況
    """
    index = await StockDataService.get_market_index()
    
    if not index:
        raise HTTPException(status_code=500, detail="無法取得大盤資訊")
    
    # 根據漲跌判斷市場氛圍
    change_pct = index["change_percent"]
    if change_pct > 1:
        mood = "強勢"
        mood_icon = "🔴"
    elif change_pct > 0:
        mood = "偏多"
        mood_icon = "🟢"
    elif change_pct > -1:
        mood = "偏空"
        mood_icon = "🟡"
    else:
        mood = "弱勢"
        mood_icon = "🟢"  # 台股跌是綠色
    
    return {
        "date": index["date"],
        "taiex": {
            "value": index["value"],
            "change": index["change"],
            "change_percent": index["change_percent"],
        },
        "mood": mood,
        "mood_icon": mood_icon,
        "ai_comment": _generate_market_comment(index),
    }


def _generate_market_comment(index: dict) -> str:
    """生成大盤 AI 評論"""
    change_pct = index["change_percent"]
    
    if change_pct > 1.5:
        return "大盤強勢上攻，多方氣勢強勁，但須留意短線過熱風險。"
    elif change_pct > 0.5:
        return "大盤穩步上揚，市場信心回復，可留意強勢類股。"
    elif change_pct > 0:
        return "大盤小幅收紅，盤勢平穩，選股不選市。"
    elif change_pct > -0.5:
        return "大盤小幅回檔，屬正常整理，無須過度擔憂。"
    elif change_pct > -1.5:
        return "大盤明顯回檔，短線宜保守，留意支撐位。"
    else:
        return "大盤重挫，市場恐慌情緒升溫，建議降低持股水位。"


@router.get("/recommend")
async def get_recommendations():
    """
    取得 AI 推薦股票
    
    V10.7 更新：優先使用 TWSE OpenAPI（全市場掃描）
    
    資料源策略：
    1. TWSE OpenAPI（全市場 1000+ 檔）
    2. 備用：固定股票清單 + yfinance
    
    選股邏輯：
    1. 從資料源取得全市場當日行情
    2. 初篩：排除低價股、低成交量股、當日跌停股
    3. 依「當日漲幅 + 成交量」排序，取前 100 名做技術分析
    4. 技術分析評分後，產生 AI 精選 + 熱門股兩個清單
    """
    import asyncio
    from app.services.twse_bulk import get_bulk_service
    
    # 檢查快取
    cached_result = StockCache.get_recommendations()
    if cached_result:
        print("📦 使用快取資料")
        return cached_result
    
    all_stocks = {}
    data_source = "unknown"
    data_date = None  # 🆕 V10.13.5: 追蹤資料日期
    
    # ============================================================
    # Step 1: 優先使用 TWSE OpenAPI（V10.7 新增）
    # ============================================================
    print("📊 嘗試 TWSE OpenAPI（全市場掃描）...")
    try:
        twse_data = await TWSEOpenAPI.get_all_stocks_summary()
        if twse_data and len(twse_data) > 100:
            data_source = "TWSE_OpenAPI"
            print(f"✅ TWSE OpenAPI: 取得 {len(twse_data)} 檔股票")
            
            # 🆕 V10.13.5: 提取資料日期（從任一股票的 date 欄位）
            sample_stock = next(iter(twse_data.values()), {})
            raw_date = sample_stock.get("date", "")
            if raw_date and len(raw_date) >= 7:
                # 民國年格式 1141230 → 2025/12/30
                try:
                    roc_year = int(raw_date[:3])
                    month = raw_date[3:5]
                    day = raw_date[5:7]
                    ad_year = roc_year + 1911
                    data_date = f"{ad_year}/{month}/{day}"
                    print(f"📅 資料日期: {data_date}")
                except:
                    data_date = raw_date
            
            # 轉換格式
            for stock_id, info in twse_data.items():
                if info.get("price") and len(stock_id) == 4:
                    all_stocks[stock_id] = {
                        "stock_id": stock_id,
                        "name": info.get("name", stock_id),
                        "close": info.get("price"),
                        "open": info.get("open"),
                        "high": info.get("high"),
                        "low": info.get("low"),
                        "change": info.get("change"),
                        "change_percent": info.get("change_percent"),
                        "volume": info.get("volume"),
                        "pe_ratio": info.get("pe_ratio"),
                        "pb_ratio": info.get("pb_ratio"),
                        "dividend_yield": info.get("dividend_yield"),
                    }
            
            # 🆕 V10.13.4: 檢查資料日期是否為今天，如不是則用 yfinance 更新價格
            from datetime import date
            today_str = date.today().strftime("%Y%m%d")
            today_roc = str(date.today().year - 1911) + date.today().strftime("%m%d")  # 民國年格式
            
            # 抽樣檢查幾檔股票的價格是否為最新
            sample_stocks = ["2330", "2317", "2454", "2308"]  # 台積電、鴻海、聯發科、台達電
            bulk_service = get_bulk_service()
            needs_price_update = False
            
            for sample_id in sample_stocks:
                if sample_id in all_stocks:
                    try:
                        yf_data = await bulk_service.get_stock_history_yf(sample_id, months=1)
                        if yf_data and len(yf_data) > 0:
                            latest_yf = yf_data[-1]
                            twse_price = all_stocks[sample_id].get("close")
                            yf_price = latest_yf.get("close")
                            # 如果價格差異超過 1%，可能是 TWSE 資料過期
                            if twse_price and yf_price and abs(twse_price - yf_price) / yf_price > 0.01:
                                print(f"⚠️ [TWSE] 價格可能過期: {sample_id} TWSE={twse_price} vs YF={yf_price}")
                                needs_price_update = True
                                break
                    except:
                        pass
            
            if needs_price_update:
                print("🔄 [TWSE] 價格資料可能過期，將在技術分析時從 yfinance 更新...")
                data_source = "TWSE_OpenAPI(需更新)"
                    
    except Exception as e:
        print(f"⚠️ TWSE OpenAPI 失敗: {e}")
    
    # ============================================================
    # Step 2: 備用方案 - 舊的 TWSE bulk API
    # ============================================================
    if not all_stocks or len(all_stocks) < 100:
        print("📊 嘗試備用 TWSE API...")
        try:
            bulk_service = get_bulk_service()
            twse_stocks = await bulk_service.get_all_stocks_daily()
            if twse_stocks and len(twse_stocks) > 100:
                all_stocks = twse_stocks
                data_source = "TWSE_Bulk"
                print(f"✅ TWSE Bulk: 取得 {len(all_stocks)} 檔股票")
        except Exception as e:
            print(f"⚠️ TWSE Bulk 失敗: {e}")
    
    # ============================================================
    # Step 3: 最後備用方案（固定清單）
    # ============================================================
    if not all_stocks or len(all_stocks) < 100:
        print("⚠️ 所有 TWSE API 失敗，使用固定清單...")
        return await _fallback_recommend()
    
    print(f"✅ 使用 {data_source} 資料源，共 {len(all_stocks)} 檔股票")
    
    bulk_service = get_bulk_service()
    
    # ============================================================
    # Step 4: 初篩條件（V10.8 優化）
    # ============================================================
    candidates = []
    for stock_id, info in all_stocks.items():
        # 排除條件
        close_price = info.get("close") or 0
        volume = info.get("volume") or 0
        change_pct = info.get("change_percent") or 0
        
        if close_price < 10:  # 排除低價股（雞蛋水餃股）
            continue
        if volume < 500_000:  # 排除成交量太低的（流動性差）
            continue
        if change_pct < -9:  # 排除跌停股
            continue
        if close_price > 2000:  # 排除超高價股（風險高）
            continue
        
        # ============================================================
        # V10.8 優化：多維度初篩公式
        # ============================================================
        # 取得基本面資料
        pe_ratio = info.get("pe_ratio")
        pb_ratio = info.get("pb_ratio")
        dividend_yield = info.get("dividend_yield")
        
        # 1. 動能分數（降低權重：5 → 3）
        momentum_score = change_pct * 3
        
        # 2. 成交量分數（維持）
        volume_score = (volume / 1_000_000) * 2
        
        # 3. 本益比分數（新增）
        pe_score = 0
        if pe_ratio and pe_ratio > 0:
            if 5 <= pe_ratio <= 15:
                pe_score = 10  # 低估值，大加分
            elif 15 < pe_ratio <= 25:
                pe_score = 5   # 合理估值，小加分
            elif pe_ratio > 50:
                pe_score = -5  # 高估值，扣分
            # pe_ratio < 5 或 > 25 且 <= 50 不加減分
        
        # 4. 殖利率分數（新增）
        yield_score = 0
        if dividend_yield and dividend_yield > 0:
            if dividend_yield >= 5:
                yield_score = 10  # 高殖利率，大加分
            elif dividend_yield >= 3:
                yield_score = 5   # 中等殖利率，小加分
            elif dividend_yield >= 2:
                yield_score = 2   # 基本殖利率
        
        # 5. 淨值比分數（新增）
        pb_score = 0
        if pb_ratio and pb_ratio > 0:
            if pb_ratio < 1:
                pb_score = 8   # 股價低於淨值，加分
            elif pb_ratio < 1.5:
                pb_score = 4   # 合理
            elif pb_ratio > 5:
                pb_score = -3  # 過高
        
        # 綜合初篩分數
        prelim_score = momentum_score + volume_score + pe_score + yield_score + pb_score
        
        candidates.append({
            "stock_id": stock_id,
            "name": info.get("name", stock_id),
            "close": close_price,
            "volume": volume,
            "change_percent": change_pct,
            "change": info.get("change", 0),
            "open": info.get("open", close_price),
            "high": info.get("high", close_price),
            "low": info.get("low", close_price),
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dividend_yield": dividend_yield,
            "prelim_score": prelim_score
        })
    
    print(f"📋 初篩後剩餘 {len(candidates)} 檔候選股")
    
    # Step 5: 依初步分數排序，取前 200 名做技術分析（V10.8 擴充）
    candidates.sort(key=lambda x: x["prelim_score"], reverse=True)
    top_candidates = candidates[:200]
    
    print(f"🔍 對前 {len(top_candidates)} 名進行技術分析...")
    
    # 🆕 V10.13：預取 TWSE 三大法人資料（避免 FinMind 402 錯誤）
    print("📊 預取 TWSE 三大法人資料...")
    inst_data_cache = {}
    try:
        inst_data_cache = await TWSEOpenAPI.get_institutional_trading() or {}
        print(f"✅ TWSE 三大法人: {len(inst_data_cache)} 檔")
        # 🆕 V10.13.3: 存入全局快取供股票分析 Tab 使用
        ChipDataCache.set_institutional(inst_data_cache)
    except Exception as e:
        print(f"⚠️ TWSE 三大法人預取失敗: {e}")
    
    print("📊 預取 TWSE 融資融券資料...")
    margin_data_cache = {}
    try:
        margin_data_cache = await TWSEOpenAPI.get_margin_trading() or {}
        print(f"✅ TWSE 融資融券: {len(margin_data_cache)} 檔")
        # 🆕 V10.13.3: 存入全局快取供股票分析 Tab 使用
        ChipDataCache.set_margin(margin_data_cache)
    except Exception as e:
        print(f"⚠️ TWSE 融資融券預取失敗: {e}")
    
    # Step 4: 對候選股進行技術分析
    async def analyze_with_tech(candidate: dict):
        """對候選股進行技術分析"""
        stock_id = candidate["stock_id"]
        try:
            # 使用 yfinance 取得歷史資料
            history = await bulk_service.get_stock_history_yf(stock_id, months=2)
            
            # 🔧 V10.14.1: 修復漲跌幅計算
            if history and len(history) > 0:
                latest = history[-1]
                yf_close = latest.get("close")
                
                # 更新價格
                if yf_close:
                    candidate["close"] = yf_close
                    
                    # 計算漲跌幅：優先用 yfinance 提供的值
                    yf_change_pct = latest.get("change_percent")
                    yf_change = latest.get("change")
                    
                    if yf_change_pct is not None:
                        # yfinance 有提供漲跌幅，直接使用
                        candidate["change_percent"] = yf_change_pct
                        if yf_change is not None:
                            candidate["change"] = yf_change
                    elif len(history) >= 2:
                        # yfinance 沒有提供，自己計算
                        # 找到正確的「前一交易日」（跳過同一天的資料）
                        today_date = latest.get("date", "")
                        prev_close = None
                        for i in range(len(history) - 2, -1, -1):
                            prev_item = history[i]
                            prev_date = prev_item.get("date", "")
                            if prev_date != today_date:
                                prev_close = prev_item.get("close")
                                break
                        
                        if prev_close and prev_close > 0:
                            change = yf_close - prev_close
                            change_pct = round((change / prev_close) * 100, 2)
                            candidate["change"] = round(change, 2)
                            candidate["change_percent"] = change_pct
            
            tech_score = 50
            bonus = 0
            vol_ratio = 1.0
            reason_parts = []
            analysis_success = False
            
            if history and len(history) >= 20:
                try:
                    analysis = TechnicalAnalysis.full_analysis(history)
                    if "error" not in analysis:
                        tech_score = analysis.get("overall_score", 50)
                        analysis_success = True
                        
                        # 技術指標分析
                        trend = analysis.get("trend", {})
                        rsi_data = analysis.get("rsi", {})
                        macd_data = analysis.get("macd", {})
                        vol_ratio = analysis.get("volume", {}).get("ratio", 1)
                        
                        # 均線
                        if trend.get("above_ma5") and trend.get("above_ma20"):
                            reason_parts.append("多頭排列")
                        elif trend.get("above_ma20"):
                            reason_parts.append("站上月線")
                        
                        # MACD
                        macd_signal = macd_data.get("signal")
                        if macd_signal == "金叉":
                            reason_parts.append("MACD 金叉")
                        elif macd_signal == "多方":
                            reason_parts.append("MACD 多方")
                        elif macd_signal == "死叉":
                            reason_parts.append("MACD 死叉")
                        
                        # RSI
                        rsi_val = rsi_data.get("value")
                        if rsi_val:
                            if rsi_val < 30:
                                reason_parts.append("RSI 超賣")
                            elif rsi_val > 70:
                                reason_parts.append("RSI 過熱")
                        
                        # 成交量
                        if vol_ratio > 2.5:
                            reason_parts.append("爆量")
                        elif vol_ratio > 1.5:
                            reason_parts.append("量增")
                        elif vol_ratio < 0.5:
                            reason_parts.append("量縮")
                except Exception as e:
                    print(f"  技術分析異常 {stock_id}: {e}")
            
            # 當日表現
            change_pct = candidate["change_percent"]
            
            if not analysis_success:
                # 技術分析失敗，根據當日表現給基礎分
                if change_pct > 7:
                    tech_score = 72
                    reason_parts.append("強勢漲停")
                elif change_pct > 5:
                    tech_score = 65
                    reason_parts.append("強勢大漲")
                elif change_pct > 3:
                    tech_score = 58
                    reason_parts.append("漲勢明顯")
                elif change_pct > 1:
                    tech_score = 52
                    reason_parts.append("小幅上漲")
                elif change_pct > -1:
                    tech_score = 48
                    reason_parts.append("盤整")
                elif change_pct > -3:
                    tech_score = 42
                    reason_parts.append("小幅回檔")
                else:
                    tech_score = 35
                    reason_parts.append("跌勢明顯")
            else:
                # V10.8.1: 技術分析成功，不再額外加分（消除雙重加分）
                # 只記錄當日表現作為理由說明
                if change_pct > 5:
                    reason_parts.append("強勢大漲")
                elif change_pct > 3:
                    reason_parts.append("漲勢明顯")
                elif change_pct < -3:
                    reason_parts.append("跌幅較大")
            
            # V10.8.1: 移除成交量重複加分（已在 technical_analysis 中計算）
            # 只添加理由說明
            if vol_ratio > 2.5:
                if "爆量" not in reason_parts and "量增" not in reason_parts:
                    reason_parts.append("爆量")
            
            # ============================================================
            # V10.10: 多維度評分整合（含新聞+產業熱度）
            # ============================================================
            
            # 1. 計算基本面分數
            fundamental_result = ScoringService.calculate_fundamental_score(
                pe_ratio=candidate.get("pe_ratio"),
                pb_ratio=candidate.get("pb_ratio"),
                dividend_yield=candidate.get("dividend_yield"),
            )
            fundamental_score = fundamental_result["score"]
            
            # 基本面摘要加入理由
            fund_summary = fundamental_result.get("summary", "")
            if fund_summary and fund_summary != "基本面中性":
                reason_parts.append(fund_summary)
            
            # 2. 籌碼面分數（V10.13: 使用預取的 TWSE 資料，避免 FinMind 402）
            chip_score = 50  # 預設中性
            inst_data = inst_data_cache.get(stock_id)
            if inst_data:
                chip_result = ScoringService.calculate_chip_score(
                    foreign_net=inst_data.get("foreign_net"),
                    trust_net=inst_data.get("trust_net"),
                    dealer_net=inst_data.get("dealer_net"),
                )
                chip_score = chip_result["score"]
                
                # 籌碼摘要加入理由
                chip_summary = chip_result.get("summary", "")
                if chip_summary and chip_summary != "籌碼中性":
                    reason_parts.append(chip_summary)
                
                # 🆕 融資融券加分（如果有資料）
                margin_data = margin_data_cache.get(stock_id)
                if margin_data:
                    margin_buy = margin_data.get("margin_buy", 0) or 0
                    margin_sell = margin_data.get("margin_sell", 0) or 0
                    short_balance = margin_data.get("short_balance", 0) or 0
                    margin_balance = margin_data.get("margin_balance", 0) or 0
                    
                    # 融資減少 = 籌碼沉澱
                    if margin_sell > margin_buy + 500:
                        chip_score = min(85, chip_score + 6)
                        reason_parts.append("融資減少")
                    
                    # 券資比高 = 軋空潛力
                    if margin_balance > 0:
                        short_ratio = (short_balance / margin_balance) * 100
                        if short_ratio > 30:
                            chip_score = min(85, chip_score + 8)
                            reason_parts.append("高券資比")
                        elif short_ratio > 20:
                            chip_score = min(85, chip_score + 4)
            
            # 3. 新聞情緒分數（V10.10 新增）
            news_score = 50  # 預設中性
            stock_tags = get_stock_tags(stock_id)  # 提前初始化
            stock_name_for_news = candidate.get("name", stock_id)  # 取得股票名稱
            try:
                from ..services.news_service import get_news_service
                news_service = get_news_service()
                
                news_list = []
                # 方案 1：使用產業新聞（較快）
                industry = stock_tags.get("industry", "")
                if industry:
                    news_list = await news_service.get_industry_news(industry, limit=5)
                
                # 方案 2：如果沒有產業或產業新聞為空，使用股票名稱搜尋
                if not news_list and stock_name_for_news and stock_name_for_news != stock_id:
                    news_list = await news_service.get_stock_news(stock_name_for_news, limit=3)
                
                if news_list:
                    news_summary = news_service.get_news_summary(news_list)
                    news_result = ScoringService.calculate_news_score(
                        positive_count=news_summary.get("positive_count", 0),
                        negative_count=news_summary.get("negative_count", 0),
                        total_count=news_summary.get("total", 0),
                        sentiment_trend=news_summary.get("trend", "neutral"),
                    )
                    news_score = news_result["score"]
            except Exception as e:
                pass  # 新聞取得失敗，使用預設分數
            
            # 4. 產業熱度加分（V10.10 新增）
            industry_result = ScoringService.calculate_industry_bonus(
                industry=stock_tags.get("industry"),
                tags=stock_tags.get("tags", []),
            )
            industry_bonus = industry_result["bonus"]
            
            # 如果是熱門題材，加入理由
            if industry_result.get("summary"):
                reason_parts.append(industry_result["summary"])
            
            # 5. 計算最終綜合分數
            scoring_result = ScoringService.calculate_final_score(
                technical_score=tech_score,
                fundamental_score=fundamental_score,
                chip_score=chip_score,
                news_score=news_score,
                industry_bonus=industry_bonus,
            )
            final_score = scoring_result["final_score"]
            signal = scoring_result["signal"]
            
            # 組合理由
            reason = "，".join(reason_parts[:4]) if reason_parts else "技術面中性"
            
            # 產業標籤（已在上面取得）
            # stock_tags = get_stock_tags(stock_id)
            
            price = candidate["close"]
            name = candidate.get("name", stock_id)  # 🔧 V10.7.1: 安全存取 name
            
            return {
                "stock_id": stock_id,
                "name": name,
                "price": price,
                "change": candidate["change"],
                "change_percent": change_pct,
                "confidence": final_score,
                "signal": signal,
                "reason": reason,
                "industry": stock_tags.get("industry", ""),
                "tags": stock_tags.get("tags", []),
                "action": f"建議價位 ${round(price * 0.98, 1)}-{price}",
                "stop_loss": round(price * 0.95, 2),
                "target": round(price * 1.10, 2),
                "volume_ratio": vol_ratio,
                # V10.8: 基本面資料
                "pe_ratio": candidate.get("pe_ratio"),
                "pb_ratio": candidate.get("pb_ratio"),
                "dividend_yield": candidate.get("dividend_yield"),
                # V10.10: 多維度分數明細（含新聞+產業）
                "score_breakdown": {
                    "technical": tech_score,
                    "fundamental": fundamental_score,
                    "chip": chip_score,
                    "news": news_score,
                    "industry_bonus": industry_bonus,
                },
            }
        except Exception as e:
            print(f"分析失敗 {stock_id}: {e}")
            price = candidate["close"]
            change_pct = candidate["change_percent"]
            
            # 產業標籤
            stock_tags = get_stock_tags(stock_id)
            
            # 基於當日表現的技術分數
            if change_pct > 7:
                tech_score = 72
                reason = "強勢漲停"
            elif change_pct > 5:
                tech_score = 65
                reason = "強勢大漲"
            elif change_pct > 3:
                tech_score = 58
                reason = "漲勢明顯"
            elif change_pct > 1:
                tech_score = 52
                reason = "小幅上漲"
            elif change_pct > -1:
                tech_score = 48
                reason = "盤整"
            elif change_pct > -3:
                tech_score = 42
                reason = "小幅回檔"
            else:
                tech_score = 35
                reason = "跌勢明顯"
            
            # V10.9: 計算基本面分數
            fundamental_result = ScoringService.calculate_fundamental_score(
                pe_ratio=candidate.get("pe_ratio"),
                pb_ratio=candidate.get("pb_ratio"),
                dividend_yield=candidate.get("dividend_yield"),
            )
            fundamental_score = fundamental_result["score"]
            
            # V10.9: 計算最終綜合分數（籌碼預設中性）
            scoring_result = ScoringService.calculate_final_score(
                technical_score=tech_score,
                fundamental_score=fundamental_score,
                chip_score=50,
            )
            final_score = scoring_result["final_score"]
            signal = scoring_result["signal"]
            
            return {
                "stock_id": stock_id,
                "name": candidate.get("name", stock_id),
                "price": price,
                "change": candidate["change"],
                "change_percent": change_pct,
                "confidence": final_score,
                "signal": signal,
                "reason": reason,
                "industry": stock_tags.get("industry", ""),
                "tags": stock_tags.get("tags", []),
                "action": f"建議價位 ${round(price * 0.98, 1)}-{price}",
                "stop_loss": round(price * 0.95, 2),
                "target": round(price * 1.10, 2),
                "volume_ratio": 1.0,
                "pe_ratio": candidate.get("pe_ratio"),
                "pb_ratio": candidate.get("pb_ratio"),
                "dividend_yield": candidate.get("dividend_yield"),
                "score_breakdown": {
                    "technical": tech_score,
                    "fundamental": fundamental_score,
                    "chip": 50,
                },
            }
    
    # 批次分析（每批10個，間隔1秒，避免 yfinance 限流）
    batch_size = 10
    results = []
    
    for i in range(0, len(top_candidates), batch_size):
        batch = top_candidates[i:i+batch_size]
        print(f"  分析第 {i+1}-{min(i+batch_size, len(top_candidates))} 檔...")
        # V10.11.8: 每個股票獨立取得籌碼資料
        tasks = [analyze_with_tech(c) for c in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend([r for r in batch_results if r])
        
        # 批次間延遲
        if i + batch_size < len(top_candidates):
            await asyncio.sleep(1.0)
    
    print(f"✅ 完成分析 {len(results)} 檔股票")
    
    # V10.8: 擴充各列表數量 20 → 30
    # AI 精選：按信心分數排序（前30名）
    ai_picks = sorted(results, key=lambda x: x["confidence"], reverse=True)[:30]
    
    # 熱門飆股：當日漲幅最高（前30名）
    hot_stocks = sorted(results, key=lambda x: x["change_percent"], reverse=True)[:30]
    
    # 成交熱門：成交量比率最高（前30名）
    volume_hot = sorted(results, key=lambda x: x.get("volume_ratio", 1), reverse=True)[:30]
    
    # 潛力黑馬：分數中等但有上漲動能的股票（前30名）
    dark_horses = [r for r in results if 55 <= r["confidence"] <= 75 and r["change_percent"] > 0]
    dark_horses = sorted(dark_horses, key=lambda x: x["change_percent"], reverse=True)[:30]
    
    # 大盤資訊
    market = await bulk_service.get_market_index()
    
    # 取得市場新聞
    news_service = get_news_service()
    try:
        market_news = await news_service.get_market_news(limit=5)
        news_summary = news_service.get_news_summary(market_news)
    except Exception as e:
        print(f"取得新聞失敗: {e}")
        market_news = []
        news_summary = {"trend": "neutral", "summary": "暫無新聞"}
    
    result = {
        "updated_at": datetime.now().isoformat(),
        "data_date": data_date,  # 🆕 V10.13.5: 資料日期（TWSE 資料的實際日期）
        "market": {
            "value": market["value"] if market else 0,
            "change_percent": market["change_percent"] if market else 0,
            "mood": "偏多" if market and market["change_percent"] > 0 else "偏空",
        } if market else None,
        "scanned": len(all_stocks),  # 顯示掃描了多少檔
        "analyzed": len(results),    # 實際分析了多少檔
        "recommendations": ai_picks,      # AI 精選
        "hot_stocks": hot_stocks,         # 熱門飆股
        "volume_hot": volume_hot,         # 成交熱門
        "dark_horses": dark_horses,       # 潛力黑馬
        "news": market_news,              # 市場新聞
        "news_summary": news_summary,     # 新聞摘要
    }

    # V10.35.5 方案 D: 自動記錄 AI 精選到績效追蹤
    try:
        tracker = get_performance_tracker()
        recorded_count = 0
        for pick in ai_picks[:10]:  # 只記錄前 10 名
            tracker.record_recommendation(
                stock_id=pick["stock_id"],
                name=pick["name"],
                price=pick["price"],
                signal=pick["signal"],
                confidence=pick["confidence"],
                reason=pick.get("reason", ""),
            )
            recorded_count += 1
        print(f"📊 已記錄 {recorded_count} 檔 AI 精選到績效追蹤")
    except Exception as e:
        print(f"⚠️ 績效追蹤記錄失敗: {e}")

    # 設定快取（3分鐘）
    StockCache.set_recommendations(result)
    print("📦 已更新快取")
    
    return result


async def _fallback_recommend():
    """備用推薦方案（當 TWSE API 失敗時）- 使用 yfinance"""
    from app.services.github_data import SmartStockService
    from app.services.twse_bulk import get_bulk_service
    import asyncio
    
    bulk_service = get_bulk_service()
    
    # ============================================================
    # 核心股票清單 V10.7（2024/12 更新）
    # ⚠️ 已移除所有 404 / delisted 的股票
    # ============================================================
    core_stocks = [
        # ==================== 權值股 TOP20 ====================
        "2330", "2454", "2317", "2308", "2303", "2412", "3711", "2382", "2357", "3034",
        "2881", "2882", "2886", "2891", "1301", "2002", "1303", "1326", "2912", "1216",
        
        # ==================== 金融股 (15) ====================
        "2884", "2892", "2883", "2887", "2880", "5880", "2801", "5876", "2890", "2885",
        "2889", "2834", "2838", "2836", "2823",
        
        # ==================== 半導體 (15) - 移除 6488, 5483 ====================
        "2379", "2408", "3008", "2344", "3443", "2449", "3661", "2337", "6415",
        "8046", "2436", "6239", "6770", "3035", "2458",
        
        # ==================== AI/伺服器概念股 (12) - 移除 3653 ====================
        "2345", "3017", "3044", "3231", "3533", "3550", "4966", "6669", "2049",
        "2059", "6285", "6166",
        
        # ==================== 電子代工/零組件 (18) - 移除 3037 ====================
        "2324", "2353", "2356", "2360", "2376", "2377", "2385", "2395", "2409", "2474",
        "3014", "3026", "3706", "2327", "2301", "2354", "2393", "2383",
        
        # ==================== 生技醫療 (6) - 移除 4743, 4142, 4147 ====================
        "6446", "6472", "1760", "4108", "4164", "4763",
        
        # ==================== 傳產績優 (15) ====================
        "1101", "1102", "1227", "1402", "1434", "1504", "1605", "1722", "2105", "2207",
        "2201", "2204", "2206", "9910", "1476",
        
        # ==================== 航運/運輸 (10) ====================
        "2603", "2606", "2609", "2610", "2615", "2618", "2634", "5871", "2637", "2636",
        
        # ==================== 電信/網通 (5) ====================
        "3045", "4904", "2498", "4906", "6214",
        
        # ==================== ETF (8) - 移除 006208 ====================
        "0050", "0056", "00878", "00919", "00929", "00713", "00881", "00882",
    ]
    
    # 去重
    core_stocks = list(dict.fromkeys(core_stocks))
    
    print(f"⚠️ 使用備用方案，掃描 {len(core_stocks)} 檔核心股票...")
    
    async def analyze_stock(stock_id: str):
        try:
            # 取得即時資訊
            info = await StockDataService.get_stock_info(stock_id)
            if not info:
                return None
            
            name = info.get("name", stock_id)
            if name == stock_id:
                name = SmartStockService.POPULAR_STOCKS.get(stock_id, stock_id)
            
            # 取得歷史資料做技術分析
            history = await bulk_service.get_stock_history_yf(stock_id, months=2)
            
            tech_score = 50
            bonus = 0
            vol_ratio = 1.0
            reason_parts = []
            analysis_success = False
            
            if history and len(history) >= 20:
                try:
                    analysis = TechnicalAnalysis.full_analysis(history)
                    if "error" not in analysis:
                        tech_score = analysis.get("overall_score", 50)
                        analysis_success = True
                        vol_ratio = analysis.get("volume", {}).get("ratio", 1)
                        
                        # 技術指標
                        trend = analysis.get("trend", {})
                        macd_data = analysis.get("macd", {})
                        rsi_data = analysis.get("rsi", {})
                        
                        if trend.get("above_ma5") and trend.get("above_ma20"):
                            reason_parts.append("多頭排列")
                        
                        macd_signal = macd_data.get("signal")
                        if macd_signal == "金叉":
                            reason_parts.append("MACD 金叉")
                        elif macd_signal == "多方":
                            reason_parts.append("MACD 多方")
                        
                        rsi_val = rsi_data.get("value")
                        if rsi_val and rsi_val < 30:
                            reason_parts.append("RSI 超賣")
                        elif rsi_val and rsi_val > 70:
                            reason_parts.append("RSI 過熱")
                        
                        if vol_ratio > 2:
                            reason_parts.append("量增")
                except Exception as e:
                    print(f"  技術分析異常 {stock_id}: {e}")
            
            # 當日表現
            change_pct = info.get("change_percent", 0)
            
            if not analysis_success:
                # 技術分析失敗，根據當日表現給基礎分
                if change_pct > 7:
                    tech_score = 72
                    reason_parts.append("強勢漲停")
                elif change_pct > 5:
                    tech_score = 65
                    reason_parts.append("強勢大漲")
                elif change_pct > 3:
                    tech_score = 58
                    reason_parts.append("漲勢明顯")
                elif change_pct > 1:
                    tech_score = 52
                    reason_parts.append("小幅上漲")
                elif change_pct > -1:
                    tech_score = 48
                    reason_parts.append("盤整")
                elif change_pct > -3:
                    tech_score = 42
                    reason_parts.append("小幅回檔")
                else:
                    tech_score = 35
                    reason_parts.append("跌勢明顯")
            else:
                # 技術分析成功，當日表現加分
                if change_pct > 5:
                    bonus += 10
                    reason_parts.append("強勢大漲")
                elif change_pct > 2:
                    bonus += 5
                    reason_parts.append("漲勢明顯")
                elif change_pct < -3:
                    bonus -= 8
                    reason_parts.append("跌幅較大")
            
            # 成交量加分
            if vol_ratio > 2.5:
                bonus += 8
            elif vol_ratio > 1.5:
                bonus += 4
            
            final_score = max(15, min(95, tech_score + bonus))
            
            if final_score >= 80:
                signal = "強力買進"
            elif final_score >= 70:
                signal = "買進"
            elif final_score >= 55:
                signal = "持有"
            elif final_score >= 40:
                signal = "觀望"
            else:
                signal = "減碼"
            
            reason = "，".join(reason_parts[:4]) if reason_parts else "技術面中性"
            
            # 產業標籤（只顯示，不影響評分）
            stock_tags = get_stock_tags(stock_id)
            
            price = info["close"]
            
            return {
                "stock_id": stock_id,
                "name": name,
                "price": price,
                "change": info.get("change", 0),
                "change_percent": change_pct,
                "confidence": final_score,
                "signal": signal,
                "reason": reason,
                "industry": stock_tags.get("industry", ""),
                "tags": stock_tags.get("tags", []),
                "action": f"建議價位 ${round(price * 0.98, 1)}-{price}",
                "stop_loss": round(price * 0.95, 2),
                "target": round(price * 1.10, 2),
                "volume_ratio": vol_ratio,
            }
        except Exception as e:
            print(f"分析失敗 {stock_id}: {e}")
            return None
    
    # 批次分析
    batch_size = 10
    results = []
    
    for i in range(0, len(core_stocks), batch_size):
        batch = core_stocks[i:i+batch_size]
        print(f"  分析第 {i+1}-{min(i+batch_size, len(core_stocks))} 檔...")
        tasks = [analyze_stock(sid) for sid in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend([r for r in batch_results if r])
        
        if i + batch_size < len(core_stocks):
            await asyncio.sleep(1.0)
    
    print(f"✅ 備用方案完成分析 {len(results)} 檔股票")
    
    # 排序
    ai_picks = sorted(results, key=lambda x: x["confidence"], reverse=True)[:20]
    hot_stocks = sorted(results, key=lambda x: x["change_percent"], reverse=True)[:20]
    volume_hot = sorted(results, key=lambda x: x.get("volume_ratio", 1), reverse=True)[:20]
    dark_horses = [r for r in results if 55 <= r["confidence"] <= 75 and r["change_percent"] > 0][:20]
    
    # 取得市場新聞
    news_service = get_news_service()
    try:
        market_news = await news_service.get_market_news(limit=5)
        news_summary = news_service.get_news_summary(market_news)
    except Exception as e:
        print(f"取得新聞失敗: {e}")
        market_news = []
        news_summary = {"trend": "neutral", "summary": "暫無新聞"}
    
    result = {
        "updated_at": datetime.now().isoformat(),
        "market": None,
        "scanned": len(core_stocks),
        "analyzed": len(results),
        "recommendations": ai_picks,
        "hot_stocks": hot_stocks,
        "volume_hot": volume_hot,
        "dark_horses": dark_horses,
        "news": market_news,
        "news_summary": news_summary,
    }
    
    # 設定快取（3分鐘）
    StockCache.set_recommendations(result)
    print("📦 已更新快取")
    
    return result


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1, description="搜尋關鍵字")):
    """
    搜尋股票（依股號或名稱）
    """
    results = await StockDataService.search_stock(q)
    
    # 取得每檔股票的價格資訊
    enriched_results = []
    for stock in results[:10]:  # 最多10筆
        info = await StockDataService.get_stock_info(stock["stock_id"])
        if info:
            enriched_results.append({
                "stock_id": stock["stock_id"],
                "name": stock["name"],
                "price": info["close"],
                "change_percent": info["change_percent"],
            })
    
    return {
        "query": q,
        "count": len(enriched_results),
        "results": enriched_results
    }


# ===== 新聞 API =====

@router.get("/news/stock/{stock_id}")
async def get_stock_news(stock_id: str, limit: int = Query(5, ge=1, le=20)):
    """
    取得個股相關新聞
    """
    from ..services.news_service import get_news_service
    
    news_service = get_news_service()
    news_list = await news_service.get_stock_news(stock_id, limit)
    summary = news_service.get_news_summary(news_list)
    
    return {
        "stock_id": stock_id,
        "news": news_list,
        "summary": summary,
    }


@router.get("/news/market")
async def get_market_news(limit: int = Query(10, ge=1, le=30)):
    """
    取得大盤/市場新聞
    """
    from ..services.news_service import get_news_service
    
    news_service = get_news_service()
    news_list = await news_service.get_market_news(limit)
    summary = news_service.get_news_summary(news_list)
    
    return {
        "news": news_list,
        "summary": summary,
    }


@router.get("/news/industry/{industry}")
async def get_industry_news(industry: str, limit: int = Query(5, ge=1, le=20)):
    """
    取得產業新聞
    支援的產業：半導體、AI、記憶體、電動車、金融、航運、面板
    """
    from ..services.news_service import get_news_service
    
    news_service = get_news_service()
    news_list = await news_service.get_industry_news(industry, limit)
    summary = news_service.get_news_summary(news_list)
    
    return {
        "industry": industry,
        "news": news_list,
        "summary": summary,
    }


# ===== 快取管理 API =====

@router.get("/cache/stats")
async def get_cache_stats():
    """取得快取統計"""
    return StockCache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """清除所有快取"""
    StockCache.clear_all()
    return {"message": "快取已清除", "timestamp": datetime.now().isoformat()}


# ===== 自選股 API =====

from ..services.watchlist_service import get_watchlist_service

@router.get("/watchlist")
async def get_watchlist():
    """取得自選股清單"""
    service = get_watchlist_service()
    watchlist = service.get_watchlist()
    
    # 取得每檔股票的即時資訊
    enriched = []
    for item in watchlist:
        try:
            info = await StockDataService.get_stock_info(item["stock_id"])
            if info:
                enriched.append({
                    **item,
                    "price": info.get("close"),
                    "change_percent": info.get("change_percent"),
                    "name": info.get("name", item.get("name", item["stock_id"])),
                })
            else:
                enriched.append(item)
        except:
            enriched.append(item)
    
    return {"watchlist": enriched, "count": len(enriched)}


@router.post("/watchlist/{stock_id}")
async def add_to_watchlist(stock_id: str, note: str = ""):
    """加入自選股"""
    service = get_watchlist_service()
    
    # 取得股票名稱
    name = stock_id
    try:
        info = await StockDataService.get_stock_info(stock_id)
        if info:
            name = info.get("name", stock_id)
    except:
        pass
    
    return service.add_to_watchlist(stock_id, name, note)


@router.delete("/watchlist/{stock_id}")
async def remove_from_watchlist(stock_id: str):
    """從自選股移除"""
    service = get_watchlist_service()
    return service.remove_from_watchlist(stock_id)


@router.get("/watchlist/check/{stock_id}")
async def check_watchlist(stock_id: str):
    """檢查是否在自選股中"""
    service = get_watchlist_service()
    return {"in_watchlist": service.is_in_watchlist(stock_id)}


# ===== 回測 API =====

@router.get("/backtest/{stock_id}")
async def run_backtest_api(
    stock_id: str,
    start_date: str = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="結束日期 YYYY-MM-DD"),
    months: int = Query(None, description="回測月數（優先使用 start_date/end_date）"),
    strategy: str = Query("ma_crossover", description="策略：ma_crossover, rsi, macd, bollinger, volume_breakout, combined"),
    initial_capital: float = Query(1000000, description="初始資金"),
):
    """
    執行回測

    可用策略：
    - ma_crossover: 均線交叉策略（MA5/MA20）
    - rsi: RSI 超買超賣策略
    - macd: MACD 策略
    - bollinger: 布林通道策略
    - volume_breakout: 量價突破策略
    - combined: 綜合策略
    """
    from ..services.backtest_engine import run_backtest
    from datetime import datetime, timedelta

    # 計算日期範圍
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    if not start_date:
        # 優先使用 months 參數，否則預設 6 個月
        days = (months or 6) * 30
        start = datetime.now() - timedelta(days=days)
        start_date = start.strftime("%Y-%m-%d")

    print(f"📊 [回測] 股票: {stock_id}, 策略: {strategy}, 期間: {start_date} ~ {end_date}")

    try:
        result = await run_backtest(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            initial_capital=initial_capital,
        )

        # 添加回測結果摘要日誌
        if "stats" in result:
            stats = result["stats"]
            print(f"✅ [回測完成] 交易次數: {stats.get('total_trades', 0)}, 報酬率: {stats.get('total_return_pct', 0)}%")
        elif "error" in result:
            print(f"⚠️ [回測失敗] {result.get('error')}")

        return result
    except Exception as e:
        print(f"❌ [回測異常] {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@router.get("/backtest/strategies")
async def get_backtest_strategies():
    """取得可用的回測策略列表"""
    return {
        "strategies": [
            {
                "id": "ma_crossover",
                "name": "均線交叉策略",
                "description": "當 MA5 向上穿越 MA20 時買進，向下穿越時賣出",
                "params": ["short_period", "long_period"],
                "risk": "中",
            },
            {
                "id": "rsi",
                "name": "RSI 超買超賣策略",
                "description": "RSI < 30 時買進（超賣），RSI > 70 時賣出（超買）",
                "params": ["period", "oversold", "overbought"],
                "risk": "中",
            },
            {
                "id": "macd",
                "name": "MACD 策略",
                "description": "MACD 線向上穿越零軸時買進，向下穿越時賣出",
                "params": ["fast", "slow", "signal"],
                "risk": "中",
            },
            {
                "id": "bollinger",
                "name": "布林通道策略",
                "description": "價格觸及下軌買進，觸及上軌賣出",
                "params": ["period", "std_dev"],
                "risk": "低",
            },
            {
                "id": "volume_breakout",
                "name": "量價突破策略",
                "description": "帶量突破均線時買進，帶量跌破時賣出",
                "params": ["ma_period", "volume_ratio"],
                "risk": "高",
            },
            {
                "id": "combined",
                "name": "綜合策略",
                "description": "結合 MA + RSI + MACD 多指標綜合判斷",
                "params": [],
                "risk": "低",
            },
        ]
    }


# ============================================================
# 🤖 AI 智能選股 API（V10）
# ============================================================

@router.get("/ai/picks")
async def get_ai_picks(top_n: int = Query(default=10, ge=5, le=30)):
    """
    🤖 AI 智能選股
    
    整合多維度分析：
    - 技術面：MA, RSI, MACD, 成交量
    - 籌碼面：三大法人, 融資融券
    - 基本面：PER, PBR, 營收成長, 殖利率
    
    Returns:
        AI 精選 Top N 股票，含完整分析報告
    """
    try:
        result = await get_ai_top_picks(top_n)
        return result
    except Exception as e:
        print(f"❌ AI 選股失敗: {e}")
        return {
            "error": str(e),
            "updated_at": datetime.now().isoformat(),
            "top_picks": [],
        }


@router.get("/ai/analyze/{stock_id}")
async def ai_analyze_stock(stock_id: str):
    """
    🔍 AI 深度分析單一股票
    
    Returns:
        該股票的完整多維度分析報告
    """
    try:
        # 取得基本資訊
        info = await StockDataService.get_stock_info(stock_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"找不到股票 {stock_id}")
        
        stock_data = {
            "stock_id": stock_id,
            "close": info.get("price", 0),
            "change_percent": info.get("change_percent", 0),
            "volume": info.get("volume", 0),
        }
        
        # 深度分析
        analysis = await AIStockPicker._deep_analyze(stock_data)
        
        if not analysis:
            raise HTTPException(status_code=500, detail="分析失敗")
        
        return {
            "updated_at": datetime.now().isoformat(),
            "analysis": analysis,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 💼 投資組合管理 API
# ============================================================

from ..services.portfolio_service import PortfolioService, get_stock_name

@router.get("/portfolio")
async def get_portfolio():
    """取得投資組合所有持股"""
    try:
        holdings = await PortfolioService.get_holdings()
        return {
            "success": True,
            "holdings": holdings,
            "count": len(holdings)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/portfolio/summary")
async def get_portfolio_summary():
    """取得投資組合總覽"""
    try:
        summary = await PortfolioService.get_summary()
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/portfolio/add")
async def add_portfolio_holding(
    stock_id: str = Query(..., description="股票代號"),
    buy_price: float = Query(..., description="買入價格"),
    quantity: int = Query(..., description="股數"),
    buy_date: str = Query(None, description="買入日期 (YYYY-MM-DD)"),
    note: str = Query("", description="備註")
):
    """新增持股"""
    try:
        stock_name = get_stock_name(stock_id)
        result = await PortfolioService.add_holding(
            stock_id=stock_id,
            stock_name=stock_name,
            buy_price=buy_price,
            quantity=quantity,
            buy_date=buy_date,
            note=note
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.put("/portfolio/{holding_id}")
async def update_portfolio_holding(
    holding_id: str,
    buy_price: float = Query(None, description="買入價格"),
    quantity: int = Query(None, description="股數"),
    note: str = Query(None, description="備註")
):
    """更新持股資訊"""
    try:
        result = await PortfolioService.update_holding(
            holding_id=holding_id,
            buy_price=buy_price,
            quantity=quantity,
            note=note
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/portfolio/{holding_id}")
async def delete_portfolio_holding(holding_id: str):
    """刪除持股"""
    try:
        result = await PortfolioService.delete_holding(holding_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/portfolio/sell/{holding_id}")
async def sell_portfolio_holding(
    holding_id: str,
    sell_price: float = Query(..., description="賣出價格"),
    quantity: int = Query(None, description="賣出股數（不填則全部賣出）")
):
    """賣出持股"""
    try:
        result = await PortfolioService.sell_holding(
            holding_id=holding_id,
            sell_price=sell_price,
            sell_quantity=quantity
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/portfolio/transactions")
async def get_portfolio_transactions(limit: int = Query(default=20, ge=1, le=100)):
    """取得交易紀錄"""
    try:
        transactions = await PortfolioService.get_transactions(limit)
        return {
            "success": True,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🆕 TWSE OpenAPI 端點 (V10.7)
# ============================================================

@router.get("/twse/per-dividend")
async def get_twse_per_dividend():
    """
    📊 取得全市場本益比、殖利率、淨值比
    
    資料來源：TWSE OpenAPI
    更新頻率：每日收盤後
    
    Returns:
        所有上市股票的 P/E、殖利率、P/B 資料
    """
    data = await TWSEOpenAPI.get_per_dividend_all()
    
    if not data:
        return {
            "success": False,
            "message": "無法取得資料（可能是非交易時間或 API 暫時無法連線）",
            "count": 0,
            "data": {}
        }
    
    return {
        "success": True,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


@router.get("/twse/daily-trading")
async def get_twse_daily_trading():
    """
    📊 取得全市場每日成交資訊
    
    資料來源：TWSE OpenAPI
    包含：開高低收、成交量、漲跌
    
    Returns:
        所有上市股票的當日成交資料
    """
    data = await TWSEOpenAPI.get_daily_trading_all()
    
    if not data:
        return {
            "success": False,
            "message": "無法取得資料",
            "count": 0,
            "data": {}
        }
    
    return {
        "success": True,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


@router.get("/twse/market-index")
async def get_twse_market_index():
    """
    📊 取得大盤指數

    資料來源：TWSE OpenAPI
    包含：加權指數、台灣50、電子類、金融類等

    Returns:
        各主要指數的即時資料
    """
    data = await TWSEOpenAPI.get_market_index()

    return {
        "success": True if data else False,
        "updated_at": datetime.now().isoformat(),
        "indices": data
    }


@router.get("/market-index")
async def get_market_index_alias():
    """
    📊 取得大盤指數（別名路由）

    與 /twse/market-index 相同，提供相容性
    回傳格式適合 MarketDashboard 使用
    """
    data = await TWSEOpenAPI.get_market_index()

    # 回傳 taiex 的資料，格式化為前端期望的格式
    if data and "taiex" in data:
        taiex = data["taiex"]
        return {
            "success": True,
            "name": taiex.get("name", "加權指數"),
            "value": taiex.get("value"),
            "change": taiex.get("change"),
            "change_percent": taiex.get("change_percent"),
            "updated_at": datetime.now().isoformat(),
        }

    return {
        "success": False,
        "message": "無法取得大盤指數"
    }


@router.get("/twse/institutional")
async def get_twse_institutional(date: str = None):
    """
    📊 取得三大法人買賣超
    
    資料來源：TWSE 官方 API
    
    Args:
        date: 日期格式 YYYYMMDD，預設為今天
        
    Returns:
        所有股票的外資、投信、自營商買賣超
    """
    data = await TWSEOpenAPI.get_institutional_trading(date)
    
    if not data:
        return {
            "success": False,
            "message": "無法取得資料（可能是非交易日）",
            "count": 0,
            "data": {}
        }
    
    # 計算外資買超前 10 名
    top_foreign_buy = sorted(
        [(k, v) for k, v in data.items() if v.get('foreign_net') and v.get('foreign_net') > 0],
        key=lambda x: x[1].get('foreign_net', 0),
        reverse=True
    )[:10]
    
    # 計算投信買超前 10 名
    top_trust_buy = sorted(
        [(k, v) for k, v in data.items() if v.get('trust_net') and v.get('trust_net') > 0],
        key=lambda x: x[1].get('trust_net', 0),
        reverse=True
    )[:10]
    
    return {
        "success": True,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "summary": {
            "top_foreign_buy": [{"stock_id": k, **v} for k, v in top_foreign_buy],
            "top_trust_buy": [{"stock_id": k, **v} for k, v in top_trust_buy],
        },
        "data": data
    }


@router.get("/twse/margin")
async def get_twse_margin(date: str = None):
    """
    📊 取得融資融券資料
    
    資料來源：TWSE 官方 API
    
    Args:
        date: 日期格式 YYYYMMDD，預設為今天
        
    Returns:
        所有股票的融資融券餘額
    """
    data = await TWSEOpenAPI.get_margin_trading(date)
    
    if not data:
        return {
            "success": False,
            "message": "無法取得資料（可能是非交易日）",
            "count": 0,
            "data": {}
        }
    
    return {
        "success": True,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


@router.get("/twse/realtime")
async def get_twse_realtime(
    stock_ids: str = Query(..., description="股票代號，用逗號分隔，例如: 2330,2454,2317")
):
    """
    📊 取得即時報價
    
    資料來源：TWSE 即時報價 API
    
    Args:
        stock_ids: 股票代號列表（逗號分隔）
        
    Returns:
        即時股價、漲跌、成交量
    """
    ids = [s.strip() for s in stock_ids.split(",") if s.strip()]
    
    if not ids:
        return {"success": False, "message": "請提供股票代號"}
    
    if len(ids) > 20:
        return {"success": False, "message": "一次最多查詢 20 檔股票"}
    
    data = await TWSEOpenAPI.get_realtime_quotes(ids)
    
    return {
        "success": True if data else False,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


@router.get("/twse/stock/{stock_id}")
async def get_twse_stock_full(stock_id: str):
    """
    📊 取得單一股票完整資訊（整合多個 TWSE API）
    
    資料來源：TWSE OpenAPI + 官方 API
    
    整合資料：
    - 本益比、殖利率、淨值比
    - 當日成交（開高低收）
    - 三大法人買賣超
    
    Returns:
        股票的完整即時資訊
    """
    data = await TWSEOpenAPI.get_stock_full_info(stock_id)
    
    return {
        "success": True if data.get("price") else False,
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


@router.get("/twse/all-summary")
async def get_twse_all_summary():
    """
    📊 取得全市場股票摘要（最常用 API）
    
    資料來源：TWSE OpenAPI
    
    整合資料：
    - 所有股票的當日成交
    - 本益比、殖利率、淨值比
    
    Returns:
        全市場股票摘要資料（約 900+ 檔）
    """
    data = await TWSEOpenAPI.get_all_stocks_summary()
    
    if not data:
        return {
            "success": False,
            "message": "無法取得資料",
            "count": 0,
            "data": {}
        }
    
    # 統計
    with_price = sum(1 for d in data.values() if d.get('price'))
    with_pe = sum(1 for d in data.values() if d.get('pe_ratio'))
    
    # 漲幅前 10
    top_gainers = sorted(
        [(k, v) for k, v in data.items() if v.get('change_percent') and v.get('change_percent') > 0],
        key=lambda x: x[1].get('change_percent', 0),
        reverse=True
    )[:10]
    
    # 跌幅前 10
    top_losers = sorted(
        [(k, v) for k, v in data.items() if v.get('change_percent') and v.get('change_percent') < 0],
        key=lambda x: x[1].get('change_percent', 0)
    )[:10]
    
    return {
        "success": True,
        "count": len(data),
        "stats": {
            "with_price": with_price,
            "with_pe": with_pe,
        },
        "highlights": {
            "top_gainers": [{"stock_id": k, **v} for k, v in top_gainers],
            "top_losers": [{"stock_id": k, **v} for k, v in top_losers],
        },
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


# ============================================================
# 🆕 V10.11 新增 API 端點
# ============================================================

@router.get("/stocks/list")
async def get_all_stocks_list():
    """
    📋 取得全市場股票清單（供回測選擇用）
    
    資料來源：TWSE OpenAPI
    
    Returns:
        所有上市股票的代號和名稱列表
    """
    try:
        data = await TWSEOpenAPI.get_daily_trading_all()
        
        if not data:
            # 備用方案：使用固定清單
            from .stocks import CORE_STOCKS
            return {
                "success": True,
                "source": "fallback",
                "count": len(CORE_STOCKS),
                "stocks": [{"id": sid, "name": CORE_STOCKS.get(sid, sid)} for sid in CORE_STOCKS]
            }
        
        # 按代號排序（支援 4-6 碼，包含 ETF）
        stocks = sorted([
            {"id": stock_id, "name": info.get("name", stock_id)}
            for stock_id, info in data.items()
            if stock_id and 4 <= len(stock_id) <= 6 and stock_id.isdigit()
        ], key=lambda x: x["id"])
        
        return {
            "success": True,
            "source": "twse",
            "count": len(stocks),
            "updated_at": datetime.now().isoformat(),
            "stocks": stocks
        }
        
    except Exception as e:
        print(f"❌ 取得股票清單錯誤: {e}")
        return {
            "success": False,
            "message": str(e),
            "count": 0,
            "stocks": []
        }


@router.get("/twse/attention")
async def get_twse_attention_stocks():
    """
    ⚠️ 取得當日注意股票
    
    資料來源：TWSE OpenAPI
    
    注意股票是指近期股價異常波動的股票，
    投資時需特別注意風險。
    
    Returns:
        當日公布的注意股票列表
    """
    data = await TWSEOpenAPI.get_attention_stocks()
    
    if not data:
        return {
            "success": True,
            "message": "今日無注意股票公告",
            "count": 0,
            "data": {}
        }
    
    return {
        "success": True,
        "count": len(data),
        "warning": "以下股票近期股價異常波動，投資需注意風險",
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


@router.get("/twse/revenue")
async def get_twse_monthly_revenue():
    """
    📈 取得上市公司每月營業收入
    
    資料來源：TWSE OpenAPI
    
    包含：
    - 當月營收
    - 月增率
    - 年增率
    
    Returns:
        所有上市公司的最新月營收資料
    """
    data = await TWSEOpenAPI.get_monthly_revenue()
    
    if not data:
        return {
            "success": False,
            "message": "無法取得營收資料",
            "count": 0,
            "data": {}
        }
    
    # 營收成長前 20 名（年增率）
    top_growth = sorted(
        [(k, v) for k, v in data.items() if v.get('revenue_yoy') and v.get('revenue_yoy') > 0],
        key=lambda x: x[1].get('revenue_yoy', 0),
        reverse=True
    )[:20]
    
    return {
        "success": True,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "highlights": {
            "top_growth": [{"stock_id": k, **v} for k, v in top_growth],
        },
        "data": data
    }


@router.get("/twse/dividend")
async def get_twse_dividend_schedule():
    """
    💰 取得除權除息預告表
    
    資料來源：TWSE OpenAPI
    
    包含：
    - 除權息日期
    - 現金股利
    - 股票股利
    
    Returns:
        近期即將除權息的股票列表
    """
    data = await TWSEOpenAPI.get_dividend_schedule()
    
    if not data:
        return {
            "success": True,
            "message": "近期無除權息股票",
            "count": 0,
            "data": {}
        }
    
    # 按日期排序
    sorted_data = dict(sorted(
        data.items(),
        key=lambda x: x[1].get('ex_date', ''),
        reverse=False
    ))
    
    return {
        "success": True,
        "count": len(data),
        "updated_at": datetime.now().isoformat(),
        "data": sorted_data
    }


@router.get("/twse/stock-extended/{stock_id}")
async def get_twse_stock_extended(stock_id: str):
    """
    📊 取得單一股票擴展資訊（V10.11）
    
    整合多個 TWSE API 取得完整資料：
    - 基本面（本益比、殖利率、淨值比）
    - 籌碼面（三大法人、融資融券）
    - 營收動能
    - 注意股票狀態
    
    Args:
        stock_id: 股票代號
        
    Returns:
        整合後的完整股票資訊
    """
    result = {
        "stock_id": stock_id,
        "name": None,
    }
    
    # 1. 基本資訊和本益比
    per_data = await TWSEOpenAPI.get_per_dividend_all()
    if per_data and stock_id in per_data:
        info = per_data[stock_id]
        result["name"] = info.get("name")
        result["pe_ratio"] = info.get("pe_ratio")
        result["pb_ratio"] = info.get("pb_ratio")
        result["dividend_yield"] = info.get("dividend_yield")
    
    # 2. 當日成交
    daily_data = await TWSEOpenAPI.get_daily_trading_all()
    if daily_data and stock_id in daily_data:
        info = daily_data[stock_id]
        result["name"] = result["name"] or info.get("name")
        result["price"] = info.get("close")
        result["change"] = info.get("change")
        result["change_percent"] = info.get("change_percent")
        result["volume"] = info.get("trade_volume")
    
    # 3. 三大法人
    inst_data = await TWSEOpenAPI.get_institutional_trading()
    if inst_data and stock_id in inst_data:
        info = inst_data[stock_id]
        result["institutional"] = {
            "foreign_net": info.get("foreign_net"),
            "trust_net": info.get("trust_net"),
            "dealer_net": info.get("dealer_net"),
            "total_net": info.get("total_net"),
        }
    
    # 4. 融資融券
    margin_data = await TWSEOpenAPI.get_margin_trading()
    if margin_data and stock_id in margin_data:
        info = margin_data[stock_id]
        result["margin"] = {
            "margin_balance": info.get("margin_balance"),
            "short_balance": info.get("short_balance"),
        }
    
    # 5. 營收
    revenue_data = await TWSEOpenAPI.get_monthly_revenue()
    if revenue_data and stock_id in revenue_data:
        info = revenue_data[stock_id]
        result["revenue"] = {
            "revenue": info.get("revenue"),
            "revenue_mom": info.get("revenue_mom"),
            "revenue_yoy": info.get("revenue_yoy"),
            "revenue_date": info.get("revenue_date"),
        }
    
    # 6. 注意股票
    attention_data = await TWSEOpenAPI.get_attention_stocks()
    if attention_data and stock_id in attention_data:
        result["is_attention"] = True
        result["attention_reason"] = attention_data[stock_id].get("attention_reason")
    else:
        result["is_attention"] = False
    
    if not result.get("name"):
        return {
            "success": False,
            "message": f"找不到股票 {stock_id}",
        }

    return {
        "success": True,
        "updated_at": datetime.now().isoformat(),
        "data": result
    }


# ============================================================
# 🆕 V10.23: 自動資料更新 API
# ============================================================

from ..services.data_scheduler import get_scheduler, get_update_tracker
from ..services.performance_tracker import get_performance_tracker

@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    V10.23: 取得排程器狀態

    返回排程器的運行狀態、更新次數等資訊
    """
    scheduler = get_scheduler()
    return {
        "success": True,
        **scheduler.get_status()
    }


@router.post("/scheduler/start")
async def start_scheduler():
    """
    V10.23: 啟動排程器

    開始自動更新資料（盤中會自動更新熱門股票）
    """
    scheduler = get_scheduler()
    await scheduler.start()
    return {
        "success": True,
        "message": "排程器已啟動",
        **scheduler.get_status()
    }


@router.post("/scheduler/stop")
async def stop_scheduler():
    """
    V10.23: 停止排程器
    """
    scheduler = get_scheduler()
    await scheduler.stop()
    return {
        "success": True,
        "message": "排程器已停止",
        **scheduler.get_status()
    }


@router.post("/scheduler/force-update")
async def force_update(stock_id: Optional[str] = Query(None, description="股票代號，空表示更新所有")):
    """
    V10.23: 強制更新資料

    Args:
        stock_id: 指定股票代號，不指定則更新所有追蹤股票
    """
    scheduler = get_scheduler()
    result = await scheduler.force_update(stock_id)
    return result


@router.get("/scheduler/tracked-stocks")
async def get_tracked_stocks():
    """
    V10.23: 取得追蹤股票清單
    """
    scheduler = get_scheduler()
    return {
        "success": True,
        "tracked_stocks": scheduler.get_tracked_stocks(),
        "count": len(scheduler.get_tracked_stocks())
    }


@router.post("/scheduler/track/{stock_id}")
async def add_tracked_stock(stock_id: str):
    """
    V10.23: 添加追蹤股票
    """
    scheduler = get_scheduler()
    scheduler.add_tracked_stock(stock_id)
    return {
        "success": True,
        "message": f"已添加 {stock_id} 到追蹤清單",
        "tracked_stocks": scheduler.get_tracked_stocks()
    }


@router.delete("/scheduler/track/{stock_id}")
async def remove_tracked_stock(stock_id: str):
    """
    V10.23: 移除追蹤股票
    """
    scheduler = get_scheduler()
    scheduler.remove_tracked_stock(stock_id)
    return {
        "success": True,
        "message": f"已從追蹤清單移除 {stock_id}",
        "tracked_stocks": scheduler.get_tracked_stocks()
    }


@router.get("/update-tracker/status")
async def get_update_tracker_status():
    """
    V10.23: 取得資料更新狀態
    """
    tracker = get_update_tracker()
    return {
        "success": True,
        **tracker.get_all_status()
    }


@router.get("/data-status")
async def get_data_status():
    """
    V10.35: 取得資料狀態（供前端顯示）

    回傳：
    - data_date: 資料日期
    - current_date: 今日日期
    - is_stale: 資料是否過期
    - is_trading_hours: 是否交易時段
    - is_weekend: 是否週末
    - message: 狀態訊息
    """
    from app.services.cache_service import is_trading_hours

    now = datetime.now()
    current_date = now.strftime("%Y/%m/%d")
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    is_weekend = weekday >= 5

    # 取得最近的交易日期
    # 週六：上週五，週日：上週五
    if weekday == 5:  # Saturday
        last_trading_day = now - timedelta(days=1)
    elif weekday == 6:  # Sunday
        last_trading_day = now - timedelta(days=2)
    else:
        last_trading_day = now

    last_trading_date = last_trading_day.strftime("%Y/%m/%d")

    # 嘗試從快取取得資料日期
    data_date = None
    try:
        # 從 TWSE 資料取得實際資料日期
        twse_data = await TWSEOpenAPI.get_per_dividend_all()
        if twse_data:
            sample = next(iter(twse_data.values()), {})
            raw_date = sample.get("date", "")
            if raw_date:
                # 轉換民國年為西元年
                try:
                    roc_year = int(raw_date[:3])
                    month = raw_date[3:5]
                    day = raw_date[5:7]
                    ad_year = roc_year + 1911
                    data_date = f"{ad_year}/{month}/{day}"
                except:
                    data_date = raw_date
    except:
        pass

    # 判斷資料是否過期
    # 週末：只要資料是上週五的就不算過期
    # 平日：如果資料日期不是今天，且已經過了開盤時間（09:30 後），則過期
    is_stale = False
    message = "資料正常"

    if data_date:
        if is_weekend:
            # 週末：資料應該是最近交易日的
            is_stale = False
            message = f"週末休市，顯示 {data_date} 資料"
        else:
            # 平日
            if data_date == current_date:
                is_stale = False
                message = "資料為最新"
            else:
                # 資料日期不是今天
                if now.hour < 9 or (now.hour == 9 and now.minute < 30):
                    # 早上9:30前，還沒開盤
                    is_stale = False
                    message = f"盤前，顯示 {data_date} 資料"
                else:
                    # 已經開盤但資料未更新
                    is_stale = True
                    message = f"資料需要更新（目前: {data_date}）"
    else:
        if is_weekend:
            is_stale = False
            message = "週末休市"
        else:
            is_stale = True
            message = "無法取得資料日期"

    return {
        "success": True,
        "data_date": data_date or last_trading_date,
        "current_date": current_date,
        "is_stale": is_stale,
        "is_trading_hours": is_trading_hours(),
        "is_weekend": is_weekend,
        "message": message
    }


@router.get("/update-tracker/stale")
async def get_stale_data(max_age_minutes: int = Query(30, description="過期時間（分鐘）")):
    """
    V10.23: 取得過期資料清單
    """
    tracker = get_update_tracker()
    stale = tracker.get_stale_data(max_age_minutes)
    return {
        "success": True,
        "stale_data": stale,
        "count": len(stale)
    }


# ============================================================
# V10.37: V10.23 歷史績效追蹤 API 已移至 performance_routes.py
# ============================================================

# =============================================================================
# V10.35.5 方案 G: 評分權重方案 API
# =============================================================================

@router.get("/scoring/weight-presets")
async def get_weight_presets():
    """
    V10.35.5: 取得評分權重方案列表

    返回可用的權重方案（均衡型、動能型、價值型、籌碼型）
    """
    from app.services.scoring_service import ScoringService
    presets = ScoringService.get_weight_presets()
    return {
        "success": True,
        "presets": presets,
    }


# =============================================================================
# V10.37: 美股支援 API 已移至 us_stock_routes.py
# V10.37: 美股技術分析 API 已移至 us_stock_routes.py
# =============================================================================

# =============================================================================
# V10.25: 增強版 AI 分析 API
# =============================================================================

from app.services.enhanced_ai_analysis import EnhancedAIAnalysis, enhanced_ai


@router.post("/enhanced-ai/sentiment")
async def analyze_sentiment(text: str, news_time: Optional[str] = None):
    """
    V10.25: 進階情緒分析
    分析新聞標題或內容的情緒傾向
    """
    try:
        time_obj = None
        if news_time:
            try:
                time_obj = datetime.fromisoformat(news_time)
            except:
                pass

        result = EnhancedAIAnalysis.analyze_sentiment(text, time_obj)
        return {
            "success": True,
            "data": {
                "score": result.score,
                "label": result.label,
                "strength": result.strength,
                "confidence": result.confidence,
                "details": result.details,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/enhanced-ai/industry/{stock_id}")
async def analyze_industry(stock_id: str):
    """
    V10.25: 產業連動分析
    分析股票的產業相關性和連動影響
    """
    try:
        result = EnhancedAIAnalysis.analyze_industry(stock_id)
        return {
            "success": True,
            "data": {
                "industry": result.industry,
                "correlation_score": result.correlation_score,
                "supply_chain_impact": result.supply_chain_impact,
                "rotation_signal": result.rotation_signal,
                "related_stocks": result.related_stocks,
                "details": result.details,
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/enhanced-ai/score")
async def calculate_enhanced_score(
    technical_score: int = Query(..., ge=0, le=100),
    chip_score: int = Query(..., ge=0, le=100),
    fundamental_score: int = Query(..., ge=0, le=100),
    sentiment_score: int = Query(50, ge=0, le=100),
    industry_score: int = Query(50, ge=0, le=100),
):
    """
    V10.25: 計算增強版綜合評分
    使用動態權重和多因子模型
    """
    try:
        # 建立模擬的情緒和產業分析結果
        from app.services.enhanced_ai_analysis import SentimentResult, IndustryAnalysis

        sentiment_result = SentimentResult(
            score=sentiment_score,
            label="利多" if sentiment_score > 55 else ("利空" if sentiment_score < 45 else "中性"),
            strength="中",
            confidence=0.6,
            details={}
        )

        industry_analysis = IndustryAnalysis(
            industry="未知",
            correlation_score=industry_score,
            supply_chain_impact="一般",
            rotation_signal="中性",
            related_stocks=[],
            details={}
        )

        result = EnhancedAIAnalysis.calculate_enhanced_score(
            technical_score=technical_score,
            chip_score=chip_score,
            fundamental_score=fundamental_score,
            sentiment_result=sentiment_result,
            industry_analysis=industry_analysis
        )

        # 取得推薦
        recommendation = EnhancedAIAnalysis.get_ai_recommendation(
            result["final_score"],
            result["confidence"]
        )

        return {
            "success": True,
            "data": {
                **result,
                "recommendation": recommendation
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/enhanced-ai/industry-map")
async def get_industry_map():
    """
    V10.25: 取得產業分類對照表
    """
    return {
        "success": True,
        "data": {
            "industries": list(EnhancedAIAnalysis.INDUSTRY_MAP.keys()),
            "industry_stocks": EnhancedAIAnalysis.INDUSTRY_MAP,
            "supply_chain": list(EnhancedAIAnalysis.SUPPLY_CHAIN.keys()),
        }
    }


@router.get("/enhanced-ai/related-stocks/{stock_id}")
async def get_related_stocks(stock_id: str):
    """
    V10.25: 取得相關股票（產業連動）
    """
    try:
        analysis = EnhancedAIAnalysis.analyze_industry(stock_id)

        # 取得供應鏈相關
        supply_chain_stocks = []
        if stock_id in EnhancedAIAnalysis.SUPPLY_CHAIN:
            chain = EnhancedAIAnalysis.SUPPLY_CHAIN[stock_id]
            supply_chain_stocks = chain.get("downstream", []) + chain.get("upstream", [])

        return {
            "success": True,
            "data": {
                "stock_id": stock_id,
                "industry": analysis.industry,
                "same_industry": analysis.related_stocks,
                "supply_chain": supply_chain_stocks[:5],
                "total_related": len(analysis.related_stocks) + len(supply_chain_stocks),
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# V10.37: 進階績效統計 API 已移至 performance_routes.py
# V10.37: 風險管理 API 已移至 risk_routes.py
# V10.37: ML 預測 API 已移至 ml_routes.py
# =============================================================================
