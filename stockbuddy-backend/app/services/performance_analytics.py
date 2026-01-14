"""
進階績效分析服務 V10.15
參考券商 APP（國泰樹精靈、元大、凱基）及 FinLab 交易練習生

提供功能：
1. Alpha / Beta 計算
2. 夏普比率 (Sharpe Ratio)
3. Sortino Ratio
4. Calmar Ratio
5. 最大回撤 (Max Drawdown)
6. VaR (Value at Risk)
7. Conditional VaR (CVaR / Expected Shortfall)
8. 勝率與期望值
9. Profit Factor
10. 月報酬熱力圖數據
11. 年度績效統計
"""

import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math


class PerformanceAnalytics:
    """進階績效分析服務"""

    # 預設無風險利率 (年化，台灣定存約 1.5%)
    RISK_FREE_RATE = 0.015

    @classmethod
    def calculate_returns(cls, prices: List[float]) -> List[float]:
        """
        計算每日報酬率

        Args:
            prices: 價格序列

        Returns:
            每日報酬率列表
        """
        if len(prices) < 2:
            return []

        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                ret = (prices[i] - prices[i - 1]) / prices[i - 1]
                returns.append(ret)

        return returns

    @classmethod
    def calculate_alpha_beta(
        cls,
        stock_returns: List[float],
        market_returns: List[float],
        risk_free_rate: float = None
    ) -> Dict[str, float]:
        """
        計算 Alpha 和 Beta

        Alpha: 超額報酬（相對於市場的額外報酬）
        Beta: 系統性風險（相對於市場的波動性）

        Args:
            stock_returns: 股票日報酬率
            market_returns: 市場（大盤）日報酬率
            risk_free_rate: 年化無風險利率

        Returns:
            {"alpha": float, "beta": float, "r_squared": float}
        """
        if risk_free_rate is None:
            risk_free_rate = cls.RISK_FREE_RATE

        if len(stock_returns) < 20 or len(market_returns) < 20:
            return {"alpha": 0, "beta": 1, "r_squared": 0}

        # 確保長度一致
        min_len = min(len(stock_returns), len(market_returns))
        stock_returns = stock_returns[-min_len:]
        market_returns = market_returns[-min_len:]

        # 計算均值
        stock_mean = np.mean(stock_returns)
        market_mean = np.mean(market_returns)

        # 計算 Beta (Covariance / Variance)
        covariance = np.cov(stock_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)

        if market_variance == 0:
            return {"alpha": 0, "beta": 1, "r_squared": 0}

        beta = covariance / market_variance

        # 計算 Alpha (年化)
        daily_rf = risk_free_rate / 252
        alpha = (stock_mean - daily_rf) - beta * (market_mean - daily_rf)
        alpha_annualized = alpha * 252  # 年化

        # 計算 R-squared
        correlation = np.corrcoef(stock_returns, market_returns)[0][1]
        r_squared = correlation ** 2

        return {
            "alpha": round(alpha_annualized * 100, 2),  # 百分比
            "beta": round(beta, 2),
            "r_squared": round(r_squared, 4),
        }

    @classmethod
    def calculate_sharpe_ratio(
        cls,
        returns: List[float],
        risk_free_rate: float = None
    ) -> float:
        """
        計算夏普比率 (Sharpe Ratio)

        衡量每單位風險的超額報酬

        Args:
            returns: 日報酬率
            risk_free_rate: 年化無風險利率

        Returns:
            年化夏普比率
        """
        if risk_free_rate is None:
            risk_free_rate = cls.RISK_FREE_RATE

        if len(returns) < 20:
            return 0

        avg_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)

        if std_return == 0:
            return 0

        daily_rf = risk_free_rate / 252
        excess_return = avg_return - daily_rf

        # 年化
        sharpe = (excess_return / std_return) * np.sqrt(252)

        return round(sharpe, 2)

    @classmethod
    def calculate_sortino_ratio(
        cls,
        returns: List[float],
        risk_free_rate: float = None
    ) -> float:
        """
        計算 Sortino Ratio

        只考慮下行風險的夏普比率變體

        Args:
            returns: 日報酬率
            risk_free_rate: 年化無風險利率

        Returns:
            年化 Sortino Ratio
        """
        if risk_free_rate is None:
            risk_free_rate = cls.RISK_FREE_RATE

        if len(returns) < 20:
            return 0

        avg_return = np.mean(returns)
        daily_rf = risk_free_rate / 252

        # 計算下行標準差（只計算負報酬）
        negative_returns = [r for r in returns if r < daily_rf]
        if len(negative_returns) == 0:
            return 10  # 沒有負報酬，非常好

        downside_std = np.std(negative_returns, ddof=1)

        if downside_std == 0:
            return 0

        excess_return = avg_return - daily_rf
        sortino = (excess_return / downside_std) * np.sqrt(252)

        return round(sortino, 2)

    @classmethod
    def calculate_calmar_ratio(
        cls,
        returns: List[float],
        prices: List[float] = None
    ) -> float:
        """
        計算 Calmar Ratio

        年化報酬率 / 最大回撤

        Args:
            returns: 日報酬率
            prices: 價格序列（可選，用於更精確計算回撤）

        Returns:
            Calmar Ratio
        """
        if len(returns) < 20:
            return 0

        # 計算年化報酬
        total_return = np.prod([1 + r for r in returns]) - 1
        years = len(returns) / 252
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return

        # 計算最大回撤
        if prices:
            max_drawdown = cls.calculate_max_drawdown(prices)["max_drawdown_pct"] / 100
        else:
            # 從報酬率計算累積淨值
            cumulative = [1]
            for r in returns:
                cumulative.append(cumulative[-1] * (1 + r))
            max_drawdown = cls.calculate_max_drawdown(cumulative)["max_drawdown_pct"] / 100

        if max_drawdown == 0:
            return 10

        calmar = annualized_return / max_drawdown

        return round(calmar, 2)

    @classmethod
    def calculate_max_drawdown(cls, prices: List[float]) -> Dict[str, Any]:
        """
        計算最大回撤

        Args:
            prices: 價格或淨值序列

        Returns:
            {
                "max_drawdown": 最大回撤金額,
                "max_drawdown_pct": 最大回撤百分比,
                "peak_date_idx": 高點索引,
                "trough_date_idx": 低點索引,
                "recovery_date_idx": 恢復點索引（如果有）
            }
        """
        if len(prices) < 2:
            return {"max_drawdown": 0, "max_drawdown_pct": 0}

        peak = prices[0]
        peak_idx = 0
        max_drawdown = 0
        max_drawdown_pct = 0
        trough_idx = 0

        for i, price in enumerate(prices):
            if price > peak:
                peak = price
                peak_idx = i

            drawdown = peak - price
            drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0

            if drawdown_pct > max_drawdown_pct:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
                trough_idx = i

        return {
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "peak_idx": peak_idx,
            "trough_idx": trough_idx,
        }

    @classmethod
    def calculate_var(
        cls,
        returns: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """
        計算 VaR (Value at Risk)

        在給定信心水準下，最大可能損失

        Args:
            returns: 日報酬率
            confidence_level: 信心水準（預設 95%）

        Returns:
            VaR (正數表示損失)
        """
        if len(returns) < 20:
            return 0

        # 歷史模擬法
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        var = -sorted_returns[index] if index < len(sorted_returns) else 0

        return round(var * 100, 2)  # 百分比

    @classmethod
    def calculate_cvar(
        cls,
        returns: List[float],
        confidence_level: float = 0.95
    ) -> float:
        """
        計算 CVaR / Expected Shortfall

        超過 VaR 的預期損失

        Args:
            returns: 日報酬率
            confidence_level: 信心水準（預設 95%）

        Returns:
            CVaR (正數表示損失)
        """
        if len(returns) < 20:
            return 0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        # 計算低於 VaR 的平均損失
        tail_returns = sorted_returns[:index + 1]
        if len(tail_returns) == 0:
            return 0

        cvar = -np.mean(tail_returns)

        return round(cvar * 100, 2)  # 百分比

    @classmethod
    def calculate_win_rate(cls, trades: List[Dict]) -> Dict[str, float]:
        """
        計算勝率與期望值

        Args:
            trades: 交易記錄 [{"profit": float, "profit_pct": float}]

        Returns:
            {
                "win_rate": 勝率百分比,
                "avg_win": 平均獲利,
                "avg_loss": 平均虧損,
                "expectancy": 期望值,
                "profit_factor": 獲利因子
            }
        """
        if not trades:
            return {
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "expectancy": 0,
                "profit_factor": 0,
            }

        wins = [t for t in trades if t.get("profit", 0) > 0]
        losses = [t for t in trades if t.get("profit", 0) <= 0]

        win_count = len(wins)
        loss_count = len(losses)
        total_count = win_count + loss_count

        win_rate = (win_count / total_count * 100) if total_count > 0 else 0

        avg_win = np.mean([t["profit"] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t["profit"] for t in losses])) if losses else 0

        # 期望值 = 勝率 * 平均獲利 - 敗率 * 平均虧損
        loss_rate = 1 - (win_rate / 100)
        expectancy = (win_rate / 100 * avg_win) - (loss_rate * avg_loss)

        # 獲利因子 = 總獲利 / 總虧損
        total_wins = sum(t["profit"] for t in wins) if wins else 0
        total_losses = abs(sum(t["profit"] for t in losses)) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        return {
            "win_rate": round(win_rate, 1),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "profit_factor": round(profit_factor, 2),
        }

    @classmethod
    def calculate_monthly_returns(
        cls,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        計算月報酬率（用於熱力圖）

        Args:
            history: 歷史K線資料 [{"date": "YYYY-MM-DD", "close": float}]

        Returns:
            {
                "2025": {"1": 5.2, "2": -2.1, ...},
                "2024": {"1": 3.1, ...},
                ...
            }
        """
        if not history or len(history) < 2:
            return {}

        # 依月份分組
        monthly_prices = {}  # {(year, month): [prices]}

        for item in history:
            try:
                date_str = item.get("date", "")
                if not date_str:
                    continue

                # 解析日期
                if "-" in date_str:
                    parts = date_str.split("-")
                elif "/" in date_str:
                    parts = date_str.split("/")
                else:
                    continue

                year = parts[0]
                month = str(int(parts[1]))  # 去掉前導零

                key = (year, month)
                if key not in monthly_prices:
                    monthly_prices[key] = []

                monthly_prices[key].append(item.get("close", 0))
            except:
                continue

        # 計算每月報酬率
        result = {}
        sorted_keys = sorted(monthly_prices.keys())

        for i, key in enumerate(sorted_keys):
            year, month = key
            prices = monthly_prices[key]

            if len(prices) < 2:
                continue

            # 月報酬 = (月末 - 月初) / 月初
            month_return = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0

            if year not in result:
                result[year] = {}

            result[year][month] = round(month_return, 2)

        return result

    @classmethod
    def calculate_yearly_stats(
        cls,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        計算年度績效統計

        Args:
            history: 歷史K線資料

        Returns:
            {
                "2025": {"return": 15.2, "volatility": 18.5, "sharpe": 1.2},
                ...
            }
        """
        if not history or len(history) < 20:
            return {}

        # 依年份分組
        yearly_data = {}

        for item in history:
            try:
                date_str = item.get("date", "")
                if "-" in date_str:
                    year = date_str.split("-")[0]
                elif "/" in date_str:
                    year = date_str.split("/")[0]
                else:
                    continue

                if year not in yearly_data:
                    yearly_data[year] = []

                yearly_data[year].append(item.get("close", 0))
            except:
                continue

        result = {}
        for year, prices in yearly_data.items():
            if len(prices) < 10:
                continue

            # 計算年報酬
            year_return = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0

            # 計算日報酬率
            returns = cls.calculate_returns(prices)
            if not returns:
                continue

            # 波動率（年化）
            volatility = np.std(returns) * np.sqrt(252) * 100

            # 夏普比率
            sharpe = cls.calculate_sharpe_ratio(returns)

            result[year] = {
                "return": round(year_return, 2),
                "volatility": round(volatility, 2),
                "sharpe": sharpe,
                "trading_days": len(prices),
            }

        return result

    @classmethod
    def full_performance_analysis(
        cls,
        stock_history: List[Dict],
        market_history: List[Dict] = None,
        trades: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        完整績效分析

        Args:
            stock_history: 股票歷史資料
            market_history: 市場（大盤）歷史資料
            trades: 交易記錄

        Returns:
            完整分析結果
        """
        if not stock_history or len(stock_history) < 20:
            return {"error": "資料不足"}

        # 提取價格
        prices = [h.get("close", 0) for h in stock_history if h.get("close", 0) > 0]
        if len(prices) < 20:
            return {"error": "價格資料不足"}

        # 計算報酬率
        returns = cls.calculate_returns(prices)

        # Alpha / Beta
        alpha_beta = {"alpha": 0, "beta": 1, "r_squared": 0}
        if market_history and len(market_history) >= 20:
            market_prices = [h.get("close", 0) for h in market_history if h.get("close", 0) > 0]
            market_returns = cls.calculate_returns(market_prices)
            alpha_beta = cls.calculate_alpha_beta(returns, market_returns)

        # 各種指標
        sharpe = cls.calculate_sharpe_ratio(returns)
        sortino = cls.calculate_sortino_ratio(returns)
        calmar = cls.calculate_calmar_ratio(returns, prices)
        max_dd = cls.calculate_max_drawdown(prices)
        var_95 = cls.calculate_var(returns, 0.95)
        cvar_95 = cls.calculate_cvar(returns, 0.95)

        # 勝率分析（如果有交易記錄）
        win_stats = cls.calculate_win_rate(trades) if trades else None

        # 月報酬熱力圖
        monthly_returns = cls.calculate_monthly_returns(stock_history)

        # 年度統計
        yearly_stats = cls.calculate_yearly_stats(stock_history)

        # 總報酬
        total_return = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0
        days = len(prices)
        annualized_return = ((1 + total_return / 100) ** (252 / days) - 1) * 100 if days > 0 else 0

        return {
            "summary": {
                "total_return_pct": round(total_return, 2),
                "annualized_return_pct": round(annualized_return, 2),
                "trading_days": days,
                "start_price": prices[0],
                "end_price": prices[-1],
            },
            "risk_adjusted": {
                "alpha": alpha_beta["alpha"],
                "beta": alpha_beta["beta"],
                "r_squared": alpha_beta["r_squared"],
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "calmar_ratio": calmar,
            },
            "risk_metrics": {
                "max_drawdown_pct": max_dd["max_drawdown_pct"],
                "var_95": var_95,
                "cvar_95": cvar_95,
                "volatility_annual": round(np.std(returns) * np.sqrt(252) * 100, 2),
            },
            "win_statistics": win_stats,
            "monthly_returns": monthly_returns,
            "yearly_stats": yearly_stats,
        }


# 便捷函數
def calculate_performance(stock_history, market_history=None, trades=None):
    return PerformanceAnalytics.full_performance_analysis(stock_history, market_history, trades)

def calculate_sharpe(returns):
    return PerformanceAnalytics.calculate_sharpe_ratio(returns)

def calculate_max_drawdown(prices):
    return PerformanceAnalytics.calculate_max_drawdown(prices)

def calculate_monthly_heatmap(history):
    return PerformanceAnalytics.calculate_monthly_returns(history)
