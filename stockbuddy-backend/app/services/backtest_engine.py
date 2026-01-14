"""
回測引擎
- 模擬買賣交易
- 計算績效指標
- V10.38: 新增滑點計算、動態無風險利率
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math


class BacktestEngine:
    """回測引擎 (V10.38 增強版)"""

    # V10.38: 動態無風險利率配置（按年份）
    RISK_FREE_RATES = {
        2020: 0.008,  # 0.8%
        2021: 0.003,  # 0.3%
        2022: 0.012,  # 1.2%
        2023: 0.015,  # 1.5%
        2024: 0.018,  # 1.8%
        2025: 0.020,  # 2.0%
        2026: 0.020,  # 2.0%
    }
    DEFAULT_RISK_FREE_RATE = 0.02  # 預設 2%

    def __init__(
        self,
        initial_capital: float = 1000000,
        slippage_rate: float = 0.001,  # V10.38: 滑點率（預設 0.1%）
        enable_slippage: bool = True,  # V10.38: 是否啟用滑點
    ):
        """
        Args:
            initial_capital: 初始資金（預設 100 萬）
            slippage_rate: 滑點率（預設 0.1%）
            enable_slippage: 是否啟用滑點計算
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # {stock_id: {"shares": 0, "avg_cost": 0}}
        self.trades = []     # 交易記錄
        self.daily_values = []  # 每日淨值

        # V10.38: 滑點設定
        self.slippage_rate = slippage_rate
        self.enable_slippage = enable_slippage
        self.total_slippage = 0  # 累計滑點成本

    def _apply_slippage(self, price: float, is_buy: bool) -> float:
        """
        V10.38: 計算滑點後的實際成交價

        Args:
            price: 理論價格
            is_buy: 是否為買入（買入滑點向上，賣出滑點向下）

        Returns:
            實際成交價
        """
        if not self.enable_slippage:
            return price

        # 買入時價格向上滑點，賣出時向下滑點
        if is_buy:
            actual_price = price * (1 + self.slippage_rate)
        else:
            actual_price = price * (1 - self.slippage_rate)

        return actual_price

    @classmethod
    def get_risk_free_rate(cls, year: int = None) -> float:
        """
        V10.38: 取得指定年份的無風險利率

        Args:
            year: 年份（預設為當年）

        Returns:
            無風險利率
        """
        if year is None:
            year = datetime.now().year
        return cls.RISK_FREE_RATES.get(year, cls.DEFAULT_RISK_FREE_RATE)
    
    def reset(self):
        """重設回測狀態"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_values = []
        self.total_slippage = 0  # V10.38: 重設滑點累計

    def buy(self, stock_id: str, price: float, shares: int, date: str, reason: str = ""):
        """買入股票（V10.38: 含滑點計算）"""
        # V10.38: 計算滑點後的實際成交價
        actual_price = self._apply_slippage(price, is_buy=True)
        slippage_cost = (actual_price - price) * shares

        cost = actual_price * shares
        fee = cost * 0.001425  # 手續費 0.1425%
        total_cost = cost + fee
        
        if total_cost > self.capital:
            return {"success": False, "message": "資金不足"}
        
        # 更新持股
        if stock_id in self.positions:
            pos = self.positions[stock_id]
            total_shares = pos["shares"] + shares
            total_cost_basis = pos["shares"] * pos["avg_cost"] + cost
            pos["shares"] = total_shares
            pos["avg_cost"] = total_cost_basis / total_shares
        else:
            self.positions[stock_id] = {
                "shares": shares,
                "avg_cost": actual_price  # V10.38: 使用實際成交價
            }

        self.capital -= total_cost
        self.total_slippage += slippage_cost  # V10.38: 累計滑點

        trade = {
            "date": date,
            "type": "buy",
            "stock_id": stock_id,
            "price": price,
            "actual_price": round(actual_price, 2),  # V10.38: 實際成交價
            "shares": shares,
            "cost": total_cost,
            "fee": fee,
            "slippage": round(slippage_cost, 2),  # V10.38: 滑點成本
            "reason": reason,
        }
        self.trades.append(trade)

        return {"success": True, "trade": trade}
    
    def sell(self, stock_id: str, price: float, shares: int, date: str, reason: str = ""):
        """賣出股票（V10.38: 含滑點計算）"""
        if stock_id not in self.positions:
            return {"success": False, "message": "無持股"}

        pos = self.positions[stock_id]
        if shares > pos["shares"]:
            shares = pos["shares"]  # 全部賣出

        # V10.38: 計算滑點後的實際成交價
        actual_price = self._apply_slippage(price, is_buy=False)
        slippage_cost = (price - actual_price) * shares

        proceeds = actual_price * shares
        fee = proceeds * 0.001425  # 手續費
        tax = proceeds * 0.003     # 交易稅 0.3%
        net_proceeds = proceeds - fee - tax

        # 計算損益
        cost_basis = pos["avg_cost"] * shares
        profit = net_proceeds - cost_basis
        profit_pct = (profit / cost_basis) * 100 if cost_basis > 0 else 0

        # 更新持股
        pos["shares"] -= shares
        if pos["shares"] == 0:
            del self.positions[stock_id]

        self.capital += net_proceeds
        self.total_slippage += slippage_cost  # V10.38: 累計滑點

        trade = {
            "date": date,
            "type": "sell",
            "stock_id": stock_id,
            "price": price,
            "actual_price": round(actual_price, 2),  # V10.38: 實際成交價
            "shares": shares,
            "proceeds": net_proceeds,
            "fee": fee + tax,
            "slippage": round(slippage_cost, 2),  # V10.38: 滑點成本
            "profit": profit,
            "profit_pct": profit_pct,
            "reason": reason,
        }
        self.trades.append(trade)

        return {"success": True, "trade": trade}
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """計算投資組合總值"""
        stock_value = sum(
            pos["shares"] * current_prices.get(stock_id, pos["avg_cost"])
            for stock_id, pos in self.positions.items()
        )
        return self.capital + stock_value
    
    def record_daily_value(self, date: str, current_prices: Dict[str, float]):
        """記錄每日淨值"""
        value = self.get_portfolio_value(current_prices)
        self.daily_values.append({
            "date": date,
            "value": value,
            "return_pct": ((value / self.initial_capital) - 1) * 100
        })
    
    def calculate_stats(self) -> Dict:
        """計算績效指標 (V10.38: 動態無風險利率、滑點統計)"""
        if not self.daily_values:
            return {"error": "無回測資料"}

        # 基本指標
        final_value = self.daily_values[-1]["value"]
        total_return = final_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # 交易統計
        buy_trades = [t for t in self.trades if t["type"] == "buy"]
        sell_trades = [t for t in self.trades if t["type"] == "sell"]

        wins = [t for t in sell_trades if t.get("profit", 0) > 0]
        losses = [t for t in sell_trades if t.get("profit", 0) <= 0]

        win_rate = len(wins) / len(sell_trades) * 100 if sell_trades else 0

        avg_win = sum(t["profit"] for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t["profit"] for t in losses) / len(losses)) if losses else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

        # 最大回撤
        peak = self.initial_capital
        max_drawdown = 0
        max_drawdown_pct = 0

        for dv in self.daily_values:
            value = dv["value"]
            if value > peak:
                peak = value
            drawdown = peak - value
            drawdown_pct = (drawdown / peak) * 100
            if drawdown_pct > max_drawdown_pct:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct

        # 年化報酬率
        days = len(self.daily_values)
        annual_return_pct = (((final_value / self.initial_capital) ** (252 / days)) - 1) * 100 if days > 0 else 0

        # V10.38: 使用動態無風險利率
        # 從回測期間的最後日期取得年份
        backtest_year = None
        if self.daily_values:
            try:
                last_date = self.daily_values[-1].get("date", "")
                if last_date:
                    backtest_year = int(last_date[:4])
            except (ValueError, IndexError):
                pass
        risk_free_rate = self.get_risk_free_rate(backtest_year)

        # 夏普比率 (V10.38: 動態無風險利率)
        returns = []
        for i in range(1, len(self.daily_values)):
            prev = self.daily_values[i-1]["value"]
            curr = self.daily_values[i]["value"]
            returns.append((curr - prev) / prev)

        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = ((avg_return * 252) - risk_free_rate) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0

        # V10.38: 計算滑點相關統計
        total_slippage_from_trades = sum(t.get("slippage", 0) for t in self.trades)
        slippage_impact_pct = (total_slippage_from_trades / self.initial_capital) * 100 if self.initial_capital > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annual_return_pct": round(annual_return_pct, 2),
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "risk_free_rate_used": risk_free_rate,  # V10.38: 顯示使用的無風險利率
            "total_trades": len(self.trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "trading_days": days,
            # V10.38: 滑點統計
            "slippage_enabled": self.enable_slippage,
            "slippage_rate": self.slippage_rate,
            "total_slippage": round(total_slippage_from_trades, 2),
            "slippage_impact_pct": round(slippage_impact_pct, 4),
        }


class SimpleStrategy:
    """簡單策略"""
    
    @staticmethod
    def ma_crossover(history: List[Dict], short_period: int = 5, long_period: int = 20) -> Dict:
        """
        均線交叉策略（優化版 V2）
        
        不只看交叉，也看：
        - 排列狀態變化
        - 價格與均線的相對位置
        - 動能變化
        
        Args:
            history: 歷史 K 線資料 [{"date", "close", ...}]
            short_period: 短期均線天數
            long_period: 長期均線天數
            
        Returns:
            {"signal": "buy"/"sell"/"hold", "reason": "..."}
        """
        if len(history) < long_period + 10:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        current_price = closes[-1]
        prev_price = closes[-2]
        
        # 計算均線
        short_ma = sum(closes[-short_period:]) / short_period
        long_ma = sum(closes[-long_period:]) / long_period
        
        prev_closes = closes[:-1]
        prev_short_ma = sum(prev_closes[-short_period:]) / short_period
        prev_long_ma = sum(prev_closes[-long_period:]) / long_period
        
        # 計算 5 天前和 10 天前的均線狀態
        closes_5d_ago = closes[:-5]
        closes_10d_ago = closes[:-10]
        
        was_bearish_5d = False
        was_bearish_10d = False
        if len(closes_5d_ago) >= long_period:
            short_ma_5d = sum(closes_5d_ago[-short_period:]) / short_period
            long_ma_5d = sum(closes_5d_ago[-long_period:]) / long_period
            was_bearish_5d = short_ma_5d < long_ma_5d
        if len(closes_10d_ago) >= long_period:
            short_ma_10d = sum(closes_10d_ago[-short_period:]) / short_period
            long_ma_10d = sum(closes_10d_ago[-long_period:]) / long_period
            was_bearish_10d = short_ma_10d < long_ma_10d
        
        # 判斷狀態
        is_bullish = short_ma > long_ma
        was_bullish = prev_short_ma > prev_long_ma
        price_above_short = current_price > short_ma
        price_above_long = current_price > long_ma
        
        # 計算動能
        price_5d_ago = closes[-6] if len(closes) >= 6 else closes[0]
        price_10d_ago = closes[-11] if len(closes) >= 11 else closes[0]
        momentum_5d = (current_price - price_5d_ago) / price_5d_ago * 100
        momentum_10d = (current_price - price_10d_ago) / price_10d_ago * 100
        daily_change = (current_price - prev_price) / prev_price * 100
        
        # ===== 買進訊號 =====
        
        # 1. 黃金交叉：短均線向上穿越長均線（最強訊號）
        if not was_bullish and is_bullish:
            return {"signal": "buy", "reason": f"MA{short_period} 向上穿越 MA{long_period}（黃金交叉）"}
        
        # 2. 近期轉多頭（5-10天內）且價格站穩
        if is_bullish and (was_bearish_5d or was_bearish_10d) and price_above_short:
            return {"signal": "buy", "reason": f"近期轉多頭排列，價格站穩 MA{short_period}"}
        
        # 3. 多頭排列中，價格回測短均線後反彈
        if is_bullish and price_above_short:
            prev_short_ma_val = sum(closes[-short_period-1:-1]) / short_period
            if prev_price < prev_short_ma_val and current_price > short_ma:
                return {"signal": "buy", "reason": f"多頭回測 MA{short_period} 後反彈"}
        
        # 4. 多頭排列中，價格回測長均線後反彈（較強支撐）
        if is_bullish and price_above_long:
            prev_long_ma_val = sum(closes[-long_period-1:-1]) / long_period
            if prev_price < prev_long_ma_val * 1.01 and current_price > long_ma:
                return {"signal": "buy", "reason": f"多頭回測 MA{long_period} 後反彈（強支撐）"}
        
        # 5. 【優化】多頭排列 + 動能正向（降低門檻到 1.5%）
        if is_bullish and price_above_short and momentum_5d > 1.5:
            return {"signal": "buy", "reason": f"多頭動能加速，5日漲 {momentum_5d:.1f}%"}
        
        # 6. 【優化】多頭排列 + 當日上漲（降低門檻到 1%）
        if is_bullish and daily_change > 1:
            return {"signal": "buy", "reason": f"多頭強勢上攻，今日 +{daily_change:.1f}%"}
        
        # 7. 【新增】多頭排列 + 價格創近 10 日新高
        high_10d = max(closes[-10:])
        if is_bullish and current_price >= high_10d * 0.995:
            return {"signal": "buy", "reason": f"多頭排列，接近10日高點"}
        
        # 8. 【新增】多頭排列持續超過 5 天（趨勢確認）
        if is_bullish and was_bearish_10d and not was_bearish_5d:
            return {"signal": "buy", "reason": f"多頭趨勢確認（持續5天以上）"}
        
        # ===== 賣出訊號 =====
        
        # 9. 死亡交叉
        if was_bullish and not is_bullish:
            return {"signal": "sell", "reason": f"MA{short_period} 向下穿越 MA{long_period}（死亡交叉）"}
        
        # 10. 空頭排列中，價格跌破短均線
        if not is_bullish and not price_above_short:
            if prev_price >= prev_short_ma:
                return {"signal": "sell", "reason": f"空頭排列，跌破 MA{short_period}"}
        
        # 11.【優化】多頭排列但動能轉弱（降低門檻）
        if is_bullish and momentum_5d < -1.5 and daily_change < -0.5:
            return {"signal": "sell", "reason": f"多頭動能轉弱，5日跌 {abs(momentum_5d):.1f}%"}
        
        # 12.【新增】跌破長均線（趨勢可能反轉）
        if prev_price > long_ma and current_price < long_ma:
            return {"signal": "sell", "reason": f"跌破 MA{long_period}，注意趨勢"}
        
        # 13.【新增】價格創近 10 日新低
        low_10d = min(closes[-10:])
        if not is_bullish and current_price <= low_10d * 1.005:
            return {"signal": "sell", "reason": f"空頭排列，接近10日低點"}
        
        # ===== 持有/觀望 =====
        if is_bullish:
            return {"signal": "hold", "reason": f"多頭排列，持有觀察"}
        else:
            return {"signal": "hold", "reason": f"空頭排列，觀望"}
    
    @staticmethod
    def rsi_strategy(history: List[Dict], period: int = 14, oversold: int = 30, overbought: int = 70) -> Dict:
        """
        RSI 策略
        
        Args:
            history: 歷史 K 線資料
            period: RSI 週期
            oversold: 超賣門檻
            overbought: 超買門檻
        """
        if len(history) < period + 1:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        
        # 計算 RSI
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
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi < oversold:
            return {"signal": "buy", "reason": f"RSI {rsi:.1f} 進入超賣區"}
        elif rsi > overbought:
            return {"signal": "sell", "reason": f"RSI {rsi:.1f} 進入超買區"}
        else:
            return {"signal": "hold", "reason": f"RSI {rsi:.1f} 正常區間"}
    
    @staticmethod
    def macd_strategy(history: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        MACD 策略
        
        Args:
            history: 歷史 K 線資料
            fast: 快線週期
            slow: 慢線週期
            signal: 訊號線週期
        """
        if len(history) < slow + signal:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        
        # 計算 EMA
        def ema(data, period):
            if len(data) < period:
                return sum(data) / len(data)
            multiplier = 2 / (period + 1)
            ema_val = sum(data[:period]) / period
            for price in data[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return ema_val
        
        # 計算 MACD
        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)
        macd_line = ema_fast - ema_slow
        
        # 計算前一天的 MACD
        prev_closes = closes[:-1]
        prev_ema_fast = ema(prev_closes, fast)
        prev_ema_slow = ema(prev_closes, slow)
        prev_macd = prev_ema_fast - prev_ema_slow
        
        # 簡化：用 MACD 線穿越零軸判斷
        if prev_macd <= 0 and macd_line > 0:
            return {"signal": "buy", "reason": f"MACD 向上穿越零軸"}
        elif prev_macd >= 0 and macd_line < 0:
            return {"signal": "sell", "reason": f"MACD 向下穿越零軸"}
        elif macd_line > 0:
            return {"signal": "hold", "reason": f"MACD 多方，持有"}
        else:
            return {"signal": "hold", "reason": f"MACD 空方，觀望"}
    
    @staticmethod
    def bollinger_strategy(history: List[Dict], period: int = 20, std_dev: float = 2.0) -> Dict:
        """
        布林通道策略
        
        Args:
            history: 歷史 K 線資料
            period: 均線週期
            std_dev: 標準差倍數
        """
        if len(history) < period:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        recent_closes = closes[-period:]
        
        # 計算布林通道
        ma = sum(recent_closes) / period
        variance = sum((x - ma) ** 2 for x in recent_closes) / period
        std = variance ** 0.5
        
        upper_band = ma + std_dev * std
        lower_band = ma - std_dev * std
        
        current_price = closes[-1]
        
        # 價格觸及下軌買入，觸及上軌賣出
        if current_price <= lower_band:
            return {"signal": "buy", "reason": f"價格觸及布林下軌 ({lower_band:.2f})"}
        elif current_price >= upper_band:
            return {"signal": "sell", "reason": f"價格觸及布林上軌 ({upper_band:.2f})"}
        else:
            band_width = (upper_band - lower_band) / ma * 100
            return {"signal": "hold", "reason": f"價格在通道內，帶寬 {band_width:.1f}%"}
    
    @staticmethod
    def volume_breakout_strategy(history: List[Dict], ma_period: int = 20, volume_ratio: float = 1.3) -> Dict:
        """
        量價突破策略（優化版）
        
        不只看「突破那天」，也看量價配合的趨勢
        
        Args:
            history: 歷史 K 線資料
            ma_period: 均線週期
            volume_ratio: 量能放大倍數門檻（降低到 1.3）
        """
        if len(history) < ma_period + 5:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        volumes = [h.get("volume", 0) for h in history]
        
        # 計算均線和均量
        ma = sum(closes[-ma_period:]) / ma_period
        avg_volume = sum(volumes[-ma_period:-1]) / (ma_period - 1) if ma_period > 1 else volumes[-1]
        
        current_price = closes[-1]
        current_volume = volumes[-1]
        prev_price = closes[-2]
        
        # 量能比
        vol_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # 計算近 5 天的價格變化
        price_5d_ago = closes[-6] if len(closes) >= 6 else closes[0]
        momentum_5d = (current_price - price_5d_ago) / price_5d_ago * 100
        
        # 計算近 3 天平均量能
        avg_vol_3d = sum(volumes[-3:]) / 3 if len(volumes) >= 3 else current_volume
        vol_ratio_3d = avg_vol_3d / avg_volume if avg_volume > 0 else 1
        
        # 1. 經典突破：帶量突破均線
        if current_price > ma and prev_price <= ma and vol_ratio >= volume_ratio:
            return {"signal": "buy", "reason": f"帶量突破 MA{ma_period}，量能 {vol_ratio:.1f}x"}
        
        # 2. 經典跌破：帶量跌破均線
        if current_price < ma and prev_price >= ma and vol_ratio >= volume_ratio:
            return {"signal": "sell", "reason": f"帶量跌破 MA{ma_period}，量能 {vol_ratio:.1f}x"}
        
        # 3. 新增：站穩均線上方 + 連續放量 + 動能向上
        if current_price > ma and vol_ratio_3d >= 1.2 and momentum_5d > 2:
            return {"signal": "buy", "reason": f"均線上方放量上攻，5日漲 {momentum_5d:.1f}%"}
        
        # 4. 新增：均線上方 + 今日大量上漲
        daily_change = (current_price - prev_price) / prev_price * 100
        if current_price > ma and vol_ratio >= 1.5 and daily_change > 1.5:
            return {"signal": "buy", "reason": f"量增價漲，今日 +{daily_change:.1f}%"}
        
        # 5. 新增：均線下方 + 縮量（可能見底）
        if current_price < ma * 0.98 and vol_ratio < 0.7:
            # 檢查是否連續縮量
            if len(volumes) >= 3 and volumes[-1] < volumes[-2] < volumes[-3]:
                return {"signal": "buy", "reason": f"跌深縮量，可能見底"}
        
        # 6. 新增：均線上方 + 量縮價跌（獲利了結訊號）
        if current_price > ma and daily_change < -2 and vol_ratio > 1.5:
            return {"signal": "sell", "reason": f"量增價跌，注意風險"}
        
        # 持有/觀望
        if current_price > ma:
            return {"signal": "hold", "reason": f"站穩均線上方，量能 {vol_ratio:.1f}x"}
        else:
            return {"signal": "hold", "reason": f"位於均線下方"}
    
    @staticmethod
    def combined_strategy(history: List[Dict]) -> Dict:
        """
        綜合策略：結合多個指標
        
        使用 MA + RSI + MACD + 動能 綜合判斷
        V10.11.6 優化：對穩定型 ETF 也能產生訊號
        """
        if len(history) < 30:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        current_price = closes[-1]
        prev_price = closes[-2]
        
        # 計算均線
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20
        
        prev_closes = closes[:-1]
        prev_ma5 = sum(prev_closes[-5:]) / 5 if len(prev_closes) >= 5 else ma5
        prev_ma10 = sum(prev_closes[-10:]) / 10 if len(prev_closes) >= 10 else ma10
        prev_ma20 = sum(prev_closes[-20:]) / 20 if len(prev_closes) >= 20 else ma20
        
        # RSI
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
        
        # 計分系統
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # 1. 均線交叉訊號（權重高）
        # MA5 向上穿越 MA10
        if prev_ma5 <= prev_ma10 and ma5 > ma10:
            buy_score += 3
            reasons.append("MA5上穿MA10")
        # MA5 向下穿越 MA10
        elif prev_ma5 >= prev_ma10 and ma5 < ma10:
            sell_score += 3
            reasons.append("MA5下穿MA10")
        
        # 🆕 價格突破 MA20（對 ETF 很重要）
        if prev_price <= prev_ma20 and current_price > ma20:
            buy_score += 2
            reasons.append("突破MA20")
        elif prev_price >= prev_ma20 and current_price < ma20:
            sell_score += 2
            reasons.append("跌破MA20")
        
        # 2. 趨勢位置
        if ma5 > ma20:
            buy_score += 1
            if ma5 > ma10 > ma20:
                buy_score += 1  # 完美多頭排列
        else:
            sell_score += 1
            if ma5 < ma10 < ma20:
                sell_score += 1  # 完美空頭排列
        
        # 3. 價格位置
        if current_price > ma5:
            buy_score += 0.5
        elif current_price < ma5:
            sell_score += 0.5
        
        # 🆕 價格站穩 MA20 上方
        if current_price > ma20:
            buy_score += 0.5
        else:
            sell_score += 0.5
        
        # 4. RSI（進一步放寬門檻）
        if rsi < 40:
            buy_score += 2
            reasons.append(f"RSI{rsi:.0f}偏低")
        elif rsi < 48:
            buy_score += 1
        elif rsi > 60:
            sell_score += 2
            reasons.append(f"RSI{rsi:.0f}偏高")
        elif rsi > 52:
            sell_score += 1
        
        # 5. 短期動能（放寬到 0.5%）
        price_5d_ago = closes[-6] if len(closes) >= 6 else closes[0]
        momentum = (current_price - price_5d_ago) / price_5d_ago * 100
        if momentum > 0.5:
            buy_score += 1
            if momentum > 2:
                buy_score += 1
                reasons.append(f"動能+{momentum:.1f}%")
        elif momentum < -0.5:
            sell_score += 1
            if momentum < -2:
                sell_score += 1
        
        # 6. 當日漲跌（放寬到 0.3%）
        daily_change = (current_price - prev_price) / prev_price * 100
        if daily_change > 0.3:
            buy_score += 0.5
            if daily_change > 1:
                buy_score += 0.5
        elif daily_change < -0.3:
            sell_score += 0.5
            if daily_change < -1:
                sell_score += 0.5
        
        # 🆕 7. 連續上漲/下跌（降低到 2 天）
        consecutive_up = 0
        consecutive_down = 0
        for i in range(len(closes)-1, max(0, len(closes)-6), -1):
            if closes[i] > closes[i-1]:
                if consecutive_down == 0:
                    consecutive_up += 1
                else:
                    break
            else:
                if consecutive_up == 0:
                    consecutive_down += 1
                else:
                    break
        
        if consecutive_up >= 2:
            buy_score += 1
            if consecutive_up >= 4:
                reasons.append(f"連漲{consecutive_up}日")
        elif consecutive_down >= 2:
            sell_score += 1
        
        # 🆕 8. 接近區間高點/低點（10日）
        high_10d = max(closes[-10:])
        low_10d = min(closes[-10:])
        range_10d = high_10d - low_10d
        if range_10d > 0:
            position = (current_price - low_10d) / range_10d
            if position > 0.85:
                # 接近高點，小心追高
                sell_score += 0.3
            elif position < 0.15:
                # 接近低點，可能超跌
                buy_score += 0.5
        
        # 🆕 9. 創新高/新低（20日）
        high_20d = max(closes[-20:])
        low_20d = min(closes[-20:])
        if current_price >= high_20d:
            buy_score += 1
            reasons.append("創20日新高")
        elif current_price <= low_20d:
            sell_score += 1
        
        # 綜合判斷（門檻降到 1 分，更敏感）
        if buy_score >= 1 and buy_score > sell_score:
            return {"signal": "buy", "reason": "綜合訊號買進：" + ("、".join(reasons) if reasons else "多項指標偏多")}
        elif sell_score >= 1 and sell_score > buy_score:
            return {"signal": "sell", "reason": "綜合訊號賣出：" + ("、".join(reasons) if reasons else "多項指標偏空")}
        else:
            return {"signal": "hold", "reason": f"綜合評分 買{buy_score:.1f}/賣{sell_score:.1f}，觀望"}


