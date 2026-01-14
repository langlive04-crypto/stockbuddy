"""
風險計算服務 V10.36

提供止損止盈計算、倉位管理、投資組合風險評估功能

功能：
- 基於 ATR 的止損止盈計算
- 凱利公式倉位管理
- 投資組合風險評估
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import math


@dataclass
class StopLossTarget:
    """止損止盈建議"""
    stock_id: str
    entry_price: float
    stop_loss: float
    stop_loss_pct: float
    target_1: float
    target_2: float
    target_3: float
    risk_reward_ratio: float
    atr_based: bool = True


@dataclass
class PositionSize:
    """倉位建議"""
    recommended_position: float  # 建議倉位比例 (0-1)
    recommended_amount: float    # 建議金額
    max_position: float          # 最大倉位比例
    risk_tolerance: str          # 風險偏好
    kelly_value: float           # 原始凱利值
    explanation: str             # 說明


@dataclass
class PortfolioRisk:
    """投資組合風險評估"""
    total_value: float
    holdings_count: int
    sector_exposure: Dict[str, float]
    max_single_exposure: float
    diversification_score: int
    warnings: List[str]
    recommendations: List[str]


class RiskCalculator:
    """風險計算器"""

    # 預設參數
    DEFAULT_ATR_MULTIPLIER = 2.0      # ATR 倍數
    DEFAULT_RISK_REWARD_RATIOS = [1.5, 2.0, 3.0]  # 風險報酬比
    MAX_STOP_LOSS_PCT = 0.10          # 最大止損 10%
    MIN_STOP_LOSS_PCT = 0.03          # 最小止損 3%

    # 凱利公式係數
    KELLY_FRACTIONS = {
        "conservative": 0.25,   # 1/4 Kelly
        "moderate": 0.5,        # 1/2 Kelly
        "aggressive": 0.75,     # 3/4 Kelly
    }

    @classmethod
    def calculate_stop_loss(
        cls,
        current_price: float,
        atr: Optional[float] = None,
        multiplier: float = None,
        volatility: Optional[float] = None
    ) -> Dict[str, float]:
        """
        計算止損價位

        Args:
            current_price: 當前/進場價格
            atr: ATR 值（可選，若無則用波動率估算）
            multiplier: ATR 倍數，預設 2.0
            volatility: 20日波動率（若無 ATR 時使用）

        Returns:
            止損資訊 dict
        """
        if multiplier is None:
            multiplier = cls.DEFAULT_ATR_MULTIPLIER

        # 決定止損幅度
        if atr is not None and atr > 0:
            stop_loss_amount = atr * multiplier
            atr_based = True
        elif volatility is not None and volatility > 0:
            # 用波動率估算（波動率 * 2 作為近似）
            stop_loss_amount = current_price * volatility * 2
            atr_based = False
        else:
            # 預設使用 5% 止損
            stop_loss_amount = current_price * 0.05
            atr_based = False

        # 計算止損百分比
        stop_loss_pct = stop_loss_amount / current_price

        # 限制止損範圍
        stop_loss_pct = max(cls.MIN_STOP_LOSS_PCT, min(stop_loss_pct, cls.MAX_STOP_LOSS_PCT))

        stop_loss = current_price * (1 - stop_loss_pct)

        return {
            "stop_loss": round(stop_loss, 2),
            "stop_loss_pct": round(stop_loss_pct * 100, 2),
            "atr_based": atr_based,
        }

    @classmethod
    def calculate_targets(
        cls,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratios: List[float] = None
    ) -> Dict[str, float]:
        """
        計算獲利目標

        Args:
            entry_price: 進場價格
            stop_loss: 止損價格
            risk_reward_ratios: 風險報酬比列表

        Returns:
            獲利目標 dict
        """
        if risk_reward_ratios is None:
            risk_reward_ratios = cls.DEFAULT_RISK_REWARD_RATIOS

        risk = entry_price - stop_loss

        targets = {}
        for i, rr in enumerate(risk_reward_ratios, 1):
            targets[f"target_{i}"] = round(entry_price + (risk * rr), 2)
            targets[f"target_{i}_pct"] = round(rr * (risk / entry_price) * 100, 2)

        return targets

    @classmethod
    def calculate_stop_loss_targets(
        cls,
        stock_id: str,
        entry_price: float,
        atr: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> StopLossTarget:
        """
        計算完整的止損止盈建議

        Args:
            stock_id: 股票代碼
            entry_price: 進場價格
            atr: ATR 值
            volatility: 波動率

        Returns:
            StopLossTarget 物件
        """
        # 計算止損
        stop_info = cls.calculate_stop_loss(entry_price, atr, volatility=volatility)
        stop_loss = stop_info["stop_loss"]

        # 計算目標
        targets = cls.calculate_targets(entry_price, stop_loss)

        # 計算風險報酬比（以 target_2 為基準）
        risk = entry_price - stop_loss
        reward = targets["target_2"] - entry_price
        rr_ratio = round(reward / risk, 2) if risk > 0 else 0

        return StopLossTarget(
            stock_id=stock_id,
            entry_price=entry_price,
            stop_loss=stop_loss,
            stop_loss_pct=stop_info["stop_loss_pct"],
            target_1=targets["target_1"],
            target_2=targets["target_2"],
            target_3=targets["target_3"],
            risk_reward_ratio=rr_ratio,
            atr_based=stop_info["atr_based"],
        )

    @classmethod
    def kelly_criterion(
        cls,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        計算凱利公式值

        Args:
            win_rate: 勝率 (0-1)
            avg_win: 平均獲利 (%)
            avg_loss: 平均虧損 (%)

        Returns:
            凱利值 (建議倉位比例)
        """
        if avg_loss == 0 or avg_win == 0:
            return 0

        # 轉換為比率
        W = win_rate
        R = avg_win / avg_loss  # 盈虧比

        # Kelly = W - (1-W)/R = (W*R - (1-W)) / R
        kelly = (W * R - (1 - W)) / R

        return kelly

    @classmethod
    def calculate_position_size(
        cls,
        win_rate: float = 0.5,
        avg_win: float = 10.0,
        avg_loss: float = 5.0,
        capital: float = 1000000,
        risk_tolerance: str = "moderate"
    ) -> PositionSize:
        """
        計算建議倉位

        Args:
            win_rate: 勝率 (0-1)
            avg_win: 平均獲利 (%)
            avg_loss: 平均虧損 (%)
            capital: 當前資金
            risk_tolerance: 風險偏好 (conservative/moderate/aggressive)

        Returns:
            PositionSize 物件
        """
        # 取得凱利係數
        fraction = cls.KELLY_FRACTIONS.get(risk_tolerance, 0.5)

        # 計算原始凱利值
        kelly = cls.kelly_criterion(win_rate, avg_win, avg_loss)

        # 套用係數
        adjusted_kelly = kelly * fraction

        # 限制範圍 (0% - 25%)
        recommended_position = max(0, min(adjusted_kelly, 0.25))

        # 計算建議金額
        recommended_amount = capital * recommended_position

        # 最大倉位 (不超過 30%)
        max_position = min(kelly * 0.75, 0.30) if kelly > 0 else 0.10

        # 產生說明
        explanation = (
            f"基於 {win_rate*100:.1f}% 勝率和 {avg_win/avg_loss:.2f} 盈虧比，"
            f"使用 {fraction*100:.0f}% Kelly"
        )

        return PositionSize(
            recommended_position=round(recommended_position, 4),
            recommended_amount=round(recommended_amount, 0),
            max_position=round(max_position, 4),
            risk_tolerance=risk_tolerance,
            kelly_value=round(kelly, 4),
            explanation=explanation,
        )

    @classmethod
    def assess_portfolio_risk(
        cls,
        holdings: List[Dict[str, Any]]
    ) -> PortfolioRisk:
        """
        評估投資組合風險

        Args:
            holdings: 持股列表，每項包含:
                - stock_id: 股票代碼
                - stock_name: 股票名稱
                - market_value: 市值
                - industry: 產業 (可選)

        Returns:
            PortfolioRisk 物件
        """
        if not holdings:
            return PortfolioRisk(
                total_value=0,
                holdings_count=0,
                sector_exposure={},
                max_single_exposure=0,
                diversification_score=0,
                warnings=["投資組合為空"],
                recommendations=["請先建立投資組合"],
            )

        # 計算總市值
        total_value = sum(h.get("market_value", 0) for h in holdings)

        if total_value == 0:
            return PortfolioRisk(
                total_value=0,
                holdings_count=len(holdings),
                sector_exposure={},
                max_single_exposure=0,
                diversification_score=0,
                warnings=["投資組合市值為零"],
                recommendations=["請更新持股市值資料"],
            )

        # 計算產業曝險
        sector_exposure = {}
        for h in holdings:
            sector = h.get("industry", "未分類")
            value = h.get("market_value", 0)
            sector_exposure[sector] = sector_exposure.get(sector, 0) + value

        # 轉換為百分比
        sector_exposure = {
            k: round(v / total_value * 100, 1)
            for k, v in sector_exposure.items()
        }

        # 計算單一股票最大曝險
        max_single_value = max(h.get("market_value", 0) for h in holdings)
        max_single_exposure = round(max_single_value / total_value * 100, 1)

        # 計算分散度分數 (0-100)
        # 考量因素：持股數量、產業分散、單一曝險
        holdings_score = min(len(holdings) * 10, 40)  # 最高 40 分
        sector_score = min(len(sector_exposure) * 10, 30)  # 最高 30 分
        concentration_score = max(0, 30 - max_single_exposure)  # 最高 30 分

        diversification_score = int(holdings_score + sector_score + concentration_score)

        # 產生警告
        warnings = []
        recommendations = []

        # 檢查單一股票集中
        if max_single_exposure > 30:
            warnings.append(f"單一股票佔比過高: {max_single_exposure}% (建議 <30%)")

        # 檢查產業集中
        for sector, exposure in sector_exposure.items():
            if exposure > 40:
                warnings.append(f"產業集中: {sector} 佔比 {exposure}% 超過 40%")

        # 檢查持股數量
        if len(holdings) < 5:
            recommendations.append("建議增加持股至 5-10 檔以分散風險")
        elif len(holdings) > 20:
            recommendations.append("持股過多可能影響管理效率，建議精簡至 10-15 檔")

        # 產業分散建議
        if len(sector_exposure) < 3:
            recommendations.append("考慮增加其他產業配置以分散風險")

        if not warnings:
            recommendations.append("投資組合風險分散良好")

        return PortfolioRisk(
            total_value=total_value,
            holdings_count=len(holdings),
            sector_exposure=sector_exposure,
            max_single_exposure=max_single_exposure,
            diversification_score=diversification_score,
            warnings=warnings,
            recommendations=recommendations,
        )


# 便捷函數
def get_stop_loss_target(stock_id: str, entry_price: float,
                         atr: float = None, volatility: float = None) -> Dict:
    """取得止損止盈建議"""
    result = RiskCalculator.calculate_stop_loss_targets(
        stock_id, entry_price, atr, volatility
    )
    return asdict(result)


def get_position_size(win_rate: float = 0.5, avg_win: float = 10.0,
                      avg_loss: float = 5.0, capital: float = 1000000,
                      risk_tolerance: str = "moderate") -> Dict:
    """取得倉位建議"""
    result = RiskCalculator.calculate_position_size(
        win_rate, avg_win, avg_loss, capital, risk_tolerance
    )
    return asdict(result)


def assess_portfolio(holdings: List[Dict]) -> Dict:
    """評估投資組合風險"""
    result = RiskCalculator.assess_portfolio_risk(holdings)
    return asdict(result)
