"""
StockBuddy V10.10 - 多維度評分服務
整合技術面、基本面、籌碼面、新聞情緒、產業熱度的綜合評分

V10.10 更新：
- 新增新聞情緒評分（10%）
- 新增產業熱度加分（額外 -5 ~ +12）
- 調整權重：技術50% + 基本25% + 籌碼15% + 新聞10%
"""

import math
from typing import Dict, Any, Optional, List


class ScoringService:
    """多維度評分服務"""

    # 評分權重配置（V10.10 更新）
    WEIGHTS = {
        "technical": 0.50,    # 技術面 50%（原55%）
        "fundamental": 0.25,  # 基本面 25%（原30%）
        "chip": 0.15,         # 籌碼面 15%（不變）
        "news": 0.10,         # 新聞情緒 10%（新增）
    }

    # V10.35.5 方案 G: 預設權重方案
    WEIGHT_PRESETS = {
        "default": {
            "name": "均衡型",
            "description": "平衡技術面與基本面，適合大多數投資人",
            "weights": {
                "technical": 0.50,
                "fundamental": 0.25,
                "chip": 0.15,
                "news": 0.10,
            }
        },
        "momentum": {
            "name": "動能型",
            "description": "重視技術面與籌碼面，適合短線交易者",
            "weights": {
                "technical": 0.55,
                "fundamental": 0.15,
                "chip": 0.20,
                "news": 0.10,
            }
        },
        "value": {
            "name": "價值型",
            "description": "重視基本面與穩定性，適合長期投資人",
            "weights": {
                "technical": 0.30,
                "fundamental": 0.40,
                "chip": 0.15,
                "news": 0.15,
            }
        },
        "chip_focused": {
            "name": "籌碼型",
            "description": "重視法人動向，適合跟單投資人",
            "weights": {
                "technical": 0.35,
                "fundamental": 0.20,
                "chip": 0.35,
                "news": 0.10,
            }
        },
    }

    @classmethod
    def get_weight_presets(cls) -> Dict[str, Any]:
        """取得所有預設權重方案"""
        return cls.WEIGHT_PRESETS

    @classmethod
    def get_weights(cls, preset: str = "default") -> Dict[str, float]:
        """取得指定權重方案的權重"""
        if preset in cls.WEIGHT_PRESETS:
            return cls.WEIGHT_PRESETS[preset]["weights"]
        return cls.WEIGHTS
    
    # V10.38: 產業熱度改為動態計算
    # 以下為 LEGACY 備用值，僅在動態服務失敗時使用
    # 實際使用請呼叫 calculate_industry_bonus_async() 或 get_industry_score()
    HOT_INDUSTRIES_LEGACY = {
        # 熱門題材
        "AI": 12, "AI伺服器": 12, "GB200": 10, "HBM": 10,
        "CoWoS": 10, "先進製程": 8, "先進封裝": 8,
        # 熱門產業
        "半導體": 6, "IC設計": 5, "封測": 4, "電動車": 5, "充電樁": 4, "5G": 4,
        # 中性產業
        "金控": 0, "銀行": 0, "壽險": 0, "電信": 0, "食品": 0, "零售": 0,
        # 冷門產業
        "塑膠": -3, "石化": -3, "水泥": -3, "紡織": -4, "鋼鐵": -2, "面板": -3,
    }

    # V10.38: 保持向後兼容，HOT_INDUSTRIES 指向 LEGACY
    HOT_INDUSTRIES = HOT_INDUSTRIES_LEGACY
    
    @classmethod
    def calculate_fundamental_score(
        cls,
        pe_ratio: Optional[float] = None,
        pb_ratio: Optional[float] = None,
        dividend_yield: Optional[float] = None,
        roe: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        計算基本面評分
        
        輸入：
        - pe_ratio: 本益比
        - pb_ratio: 股價淨值比
        - dividend_yield: 殖利率 (%)
        - roe: 股東權益報酬率 (%)
        
        輸出：
        - score: 基本面分數 (30-90)
        - details: 各項目評分明細
        """
        base_score = 50  # 基礎分
        details = {}
        
        # 1. 本益比評分（權重最高）
        pe_score = 0
        pe_desc = "無資料"
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= 8:
                pe_score = 18
                pe_desc = "極低估"
            elif pe_ratio <= 12:
                pe_score = 12
                pe_desc = "低估"
            elif pe_ratio <= 18:
                pe_score = 6
                pe_desc = "合理偏低"
            elif pe_ratio <= 25:
                pe_score = 0
                pe_desc = "合理"
            elif pe_ratio <= 40:
                pe_score = -8
                pe_desc = "偏高"
            elif pe_ratio <= 80:
                pe_score = -15
                pe_desc = "高估"
            else:
                pe_score = -25
                pe_desc = "極高估/泡沫"
        details["pe"] = {"value": pe_ratio, "score": pe_score, "desc": pe_desc}
        
        # 2. 殖利率評分
        yield_score = 0
        yield_desc = "無資料"
        if dividend_yield is not None and dividend_yield >= 0:
            if dividend_yield >= 7:
                yield_score = 15
                yield_desc = "超高殖利率"
            elif dividend_yield >= 5:
                yield_score = 12
                yield_desc = "高殖利率"
            elif dividend_yield >= 4:
                yield_score = 8
                yield_desc = "中高殖利率"
            elif dividend_yield >= 3:
                yield_score = 4
                yield_desc = "中等殖利率"
            elif dividend_yield >= 2:
                yield_score = 0
                yield_desc = "一般"
            else:
                yield_score = -3
                yield_desc = "低殖利率"
        details["dividend_yield"] = {"value": dividend_yield, "score": yield_score, "desc": yield_desc}
        
        # 3. 股價淨值比評分
        pb_score = 0
        pb_desc = "無資料"
        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio < 0.8:
                pb_score = 12
                pb_desc = "深度低於淨值"
            elif pb_ratio < 1.0:
                pb_score = 8
                pb_desc = "低於淨值"
            elif pb_ratio < 1.5:
                pb_score = 4
                pb_desc = "合理"
            elif pb_ratio < 2.5:
                pb_score = 0
                pb_desc = "中等"
            elif pb_ratio < 5:
                pb_score = -5
                pb_desc = "偏高"
            else:
                pb_score = -10
                pb_desc = "過高"
        details["pb"] = {"value": pb_ratio, "score": pb_score, "desc": pb_desc}
        
        # 4. ROE 評分（如果有）
        roe_score = 0
        roe_desc = "無資料"
        if roe is not None:
            if roe >= 20:
                roe_score = 8
                roe_desc = "優秀"
            elif roe >= 15:
                roe_score = 5
                roe_desc = "良好"
            elif roe >= 10:
                roe_score = 2
                roe_desc = "一般"
            elif roe >= 5:
                roe_score = 0
                roe_desc = "偏低"
            else:
                roe_score = -5
                roe_desc = "差"
        details["roe"] = {"value": roe, "score": roe_score, "desc": roe_desc}
        
        # 計算總分
        total_adjustment = pe_score + yield_score + pb_score + roe_score
        final_score = base_score + total_adjustment
        
        # 限制範圍 30-90
        final_score = max(30, min(90, final_score))
        
        return {
            "score": int(final_score),
            "details": details,
            "summary": cls._generate_fundamental_summary(details),
        }
    
    @classmethod
    def calculate_chip_score(
        cls,
        foreign_net: Optional[float] = None,  # 外資買賣超（張）
        trust_net: Optional[float] = None,    # 投信買賣超（張）
        dealer_net: Optional[float] = None,   # 自營商買賣超（張）
    ) -> Dict[str, Any]:
        """
        計算籌碼面評分
        
        輸入：
        - foreign_net: 外資買賣超（張），正數為買超
        - trust_net: 投信買賣超（張）
        - dealer_net: 自營商買賣超（張）
        
        輸出：
        - score: 籌碼面分數 (35-85)
        - details: 各項目評分明細
        """
        base_score = 50  # 基礎分
        details = {}
        
        # 1. 外資買賣超（權重最高）
        foreign_score = 0
        foreign_desc = "無資料"
        if foreign_net is not None:
            if foreign_net >= 10000:
                foreign_score = 18
                foreign_desc = "外資大買超"
            elif foreign_net >= 5000:
                foreign_score = 12
                foreign_desc = "外資買超"
            elif foreign_net >= 1000:
                foreign_score = 6
                foreign_desc = "外資小買超"
            elif foreign_net >= 0:
                foreign_score = 0
                foreign_desc = "外資中性"
            elif foreign_net >= -1000:
                foreign_score = -3
                foreign_desc = "外資小賣超"
            elif foreign_net >= -5000:
                foreign_score = -8
                foreign_desc = "外資賣超"
            else:
                foreign_score = -15
                foreign_desc = "外資大賣超"
        details["foreign"] = {"value": foreign_net, "score": foreign_score, "desc": foreign_desc}
        
        # 2. 投信買賣超
        trust_score = 0
        trust_desc = "無資料"
        if trust_net is not None:
            if trust_net >= 3000:
                trust_score = 10
                trust_desc = "投信大買超"
            elif trust_net >= 1000:
                trust_score = 6
                trust_desc = "投信買超"
            elif trust_net >= 0:
                trust_score = 2
                trust_desc = "投信中性偏多"
            elif trust_net >= -500:
                trust_score = -2
                trust_desc = "投信小賣超"
            else:
                trust_score = -8
                trust_desc = "投信賣超"
        details["trust"] = {"value": trust_net, "score": trust_score, "desc": trust_desc}
        
        # 3. 自營商買賣超（參考用，權重低）
        dealer_score = 0
        dealer_desc = "無資料"
        if dealer_net is not None:
            if dealer_net >= 2000:
                dealer_score = 4
                dealer_desc = "自營商買超"
            elif dealer_net >= 0:
                dealer_score = 1
                dealer_desc = "自營商中性"
            elif dealer_net >= -1000:
                dealer_score = -1
                dealer_desc = "自營商小賣超"
            else:
                dealer_score = -4
                dealer_desc = "自營商賣超"
        details["dealer"] = {"value": dealer_net, "score": dealer_score, "desc": dealer_desc}
        
        # 計算總分
        total_adjustment = foreign_score + trust_score + dealer_score
        final_score = base_score + total_adjustment
        
        # 限制範圍 35-85
        final_score = max(35, min(85, final_score))
        
        return {
            "score": int(final_score),
            "details": details,
            "summary": cls._generate_chip_summary(details),
        }
    
    @classmethod
    def calculate_final_score(
        cls,
        technical_score: int,
        fundamental_score: int,
        chip_score: int,
        news_score: int = 50,           # V10.10 新增
        industry_bonus: int = 0,         # V10.10 新增
        weight_preset: str = "default",  # V10.35.5 方案 G: 權重方案
        custom_weights: Dict[str, float] = None,  # V10.35.5: 自訂權重
    ) -> Dict[str, Any]:
        """
        計算最終綜合評分

        輸入：
        - technical_score: 技術面分數 (15-100)
        - fundamental_score: 基本面分數 (30-90)
        - chip_score: 籌碼面分數 (35-85)
        - news_score: 新聞情緒分數 (30-80)
        - industry_bonus: 產業熱度加分 (-5 ~ +12)
        - weight_preset: 權重方案 (default/momentum/value/chip_focused)
        - custom_weights: 自訂權重 (可選，會覆蓋 preset)

        輸出：
        - final_score: 最終分數
        - breakdown: 各維度分數明細
        - signal: 操作訊號
        """
        # V10.35.5: 選擇權重
        if custom_weights:
            weights = custom_weights
        else:
            weights = cls.get_weights(weight_preset)

        # 加權計算
        weighted_tech = technical_score * weights["technical"]
        weighted_fund = fundamental_score * weights["fundamental"]
        weighted_chip = chip_score * weights["chip"]
        weighted_news = news_score * weights["news"]
        
        # 基礎分數 + 產業熱度加分
        final_score = weighted_tech + weighted_fund + weighted_chip + weighted_news + industry_bonus
        final_score = int(round(max(20, min(98, final_score))))
        
        # 訊號判定
        if final_score >= 82:
            signal = "強力買進"
        elif final_score >= 72:
            signal = "買進"
        elif final_score >= 58:
            signal = "持有"
        elif final_score >= 45:
            signal = "觀望"
        else:
            signal = "減碼"
        
        return {
            "final_score": final_score,
            "signal": signal,
            "weight_preset": weight_preset,  # V10.35.5: 使用的權重方案
            "breakdown": {
                "technical": {
                    "score": technical_score,
                    "weight": weights["technical"],
                    "weighted": round(weighted_tech, 1),
                },
                "fundamental": {
                    "score": fundamental_score,
                    "weight": weights["fundamental"],
                    "weighted": round(weighted_fund, 1),
                },
                "chip": {
                    "score": chip_score,
                    "weight": weights["chip"],
                    "weighted": round(weighted_chip, 1),
                },
                "news": {
                    "score": news_score,
                    "weight": weights["news"],
                    "weighted": round(weighted_news, 1),
                },
                "industry_bonus": industry_bonus,
            },
        }
    
    # ============================================================
    # 新聞情緒評分（V10.10 新增）
    # ============================================================
    
    @classmethod
    def calculate_news_score(
        cls,
        positive_count: int = 0,
        negative_count: int = 0,
        total_count: int = 0,
        sentiment_trend: str = "neutral",
    ) -> Dict[str, Any]:
        """
        計算新聞情緒分數（30-80 分）
        
        輸入：
        - positive_count: 正面新聞數量
        - negative_count: 負面新聞數量
        - total_count: 總新聞數量
        - sentiment_trend: 情緒趨勢 (very_positive/positive/neutral/negative/very_negative)
        
        輸出：
        - score: 新聞情緒分數
        - summary: 摘要說明
        """
        base_score = 50  # 基礎分
        details = []
        
        # 依趨勢評分
        if sentiment_trend == "very_positive":
            base_score += 25
            details.append("新聞面極正向")
        elif sentiment_trend == "positive":
            base_score += 12
            details.append("新聞面正向")
        elif sentiment_trend == "negative":
            base_score -= 12
            details.append("新聞面負向")
        elif sentiment_trend == "very_negative":
            base_score -= 25
            details.append("新聞面極負向")
        else:
            details.append("新聞面中性")
        
        # 依正負比例微調
        if total_count > 0:
            positive_ratio = positive_count / total_count
            if positive_ratio >= 0.7:
                base_score += 5
            elif positive_ratio <= 0.3 and negative_count > positive_count:
                base_score -= 5
        
        # 限制範圍 30-80
        final_score = max(30, min(80, base_score))
        
        return {
            "score": int(final_score),
            "summary": details[0] if details else "新聞中性",
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_count": total_count,
            "trend": sentiment_trend,
        }
    
    # ============================================================
    # 產業熱度加分（V10.10 新增）
    # ============================================================
    
    @classmethod
    def calculate_industry_bonus(
        cls,
        industry: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        計算產業熱度加分（-5 ~ +12）
        
        輸入：
        - industry: 產業分類（如「半導體」「金控」）
        - tags: 題材標籤列表（如 ["AI", "先進製程"]）
        
        輸出：
        - bonus: 加減分
        - matched: 匹配到的熱門標籤
        - summary: 摘要說明
        """
        bonus = 0
        matched = []
        
        # 檢查產業
        if industry and industry in cls.HOT_INDUSTRIES:
            industry_bonus = cls.HOT_INDUSTRIES[industry]
            bonus += industry_bonus
            if industry_bonus != 0:
                matched.append(f"{industry}({'+' if industry_bonus > 0 else ''}{industry_bonus})")
        
        # 檢查標籤（取最高加分的標籤）
        tag_bonus = 0
        best_tag = None
        if tags:
            for tag in tags:
                if tag in cls.HOT_INDUSTRIES:
                    tb = cls.HOT_INDUSTRIES[tag]
                    if tb > tag_bonus:  # 只取正向最高的
                        tag_bonus = tb
                        best_tag = tag
        
        if best_tag:
            bonus = max(bonus, tag_bonus)  # 取產業和標籤中較高的
            if best_tag not in [m.split("(")[0] for m in matched]:
                matched.append(f"{best_tag}(+{tag_bonus})")
        
        # 限制範圍 -5 ~ +12
        bonus = max(-5, min(12, bonus))
        
        # 生成摘要
        if bonus > 5:
            summary = f"🔥 熱門題材"
        elif bonus > 0:
            summary = f"📈 產業偏熱"
        elif bonus < 0:
            summary = f"📉 產業偏冷"
        else:
            summary = ""
        
        return {
            "bonus": bonus,
            "matched": matched,
            "summary": summary,
        }

    @classmethod
    async def calculate_industry_bonus_async(
        cls,
        industry: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        V10.38: 非同步計算產業熱度加分（使用動態計算）

        這是新的推薦方法，會從市場數據動態計算產業熱度

        輸入：
        - industry: 產業分類（如「半導體」「金控」）
        - tags: 題材標籤列表（如 ["AI", "先進製程"]）

        輸出：
        - bonus: 加減分 (-10 ~ +10)
        - matched: 匹配到的熱門標籤
        - summary: 摘要說明
        - data_source: "calculated" 或 "fallback"
        """
        try:
            from .industry_heat_service import get_industry_score
        except ImportError:
            # 若新服務不可用，降級到同步版本
            result = cls.calculate_industry_bonus(industry, tags)
            result["data_source"] = "legacy"
            return result

        bonus = 0
        matched = []
        data_source = "calculated"

        # 檢查產業
        if industry:
            try:
                industry_bonus = await get_industry_score(industry)
                bonus += industry_bonus
                if industry_bonus != 0:
                    matched.append(f"{industry}({'+' if industry_bonus > 0 else ''}{industry_bonus})")
            except Exception:
                # 降級到 LEGACY
                if industry in cls.HOT_INDUSTRIES_LEGACY:
                    industry_bonus = cls.HOT_INDUSTRIES_LEGACY[industry]
                    bonus += industry_bonus
                    if industry_bonus != 0:
                        matched.append(f"{industry}({'+' if industry_bonus > 0 else ''}{industry_bonus})")
                    data_source = "fallback"

        # 檢查標籤（取最高加分的標籤）
        tag_bonus = 0
        best_tag = None
        if tags:
            for tag in tags:
                try:
                    tb = await get_industry_score(tag)
                    if tb > tag_bonus:
                        tag_bonus = tb
                        best_tag = tag
                except Exception:
                    # 降級到 LEGACY
                    if tag in cls.HOT_INDUSTRIES_LEGACY:
                        tb = cls.HOT_INDUSTRIES_LEGACY[tag]
                        if tb > tag_bonus:
                            tag_bonus = tb
                            best_tag = tag
                            data_source = "fallback"

        if best_tag:
            bonus = max(bonus, tag_bonus)
            if best_tag not in [m.split("(")[0] for m in matched]:
                matched.append(f"{best_tag}(+{tag_bonus})")

        # 限制範圍 -10 ~ +10
        bonus = max(-10, min(10, bonus))

        # 生成摘要
        if bonus > 5:
            summary = "熱門題材"
        elif bonus > 0:
            summary = "產業偏熱"
        elif bonus < 0:
            summary = "產業偏冷"
        else:
            summary = ""

        return {
            "bonus": bonus,
            "matched": matched,
            "summary": summary,
            "data_source": data_source,
        }

    @staticmethod
    def _generate_fundamental_summary(details: Dict) -> str:
        """生成基本面摘要"""
        parts = []
        
        pe = details.get("pe", {})
        if pe.get("desc") and pe.get("desc") != "無資料":
            parts.append(f"P/E {pe['desc']}")
        
        dy = details.get("dividend_yield", {})
        if dy.get("score", 0) >= 8:
            parts.append(dy["desc"])
        
        pb = details.get("pb", {})
        if pb.get("score", 0) >= 8:
            parts.append(f"P/B {pb['desc']}")
        
        return "，".join(parts) if parts else "基本面中性"
    
    @staticmethod
    def _generate_chip_summary(details: Dict) -> str:
        """生成籌碼面摘要"""
        parts = []
        
        foreign = details.get("foreign", {})
        if foreign.get("desc") and foreign.get("desc") != "無資料":
            parts.append(foreign["desc"])
        
        trust = details.get("trust", {})
        if trust.get("score", 0) >= 6:
            parts.append(trust["desc"])
        
        return "，".join(parts) if parts else "籌碼中性"
    
    # ============================================================
    # 融資融券評分（V10.11 新增）
    # ============================================================
    
    @classmethod
    def calculate_margin_score(
        cls,
        margin_balance: Optional[int] = None,
        margin_balance_prev: Optional[int] = None,
        short_balance: Optional[int] = None,
        short_balance_prev: Optional[int] = None,
        price_change: Optional[float] = None,  # V10.37 新增：股價變化 %
    ) -> Dict[str, Any]:
        """
        計算融資融券分數（加減分制）

        輸入：
        - margin_balance: 今日融資餘額（張）
        - margin_balance_prev: 前日融資餘額
        - short_balance: 今日融券餘額
        - short_balance_prev: 前日融券餘額
        - price_change: 股價漲跌幅 % (V10.37 新增)

        輸出：
        - bonus: 加減分 (-10 ~ +15)
        - summary: 摘要說明

        V10.37 修正：融資信號需同時考慮股價方向
        - 融資減少 + 股價上漲 = 真利多（籌碼沉澱）
        - 融資減少 + 股價下跌 = 可能是停損潮（風險）
        """
        bonus = 0
        details = []
        price_up = (price_change or 0) > 0

        # 1. 融資餘額變化 (V10.37 修正：結合股價方向判斷)
        if margin_balance is not None and margin_balance_prev is not None and margin_balance_prev > 0:
            margin_change = (margin_balance - margin_balance_prev) / margin_balance_prev * 100

            if margin_change <= -5:
                if price_up:
                    # 融資減少 + 股價上漲 = 籌碼沉澱，真利多
                    bonus += 10
                    details.append("融資減少+股價上漲（籌碼沉澱）")
                else:
                    # 融資減少 + 股價下跌 = 可能是停損潮
                    bonus -= 3
                    details.append("融資減少+股價下跌（停損潮風險）")
            elif margin_change <= -2:
                if price_up:
                    bonus += 5
                    details.append("融資微減+股價上漲")
                else:
                    bonus += 0  # 中性
                    details.append("融資微減")
            elif margin_change >= 10:
                bonus -= 8
                details.append("融資大增（散戶追高）")
            elif margin_change >= 5:
                if price_up:
                    bonus -= 2  # 跟風，但風險較低
                    details.append("融資增加+股價上漲（跟風）")
                else:
                    bonus -= 6  # 散戶套牢
                    details.append("融資增加+股價下跌（散戶套牢）")
        
        # 2. 券資比（融券 / 融資）
        if margin_balance and margin_balance > 0 and short_balance:
            short_ratio = short_balance / margin_balance * 100
            
            if short_ratio >= 30:
                bonus += 8
                details.append(f"券資比高 {short_ratio:.1f}%（軋空潛力）")
            elif short_ratio >= 15:
                bonus += 4
                details.append(f"券資比 {short_ratio:.1f}%")
        
        # 3. 融券餘額變化
        if short_balance is not None and short_balance_prev is not None and short_balance_prev > 0:
            short_change = (short_balance - short_balance_prev) / short_balance_prev * 100
            
            if short_change >= 20:
                bonus += 5
                details.append("融券大增（軋空機會）")
        
        # 限制範圍 -10 ~ +15
        bonus = max(-10, min(15, bonus))
        
        summary = "，".join(details) if details else "融資融券正常"
        
        return {
            "bonus": bonus,
            "summary": summary,
            "margin_balance": margin_balance,
            "short_balance": short_balance,
            "details": details,
        }
    
    # ============================================================
    # 注意股票扣分（V10.11 新增）
    # ============================================================
    
    @classmethod
    def calculate_attention_penalty(
        cls,
        is_attention: bool = False,
        attention_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        計算注意股票扣分
        
        輸入：
        - is_attention: 是否為注意股票
        - attention_reason: 注意原因
        
        輸出：
        - penalty: 扣分 (0 ~ -20)
        - warning: 警示訊息
        """
        penalty = 0
        warning = None
        
        if is_attention:
            penalty = -15
            warning = f"⚠️ 注意股票: {attention_reason or '近期股價異常波動'}"
        
        return {
            "penalty": penalty,
            "is_attention": is_attention,
            "warning": warning,
        }
    
    # ============================================================
    # 營收動能評分（V10.11 新增）
    # ============================================================
    
    @classmethod
    def calculate_revenue_score(
        cls,
        revenue_mom: Optional[float] = None,
        revenue_yoy: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        計算營收動能分數（加減分制）
        
        輸入：
        - revenue_mom: 營收月增率 (%)
        - revenue_yoy: 營收年增率 (%)
        
        輸出：
        - bonus: 加減分 (-8 ~ +15)
        - summary: 摘要說明
        """
        bonus = 0
        details = []
        
        # 1. 月增率
        if revenue_mom is not None:
            if revenue_mom >= 20:
                bonus += 8
                details.append(f"營收月增 {revenue_mom:.1f}%（爆發）")
            elif revenue_mom >= 10:
                bonus += 5
                details.append(f"營收月增 {revenue_mom:.1f}%（強勁）")
            elif revenue_mom >= 5:
                bonus += 2
                details.append(f"營收月增 {revenue_mom:.1f}%")
            elif revenue_mom <= -10:
                bonus -= 5
                details.append(f"營收月減 {revenue_mom:.1f}%")
        
        # 2. 年增率
        if revenue_yoy is not None:
            if revenue_yoy >= 30:
                bonus += 7
                details.append(f"營收年增 {revenue_yoy:.1f}%（高成長）")
            elif revenue_yoy >= 15:
                bonus += 4
                details.append(f"營收年增 {revenue_yoy:.1f}%")
            elif revenue_yoy >= 5:
                bonus += 1
            elif revenue_yoy <= -15:
                bonus -= 4
                details.append(f"營收年減 {revenue_yoy:.1f}%")
        
        # 限制範圍 -8 ~ +15
        bonus = max(-8, min(15, bonus))
        
        summary = "，".join(details) if details else "營收平穩"
        
        return {
            "bonus": bonus,
            "summary": summary,
            "revenue_mom": revenue_mom,
            "revenue_yoy": revenue_yoy,
        }


# 便捷函數
def calculate_fundamental_score(pe_ratio=None, pb_ratio=None, dividend_yield=None, roe=None):
    return ScoringService.calculate_fundamental_score(pe_ratio, pb_ratio, dividend_yield, roe)

def calculate_chip_score(foreign_net=None, trust_net=None, dealer_net=None):
    return ScoringService.calculate_chip_score(foreign_net, trust_net, dealer_net)

def calculate_news_score(positive_count=0, negative_count=0, total_count=0, sentiment_trend="neutral"):
    return ScoringService.calculate_news_score(positive_count, negative_count, total_count, sentiment_trend)

def calculate_industry_bonus(industry=None, tags=None):
    return ScoringService.calculate_industry_bonus(industry, tags)

def calculate_final_score(technical_score, fundamental_score, chip_score, news_score=50, industry_bonus=0):
    return ScoringService.calculate_final_score(technical_score, fundamental_score, chip_score, news_score, industry_bonus)

# V10.11 新增便捷函數 (V10.37 更新：新增 price_change 參數)
def calculate_margin_score(margin_balance=None, margin_balance_prev=None, short_balance=None, short_balance_prev=None, price_change=None):
    return ScoringService.calculate_margin_score(margin_balance, margin_balance_prev, short_balance, short_balance_prev, price_change)

def calculate_attention_penalty(is_attention=False, attention_reason=None):
    return ScoringService.calculate_attention_penalty(is_attention, attention_reason)

def calculate_revenue_score(revenue_mom=None, revenue_yoy=None):
    return ScoringService.calculate_revenue_score(revenue_mom, revenue_yoy)
