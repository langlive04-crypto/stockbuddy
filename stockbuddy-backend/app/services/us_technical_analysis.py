"""
美股技術分析服務 - US Stock Technical Analysis Service
V10.27 新增

功能：
- RSI 指標計算
- MACD 指標計算
- KD 指標計算
- 移動平均線
- 布林通道
- 支撐/壓力位
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import math

from app.services.us_stock_service import USStockService


@dataclass
class TechnicalIndicators:
    """技術指標結果"""
    symbol: str
    date: str

    # RSI
    rsi: Optional[float]
    rsi_signal: str  # 超買/超賣/中性

    # MACD
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    macd_cross: str  # 金叉/死叉/無

    # KD
    k: Optional[float]
    d: Optional[float]
    kd_signal: str  # 超買/超賣/黃金交叉/死亡交叉

    # 移動平均
    ma5: Optional[float]
    ma10: Optional[float]
    ma20: Optional[float]
    ma60: Optional[float]
    ma_trend: str  # 多頭排列/空頭排列/盤整

    # 布林通道
    bb_upper: Optional[float]
    bb_middle: Optional[float]
    bb_lower: Optional[float]
    bb_position: str  # 上軌/下軌/中軌

    # 支撐壓力
    support: Optional[float]
    resistance: Optional[float]

    # 綜合評分
    technical_score: int  # 0-100
    recommendation: str  # 買進/持有/賣出


class USTechnicalAnalysis:
    """美股技術分析服務"""

    @classmethod
    async def analyze(cls, symbol: str) -> Optional[TechnicalIndicators]:
        """
        對美股進行完整技術分析

        Args:
            symbol: 美股代號

        Returns:
            TechnicalIndicators: 技術分析結果
        """
        # 取得歷史資料（需要足夠長的數據來計算指標）
        history = await USStockService.get_stock_history(symbol, months=6)

        if not history or len(history) < 60:
            return None

        # 提取收盤價和成交量
        closes = [d['close'] for d in history]
        highs = [d['high'] for d in history]
        lows = [d['low'] for d in history]
        volumes = [d['volume'] for d in history]

        # 計算各指標
        rsi = cls._calculate_rsi(closes)
        macd_data = cls._calculate_macd(closes)
        kd_data = cls._calculate_kd(highs, lows, closes)
        ma_data = cls._calculate_ma(closes)
        bb_data = cls._calculate_bollinger(closes)
        support, resistance = cls._calculate_support_resistance(highs, lows, closes)

        # 判斷信號
        rsi_signal = cls._get_rsi_signal(rsi)
        macd_cross = cls._get_macd_cross(macd_data)
        kd_signal = cls._get_kd_signal(kd_data)
        ma_trend = cls._get_ma_trend(ma_data, closes[-1])
        bb_position = cls._get_bb_position(closes[-1], bb_data)

        # 計算綜合評分
        score, recommendation = cls._calculate_score(
            rsi, rsi_signal,
            macd_data, macd_cross,
            kd_data, kd_signal,
            ma_data, ma_trend,
            closes[-1]
        )

        return TechnicalIndicators(
            symbol=symbol,
            date=history[-1]['date'],
            # RSI
            rsi=rsi,
            rsi_signal=rsi_signal,
            # MACD
            macd=macd_data.get('macd'),
            macd_signal=macd_data.get('signal'),
            macd_histogram=macd_data.get('histogram'),
            macd_cross=macd_cross,
            # KD
            k=kd_data.get('k'),
            d=kd_data.get('d'),
            kd_signal=kd_signal,
            # MA
            ma5=ma_data.get('ma5'),
            ma10=ma_data.get('ma10'),
            ma20=ma_data.get('ma20'),
            ma60=ma_data.get('ma60'),
            ma_trend=ma_trend,
            # 布林
            bb_upper=bb_data.get('upper'),
            bb_middle=bb_data.get('middle'),
            bb_lower=bb_data.get('lower'),
            bb_position=bb_position,
            # 支撐壓力
            support=support,
            resistance=resistance,
            # 綜合
            technical_score=score,
            recommendation=recommendation,
        )

    @classmethod
    def _calculate_rsi(cls, closes: List[float], period: int = 14) -> Optional[float]:
        """計算 RSI"""
        if len(closes) < period + 1:
            return None

        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        # 使用最近的數據
        recent_gains = gains[-period:]
        recent_losses = losses[-period:]

        avg_gain = sum(recent_gains) / period
        avg_loss = sum(recent_losses) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    @classmethod
    def _calculate_macd(cls, closes: List[float]) -> Dict:
        """計算 MACD"""
        if len(closes) < 26:
            return {}

        # EMA 計算函數
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_values = [data[0]]
            for i in range(1, len(data)):
                ema_values.append(
                    (data[i] - ema_values[-1]) * multiplier + ema_values[-1]
                )
            return ema_values

        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)

        # DIF (MACD Line)
        macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]

        # Signal Line (9-day EMA of MACD)
        signal_line = ema(macd_line, 9)

        # Histogram
        histogram = macd_line[-1] - signal_line[-1]

        return {
            'macd': round(macd_line[-1], 4),
            'signal': round(signal_line[-1], 4),
            'histogram': round(histogram, 4),
            'prev_macd': round(macd_line[-2], 4) if len(macd_line) > 1 else None,
            'prev_signal': round(signal_line[-2], 4) if len(signal_line) > 1 else None,
        }

    @classmethod
    def _calculate_kd(cls, highs: List[float], lows: List[float], closes: List[float], period: int = 9) -> Dict:
        """計算 KD 指標"""
        if len(closes) < period:
            return {}

        # RSV = (今日收盤價 - 最近N日最低價) / (最近N日最高價 - 最近N日最低價) * 100
        lowest = min(lows[-period:])
        highest = max(highs[-period:])

        if highest == lowest:
            rsv = 50
        else:
            rsv = (closes[-1] - lowest) / (highest - lowest) * 100

        # K = 2/3 * 前日K + 1/3 * RSV (初始值 50)
        # D = 2/3 * 前日D + 1/3 * K (初始值 50)
        # 簡化版計算
        k = rsv  # 簡化
        d = rsv * 0.67  # 簡化

        return {
            'k': round(k, 2),
            'd': round(d, 2),
            'rsv': round(rsv, 2),
        }

    @classmethod
    def _calculate_ma(cls, closes: List[float]) -> Dict:
        """計算移動平均線"""
        result = {}

        for period in [5, 10, 20, 60]:
            if len(closes) >= period:
                ma = sum(closes[-period:]) / period
                result[f'ma{period}'] = round(ma, 2)

        return result

    @classmethod
    def _calculate_bollinger(cls, closes: List[float], period: int = 20, std_dev: float = 2) -> Dict:
        """計算布林通道"""
        if len(closes) < period:
            return {}

        recent = closes[-period:]
        middle = sum(recent) / period

        # 標準差
        variance = sum((x - middle) ** 2 for x in recent) / period
        std = math.sqrt(variance)

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {
            'upper': round(upper, 2),
            'middle': round(middle, 2),
            'lower': round(lower, 2),
        }

    @classmethod
    def _calculate_support_resistance(cls, highs: List[float], lows: List[float], closes: List[float]) -> tuple:
        """計算支撐壓力位"""
        recent_period = min(20, len(closes))

        recent_highs = highs[-recent_period:]
        recent_lows = lows[-recent_period:]

        # 簡化版：使用近期高低點
        resistance = max(recent_highs)
        support = min(recent_lows)

        return round(support, 2), round(resistance, 2)

    @classmethod
    def _get_rsi_signal(cls, rsi: Optional[float]) -> str:
        """判斷 RSI 信號"""
        if rsi is None:
            return '無資料'
        if rsi >= 70:
            return '超買'
        if rsi <= 30:
            return '超賣'
        if rsi >= 60:
            return '偏強'
        if rsi <= 40:
            return '偏弱'
        return '中性'

    @classmethod
    def _get_macd_cross(cls, macd_data: Dict) -> str:
        """判斷 MACD 交叉"""
        if not macd_data:
            return '無'

        macd = macd_data.get('macd')
        signal = macd_data.get('signal')
        prev_macd = macd_data.get('prev_macd')
        prev_signal = macd_data.get('prev_signal')

        if None in [macd, signal, prev_macd, prev_signal]:
            return '無'

        # 金叉：MACD 從下往上穿越 Signal
        if prev_macd <= prev_signal and macd > signal:
            return '金叉'

        # 死叉：MACD 從上往下穿越 Signal
        if prev_macd >= prev_signal and macd < signal:
            return '死叉'

        return '無'

    @classmethod
    def _get_kd_signal(cls, kd_data: Dict) -> str:
        """判斷 KD 信號"""
        if not kd_data:
            return '無資料'

        k = kd_data.get('k')
        d = kd_data.get('d')

        if k is None or d is None:
            return '無資料'

        if k > 80 and d > 80:
            return '超買'
        if k < 20 and d < 20:
            return '超賣'
        if k > d and k < 80:
            return '黃金交叉'
        if k < d and k > 20:
            return '死亡交叉'
        return '中性'

    @classmethod
    def _get_ma_trend(cls, ma_data: Dict, current_price: float) -> str:
        """判斷均線趨勢"""
        ma5 = ma_data.get('ma5')
        ma10 = ma_data.get('ma10')
        ma20 = ma_data.get('ma20')

        if None in [ma5, ma10, ma20]:
            return '資料不足'

        # 多頭排列：短均 > 中均 > 長均
        if ma5 > ma10 > ma20:
            return '多頭排列'

        # 空頭排列：短均 < 中均 < 長均
        if ma5 < ma10 < ma20:
            return '空頭排列'

        return '盤整'

    @classmethod
    def _get_bb_position(cls, price: float, bb_data: Dict) -> str:
        """判斷布林通道位置"""
        if not bb_data:
            return '無資料'

        upper = bb_data.get('upper')
        lower = bb_data.get('lower')
        middle = bb_data.get('middle')

        if None in [upper, lower, middle]:
            return '無資料'

        if price >= upper:
            return '上軌'
        if price <= lower:
            return '下軌'
        if price >= middle:
            return '中上'
        return '中下'

    @classmethod
    def _calculate_score(cls, rsi, rsi_signal, macd_data, macd_cross,
                         kd_data, kd_signal, ma_data, ma_trend, current_price) -> tuple:
        """計算綜合技術評分"""
        score = 50  # 基礎分數

        # RSI 評分 (±15)
        if rsi:
            if rsi_signal == '超賣':
                score += 15  # 超賣是買進機會
            elif rsi_signal == '超買':
                score -= 15
            elif rsi_signal == '偏強':
                score += 5
            elif rsi_signal == '偏弱':
                score -= 5

        # MACD 評分 (±15)
        if macd_cross == '金叉':
            score += 15
        elif macd_cross == '死叉':
            score -= 15
        elif macd_data.get('histogram', 0) > 0:
            score += 5
        elif macd_data.get('histogram', 0) < 0:
            score -= 5

        # KD 評分 (±10)
        if kd_signal == '黃金交叉':
            score += 10
        elif kd_signal == '死亡交叉':
            score -= 10
        elif kd_signal == '超賣':
            score += 8
        elif kd_signal == '超買':
            score -= 8

        # 均線趨勢評分 (±10)
        if ma_trend == '多頭排列':
            score += 10
        elif ma_trend == '空頭排列':
            score -= 10

        # 限制分數範圍
        score = max(0, min(100, score))

        # 決定推薦
        if score >= 70:
            recommendation = '買進'
        elif score >= 55:
            recommendation = '偏多'
        elif score >= 45:
            recommendation = '持有'
        elif score >= 30:
            recommendation = '偏空'
        else:
            recommendation = '賣出'

        return score, recommendation


# 建立全域服務實例
us_technical = USTechnicalAnalysis()
