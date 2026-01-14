"""
ML 特徵工程模組 V10.38

提供完整的特徵萃取功能，支援 ML 模型訓練

特徵類型:
- 價格技術指標 (10)
- 動能指標 (8)
- 成交量指標 (6)
- 波動率指標 (6)
- 籌碼面指標 (8)
- 基本面指標 (8)
- 市場環境指標 (4)

總計: 50+ 個特徵
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FeatureSet:
    """特徵集合"""
    stock_id: str
    features: Dict[str, float]
    feature_count: int
    missing_count: int
    timestamp: str


class MLFeatureEngine:
    """
    ML 特徵工程引擎 V10.38

    從股票數據萃取 ML 訓練所需的完整特徵集
    擴充至 50+ 個特徵，涵蓋技術面、籌碼面、基本面
    """

    # V10.38: 完整特徵定義 (50+ 個)
    FEATURE_DEFINITIONS = {
        # === 價格特徵 (10) ===
        "price_change_1d": {"type": "price", "description": "1日漲跌幅"},
        "price_change_5d": {"type": "price", "description": "5日漲跌幅"},
        "price_change_20d": {"type": "price", "description": "20日漲跌幅"},
        "price_vs_ma5": {"type": "price", "description": "價格相對MA5比率"},
        "price_vs_ma20": {"type": "price", "description": "價格相對MA20比率"},
        "price_vs_ma60": {"type": "price", "description": "價格相對MA60比率"},
        "ma5_vs_ma20": {"type": "price", "description": "MA5/MA20比率"},
        "ma20_vs_ma60": {"type": "price", "description": "MA20/MA60比率"},
        "ma5_slope": {"type": "price", "description": "MA5斜率"},
        "ma20_slope": {"type": "price", "description": "MA20斜率"},
        "ma_alignment": {"type": "price", "description": "均線排列(多頭=1,空頭=-1)"},
        "distance_from_high": {"type": "price", "description": "距離高點百分比"},
        "distance_from_low": {"type": "price", "description": "距離低點百分比"},

        # === 動能指標 (8) ===
        "rsi_14": {"type": "momentum", "description": "14日RSI"},
        "rsi_normalized": {"type": "momentum", "description": "RSI正規化(0-1)"},
        "macd_signal": {"type": "momentum", "description": "MACD信號"},
        "macd_histogram": {"type": "momentum", "description": "MACD柱狀圖"},
        "momentum_5d": {"type": "momentum", "description": "5日動能"},
        "momentum_20d": {"type": "momentum", "description": "20日動能"},
        "rate_of_change": {"type": "momentum", "description": "ROC指標"},
        "williams_r": {"type": "momentum", "description": "威廉指標"},

        # === 成交量指標 (6) ===
        "volume_ratio_5d": {"type": "volume", "description": "成交量/5日均量"},
        "volume_ratio_20d": {"type": "volume", "description": "成交量/20日均量"},
        "volume_trend": {"type": "volume", "description": "量能趨勢"},
        "volume_price_trend": {"type": "volume", "description": "量價趨勢"},
        "obv_slope": {"type": "volume", "description": "OBV斜率"},
        "volume_breakout": {"type": "volume", "description": "量能突破信號"},

        # === 波動率指標 (6) ===
        "volatility_20d": {"type": "volatility", "description": "20日波動率"},
        "atr_ratio": {"type": "volatility", "description": "ATR相對價格比"},
        "bb_position": {"type": "volatility", "description": "布林通道位置"},
        "bb_width": {"type": "volatility", "description": "布林通道寬度"},
        "intraday_range": {"type": "volatility", "description": "日內振幅"},
        "gap_ratio": {"type": "volatility", "description": "缺口比率"},

        # === 籌碼面指標 (8) ===
        "foreign_net_ratio": {"type": "chip", "description": "外資買賣超比"},
        "foreign_net_5d": {"type": "chip", "description": "外資5日淨買超"},
        "foreign_trend": {"type": "chip", "description": "外資趨勢"},
        "trust_net_ratio": {"type": "chip", "description": "投信買賣超比"},
        "trust_net_5d": {"type": "chip", "description": "投信5日淨買超"},
        "dealer_net_ratio": {"type": "chip", "description": "自營商買賣超比"},
        "institutional_score": {"type": "chip", "description": "法人綜合評分"},
        "institutional_consensus": {"type": "chip", "description": "法人共識度"},

        # === 基本面指標 (8) ===
        "pe_normalized": {"type": "fundamental", "description": "PE標準化"},
        "pb_normalized": {"type": "fundamental", "description": "PB標準化"},
        "dividend_yield": {"type": "fundamental", "description": "殖利率"},
        "revenue_growth": {"type": "fundamental", "description": "營收成長率"},
        "profit_margin": {"type": "fundamental", "description": "毛利率"},
        "roe": {"type": "fundamental", "description": "ROE"},
        "debt_ratio": {"type": "fundamental", "description": "負債比"},
        "eps_growth": {"type": "fundamental", "description": "EPS成長率"},

        # === 市場環境指標 (4) ===
        "market_trend": {"type": "market", "description": "大盤趨勢"},
        "sector_momentum": {"type": "market", "description": "產業動能"},
        "market_volatility": {"type": "market", "description": "市場波動率"},
        "industry_heat": {"type": "market", "description": "產業熱度"},

        # === 信心與評分 (2) ===
        "ai_score": {"type": "score", "description": "AI綜合評分"},
        "confidence": {"type": "score", "description": "信心指數"},
    }

    # V10.38: 特徵欄位名稱列表 (用於 ML 訓練)
    FEATURE_COLUMNS = list(FEATURE_DEFINITIONS.keys())

    def __init__(self):
        self.feature_names = list(self.FEATURE_DEFINITIONS.keys())

    def extract_features(
        self,
        stock_data: Dict,
        history: Optional[List[Dict]] = None
    ) -> FeatureSet:
        """
        V10.38: 萃取完整特徵集 (50+ 個特徵)

        Args:
            stock_data: 股票當前數據
            history: 歷史K線數據 (可選)

        Returns:
            FeatureSet 特徵集合
        """
        from datetime import datetime

        features = {}
        missing_count = 0
        stock_id = stock_data.get("stock_id", stock_data.get("id", "unknown"))

        # 基本價格數據
        price = stock_data.get("close", stock_data.get("price"))
        prev_close = stock_data.get("prev_close")
        high = stock_data.get("high")
        low = stock_data.get("low")
        open_price = stock_data.get("open")
        ma5 = stock_data.get("ma5")
        ma20 = stock_data.get("ma20")
        ma60 = stock_data.get("ma60")

        # ========== 價格特徵 (13) ==========

        # 價格變化
        if price and prev_close and prev_close > 0:
            features["price_change_1d"] = (price - prev_close) / prev_close * 100
        else:
            features["price_change_1d"] = 0
            missing_count += 1

        # 從歷史計算多日漲跌
        if history and len(history) >= 5:
            price_5d_ago = history[-5].get("close", price)
            if price_5d_ago and price_5d_ago > 0:
                features["price_change_5d"] = (price - price_5d_ago) / price_5d_ago * 100
            else:
                features["price_change_5d"] = 0
        else:
            features["price_change_5d"] = 0
            missing_count += 1

        if history and len(history) >= 20:
            price_20d_ago = history[-20].get("close", price)
            if price_20d_ago and price_20d_ago > 0:
                features["price_change_20d"] = (price - price_20d_ago) / price_20d_ago * 100
            else:
                features["price_change_20d"] = 0
        else:
            features["price_change_20d"] = 0
            missing_count += 1

        # 價格相對均線
        if price and ma5 and ma5 > 0:
            features["price_vs_ma5"] = (price / ma5 - 1) * 100
        else:
            features["price_vs_ma5"] = 0
            missing_count += 1

        if price and ma20 and ma20 > 0:
            features["price_vs_ma20"] = (price / ma20 - 1) * 100
        else:
            features["price_vs_ma20"] = 0
            missing_count += 1

        if price and ma60 and ma60 > 0:
            features["price_vs_ma60"] = (price / ma60 - 1) * 100
        else:
            features["price_vs_ma60"] = 0
            missing_count += 1

        # 均線相對位置
        if ma5 and ma20 and ma20 > 0:
            features["ma5_vs_ma20"] = (ma5 / ma20 - 1) * 100
        else:
            features["ma5_vs_ma20"] = 0
            missing_count += 1

        if ma20 and ma60 and ma60 > 0:
            features["ma20_vs_ma60"] = (ma20 / ma60 - 1) * 100
        else:
            features["ma20_vs_ma60"] = 0
            missing_count += 1

        # V10.38 新增: 均線斜率
        if history and len(history) >= 5:
            ma5_prev = history[-5].get("ma5")
            if ma5 and ma5_prev and ma5_prev > 0:
                features["ma5_slope"] = (ma5 - ma5_prev) / ma5_prev * 100
            else:
                features["ma5_slope"] = 0
        else:
            features["ma5_slope"] = 0
            missing_count += 1

        if history and len(history) >= 20:
            ma20_prev = history[-20].get("ma20")
            if ma20 and ma20_prev and ma20_prev > 0:
                features["ma20_slope"] = (ma20 - ma20_prev) / ma20_prev * 100
            else:
                features["ma20_slope"] = 0
        else:
            features["ma20_slope"] = 0
            missing_count += 1

        # V10.38 新增: 均線排列
        if ma5 and ma20 and ma60:
            if ma5 > ma20 > ma60:
                features["ma_alignment"] = 1  # 多頭排列
            elif ma5 < ma20 < ma60:
                features["ma_alignment"] = -1  # 空頭排列
            else:
                features["ma_alignment"] = 0  # 混沌
        else:
            features["ma_alignment"] = 0
            missing_count += 1

        # V10.38 新增: 距離高低點
        if history and len(history) >= 60:
            high_60d = max(h.get("high", 0) for h in history[-60:])
            low_60d = min(h.get("low", float('inf')) for h in history[-60:] if h.get("low"))
            if price and high_60d > 0:
                features["distance_from_high"] = (price - high_60d) / high_60d * 100
            else:
                features["distance_from_high"] = 0
            if price and low_60d and low_60d < float('inf'):
                features["distance_from_low"] = (price - low_60d) / low_60d * 100
            else:
                features["distance_from_low"] = 0
        else:
            features["distance_from_high"] = 0
            features["distance_from_low"] = 0
            missing_count += 2

        # ========== 動能指標 (8) ==========

        # RSI
        rsi = stock_data.get("rsi", stock_data.get("rsi_14"))
        if rsi is not None:
            features["rsi_14"] = rsi
            features["rsi_normalized"] = rsi / 100
        else:
            features["rsi_14"] = 50
            features["rsi_normalized"] = 0.5
            missing_count += 2

        # MACD
        macd = stock_data.get("macd")
        macd_signal_val = stock_data.get("macd_signal")
        macd_hist = stock_data.get("macd_histogram", stock_data.get("macd_hist"))

        if macd is not None and macd_signal_val is not None:
            features["macd_signal"] = 1 if macd > macd_signal_val else -1
        else:
            features["macd_signal"] = 0
            missing_count += 1

        # V10.38 新增: MACD 柱狀圖
        if macd_hist is not None:
            features["macd_histogram"] = macd_hist
        elif macd is not None and macd_signal_val is not None:
            features["macd_histogram"] = macd - macd_signal_val
        else:
            features["macd_histogram"] = 0
            missing_count += 1

        # 動能
        features["momentum_5d"] = features.get("price_change_5d", 0)
        features["momentum_20d"] = features.get("price_change_20d", 0)

        # V10.38 新增: ROC (Rate of Change)
        if history and len(history) >= 12:
            price_12d_ago = history[-12].get("close")
            if price and price_12d_ago and price_12d_ago > 0:
                features["rate_of_change"] = (price - price_12d_ago) / price_12d_ago * 100
            else:
                features["rate_of_change"] = 0
        else:
            features["rate_of_change"] = 0
            missing_count += 1

        # V10.38 新增: 威廉指標
        if history and len(history) >= 14:
            high_14d = max(h.get("high", 0) for h in history[-14:])
            low_14d = min(h.get("low", float('inf')) for h in history[-14:] if h.get("low"))
            if high_14d > low_14d and price:
                features["williams_r"] = (high_14d - price) / (high_14d - low_14d) * -100
            else:
                features["williams_r"] = -50
        else:
            features["williams_r"] = -50
            missing_count += 1

        # ========== 成交量指標 (6) ==========

        volume = stock_data.get("volume")
        volume_ma5 = stock_data.get("volume_ma5")
        volume_ma20 = stock_data.get("volume_ma20", stock_data.get("avg_volume"))

        if volume and volume_ma5 and volume_ma5 > 0:
            features["volume_ratio_5d"] = volume / volume_ma5
        else:
            features["volume_ratio_5d"] = 1
            missing_count += 1

        if volume and volume_ma20 and volume_ma20 > 0:
            features["volume_ratio_20d"] = volume / volume_ma20
        else:
            features["volume_ratio_20d"] = 1
            missing_count += 1

        # 量能趨勢
        if features.get("volume_ratio_20d", 1) > 1.2:
            features["volume_trend"] = 1  # 放量
        elif features.get("volume_ratio_20d", 1) < 0.8:
            features["volume_trend"] = -1  # 縮量
        else:
            features["volume_trend"] = 0

        # V10.38 新增: 量價趨勢
        price_trend = 1 if features.get("price_change_5d", 0) > 0 else -1
        vol_trend = features.get("volume_trend", 0)
        features["volume_price_trend"] = price_trend * vol_trend  # 量價配合度

        # V10.38 新增: OBV 斜率 (簡化)
        if history and len(history) >= 10:
            obv = 0
            for i in range(-10, 0):
                if history[i].get("close", 0) > history[i-1].get("close", 0):
                    obv += history[i].get("volume", 0)
                else:
                    obv -= history[i].get("volume", 0)
            features["obv_slope"] = 1 if obv > 0 else (-1 if obv < 0 else 0)
        else:
            features["obv_slope"] = 0
            missing_count += 1

        # V10.38 新增: 量能突破
        if features.get("volume_ratio_20d", 1) > 2.0:
            features["volume_breakout"] = 1
        else:
            features["volume_breakout"] = 0

        # ========== 波動率指標 (6) ==========

        volatility = stock_data.get("volatility", stock_data.get("volatility_20d"))
        if volatility is not None:
            features["volatility_20d"] = volatility
        else:
            features["volatility_20d"] = 0
            missing_count += 1

        atr = stock_data.get("atr")
        if atr is not None and price and price > 0:
            features["atr_ratio"] = atr / price * 100
        else:
            features["atr_ratio"] = 0
            missing_count += 1

        # 布林通道
        bb_upper = stock_data.get("bb_upper")
        bb_lower = stock_data.get("bb_lower")
        bb_middle = stock_data.get("bb_middle", ma20)

        if bb_upper and bb_lower and price and bb_upper != bb_lower:
            features["bb_position"] = (price - bb_lower) / (bb_upper - bb_lower)
        else:
            features["bb_position"] = 0.5
            missing_count += 1

        # V10.38 新增: 布林通道寬度
        if bb_upper and bb_lower and bb_middle and bb_middle > 0:
            features["bb_width"] = (bb_upper - bb_lower) / bb_middle * 100
        else:
            features["bb_width"] = 0
            missing_count += 1

        # V10.38 新增: 日內振幅
        if high and low and low > 0:
            features["intraday_range"] = (high - low) / low * 100
        else:
            features["intraday_range"] = 0
            missing_count += 1

        # V10.38 新增: 缺口比率
        if prev_close and open_price and prev_close > 0:
            features["gap_ratio"] = (open_price - prev_close) / prev_close * 100
        else:
            features["gap_ratio"] = 0
            missing_count += 1

        # ========== 籌碼面指標 (8) ==========

        foreign_net = stock_data.get("foreign_net", stock_data.get("foreign_buy"))
        trust_net = stock_data.get("trust_net", stock_data.get("trust_buy"))
        dealer_net = stock_data.get("dealer_net", stock_data.get("dealer_buy"))

        # 正規化籌碼數據
        if volume and volume > 0:
            volume_base = volume
        else:
            volume_base = 1000

        if foreign_net is not None:
            features["foreign_net_ratio"] = foreign_net / volume_base * 100
        else:
            features["foreign_net_ratio"] = 0
            missing_count += 1

        # V10.38 新增: 外資 5 日累計
        foreign_5d = stock_data.get("foreign_net_5d")
        if foreign_5d is not None:
            features["foreign_net_5d"] = foreign_5d
        else:
            features["foreign_net_5d"] = 0
            missing_count += 1

        # V10.38 新增: 外資趨勢
        if foreign_net is not None:
            features["foreign_trend"] = 1 if foreign_net > 0 else (-1 if foreign_net < 0 else 0)
        else:
            features["foreign_trend"] = 0
            missing_count += 1

        if trust_net is not None:
            features["trust_net_ratio"] = trust_net / volume_base * 100
        else:
            features["trust_net_ratio"] = 0
            missing_count += 1

        # V10.38 新增: 投信 5 日累計
        trust_5d = stock_data.get("trust_net_5d")
        if trust_5d is not None:
            features["trust_net_5d"] = trust_5d
        else:
            features["trust_net_5d"] = 0
            missing_count += 1

        if dealer_net is not None:
            features["dealer_net_ratio"] = dealer_net / volume_base * 100
        else:
            features["dealer_net_ratio"] = 0
            missing_count += 1

        # 法人綜合評分
        inst_score = 50
        if foreign_net is not None:
            inst_score += 10 if foreign_net > 0 else -10
        if trust_net is not None:
            inst_score += 8 if trust_net > 0 else -5
        if dealer_net is not None:
            inst_score += 5 if dealer_net > 0 else -3
        features["institutional_score"] = max(0, min(100, inst_score))

        # V10.38 新增: 法人共識度 (三大法人同向比例)
        consensus = 0
        if foreign_net is not None and foreign_net > 0:
            consensus += 1
        if trust_net is not None and trust_net > 0:
            consensus += 1
        if dealer_net is not None and dealer_net > 0:
            consensus += 1
        features["institutional_consensus"] = consensus / 3  # 0-1

        # ========== 基本面指標 (8) ==========

        pe = stock_data.get("pe", stock_data.get("pe_ratio"))
        pb = stock_data.get("pb", stock_data.get("pb_ratio"))
        dividend = stock_data.get("dividend_yield")
        revenue_growth = stock_data.get("revenue_growth")
        profit_margin = stock_data.get("profit_margin", stock_data.get("gross_margin"))
        roe = stock_data.get("roe")
        debt_ratio = stock_data.get("debt_ratio")
        eps_growth = stock_data.get("eps_growth")

        # PE 標準化 (假設合理 PE 為 15)
        if pe is not None and pe > 0:
            features["pe_normalized"] = min(max((15 - pe) / 15, -1), 1)
        else:
            features["pe_normalized"] = 0
            missing_count += 1

        # PB 標準化 (假設合理 PB 為 1.5)
        if pb is not None and pb > 0:
            features["pb_normalized"] = min(max((1.5 - pb) / 1.5, -1), 1)
        else:
            features["pb_normalized"] = 0
            missing_count += 1

        if dividend is not None:
            features["dividend_yield"] = dividend
        else:
            features["dividend_yield"] = 0
            missing_count += 1

        if revenue_growth is not None:
            features["revenue_growth"] = revenue_growth
        else:
            features["revenue_growth"] = 0
            missing_count += 1

        if profit_margin is not None:
            features["profit_margin"] = profit_margin
        else:
            features["profit_margin"] = 0
            missing_count += 1

        if roe is not None:
            features["roe"] = roe
        else:
            features["roe"] = 0
            missing_count += 1

        if debt_ratio is not None:
            features["debt_ratio"] = debt_ratio
        else:
            features["debt_ratio"] = 0
            missing_count += 1

        if eps_growth is not None:
            features["eps_growth"] = eps_growth
        else:
            features["eps_growth"] = 0
            missing_count += 1

        # ========== 市場環境指標 (4) ==========

        market_trend = stock_data.get("market_trend")
        sector_momentum = stock_data.get("sector_momentum")
        market_volatility = stock_data.get("market_volatility")
        industry_heat = stock_data.get("industry_heat")

        if market_trend is not None:
            features["market_trend"] = market_trend
        else:
            features["market_trend"] = 0
            missing_count += 1

        if sector_momentum is not None:
            features["sector_momentum"] = sector_momentum
        else:
            features["sector_momentum"] = 0
            missing_count += 1

        if market_volatility is not None:
            features["market_volatility"] = market_volatility
        else:
            features["market_volatility"] = 0
            missing_count += 1

        if industry_heat is not None:
            features["industry_heat"] = industry_heat
        else:
            features["industry_heat"] = 0
            missing_count += 1

        # ========== 信心與評分 (2) ==========

        ai_score = stock_data.get("ai_score", stock_data.get("score"))
        confidence = stock_data.get("confidence")

        if ai_score is not None:
            features["ai_score"] = ai_score
        else:
            features["ai_score"] = 50
            missing_count += 1

        if confidence is not None:
            features["confidence"] = confidence
        else:
            features["confidence"] = 50
            missing_count += 1

        return FeatureSet(
            stock_id=stock_id,
            features=features,
            feature_count=len(features),
            missing_count=missing_count,
            timestamp=datetime.now().isoformat(),
        )

    def extract_batch(
        self,
        stocks: List[Dict]
    ) -> List[FeatureSet]:
        """批次萃取特徵"""
        return [self.extract_features(s) for s in stocks]

    def get_feature_vector(
        self,
        feature_set: FeatureSet,
        feature_names: Optional[List[str]] = None
    ) -> List[float]:
        """
        將特徵集轉為向量

        Args:
            feature_set: 特徵集合
            feature_names: 指定的特徵名稱順序

        Returns:
            特徵向量
        """
        if feature_names is None:
            feature_names = self.feature_names

        return [
            feature_set.features.get(name, 0)
            for name in feature_names
        ]

    def get_feature_info(self) -> Dict[str, Any]:
        """取得特徵說明 (V10.38 更新)"""
        return {
            "version": "V10.38",
            "total_features": len(self.FEATURE_DEFINITIONS),
            "features": self.FEATURE_DEFINITIONS,
            "categories": {
                "price": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "price"],
                "momentum": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "momentum"],
                "volume": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "volume"],
                "volatility": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "volatility"],
                "chip": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "chip"],
                "fundamental": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "fundamental"],
                "market": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "market"],
                "score": [k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "score"],
            },
            "category_counts": {
                "price": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "price"]),
                "momentum": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "momentum"]),
                "volume": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "volume"]),
                "volatility": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "volatility"]),
                "chip": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "chip"]),
                "fundamental": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "fundamental"]),
                "market": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "market"]),
                "score": len([k for k, v in self.FEATURE_DEFINITIONS.items() if v["type"] == "score"]),
            },
        }


# 全域實例
_engine: Optional[MLFeatureEngine] = None


def get_feature_engine() -> MLFeatureEngine:
    """取得特徵引擎實例"""
    global _engine
    if _engine is None:
        _engine = MLFeatureEngine()
    return _engine


def extract_features(stock_data: Dict, history: Optional[List[Dict]] = None) -> Dict:
    """萃取特徵 (便捷函數)"""
    engine = get_feature_engine()
    result = engine.extract_features(stock_data, history)
    return asdict(result)
