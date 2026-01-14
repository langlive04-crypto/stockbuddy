"""
技術分析服務
計算各種技術指標
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


class TechnicalAnalysis:
    """技術分析計算"""

    @staticmethod
    def calculate_ma(prices: List[float], period: int) -> List[Optional[float]]:
        """計算移動平均線"""
        if len(prices) < period:
            return [None] * len(prices)
        
        result = [None] * (period - 1)
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            result.append(round(avg, 2))
        return result

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """計算 RSI 指標"""
        if len(prices) < period + 1:
            return [None] * len(prices)

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        result = [None] * period
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            result.append(round(rsi, 2))

        # 補上第一個 RSI
        if avg_loss == 0:
            first_rsi = 100
        else:
            rs = (sum(gains[:period]) / period) / (sum(losses[:period]) / period) if sum(losses[:period]) > 0 else 100
            first_rsi = 100 - (100 / (1 + rs)) if rs != 100 else 100
        result[period - 1] = round(first_rsi, 2)

        return [None] + result  # 第一個價格沒有變動

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[Optional[float]]]:
        """計算 MACD 指標"""
        if len(prices) < slow:
            return {
                "macd": [None] * len(prices),
                "signal": [None] * len(prices),
                "histogram": [None] * len(prices),
            }

        # 計算 EMA
        def ema(data: List[float], period: int) -> List[float]:
            multiplier = 2 / (period + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append((data[i] * multiplier) + (result[-1] * (1 - multiplier)))
            return result

        ema_fast = ema(prices, fast)
        ema_slow = ema(prices, slow)
        
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(prices))]
        signal_line = ema(macd_line, signal)
        histogram = [macd_line[i] - signal_line[i] for i in range(len(prices))]

        # 前面數據不足的部分設為 None
        for i in range(slow - 1):
            macd_line[i] = None
            signal_line[i] = None
            histogram[i] = None

        return {
            "macd": [round(v, 4) if v is not None else None for v in macd_line],
            "signal": [round(v, 4) if v is not None else None for v in signal_line],
            "histogram": [round(v, 4) if v is not None else None for v in histogram],
        }

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[Optional[float]]]:
        """計算布林通道"""
        if len(prices) < period:
            return {
                "upper": [None] * len(prices),
                "middle": [None] * len(prices),
                "lower": [None] * len(prices),
            }

        middle = TechnicalAnalysis.calculate_ma(prices, period)
        
        upper = []
        lower = []
        
        for i in range(len(prices)):
            if middle[i] is None:
                upper.append(None)
                lower.append(None)
            else:
                window = prices[i - period + 1:i + 1]
                std = np.std(window)
                upper.append(round(middle[i] + std_dev * std, 2))
                lower.append(round(middle[i] - std_dev * std, 2))

        return {
            "upper": upper,
            "middle": middle,
            "lower": lower,
        }

    @staticmethod
    def analyze_trend(prices: List[float], ma5: List[float], ma20: List[float], ma60: List[float]) -> Dict[str, Any]:
        """分析趨勢"""
        if not prices or len(prices) < 60:
            return {"trend": "資料不足", "score": 50}

        current_price = prices[-1]
        current_ma5 = ma5[-1] if ma5[-1] else 0
        current_ma20 = ma20[-1] if ma20[-1] else 0
        current_ma60 = ma60[-1] if ma60[-1] else 0

        score = 50  # 基礎分

        # 價格與均線關係
        if current_price > current_ma5:
            score += 10
        if current_price > current_ma20:
            score += 10
        if current_price > current_ma60:
            score += 10

        # 均線排列
        if current_ma5 > current_ma20 > current_ma60:
            score += 15  # 多頭排列
            trend = "多頭排列"
        elif current_ma5 < current_ma20 < current_ma60:
            score -= 15  # 空頭排列
            trend = "空頭排列"
        else:
            trend = "盤整"

        # 判斷趨勢描述
        if score >= 80:
            trend_desc = "強勢多頭"
        elif score >= 65:
            trend_desc = "偏多"
        elif score >= 50:
            trend_desc = "中性偏多"
        elif score >= 35:
            trend_desc = "中性偏空"
        else:
            trend_desc = "偏空"

        return {
            "trend": trend,
            "trend_desc": trend_desc,
            "score": int(min(100, max(0, score))),
            "above_ma5": bool(current_price > current_ma5),
            "above_ma20": bool(current_price > current_ma20),
            "above_ma60": bool(current_price > current_ma60),
        }

    @staticmethod
    def analyze_rsi(rsi_values: List[float]) -> Dict[str, Any]:
        """分析 RSI"""
        if not rsi_values or rsi_values[-1] is None:
            return {"status": "資料不足", "value": None, "score": 50}

        current_rsi = rsi_values[-1]

        if current_rsi >= 80:
            status = "嚴重超買"
            score = 20
        elif current_rsi >= 70:
            status = "超買"
            score = 35
        elif current_rsi >= 50:
            status = "偏強"
            score = 65
        elif current_rsi >= 30:
            status = "偏弱"
            score = 45
        elif current_rsi >= 20:
            status = "超賣"
            score = 70  # 超賣可能是買點
        else:
            status = "嚴重超賣"
            score = 75

        return {
            "status": status,
            "value": float(current_rsi) if current_rsi is not None else None,
            "score": int(score),
        }

    @staticmethod
    def analyze_macd(macd_data: Dict[str, List]) -> Dict[str, Any]:
        """分析 MACD"""
        macd = macd_data["macd"]
        signal = macd_data["signal"]
        histogram = macd_data["histogram"]

        if not macd or macd[-1] is None:
            return {"status": "資料不足", "signal": None, "score": 50}

        current_macd = macd[-1]
        current_signal = signal[-1]
        current_hist = histogram[-1]
        prev_hist = histogram[-2] if len(histogram) > 1 and histogram[-2] is not None else 0

        # 判斷金叉/死叉
        if current_macd > current_signal and (len(macd) < 2 or macd[-2] <= signal[-2]):
            cross_signal = "金叉"
            score = 80
        elif current_macd < current_signal and (len(macd) < 2 or macd[-2] >= signal[-2]):
            cross_signal = "死叉"
            score = 30
        elif current_macd > current_signal:
            cross_signal = "多方"
            score = 65
        else:
            cross_signal = "空方"
            score = 40

        # 柱狀圖趨勢
        if current_hist > prev_hist:
            momentum = "動能增強"
            score += 5
        else:
            momentum = "動能減弱"
            score -= 5

        return {
            "signal": cross_signal,
            "momentum": momentum,
            "macd_value": float(round(current_macd, 4)),
            "histogram": float(round(current_hist, 4)),
            "score": int(min(100, max(0, score))),
        }

    @staticmethod
    def calculate_support_resistance(prices: List[float], highs: List[float], lows: List[float]) -> Dict[str, Any]:
        """計算支撐壓力位"""
        if len(prices) < 20:
            return {"support": None, "resistance": None}

        recent_lows = lows[-20:]
        recent_highs = highs[-20:]
        current_price = prices[-1]

        # 簡單取近期低點作為支撐，高點作為壓力
        support = min(recent_lows)
        resistance = max(recent_highs)

        return {
            "support": float(round(support, 2)),
            "resistance": float(round(resistance, 2)),
            "support_distance": float(round((current_price - support) / current_price * 100, 2)),
            "resistance_distance": float(round((resistance - current_price) / current_price * 100, 2)),
        }

    @classmethod
    def full_analysis(cls, history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """完整技術分析"""
        if not history_data or len(history_data) < 20:
            return {"error": "資料不足，需要至少 20 天歷史資料", "overall_score": 50}

        # 提取價格資料
        closes = [d["close"] for d in history_data]
        highs = [d["high"] for d in history_data]
        lows = [d["low"] for d in history_data]
        volumes = [d["volume"] for d in history_data]

        # 計算各種指標（根據資料量調整）
        ma5 = cls.calculate_ma(closes, 5)
        ma20 = cls.calculate_ma(closes, min(20, len(closes) - 1))
        ma60 = cls.calculate_ma(closes, min(60, len(closes) - 1)) if len(closes) > 30 else ma20
        rsi = cls.calculate_rsi(closes, 14)
        macd = cls.calculate_macd(closes)
        bb = cls.calculate_bollinger_bands(closes)

        # 分析
        trend_analysis = cls.analyze_trend(closes, ma5, ma20, ma60)
        rsi_analysis = cls.analyze_rsi(rsi)
        macd_analysis = cls.analyze_macd(macd)
        sr_levels = cls.calculate_support_resistance(closes, highs, lows)

        # 成交量分析
        vol_period = min(20, len(volumes))
        avg_volume = sum(volumes[-vol_period:]) / vol_period if vol_period > 0 else volumes[-1]
        current_volume = volumes[-1]
        volume_ratio = round(current_volume / avg_volume, 2) if avg_volume > 0 else 1

        # === V10.8.1 改進的綜合評分（修正天花板問題）===
        base_score = (
            trend_analysis["score"] * 0.35 +
            rsi_analysis["score"] * 0.25 +
            macd_analysis["score"] * 0.40
        )
        
        # 動態加減分機制（大幅降低權重，增加扣分平衡）
        bonus = 0
        
        # 1. 價格動能（近5日表現）- 降低權重
        if len(closes) >= 5:
            recent_return = (closes[-1] - closes[-5]) / closes[-5] * 100
            if recent_return > 15:
                bonus += 8   # 原本 +15
            elif recent_return > 8:
                bonus += 5   # 原本 +10
            elif recent_return > 3:
                bonus += 2   # 原本 +5
            elif recent_return < -15:
                bonus -= 12  # 加強扣分
            elif recent_return < -8:
                bonus -= 8   # 原本 -10
            elif recent_return < -3:
                bonus -= 4   # 原本 -5
        
        # 2. 成交量異常 - 降低權重
        if volume_ratio > 3:
            bonus += 6    # 原本 +12
        elif volume_ratio > 2:
            bonus += 4    # 原本 +8
        elif volume_ratio > 1.5:
            bonus += 2    # 原本 +4
        elif volume_ratio < 0.5:
            bonus -= 4    # 縮量扣分
        elif volume_ratio < 0.3:
            bonus -= 6    # 極度縮量
        
        # 3. 連續上漲/下跌天數 - 降低權重，增加下跌扣分
        if len(closes) >= 5:
            up_days = sum(1 for i in range(-4, 0) if closes[i] > closes[i-1])
            down_days = sum(1 for i in range(-4, 0) if closes[i] < closes[i-1])
            if up_days >= 4:
                bonus += 4   # 原本 +10
            elif up_days >= 3:
                bonus += 2   # 原本 +5
            if down_days >= 4:
                bonus -= 6   # 新增：連續下跌扣分
            elif down_days >= 3:
                bonus -= 3
        
        # 4. 均線位置 - 降低權重，增加空頭扣分
        above_ma5 = trend_analysis.get("above_ma5")
        above_ma20 = trend_analysis.get("above_ma20")
        above_ma60 = trend_analysis.get("above_ma60")
        
        if above_ma5 and above_ma20 and above_ma60:
            bonus += 4    # 原本 +8（站上所有均線）
        elif above_ma5 and above_ma20:
            bonus += 2    # 原本 +4
        elif not above_ma5 and not above_ma20 and not above_ma60:
            bonus -= 6    # 新增：跌破所有均線扣分
        elif not above_ma5 and not above_ma20:
            bonus -= 3    # 新增：跌破短中期均線
        
        # 5. RSI 極端值 - 降低權重
        rsi_val = rsi_analysis.get("value")
        if rsi_val:
            if rsi_val < 20:   # 嚴重超賣
                bonus += 6    # 原本 +12
            elif rsi_val < 30:
                bonus += 3    # 原本 +6
            elif rsi_val > 85:  # 嚴重超買
                bonus -= 8    # 原本 -10
            elif rsi_val > 75:
                bonus -= 4    # 原本 -5
        
        # 6. MACD 信號 - 降低權重
        macd_signal = macd_analysis.get("signal")
        if macd_signal == "金叉":
            bonus += 6    # 原本 +15
        elif macd_signal == "多方":
            bonus += 2    # 原本 +5
        elif macd_signal == "死叉":
            bonus -= 8    # 原本 -12
        elif macd_signal == "空方":
            bonus -= 4    # 原本 -5
        
        # 最終分數（移除硬上限，使用自然分布）
        # 預期分布：基礎 50-80，bonus -30 ~ +30，總分 20-100
        final_score = int(round(max(15, min(100, base_score + bonus))))

        return {
            "current_price": float(closes[-1]),
            "ma": {
                "ma5": float(ma5[-1]) if ma5[-1] is not None else None,
                "ma20": float(ma20[-1]) if ma20[-1] is not None else None,
                "ma60": float(ma60[-1]) if ma60[-1] is not None else None,
            },
            "rsi": rsi_analysis,
            "macd": macd_analysis,
            "trend": trend_analysis,
            "bollinger": {
                "upper": float(bb["upper"][-1]) if bb["upper"][-1] is not None else None,
                "middle": float(bb["middle"][-1]) if bb["middle"][-1] is not None else None,
                "lower": float(bb["lower"][-1]) if bb["lower"][-1] is not None else None,
            },
            "support_resistance": sr_levels,
            "volume": {
                "current": int(current_volume),
                "avg_20d": int(round(avg_volume)),
                "ratio": float(volume_ratio),
                "status": "爆量" if volume_ratio > 2 else "放量" if volume_ratio > 1.5 else "縮量" if volume_ratio < 0.7 else "正常",
            },
            "overall_score": final_score,
            "summary": cls._generate_summary(trend_analysis, rsi_analysis, macd_analysis, volume_ratio),
        }

    @staticmethod
    def _generate_summary(trend: Dict, rsi: Dict, macd: Dict, volume_ratio: float) -> str:
        """生成技術分析摘要"""
        parts = []
        
        # 趨勢
        parts.append(trend["trend"])
        
        # RSI
        if rsi["value"]:
            parts.append(f"RSI {rsi['value']:.0f} ({rsi['status']})")
        
        # MACD
        parts.append(f"MACD {macd['signal']}")
        
        # 成交量
        if volume_ratio > 1.5:
            parts.append("量增")
        elif volume_ratio < 0.7:
            parts.append("量縮")

        return "，".join(parts)