async def run_backtest(
    stock_id: str,
    start_date: str,
    end_date: str,
    strategy: str = "ma_crossover",
    initial_capital: float = 1000000,
    position_size: float = 0.1  # 每次使用 10% 資金
) -> Dict:
    """
    執行回測

    Args:
        stock_id: 股票代號
        start_date: 開始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        strategy: 策略名稱
        initial_capital: 初始資金
        position_size: 倉位大小 (0-1)
    """
    from app.services.github_data import SmartStockService
    from datetime import datetime

    print(f"[Backtest] Starting {stock_id}, strategy: {strategy}")

    # 計算需要的月份數
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        months = max(((end_dt - start_dt).days // 30) + 3, 6)
    except:
        months = 12

    print(f"[Backtest] Need {months} months of history")

    # 取得歷史資料（嘗試取得更長時間）
    history = await SmartStockService.get_stock_history(stock_id, months=months)
    print(f"[Backtest] Got {len(history) if history else 0} history records")
    
    # 如果主要數據源失敗，嘗試 FinMind
    if not history or len(history) < 30:
        try:
            from app.services.finmind_service import FinMindService
            from datetime import datetime, timedelta
            
            end_date_str = datetime.now().strftime("%Y-%m-%d")
            start_date_str = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            fm_data = await FinMindService.get_stock_price(stock_id, start_date_str, end_date_str)
            if fm_data and len(fm_data) > 0:
                # 轉換 FinMind 格式為標準格式
                history = []
                for item in fm_data:
                    history.append({
                        "date": item.get("date", ""),
                        "open": item.get("open", 0),
                        "high": item.get("max", item.get("high", 0)),
                        "low": item.get("min", item.get("low", 0)),
                        "close": item.get("close", 0),
                        "volume": item.get("Trading_Volume", item.get("volume", 0))
                    })
                print(f"✅ 使用 FinMind 數據源取得 {stock_id} 歷史資料 ({len(history)} 筆)")
        except Exception as e:
            print(f"⚠️ FinMind 備用方案失敗: {e}")
    
    if not history or len(history) < 30:
        # 提供更友善的錯誤訊息
        reasons = []
        if not history:
            reasons.append("無法取得任何歷史資料")
        else:
            reasons.append(f"僅有 {len(history)} 天資料，需要至少 30 天")
        
        suggestions = [
            "確認股票代號是否正確（例如：2330、2454）",
            "該股票可能是近期上市/上櫃",
            "該股票可能已下市或代號變更",
            "部分 ETF 和特殊股票可能無法取得歷史資料"
        ]
        
        return {
            "error": f"無法回測股票 {stock_id}",
            "reason": "。".join(reasons),
            "suggestions": suggestions,
            "data_available": len(history) if history else 0,
            "data_required": 30
        }
    
    # 標準化日期格式為 YYYY-MM-DD
    def normalize_date(date_str):
        """將各種日期格式標準化為 YYYY-MM-DD"""
        if not date_str:
            return ""
        date_str = str(date_str).strip()

        # 嘗試各種格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y%m%d",
            "%Y.%m.%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str[:10], fmt)
                return dt.strftime("%Y-%m-%d")
            except:
                continue

        return date_str[:10] if len(date_str) >= 10 else date_str

    # 標準化歷史資料中的日期
    for h in history:
        h["date"] = normalize_date(h.get("date", ""))

    # 顯示歷史資料的日期範圍
    if history:
        dates = [h.get("date", "") for h in history if h.get("date")]
        if dates:
            print(f"[Backtest] History date range: {min(dates)} ~ {max(dates)}")
            print(f"[Backtest] Filter range: {start_date} ~ {end_date}")
        else:
            print(f"[Backtest] Warning: No valid dates in history data")

    # 過濾日期範圍（使用標準化後的日期）
    start_date_norm = normalize_date(start_date)
    end_date_norm = normalize_date(end_date)

    filtered_history = [
        h for h in history
        if h.get("date") and start_date_norm <= h.get("date", "") <= end_date_norm
    ]

    print(f"[Backtest] Filtered records: {len(filtered_history)}")

    # 如果過濾後資料不足，嘗試使用全部歷史資料
    if len(filtered_history) < 20 and len(history) >= 30:
        print(f"[Backtest] Warning: Using all available history data instead")
        filtered_history = history

    if len(filtered_history) < 20:
        return {
            "error": "指定日期範圍資料不足",
            "details": {
                "required": 20,
                "available": len(filtered_history),
                "date_range": f"{start_date} ~ {end_date}",
                "history_range": f"{min(dates) if history else 'N/A'} ~ {max(dates) if history else 'N/A'}"
            }
        }

    # 初始化回測引擎
    engine = BacktestEngine(initial_capital)

    # 追蹤訊號統計
    signal_counts = {"buy": 0, "sell": 0, "hold": 0}

    # 執行回測
    for i in range(20, len(filtered_history)):
        current_data = filtered_history[:i+1]
        today = current_data[-1]
        date = today["date"]
        price = today["close"]

        # 取得策略訊號
        if strategy == "ma_crossover":
            signal = SimpleStrategy.ma_crossover(current_data)
        elif strategy == "rsi":
            signal = SimpleStrategy.rsi_strategy(current_data)
        elif strategy == "macd":
            signal = SimpleStrategy.macd_strategy(current_data)
        elif strategy == "bollinger":
            signal = SimpleStrategy.bollinger_strategy(current_data)
        elif strategy == "volume_breakout":
            signal = SimpleStrategy.volume_breakout_strategy(current_data)
        elif strategy == "combined":
            signal = SimpleStrategy.combined_strategy(current_data)
        else:
            signal = {"signal": "hold", "reason": "未知策略"}

        signal_counts[signal["signal"]] = signal_counts.get(signal["signal"], 0) + 1

        # 執行交易
        if signal["signal"] == "buy":
            # 計算可買股數（支援零股交易，最小 100 股）
            available = engine.capital * position_size
            # 先嘗試整張（1000股），如果買不起則嘗試零股（100股為單位）
            shares = int(available / price / 1000) * 1000
            if shares < 1000:
                # 零股交易：以 100 股為單位
                shares = int(available / price / 100) * 100
            if shares >= 100:  # 最少買 100 股
                result = engine.buy(stock_id, price, shares, date, signal["reason"])
                if result["success"]:
                    print(f"[BUY] {date} {shares} shares @ ${price:.2f}")

        elif signal["signal"] == "sell":
            # 賣出全部
            if stock_id in engine.positions:
                shares = engine.positions[stock_id]["shares"]
                result = engine.sell(stock_id, price, shares, date, signal["reason"])
                if result["success"]:
                    print(f"[SELL] {date} {shares} shares @ ${price:.2f}")

        # 記錄每日淨值
        engine.record_daily_value(date, {stock_id: price})

    print(f"[Backtest] Signals: buy={signal_counts['buy']}, sell={signal_counts['sell']}, hold={signal_counts['hold']}")
    
    # 計算統計
    stats = engine.calculate_stats()
    
    return {
        "stock_id": stock_id,
        "strategy": strategy,
        "period": f"{start_date} ~ {end_date}",
        "stats": stats,
        "trades": engine.trades[-20:],  # 最近 20 筆交易
        "daily_values": engine.daily_values[-60:],  # 最近 60 天淨值
    }
