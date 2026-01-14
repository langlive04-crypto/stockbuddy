"""
增強版 AI 分析服務 - Enhanced AI Analysis Service
V10.25 新增

功能：
1. 進階新聞情緒分析
   - 權重化關鍵字
   - 情緒強度計算
   - 新聞時效性加權

2. 產業連動分析
   - 產業相關性矩陣
   - 上下游供應鏈分析
   - 產業輪動偵測

3. 綜合評分優化
   - 多因子評分模型
   - 動態權重調整
   - 信心度計算
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class SentimentResult:
    """情緒分析結果"""
    score: int  # 0-100
    label: str  # 利多/中性/利空
    strength: str  # 強/中/弱
    confidence: float  # 0-1
    details: Dict


@dataclass
class IndustryAnalysis:
    """產業分析結果"""
    industry: str
    correlation_score: int  # 產業連動分數
    supply_chain_impact: str  # 供應鏈影響
    rotation_signal: str  # 輪動訊號
    related_stocks: List[str]
    details: Dict


class EnhancedAIAnalysis:
    """增強版 AI 分析引擎"""

    # 權重化情緒關鍵字（關鍵字: 權重）
    WEIGHTED_POSITIVE = {
        # 強利多 (權重 3)
        "大漲": 3, "飆漲": 3, "創新高": 3, "歷史新高": 3, "爆單": 3,
        "供不應求": 3, "調升目標價": 3, "優於預期": 3, "超預期": 3,
        # 中利多 (權重 2)
        "利多": 2, "看好": 2, "成長": 2, "獲利增": 2, "訂單增": 2,
        "擴產": 2, "買超": 2, "加碼": 2, "營收年增": 2, "毛利改善": 2,
        "轉單": 2, "滿載": 2, "出貨增": 2, "需求強勁": 2,
        # 弱利多 (權重 1)
        "樂觀": 1, "正向": 1, "回升": 1, "回穩": 1, "持穩": 1,
        "優於": 1, "符合預期": 1, "穩健": 1, "持續": 1,
    }

    WEIGHTED_NEGATIVE = {
        # 強利空 (權重 3)
        "大跌": 3, "重挫": 3, "崩跌": 3, "暴跌": 3, "創新低": 3,
        "砍單": 3, "裁員": 3, "關廠": 3, "虧損": 3, "下修目標價": 3,
        # 中利空 (權重 2)
        "利空": 2, "看壞": 2, "衰退": 2, "下滑": 2, "減碼": 2,
        "賣超": 2, "庫存高": 2, "產能過剩": 2, "毛利下滑": 2,
        "營收年減": 2, "需求疲軟": 2, "出貨減": 2, "調降": 2,
        # 弱利空 (權重 1)
        "悲觀": 1, "疲弱": 1, "低迷": 1, "不振": 1, "壓力": 1,
        "保守": 1, "低於預期": 1, "持平": 1, "觀望": 1,
    }

    # 產業對照表
    INDUSTRY_MAP = {
        # 半導體產業鏈
        "IC設計": ["2454", "3034", "2379", "6415", "3443", "6239", "3661", "8046"],
        "晶圓代工": ["2330", "2303", "6770"],
        "封測": ["3711", "2311", "3035", "2325"],
        "記憶體": ["2408", "2344", "3450"],
        "半導體設備": ["3529", "6698"],
        # 電子產業鏈
        "代工組裝": ["2317", "2382", "2353", "4938"],
        "電腦周邊": ["2357", "3231", "2356"],
        "PCB": ["3037", "4958", "3706"],
        "被動元件": ["2327", "3533"],
        # AI伺服器產業鏈
        "伺服器": ["2345", "3017", "6669", "6285"],
        "散熱": ["3533", "6230", "2308"],
        "電源供應": ["2308", "3701", "3515"],
        # 金融
        "金控": ["2881", "2882", "2891", "2886", "2884", "2885", "2880"],
        "壽險": ["2882", "2823", "5863"],
        "證券": ["6005", "6024", "2855"],
        # 傳統產業
        "鋼鐵": ["2002", "2027", "2014"],
        "塑化": ["1301", "1303", "1326", "6505"],
        "紡織": ["1402", "1476", "1434"],
        # 航運
        "貨櫃航運": ["2603", "2609", "2615"],
        "散裝航運": ["2618", "2637"],
        # 電信
        "電信": ["2412", "3045", "4904"],
    }

    # 供應鏈關係（上游 -> 下游）
    SUPPLY_CHAIN = {
        "2330": {"downstream": ["2454", "3034", "6415"], "type": "晶圓代工"},  # 台積電
        "2454": {"downstream": ["2382", "2357"], "type": "IC設計"},  # 聯發科
        "2317": {"downstream": [], "upstream": ["2382", "3034"], "type": "代工"},  # 鴻海
        "3711": {"downstream": [], "upstream": ["2330", "2303"], "type": "封測"},  # 日月光
        "2308": {"downstream": ["2345", "3017"], "type": "電源"},  # 台達電
    }

    # 產業相關性矩陣（簡化版）
    INDUSTRY_CORRELATION = {
        ("IC設計", "晶圓代工"): 0.85,
        ("IC設計", "封測"): 0.75,
        ("晶圓代工", "封測"): 0.80,
        ("晶圓代工", "半導體設備"): 0.70,
        ("伺服器", "IC設計"): 0.65,
        ("伺服器", "散熱"): 0.75,
        ("伺服器", "電源供應"): 0.70,
        ("代工組裝", "PCB"): 0.60,
        ("金控", "壽險"): 0.80,
        ("鋼鐵", "塑化"): 0.50,
        ("貨櫃航運", "散裝航運"): 0.70,
    }

    @classmethod
    def analyze_sentiment(cls, text: str, news_time: datetime = None) -> SentimentResult:
        """
        進階情緒分析

        Args:
            text: 新聞標題或內容
            news_time: 新聞時間（用於時效性加權）

        Returns:
            SentimentResult: 情緒分析結果
        """
        positive_score = 0
        negative_score = 0
        positive_keywords = []
        negative_keywords = []

        # 計算權重化分數
        for keyword, weight in cls.WEIGHTED_POSITIVE.items():
            count = text.count(keyword)
            if count > 0:
                positive_score += weight * count
                positive_keywords.append(keyword)

        for keyword, weight in cls.WEIGHTED_NEGATIVE.items():
            count = text.count(keyword)
            if count > 0:
                negative_score += weight * count
                negative_keywords.append(keyword)

        # 時效性加權（新聞越新權重越高）
        time_weight = 1.0
        if news_time:
            hours_ago = (datetime.now() - news_time).total_seconds() / 3600
            if hours_ago < 6:
                time_weight = 1.2  # 6小時內加權
            elif hours_ago < 24:
                time_weight = 1.0
            elif hours_ago < 72:
                time_weight = 0.8
            else:
                time_weight = 0.5

        positive_score *= time_weight
        negative_score *= time_weight

        # 計算總分（轉換為 0-100）
        net_score = positive_score - negative_score
        total_weight = positive_score + negative_score + 1  # 避免除零

        # 標準化分數到 0-100
        if net_score > 0:
            raw_score = 50 + min(net_score * 5, 50)
        elif net_score < 0:
            raw_score = 50 + max(net_score * 5, -50)
        else:
            raw_score = 50

        score = int(raw_score)

        # 決定標籤
        if score >= 70:
            label = "利多"
            strength = "強" if score >= 85 else "中"
        elif score >= 55:
            label = "利多"
            strength = "弱"
        elif score <= 30:
            label = "利空"
            strength = "強" if score <= 15 else "中"
        elif score <= 45:
            label = "利空"
            strength = "弱"
        else:
            label = "中性"
            strength = "中"

        # 計算信心度（基於關鍵字數量和權重）
        confidence = min(1.0, total_weight / 10)

        return SentimentResult(
            score=score,
            label=label,
            strength=strength,
            confidence=confidence,
            details={
                "positive_keywords": positive_keywords,
                "negative_keywords": negative_keywords,
                "positive_score": positive_score,
                "negative_score": negative_score,
                "time_weight": time_weight,
            }
        )

    @classmethod
    def analyze_industry(cls, stock_id: str, all_stocks_data: Dict = None) -> IndustryAnalysis:
        """
        產業連動分析

        Args:
            stock_id: 股票代號
            all_stocks_data: 所有股票的資料（用於計算連動性）

        Returns:
            IndustryAnalysis: 產業分析結果
        """
        # 找出股票所屬產業
        stock_industry = None
        related_stocks = []

        for industry, stocks in cls.INDUSTRY_MAP.items():
            if stock_id in stocks:
                stock_industry = industry
                related_stocks = [s for s in stocks if s != stock_id]
                break

        if not stock_industry:
            return IndustryAnalysis(
                industry="未分類",
                correlation_score=50,
                supply_chain_impact="無",
                rotation_signal="中性",
                related_stocks=[],
                details={}
            )

        # 計算產業連動分數
        correlation_score = 50
        industry_momentum = 0

        if all_stocks_data:
            # 計算產業內股票的平均表現
            related_performance = []
            for rs in related_stocks:
                if rs in all_stocks_data:
                    change_pct = all_stocks_data[rs].get('change_percent', 0)
                    related_performance.append(change_pct)

            if related_performance:
                avg_change = sum(related_performance) / len(related_performance)
                industry_momentum = avg_change

                # 根據產業動能調整分數
                if avg_change > 2:
                    correlation_score = 75 + min(avg_change * 5, 25)
                elif avg_change > 0:
                    correlation_score = 60 + avg_change * 7.5
                elif avg_change < -2:
                    correlation_score = 25 + max(avg_change * 5, -25)
                else:
                    correlation_score = 40 + avg_change * 5

        # 供應鏈影響分析
        supply_chain_impact = cls._analyze_supply_chain(stock_id)

        # 產業輪動訊號
        rotation_signal = cls._detect_rotation_signal(stock_industry, all_stocks_data)

        return IndustryAnalysis(
            industry=stock_industry,
            correlation_score=int(correlation_score),
            supply_chain_impact=supply_chain_impact,
            rotation_signal=rotation_signal,
            related_stocks=related_stocks[:5],
            details={
                "industry_momentum": industry_momentum,
                "related_count": len(related_stocks),
            }
        )

    @classmethod
    def _analyze_supply_chain(cls, stock_id: str) -> str:
        """分析供應鏈影響"""
        if stock_id not in cls.SUPPLY_CHAIN:
            return "一般"

        chain_info = cls.SUPPLY_CHAIN[stock_id]
        downstream = chain_info.get("downstream", [])
        upstream = chain_info.get("upstream", [])

        if len(downstream) > 3:
            return "關鍵上游"
        elif len(upstream) > 3:
            return "重要下游"
        elif downstream or upstream:
            return "有連動"
        else:
            return "一般"

    @classmethod
    def _detect_rotation_signal(cls, industry: str, all_stocks_data: Dict = None) -> str:
        """偵測產業輪動訊號"""
        if not all_stocks_data:
            return "中性"

        # 計算該產業的表現
        industry_stocks = cls.INDUSTRY_MAP.get(industry, [])
        if not industry_stocks:
            return "中性"

        industry_change = []
        for sid in industry_stocks:
            if sid in all_stocks_data:
                industry_change.append(all_stocks_data[sid].get('change_percent', 0))

        if not industry_change:
            return "中性"

        avg_change = sum(industry_change) / len(industry_change)

        # 與大盤比較（假設大盤資料在 all_stocks_data 中）
        market_change = all_stocks_data.get('market', {}).get('change_percent', 0)

        relative_strength = avg_change - market_change

        if relative_strength > 2:
            return "強勢輪入"
        elif relative_strength > 0.5:
            return "輪入"
        elif relative_strength < -2:
            return "強勢輪出"
        elif relative_strength < -0.5:
            return "輪出"
        else:
            return "中性"

    @classmethod
    def calculate_enhanced_score(
        cls,
        technical_score: int,
        chip_score: int,
        fundamental_score: int,
        sentiment_result: SentimentResult,
        industry_analysis: IndustryAnalysis
    ) -> Dict:
        """
        計算增強版綜合評分

        使用動態權重和多因子模型
        """
        # 基礎權重
        weights = {
            "technical": 0.35,
            "chip": 0.25,
            "fundamental": 0.20,
            "sentiment": 0.10,
            "industry": 0.10,
        }

        # 動態調整權重（根據市場狀況）
        # 當情緒極端時增加情緒權重
        if sentiment_result.score > 80 or sentiment_result.score < 20:
            weights["sentiment"] = 0.15
            weights["technical"] = 0.30

        # 當產業有明顯訊號時增加產業權重
        if industry_analysis.rotation_signal in ["強勢輪入", "強勢輪出"]:
            weights["industry"] = 0.15
            weights["fundamental"] = 0.15

        # 正規化權重
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        # 計算加權分數
        weighted_score = (
            technical_score * weights["technical"] +
            chip_score * weights["chip"] +
            fundamental_score * weights["fundamental"] +
            sentiment_result.score * weights["sentiment"] +
            industry_analysis.correlation_score * weights["industry"]
        )

        # 信心度調整
        # 考慮情緒信心度和產業相關性
        confidence = (sentiment_result.confidence + (industry_analysis.correlation_score / 100)) / 2

        # 最終分數微調
        final_score = weighted_score * (0.8 + 0.4 * confidence)
        final_score = min(100, max(0, final_score))

        return {
            "final_score": int(final_score),
            "base_score": int(weighted_score),
            "confidence": confidence,
            "weights_used": weights,
            "component_scores": {
                "technical": technical_score,
                "chip": chip_score,
                "fundamental": fundamental_score,
                "sentiment": sentiment_result.score,
                "industry": industry_analysis.correlation_score,
            },
            "adjustments": {
                "sentiment_adjustment": "增強" if weights["sentiment"] > 0.10 else "正常",
                "industry_adjustment": "增強" if weights["industry"] > 0.10 else "正常",
            }
        }

    @classmethod
    def get_ai_recommendation(cls, final_score: int, confidence: float) -> Dict:
        """
        根據分數和信心度給出 AI 推薦
        """
        # 決定信號
        if final_score >= 80 and confidence >= 0.7:
            signal = "強力買進"
            signal_color = "green"
            action = "積極佈局"
        elif final_score >= 70:
            signal = "買進"
            signal_color = "lightgreen"
            action = "分批買進"
        elif final_score >= 55:
            signal = "持有"
            signal_color = "yellow"
            action = "續抱觀察"
        elif final_score >= 40:
            signal = "觀望"
            signal_color = "orange"
            action = "暫時觀望"
        elif final_score >= 25:
            signal = "減碼"
            signal_color = "lightcoral"
            action = "適度減碼"
        else:
            signal = "賣出"
            signal_color = "red"
            action = "出清持股"

        # 信心度標籤
        if confidence >= 0.8:
            confidence_label = "高信心"
        elif confidence >= 0.5:
            confidence_label = "中信心"
        else:
            confidence_label = "低信心"

        return {
            "signal": signal,
            "signal_color": signal_color,
            "action": action,
            "confidence_label": confidence_label,
            "score": final_score,
            "confidence": confidence,
        }


# 建立全域服務實例
enhanced_ai = EnhancedAIAnalysis()
