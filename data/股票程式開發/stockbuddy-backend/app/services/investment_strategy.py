"""
📈 綜合投資策略服務 V10.16
StockBuddy - Comprehensive Investment Strategy Service

提供專業投顧級的完整投資分析與策略建議：

1. 投資建議等級 (Investment Rating)
   - Strong Buy: 強力推薦買入
   - Buy: 推薦買入
   - Hold: 持有觀望
   - Reduce: 建議減碼
   - Sell: 建議賣出

2. 完整操作策略 (Trading Strategy)
   - Entry Strategy: 進場策略與時機
   - Add Position: 加碼策略
   - Stop Loss: 止損策略
   - Take Profit: 獲利了結策略
   - Position Sizing: 資金配置建議

3. 多維度深度分析 (Multi-Dimensional Analysis)
   - 基本面分析 (Fundamental)
   - 技術面分析 (Technical)
   - 籌碼面分析 (Chip)
   - 產業趨勢分析 (Industry)
   - 風險評估 (Risk Assessment)

4. 投資組合建議 (Portfolio Recommendations)
   - 配置比例建議
   - 分散風險策略
   - 相關性分析
"""

import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 內部服務
from app.services.twse_openapi import TWSEOpenAPI
from app.services.finmind_service import FinMindService
from app.services.performance_analytics import PerformanceAnalytics
from app.services.cache_service import SmartTTL, is_trading_hours


class InvestmentRating(str, Enum):
    """投資建議等級"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    REDUCE = "reduce"
    SELL = "sell"


class RiskLevel(str, Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class TradingStrategy:
    """交易策略"""
    # 進場策略
    entry_price: float              # 建議進場價
    entry_range: Tuple[float, float]  # 進場區間
    entry_timing: str               # 進場時機建議
    entry_signals: List[str]        # 進場訊號

    # 加碼策略
    add_position_levels: List[Dict]  # 加碼價位和比例
    add_position_condition: str      # 加碼條件

    # 止損策略
    stop_loss_price: float          # 止損價
    stop_loss_percent: float        # 止損百分比
    trailing_stop: bool             # 是否使用移動止損
    trailing_stop_percent: float    # 移動止損百分比

    # 獲利了結策略
    target_price_1: float           # 第一目標價
    target_price_2: float           # 第二目標價
    target_price_3: float           # 第三目標價
    profit_taking_plan: List[Dict]  # 分批出場計劃

    # 資金配置
    suggested_position_percent: float  # 建議倉位百分比
    max_position_percent: float        # 最大倉位百分比
    position_sizing_reason: str        # 倉位建議理由


@dataclass
class RiskAssessment:
    """風險評估"""
    overall_risk: RiskLevel         # 整體風險等級
    risk_score: int                 # 風險分數 (0-100, 越高越危險)

    # 各類風險
    market_risk: int                # 市場風險
    liquidity_risk: int             # 流動性風險
    volatility_risk: int            # 波動風險
    fundamental_risk: int           # 基本面風險

    # 風險因子
    risk_factors: List[str]         # 風險因素列表
    mitigation_strategies: List[str]  # 風險緩解策略


@dataclass
class ComprehensiveStrategy:
    """綜合投資策略"""
    # 基本資訊
    stock_id: str
    stock_name: str
    current_price: float
    analysis_time: str

    # 投資建議
    rating: InvestmentRating
    rating_score: int               # 評分 (0-100)
    rating_summary: str             # 評級摘要
    rating_reasons: List[str]       # 評級理由

    # 多維度分數
    technical_score: int
    fundamental_score: int
    chip_score: int
    sentiment_score: int
    industry_score: int

    # 交易策略
    trading_strategy: TradingStrategy

    # 風險評估
    risk_assessment: RiskAssessment

    # 詳細分析
    technical_analysis: Dict
    fundamental_analysis: Dict
    chip_analysis: Dict
    industry_analysis: Dict

    # 投資摘要
    investment_thesis: str          # 投資論點
    key_catalysts: List[str]        # 關鍵催化劑
    key_risks: List[str]            # 關鍵風險

    # 投資時間框架
    investment_horizon: str         # 投資期限建議
    suitable_investor: str          # 適合投資者類型


class InvestmentStrategyService:
    """綜合投資策略服務"""

    # 快取設定（使用智能 TTL）
    _cache: Dict[str, Any] = {}
    _cache_time: Dict[str, float] = {}
    # 🆕 V10.16.1: 改用智能 TTL，盤後自動延長快取時間

    # ============================================================
    # 主要入口
    # ============================================================

    @classmethod
    async def get_comprehensive_strategy(
        cls,
        stock_id: str,
        include_portfolio_context: bool = False
    ) -> Dict[str, Any]:
        """
        取得股票的綜合投資策略

        Args:
            stock_id: 股票代號
            include_portfolio_context: 是否包含投資組合上下文

        Returns:
            完整的投資策略分析
        """
        cache_key = f"strategy_{stock_id}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached

        print(f"📊 產生 {stock_id} 綜合投資策略...")

        try:
            # 並行取得各項資料
            tasks = [
                cls._get_stock_basic_info(stock_id),
                cls._analyze_technical_deep(stock_id),
                cls._analyze_fundamental_deep(stock_id),
                cls._analyze_chip_deep(stock_id),
                cls._analyze_industry(stock_id),
                cls._get_historical_performance(stock_id),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            basic_info = results[0] if not isinstance(results[0], Exception) else {}
            technical = results[1] if not isinstance(results[1], Exception) else {}
            fundamental = results[2] if not isinstance(results[2], Exception) else {}
            chip = results[3] if not isinstance(results[3], Exception) else {}
            industry = results[4] if not isinstance(results[4], Exception) else {}
            performance = results[5] if not isinstance(results[5], Exception) else {}

            # 計算綜合評分
            scores = cls._calculate_comprehensive_scores(
                technical, fundamental, chip, industry
            )

            # 產生投資建議
            rating, rating_score, rating_summary, rating_reasons = cls._generate_rating(
                scores, technical, fundamental, chip, industry
            )

            # 產生交易策略
            trading_strategy = cls._generate_trading_strategy(
                basic_info, scores, technical, fundamental, chip
            )

            # 風險評估
            risk_assessment = cls._assess_risk(
                basic_info, technical, fundamental, chip, performance
            )

            # 產生投資論點
            thesis, catalysts, risks = cls._generate_investment_thesis(
                basic_info, technical, fundamental, chip, industry
            )

            # 建議投資期限和適合投資者
            horizon, investor_type = cls._suggest_investment_profile(
                rating, risk_assessment, fundamental
            )

            result = {
                "stock_id": stock_id,
                "stock_name": basic_info.get("name", stock_id),
                "current_price": basic_info.get("price", 0),
                "analysis_time": datetime.now().isoformat(),

                # 投資建議
                "rating": rating.value,
                "rating_score": rating_score,
                "rating_summary": rating_summary,
                "rating_reasons": rating_reasons,

                # 多維度分數
                "technical_score": scores["technical"],
                "fundamental_score": scores["fundamental"],
                "chip_score": scores["chip"],
                "sentiment_score": scores.get("sentiment", 50),
                "industry_score": scores["industry"],
                "overall_score": scores["overall"],

                # 交易策略
                "trading_strategy": asdict(trading_strategy) if trading_strategy else None,

                # 風險評估
                "risk_assessment": asdict(risk_assessment) if risk_assessment else None,

                # 詳細分析
                "technical_analysis": technical,
                "fundamental_analysis": fundamental,
                "chip_analysis": chip,
                "industry_analysis": industry,
                "performance_analysis": performance,

                # 投資摘要
                "investment_thesis": thesis,
                "key_catalysts": catalysts,
                "key_risks": risks,

                # 投資建議
                "investment_horizon": horizon,
                "suitable_investor": investor_type,
            }

            cls._set_cache(cache_key, result)
            print(f"✅ {stock_id} 綜合投資策略產生完成")

            return result

        except Exception as e:
            print(f"❌ {stock_id} 綜合策略產生失敗: {e}")
            return {"error": str(e), "stock_id": stock_id}

    # 備用股票清單（當 TWSE API 無法連接時使用）
    FALLBACK_STOCKS = [
        "2330", "2317", "2454", "2308", "2382",  # 電子權值股
        "2881", "2882", "2891", "2886", "2884",  # 金融股
        "1301", "1303", "1326", "2002", "2412",  # 傳產/電信
        "3711", "2379", "3008", "2603", "2609",  # 熱門股
    ]

    @classmethod
    async def get_strategy_picks(cls, top_n: int = 10) -> Dict[str, Any]:
        """
        取得策略精選股票（結合 AI 和綜合策略）

        Returns:
            {
                "updated_at": "...",
                "market_overview": {...},
                "strategy_picks": [...],
                "portfolio_allocation": {...}
            }
        """
        cache_key = f"strategy_picks_{top_n}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached

        print("🎯 產生綜合投資策略精選...")

        try:
            # 取得市場資料
            all_stocks = await TWSEOpenAPI.get_all_stocks_summary()

            # 如果 TWSE API 失敗，使用備用方案
            if not all_stocks:
                print("⚠️ TWSE API 無法連接，使用備用股票清單...")
                return await cls._get_strategy_picks_fallback(top_n)

            # 初步篩選
            candidates = cls._pre_filter_stocks(all_stocks)
            print(f"📊 篩選後候選股: {len(candidates)} 檔")

            # 取前 30 檔做深度分析
            top_candidates = sorted(
                candidates,
                key=lambda x: x.get("volume", 0),
                reverse=True
            )[:30]

            # 並行深度分析
            tasks = [
                cls.get_comprehensive_strategy(stock["stock_id"])
                for stock in top_candidates
            ]

            strategies = await asyncio.gather(*tasks, return_exceptions=True)

            # 過濾有效結果並排序
            valid_strategies = []
            for s in strategies:
                if isinstance(s, dict) and "error" not in s and s.get("rating_score", 0) > 0:
                    valid_strategies.append(s)

            # 依評分排序
            valid_strategies.sort(key=lambda x: x.get("rating_score", 0), reverse=True)

            # 取前 N 檔
            top_picks = valid_strategies[:top_n]

            # 產生投資組合配置建議
            portfolio_allocation = cls._generate_portfolio_allocation(top_picks)

            # 市場概覽
            market_overview = await cls._get_market_overview()

            result = {
                "updated_at": datetime.now().isoformat(),
                "market_overview": market_overview,
                "strategy_picks": top_picks,
                "portfolio_allocation": portfolio_allocation,
                "total_analyzed": len(candidates),
            }

            cls._set_cache(cache_key, result)
            print(f"✅ 策略精選產生完成: {len(top_picks)} 檔")

            return result

        except Exception as e:
            print(f"❌ 策略精選產生失敗: {e}")
            # 發生例外時也嘗試備用方案
            try:
                return await cls._get_strategy_picks_fallback(top_n)
            except:
                return {"error": str(e), "strategy_picks": []}

    @classmethod
    async def _get_strategy_picks_fallback(cls, top_n: int) -> Dict[str, Any]:
        """
        備用方案：使用預設股票清單產生策略精選
        """
        print("🔄 使用備用方案產生策略精選...")

        # 使用備用股票清單進行分析
        tasks = [
            cls.get_comprehensive_strategy(stock_id)
            for stock_id in cls.FALLBACK_STOCKS[:top_n + 5]  # 多取幾檔以防有失敗的
        ]

        strategies = await asyncio.gather(*tasks, return_exceptions=True)

        # 過濾有效結果
        valid_strategies = []
        for s in strategies:
            if isinstance(s, dict) and "error" not in s and s.get("rating_score", 0) > 0:
                valid_strategies.append(s)

        # 排序並取前 N 檔
        valid_strategies.sort(key=lambda x: x.get("rating_score", 0), reverse=True)
        top_picks = valid_strategies[:top_n]

        # 產生配置建議
        portfolio_allocation = cls._generate_portfolio_allocation(top_picks)

        # 市場概覽（使用預設值）
        market_overview = {
            "taiex_value": None,
            "taiex_change": None,
            "taiex_change_pct": None,
            "market_sentiment": "neutral",
            "note": "市場資料暫時無法取得"
        }

        result = {
            "updated_at": datetime.now().isoformat(),
            "market_overview": market_overview,
            "strategy_picks": top_picks,
            "portfolio_allocation": portfolio_allocation,
            "total_analyzed": len(cls.FALLBACK_STOCKS),
            "is_fallback": True,  # 標記為備用方案
            "fallback_reason": "TWSE API 暫時無法連接"
        }

        print(f"✅ 備用方案完成: {len(top_picks)} 檔")
        return result

    # ============================================================
    # 資料取得
    # ============================================================

    @classmethod
    async def _get_stock_basic_info(cls, stock_id: str) -> Dict:
        """取得股票基本資訊"""
        try:
            all_data = await TWSEOpenAPI.get_all_stocks_summary()
            if stock_id in all_data:
                data = all_data[stock_id]
                return {
                    "stock_id": stock_id,
                    "name": data.get("name", stock_id),
                    "price": data.get("price", 0),
                    "change": data.get("change", 0),
                    "change_percent": data.get("change_percent", 0),
                    "volume": data.get("volume", 0),
                    "pe_ratio": data.get("pe_ratio"),
                    "pb_ratio": data.get("pb_ratio"),
                    "dividend_yield": data.get("dividend_yield"),
                }
            return {"stock_id": stock_id, "name": stock_id}
        except Exception as e:
            print(f"⚠️ 取得 {stock_id} 基本資訊失敗: {e}")
            return {"stock_id": stock_id}

    @classmethod
    async def _analyze_technical_deep(cls, stock_id: str) -> Dict:
        """深度技術面分析"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{stock_id}.TW")
            hist = ticker.history(period="6mo")

            if hist.empty or len(hist) < 20:
                return {"score": 50, "signals": [], "detail": "資料不足"}

            closes = hist['Close'].tolist()
            volumes = hist['Volume'].tolist()
            highs = hist['High'].tolist()
            lows = hist['Low'].tolist()

            current_price = closes[-1]

            # 計算各項技術指標
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
            ma20 = sum(closes[-20:]) / 20
            ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else ma20

            # RSI
            rsi = cls._calculate_rsi(closes)

            # MACD
            macd, signal, histogram = cls._calculate_macd(closes)

            # KD
            k, d = cls._calculate_kd(highs, lows, closes)

            # 布林通道
            bb_upper, bb_middle, bb_lower = cls._calculate_bollinger(closes)

            # 成交量分析
            avg_vol = sum(volumes[-20:]) / 20
            vol_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1

            # ATR (平均真實範圍)
            atr = cls._calculate_atr(highs, lows, closes)

            # 評分
            score = 50
            signals = []
            analysis = {}

            # 均線分析 (25分)
            if current_price > ma5 > ma10 > ma20:
                score += 20
                signals.append("完美多頭排列")
                analysis["ma_status"] = "strong_bullish"
            elif current_price > ma5 > ma20:
                score += 15
                signals.append("多頭排列")
                analysis["ma_status"] = "bullish"
            elif current_price > ma5:
                score += 8
                signals.append("站上5日線")
                analysis["ma_status"] = "neutral_bullish"
            elif current_price < ma5 < ma10 < ma20:
                score -= 15
                signals.append("空頭排列")
                analysis["ma_status"] = "bearish"

            # 季線分析
            if current_price > ma60:
                score += 5
                signals.append("站上季線")

            # RSI 分析 (15分)
            if 30 <= rsi <= 40:
                score += 15
                signals.append("RSI 超賣回升")
            elif 40 < rsi <= 60:
                score += 8
                signals.append("RSI 中性健康")
            elif rsi < 30:
                score += 10
                signals.append("RSI 極度超賣")
            elif rsi > 80:
                score -= 10
                signals.append("RSI 超買警戒")

            # MACD 分析 (15分)
            if histogram > 0 and macd > signal:
                score += 12
                signals.append("MACD 金叉")
            elif histogram > 0:
                score += 5
                signals.append("MACD 多頭")
            elif histogram < 0 and macd < signal:
                score -= 8
                signals.append("MACD 死叉")

            # KD 分析 (10分)
            if k > d and k < 80:
                score += 8
                signals.append("KD 黃金交叉")
            elif k < d and k > 20:
                score -= 5
                signals.append("KD 死亡交叉")
            elif k < 20:
                score += 5
                signals.append("KD 超賣區")

            # 成交量分析 (10分)
            if vol_ratio > 2:
                score += 10
                signals.append("爆量突破")
            elif vol_ratio > 1.5:
                score += 6
                signals.append("量增")
            elif vol_ratio < 0.5:
                score -= 3
                signals.append("量縮")

            # 布林通道分析 (5分)
            if current_price > bb_upper:
                signals.append("突破布林上軌")
            elif current_price < bb_lower:
                score += 5
                signals.append("觸及布林下軌")

            # 限制分數範圍
            score = max(10, min(95, score))

            return {
                "score": score,
                "signals": signals,
                "indicators": {
                    "ma5": round(ma5, 2),
                    "ma10": round(ma10, 2),
                    "ma20": round(ma20, 2),
                    "ma60": round(ma60, 2),
                    "rsi": round(rsi, 2),
                    "macd": round(macd, 4),
                    "macd_signal": round(signal, 4),
                    "macd_histogram": round(histogram, 4),
                    "k": round(k, 2),
                    "d": round(d, 2),
                    "bb_upper": round(bb_upper, 2),
                    "bb_lower": round(bb_lower, 2),
                    "volume_ratio": round(vol_ratio, 2),
                    "atr": round(atr, 2),
                },
                "analysis": analysis,
                "trend": "bullish" if score >= 65 else "bearish" if score <= 35 else "neutral",
            }

        except Exception as e:
            print(f"⚠️ {stock_id} 技術分析失敗: {e}")
            return {"score": 50, "signals": [], "detail": str(e)}

    @classmethod
    async def _analyze_fundamental_deep(cls, stock_id: str) -> Dict:
        """深度基本面分析"""
        try:
            # 取得本益比、殖利率等資料
            per_data = await TWSEOpenAPI.get_per_dividend_all()

            score = 50
            signals = []

            if stock_id in per_data:
                data = per_data[stock_id]
                pe = data.get("pe_ratio")
                dy = data.get("dividend_yield")
                pb = data.get("pb_ratio")

                # 本益比分析 (25分)
                if pe:
                    if pe < 10:
                        score += 20
                        signals.append("P/E 低估")
                    elif pe < 15:
                        score += 15
                        signals.append("P/E 合理偏低")
                    elif pe < 20:
                        score += 8
                        signals.append("P/E 合理")
                    elif pe > 30:
                        score -= 10
                        signals.append("P/E 偏高")
                    elif pe > 50:
                        score -= 15
                        signals.append("P/E 過高")

                # 殖利率分析 (20分)
                if dy:
                    if dy > 6:
                        score += 18
                        signals.append("高殖利率")
                    elif dy > 4:
                        score += 12
                        signals.append("殖利率優良")
                    elif dy > 2:
                        score += 5
                        signals.append("殖利率一般")

                # 淨值比分析 (10分)
                if pb:
                    if pb < 1:
                        score += 10
                        signals.append("股價低於淨值")
                    elif pb < 1.5:
                        score += 5
                        signals.append("P/B 合理")
                    elif pb > 3:
                        score -= 5
                        signals.append("P/B 偏高")

                return {
                    "score": max(10, min(95, score)),
                    "signals": signals,
                    "metrics": {
                        "pe_ratio": pe,
                        "dividend_yield": dy,
                        "pb_ratio": pb,
                    },
                    "valuation": "undervalued" if score >= 70 else "overvalued" if score <= 30 else "fair",
                }

            return {"score": 50, "signals": ["資料不足"], "metrics": {}}

        except Exception as e:
            print(f"⚠️ {stock_id} 基本面分析失敗: {e}")
            return {"score": 50, "signals": [], "detail": str(e)}

    @classmethod
    async def _analyze_chip_deep(cls, stock_id: str) -> Dict:
        """深度籌碼面分析"""
        try:
            inst_data = await TWSEOpenAPI.get_institutional_trading()

            score = 50
            signals = []

            if stock_id in inst_data:
                data = inst_data[stock_id]
                foreign_net = data.get("foreign_net", 0) or 0
                trust_net = data.get("trust_net", 0) or 0
                dealer_net = data.get("dealer_net", 0) or 0
                total_net = data.get("total_net", 0) or 0

                # 外資分析 (25分)
                if foreign_net > 5000:
                    score += 20
                    signals.append("外資大買超")
                elif foreign_net > 1000:
                    score += 12
                    signals.append("外資買超")
                elif foreign_net < -5000:
                    score -= 15
                    signals.append("外資大賣超")
                elif foreign_net < -1000:
                    score -= 8
                    signals.append("外資賣超")

                # 投信分析 (20分)
                if trust_net > 500:
                    score += 15
                    signals.append("投信買超")
                elif trust_net > 100:
                    score += 8
                    signals.append("投信小幅買超")
                elif trust_net < -500:
                    score -= 10
                    signals.append("投信賣超")

                # 三大法人合計 (10分)
                if total_net > 10000:
                    score += 10
                    signals.append("三大法人聯手買超")
                elif total_net < -10000:
                    score -= 10
                    signals.append("三大法人聯手賣超")

                return {
                    "score": max(10, min(95, score)),
                    "signals": signals,
                    "institutional": {
                        "foreign_net": foreign_net,
                        "trust_net": trust_net,
                        "dealer_net": dealer_net,
                        "total_net": total_net,
                    },
                    "chip_trend": "bullish" if total_net > 0 else "bearish",
                }

            return {"score": 50, "signals": ["無法人資料"], "institutional": {}}

        except Exception as e:
            print(f"⚠️ {stock_id} 籌碼分析失敗: {e}")
            return {"score": 50, "signals": [], "detail": str(e)}

    @classmethod
    async def _analyze_industry(cls, stock_id: str) -> Dict:
        """產業趨勢分析"""
        # 產業分類對照表
        INDUSTRY_MAP = {
            # 半導體
            "2330": ("半導體", ["AI", "晶圓代工", "台積電概念"]),
            "2454": ("半導體", ["IC設計", "聯發科概念"]),
            "2303": ("半導體", ["記憶體", "DRAM"]),
            "3711": ("半導體", ["日月光概念", "封測"]),
            # 電子
            "2317": ("電子代工", ["蘋果概念", "組裝代工"]),
            "2382": ("電子代工", ["雲端", "伺服器"]),
            # 金融
            "2881": ("金融", ["壽險", "金控"]),
            "2882": ("金融", ["銀行", "金控"]),
            # 傳產
            "1301": ("塑膠", ["台塑集團", "石化"]),
            "1303": ("塑膠", ["台塑集團", "電子材料"]),
            "2002": ("鋼鐵", ["中鋼集團"]),
            # 航運
            "2603": ("航運", ["貨櫃", "海運"]),
            "2609": ("航運", ["散裝", "海運"]),
        }

        industry, tags = INDUSTRY_MAP.get(stock_id, ("其他", []))

        # V10.38: 使用動態產業熱度評分
        try:
            from .industry_heat_service import IndustryHeatService

            heat_score = 0

            # 取得產業熱度
            if industry:
                heat = await IndustryHeatService.get_industry_heat(industry)
                heat_score = heat.heat_score

            # 取得標籤熱度（取最高）
            for tag in tags:
                tag_heat = await IndustryHeatService.get_industry_heat(tag)
                heat_score = max(heat_score, tag_heat.heat_score)

            # 轉換為 0-100 分數
            # heat_score 範圍 -10 ~ +10，轉換為 30 ~ 80
            score = 50 + (heat_score * 3)
            score = max(30, min(80, score))

            # 決定趨勢
            if heat_score >= 5:
                trend = "bullish"
                outlook = "看好"
            elif heat_score <= -3:
                trend = "bearish"
                outlook = "保守"
            else:
                trend = "neutral"
                outlook = "持平"

        except Exception:
            # V10.38: 降級到靜態評分
            HOT_INDUSTRIES = ["半導體", "AI", "電動車", "綠能"]
            WEAK_INDUSTRIES = ["傳產", "塑膠", "鋼鐵"]

            score = 50
            trend = "neutral"
            outlook = "持平"

            if industry in HOT_INDUSTRIES or any(t in HOT_INDUSTRIES for t in tags):
                score = 75
                trend = "bullish"
                outlook = "看好"
            elif industry in WEAK_INDUSTRIES:
                score = 35
                trend = "bearish"
                outlook = "保守"

        return {
            "score": score,
            "industry": industry,
            "tags": tags,
            "trend": trend,
            "outlook": outlook,
        }

    @classmethod
    async def _get_historical_performance(cls, stock_id: str) -> Dict:
        """取得歷史績效"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{stock_id}.TW")
            hist = ticker.history(period="1y")

            if hist.empty:
                return {}

            closes = hist['Close'].tolist()

            # 計算報酬率
            returns = []
            for i in range(1, len(closes)):
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)

            if not returns:
                return {}

            # 計算績效指標
            import numpy as np

            total_return = (closes[-1] - closes[0]) / closes[0] * 100
            volatility = np.std(returns) * np.sqrt(252) * 100

            # 最大回撤
            max_dd = PerformanceAnalytics.calculate_max_drawdown(closes)

            return {
                "total_return_pct": round(total_return, 2),
                "volatility_annual": round(volatility, 2),
                "max_drawdown_pct": max_dd.get("max_drawdown_pct", 0),
                "trading_days": len(closes),
            }

        except Exception as e:
            print(f"⚠️ {stock_id} 績效分析失敗: {e}")
            return {}

    # ============================================================
    # 評分與策略生成
    # ============================================================

    @classmethod
    def _calculate_comprehensive_scores(
        cls,
        technical: Dict,
        fundamental: Dict,
        chip: Dict,
        industry: Dict
    ) -> Dict[str, int]:
        """計算綜合評分"""
        tech_score = technical.get("score", 50)
        fund_score = fundamental.get("score", 50)
        chip_score = chip.get("score", 50)
        ind_score = industry.get("score", 50)

        # 權重: 技術 30%, 籌碼 30%, 基本面 25%, 產業 15%
        overall = int(
            tech_score * 0.30 +
            chip_score * 0.30 +
            fund_score * 0.25 +
            ind_score * 0.15
        )

        return {
            "technical": tech_score,
            "fundamental": fund_score,
            "chip": chip_score,
            "industry": ind_score,
            "overall": max(10, min(95, overall)),
        }

    @classmethod
    def _generate_rating(
        cls,
        scores: Dict,
        technical: Dict,
        fundamental: Dict,
        chip: Dict,
        industry: Dict
    ) -> Tuple[InvestmentRating, int, str, List[str]]:
        """生成投資建議"""
        overall = scores["overall"]
        reasons = []

        # 收集所有訊號作為理由
        reasons.extend(technical.get("signals", [])[:3])
        reasons.extend(fundamental.get("signals", [])[:2])
        reasons.extend(chip.get("signals", [])[:2])

        # 決定評級
        if overall >= 80:
            rating = InvestmentRating.STRONG_BUY
            summary = "強力推薦買入：多項指標呈現強勢，建議積極布局"
        elif overall >= 65:
            rating = InvestmentRating.BUY
            summary = "推薦買入：整體表現良好，可考慮進場"
        elif overall >= 45:
            rating = InvestmentRating.HOLD
            summary = "持有觀望：指標中性，建議等待更明確訊號"
        elif overall >= 30:
            rating = InvestmentRating.REDUCE
            summary = "建議減碼：部分指標轉弱，建議降低持股比例"
        else:
            rating = InvestmentRating.SELL
            summary = "建議賣出：多項指標呈現弱勢，建議出場觀望"

        return rating, overall, summary, reasons

    @classmethod
    def _generate_trading_strategy(
        cls,
        basic_info: Dict,
        scores: Dict,
        technical: Dict,
        fundamental: Dict,
        chip: Dict
    ) -> TradingStrategy:
        """生成交易策略"""
        price = basic_info.get("price", 0)
        if price <= 0:
            price = 100  # 預設值

        indicators = technical.get("indicators", {})
        atr = indicators.get("atr", price * 0.03)

        overall_score = scores["overall"]

        # 進場策略
        entry_price = price
        entry_low = round(price * 0.97, 2)
        entry_high = round(price * 1.02, 2)

        if overall_score >= 70:
            entry_timing = "可積極進場，分批建立部位"
            entry_signals = ["多頭趨勢確立", "各維度指標強勢"]
        elif overall_score >= 55:
            entry_timing = "可伺機進場，建議逢回買進"
            entry_signals = ["整體趨勢偏多", "等待回檔訊號"]
        else:
            entry_timing = "建議觀望，等待更佳買點"
            entry_signals = ["趨勢尚未明朗"]

        # 加碼策略
        add_levels = [
            {"price": round(price * 0.95, 2), "percent": 30, "condition": "跌破5%加碼"},
            {"price": round(price * 0.90, 2), "percent": 20, "condition": "跌破10%加碼"},
        ]

        # 止損策略
        stop_loss_pct = 0.08 if overall_score >= 60 else 0.06
        stop_loss_price = round(price * (1 - stop_loss_pct), 2)

        # 目標價
        target_multiplier = 1 + (overall_score / 100)
        target_1 = round(price * 1.10, 2)
        target_2 = round(price * 1.20, 2)
        target_3 = round(price * target_multiplier, 2)

        # 分批出場計劃
        profit_plan = [
            {"target": target_1, "sell_percent": 30, "reason": "達成第一目標10%"},
            {"target": target_2, "sell_percent": 30, "reason": "達成第二目標20%"},
            {"target": target_3, "sell_percent": 40, "reason": "達成最終目標"},
        ]

        # 資金配置
        if overall_score >= 75:
            position_pct = 15
            max_position_pct = 20
            position_reason = "高評分股票，可較大比例配置"
        elif overall_score >= 60:
            position_pct = 10
            max_position_pct = 15
            position_reason = "中高評分，建議適度配置"
        else:
            position_pct = 5
            max_position_pct = 10
            position_reason = "評分一般，建議小比例試單"

        return TradingStrategy(
            entry_price=entry_price,
            entry_range=(entry_low, entry_high),
            entry_timing=entry_timing,
            entry_signals=entry_signals,
            add_position_levels=add_levels,
            add_position_condition="依紀律分批加碼，不追高",
            stop_loss_price=stop_loss_price,
            stop_loss_percent=stop_loss_pct * 100,
            trailing_stop=overall_score >= 70,
            trailing_stop_percent=5.0,
            target_price_1=target_1,
            target_price_2=target_2,
            target_price_3=target_3,
            profit_taking_plan=profit_plan,
            suggested_position_percent=position_pct,
            max_position_percent=max_position_pct,
            position_sizing_reason=position_reason,
        )

    @classmethod
    def _assess_risk(
        cls,
        basic_info: Dict,
        technical: Dict,
        fundamental: Dict,
        chip: Dict,
        performance: Dict
    ) -> RiskAssessment:
        """風險評估"""
        risk_factors = []
        mitigation = []

        # 市場風險
        market_risk = 50

        # 流動性風險
        volume = basic_info.get("volume", 0)
        if volume < 500000:
            liquidity_risk = 70
            risk_factors.append("成交量偏低，流動性風險較高")
            mitigation.append("避免大單進出，分批操作")
        elif volume < 1000000:
            liquidity_risk = 50
        else:
            liquidity_risk = 30

        # 波動風險
        volatility = performance.get("volatility_annual", 30)
        if volatility > 50:
            volatility_risk = 80
            risk_factors.append("年化波動率高，價格波動劇烈")
            mitigation.append("設定較寬止損，控制倉位")
        elif volatility > 30:
            volatility_risk = 50
        else:
            volatility_risk = 30

        # 基本面風險
        pe = fundamental.get("metrics", {}).get("pe_ratio")
        if pe and pe > 50:
            fundamental_risk = 70
            risk_factors.append("本益比偏高，估值風險")
            mitigation.append("關注獲利成長是否支撐估值")
        elif pe and pe < 0:
            fundamental_risk = 80
            risk_factors.append("公司虧損中")
            mitigation.append("密切關注財報轉盈進度")
        else:
            fundamental_risk = 40

        # 綜合風險分數
        overall_risk_score = int(
            market_risk * 0.25 +
            liquidity_risk * 0.25 +
            volatility_risk * 0.30 +
            fundamental_risk * 0.20
        )

        # 判定風險等級
        if overall_risk_score >= 70:
            risk_level = RiskLevel.VERY_HIGH
        elif overall_risk_score >= 55:
            risk_level = RiskLevel.HIGH
        elif overall_risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        if not risk_factors:
            risk_factors.append("整體風險可控")
        if not mitigation:
            mitigation.append("維持正常風險管理策略")

        return RiskAssessment(
            overall_risk=risk_level,
            risk_score=overall_risk_score,
            market_risk=market_risk,
            liquidity_risk=liquidity_risk,
            volatility_risk=volatility_risk,
            fundamental_risk=fundamental_risk,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation,
        )

    @classmethod
    def _generate_investment_thesis(
        cls,
        basic_info: Dict,
        technical: Dict,
        fundamental: Dict,
        chip: Dict,
        industry: Dict
    ) -> Tuple[str, List[str], List[str]]:
        """生成投資論點"""
        name = basic_info.get("name", "此股票")
        tech_signals = technical.get("signals", [])
        fund_signals = fundamental.get("signals", [])
        chip_signals = chip.get("signals", [])
        ind_tags = industry.get("tags", [])

        # 投資論點
        thesis_parts = []
        if any("多頭" in s for s in tech_signals):
            thesis_parts.append("技術面呈現多頭格局")
        if any("買超" in s for s in chip_signals):
            thesis_parts.append("法人積極布局")
        if any("低估" in s or "殖利率" in s for s in fund_signals):
            thesis_parts.append("估值具吸引力")

        thesis = f"{name}" + "，".join(thesis_parts) if thesis_parts else f"{name}整體表現中性，建議觀察後續發展"

        # 催化劑
        catalysts = []
        if ind_tags:
            catalysts.append(f"受惠{'/'.join(ind_tags[:2])}題材")
        if any("外資" in s and "買" in s for s in chip_signals):
            catalysts.append("外資持續買超")
        if any("金叉" in s for s in tech_signals):
            catalysts.append("技術面出現黃金交叉")

        if not catalysts:
            catalysts.append("待觀察後續催化因素")

        # 風險
        risks = []
        if any("空頭" in s or "死叉" in s for s in tech_signals):
            risks.append("技術面轉弱風險")
        if any("賣超" in s for s in chip_signals):
            risks.append("法人賣超壓力")
        if any("偏高" in s or "過高" in s for s in fund_signals):
            risks.append("估值偏高風險")

        if not risks:
            risks.append("目前無重大風險訊號")

        return thesis, catalysts, risks

    @classmethod
    def _suggest_investment_profile(
        cls,
        rating: InvestmentRating,
        risk: RiskAssessment,
        fundamental: Dict
    ) -> Tuple[str, str]:
        """建議投資期限和適合投資者"""

        # 投資期限
        if rating in [InvestmentRating.STRONG_BUY, InvestmentRating.BUY]:
            horizon = "短中期 (1-6個月)"
        elif rating == InvestmentRating.HOLD:
            horizon = "中長期 (3-12個月)"
        else:
            horizon = "不建議持有"

        # 適合投資者
        if risk.overall_risk == RiskLevel.LOW:
            investor = "適合保守型至積極型投資者"
        elif risk.overall_risk == RiskLevel.MEDIUM:
            investor = "適合穩健型至積極型投資者"
        elif risk.overall_risk == RiskLevel.HIGH:
            investor = "適合積極型投資者，需具備風險承受能力"
        else:
            investor = "僅適合高風險承受度之專業投資者"

        return horizon, investor

    # ============================================================
    # 投資組合配置
    # ============================================================

    @classmethod
    def _generate_portfolio_allocation(cls, picks: List[Dict]) -> Dict:
        """生成投資組合配置建議"""
        if not picks:
            return {}

        # 依評分分配權重
        total_score = sum(p.get("rating_score", 50) for p in picks)

        allocations = []
        for pick in picks:
            score = pick.get("rating_score", 50)
            weight = (score / total_score * 100) if total_score > 0 else (100 / len(picks))

            # 單一股票不超過 20%
            weight = min(weight, 20)

            allocations.append({
                "stock_id": pick.get("stock_id"),
                "stock_name": pick.get("stock_name"),
                "weight_percent": round(weight, 1),
                "rating": pick.get("rating"),
                "rating_score": score,
            })

        # 重新正規化到 100%
        total_weight = sum(a["weight_percent"] for a in allocations)
        if total_weight > 0:
            for a in allocations:
                a["weight_percent"] = round(a["weight_percent"] / total_weight * 100, 1)

        return {
            "allocations": allocations,
            "total_stocks": len(allocations),
            "strategy": "依綜合評分加權配置，單一股票上限20%",
            "rebalance_frequency": "建議每月檢視一次",
        }

    @classmethod
    async def _get_market_overview(cls) -> Dict:
        """取得市場概覽"""
        try:
            index = await TWSEOpenAPI.get_market_index()
            taiex = index.get("taiex", {})

            return {
                "taiex_value": taiex.get("value"),
                "taiex_change": taiex.get("change"),
                "taiex_change_pct": taiex.get("change_percent"),
                "market_sentiment": "bullish" if (taiex.get("change_percent") or 0) > 0 else "bearish",
            }
        except:
            return {}

    @classmethod
    def _pre_filter_stocks(cls, all_stocks: Dict) -> List[Dict]:
        """初步篩選股票"""
        filtered = []
        for stock_id, data in all_stocks.items():
            price = data.get("price", 0)
            volume = data.get("volume", 0)

            # 篩選條件
            if not price or price < 15 or price > 1500:
                continue
            if not volume or volume < 300000:
                continue
            if len(stock_id) != 4:
                continue

            filtered.append({
                "stock_id": stock_id,
                **data
            })

        return filtered

    # ============================================================
    # 技術指標計算
    # ============================================================

    @staticmethod
    def _calculate_rsi(closes: List[float], period: int = 14) -> float:
        """計算 RSI"""
        if len(closes) < period + 1:
            return 50

        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def _calculate_macd(
        closes: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[float, float, float]:
        """計算 MACD"""
        if len(closes) < slow:
            return 0, 0, 0

        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_val = data[0]
            for price in data[1:]:
                ema_val = (price * multiplier) + (ema_val * (1 - multiplier))
            return ema_val

        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)
        macd_line = ema_fast - ema_slow

        # 簡化的 signal line
        signal_line = macd_line * 0.9
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def _calculate_kd(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 9
    ) -> Tuple[float, float]:
        """計算 KD"""
        if len(closes) < period:
            return 50, 50

        highest = max(highs[-period:])
        lowest = min(lows[-period:])

        if highest == lowest:
            return 50, 50

        rsv = (closes[-1] - lowest) / (highest - lowest) * 100
        k = rsv  # 簡化版
        d = k * 0.9  # 簡化版

        return k, d

    @staticmethod
    def _calculate_bollinger(
        closes: List[float],
        period: int = 20,
        std_dev: float = 2
    ) -> Tuple[float, float, float]:
        """計算布林通道"""
        if len(closes) < period:
            return closes[-1], closes[-1], closes[-1]

        import numpy as np

        recent = closes[-period:]
        middle = np.mean(recent)
        std = np.std(recent)

        upper = middle + std_dev * std
        lower = middle - std_dev * std

        return upper, middle, lower

    @staticmethod
    def _calculate_atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14
    ) -> float:
        """計算 ATR"""
        if len(closes) < period + 1:
            return 0

        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)

        atr = sum(true_ranges[-period:]) / period
        return atr

    # ============================================================
    # 快取管理
    # ============================================================

    @classmethod
    def _get_cache(cls, key: str) -> Optional[Any]:
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            # 🆕 V10.16.1: 使用智能 TTL，盤後自動延長快取時間
            ttl = SmartTTL.get_ttl("strategy")
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, value: Any):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()

    @classmethod
    def clear_cache(cls):
        """清除快取"""
        cls._cache.clear()
        cls._cache_time.clear()
        print("🗑️ [InvestmentStrategy] 快取已清除")


# ============================================================
# 便捷函數
# ============================================================

async def get_investment_strategy(stock_id: str) -> Dict:
    """取得股票綜合投資策略"""
    return await InvestmentStrategyService.get_comprehensive_strategy(stock_id)

async def get_strategy_picks(top_n: int = 10) -> Dict:
    """取得策略精選股票"""
    return await InvestmentStrategyService.get_strategy_picks(top_n)
