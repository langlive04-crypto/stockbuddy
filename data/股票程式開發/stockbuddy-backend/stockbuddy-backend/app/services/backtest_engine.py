"""
回測引擎
- 模擬買賣交易
- 計算績效指標
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math


class BacktestEngine:
    """回測引擎"""
    
    def __init__(self, initial_capital: float = 1000000):
        """
        Args:
            initial_capital: 初始資金（預設 100 萬）
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # {stock_id: {"shares": 0, "avg_cost": 0}}
        self.trades = []     # 交易記錄
        self.daily_values = []  # 每日淨值
    
    def reset(self):
        """重設回測狀態"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_values = []
    
    def buy(self, stock_id: str, price: float, shares: int, date: str, reason: str = ""):
        """買入股票"""
        cost = price * shares
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
                "avg_cost": price
            }
        
        self.capital -= total_cost
        
        trade = {
            "date": date,
            "type": "buy",
            "stock_id": stock_id,
            "price": price,
            "shares": shares,
            "cost": total_cost,
            "fee": fee,
            "reason": reason,
        }
        self.trades.append(trade)
        
        return {"success": True, "trade": trade}
    
    def sell(self, stock_id: str, price: float, shares: int, date: str, reason: str = ""):
        """賣出股票"""
        if stock_id not in self.positions:
            return {"success": False, "message": "無持股"}
        
        pos = self.positions[stock_id]
        if shares > pos["shares"]:
            shares = pos["shares"]  # 全部賣出
        
        proceeds = price * shares
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
        
        trade = {
            "date": date,
            "type": "sell",
            "stock_id": stock_id,
            "price": price,
            "shares": shares,
            "proceeds": net_proceeds,
            "fee": fee + tax,
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
        """計算績效指標"""
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
        
        # 夏普比率 (簡化計算，假設無風險利率為 2%)
        returns = []
        for i in range(1, len(self.daily_values)):
            prev = self.daily_values[i-1]["value"]
            curr = self.daily_values[i]["value"]
            returns.append((curr - prev) / prev)
        
        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = ((avg_return * 252) - 0.02) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annual_return_pct": round(annual_return_pct, 2),
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "total_trades": len(self.trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "trading_days": days,
        }


class SimpleStrategy:
    """簡單策略"""
    
    @staticmethod
    def ma_crossover(history: List[Dict], short_period: int = 5, long_period: int = 20) -> Dict:
        """
        均線交叉策略
        
        Args:
            history: 歷史 K 線資料 [{"date", "close", ...}]
            short_period: 短期均線天數
            long_period: 長期均線天數
            
        Returns:
            {"signal": "buy"/"sell"/"hold", "reason": "..."}
        """
        if len(history) < long_period:
            return {"signal": "hold", "reason": "資料不足"}
        
        closes = [h["close"] for h in history]
        
        # 計算均線
        short_ma = sum(closes[-short_period:]) / short_period
        long_ma = sum(closes[-long_period:]) / long_period
        
        prev_closes = closes[:-1]
        prev_short_ma = sum(prev_closes[-short_period:]) / short_period if len(prev_closes) >= short_period else short_ma
        prev_long_ma = sum(prev_closes[-long_period:]) / long_period if len(prev_closes) >= long_period else long_ma
        
        # 判斷交叉
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            return {"signal": "buy", "reason": f"MA{short_period} 向上穿越 MA{long_period}"}
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            return {"signal": "sell", "reason": f"MA{short_period} 向下穿越 MA{long_period}"}
        elif short_ma > long_ma:
            return {"signal": "hold_long", "reason": f"多頭排列，持有"}
        else:
            return {"signal": "hold_short", "reason": f"空頭排列，觀望"}
    
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
            return {"signal": "hold_long", "reason": f"MACD 多方，持有"}
        else:
            return {"signal": "hold_short", "reason": f"MACD 空方，觀望"}
    
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
    def volume_breakout_strategy(history: List[Dict], ma_period: int = 20, volume_ratio: float = 1.5) -> Dict:
        """
        量價突破策略
        
        Args:
            history: 歷史 K 線資料
            ma_period: 均線週期
            volume_ratio: 量能放大倍數門檻
        """
        if len(history) < ma_period + 1:
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
        
        # 帶量突破均線
        if current_price > ma and prev_price <= ma and vol_ratio >= volume_ratio:
            return {"signal": "buy", "reason": f"帶量突破 MA{ma_period}，量能 {vol_ratio:.1f}x"}
        elif current_price < ma and prev_price >= ma and vol_ratio >= volume_ratio:
            return {"signal": "sell", "reason": f"帶量跌破 MA{ma_period}，量能 {vol_ratio:.1f}x"}
        elif current_price > ma:
            return {"signal": "hold_long", "reason": f"站穩均線上方"}
        else:
            return {"signal": "hold_short", "reason": f"位於均線下方"}
    
    @staticmethod
    def combined_strategy(history: List[Dict]) -> Dict:
        """
        綜合策略：結合多個指標
        
        使用 MA + RSI + MACD 綜合判斷
        """
        if len(history) < 30:
            return {"signal": "hold", "reason": "資料不足"}
        
        # 取得各策略訊號
        ma_signal = SimpleStrategy.ma_crossover(history)
        rsi_signal = SimpleStrategy.rsi_strategy(history)
        macd_signal = SimpleStrategy.macd_strategy(history)
        
        # 計分系統
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # MA 訊號
        if ma_signal["signal"] == "buy":
            buy_score += 2
            reasons.append("均線多頭交叉")
        elif ma_signal["signal"] == "sell":
            sell_score += 2
            reasons.append("均線空頭交叉")
        elif ma_signal["signal"] == "hold_long":
            buy_score += 1
        elif ma_signal["signal"] == "hold_short":
            sell_score += 1
        
        # RSI 訊號
        if rsi_signal["signal"] == "buy":
            buy_score += 2
            reasons.append("RSI 超賣")
        elif rsi_signal["signal"] == "sell":
            sell_score += 2
            reasons.append("RSI 超買")
        
        # MACD 訊號
        if macd_signal["signal"] == "buy":
            buy_score += 2
            reasons.append("MACD 翻多")
        elif macd_signal["signal"] == "sell":
            sell_score += 2
            reasons.append("MACD 翻空")
        elif macd_signal["signal"] == "hold_long":
            buy_score += 1
        elif macd_signal["signal"] == "hold_short":
            sell_score += 1
        
        # 綜合判斷（需要至少 4 分才行動）
        if buy_score >= 4 and buy_score > sell_score:
            return {"signal": "buy", "reason": "綜合訊號買進：" + "、".join(reasons)}
        elif sell_score >= 4 and sell_score > buy_score:
            return {"signal": "sell", "reason": "綜合訊號賣出：" + "、".join(reasons)}
        else:
            return {"signal": "hold", "reason": f"綜合評分 買{buy_score}/賣{sell_score}，觀望"}


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
    
    # 計算需要的月份數
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        months = max(((end_dt - start_dt).days // 30) + 3, 6)
    except:
        months = 12
    
    # 取得歷史資料（嘗試取得更長時間）
    history = await SmartStockService.get_stock_history(stock_id, months=months)
    
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
    
    # 過濾日期範圍
    filtered_history = [
        h for h in history 
        if start_date <= h["date"] <= end_date
    ]
    
    if len(filtered_history) < 20:
        return {"error": "指定日期範圍資料不足"}
    
    # 初始化回測引擎
    engine = BacktestEngine(initial_capital)
    
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
        
        # 執行交易
        if signal["signal"] == "buy":
            # 計算可買股數
            available = engine.capital * position_size
            shares = int(available / price / 1000) * 1000  # 整張
            if shares >= 1000:
                engine.buy(stock_id, price, shares, date, signal["reason"])
        
        elif signal["signal"] == "sell":
            # 賣出全部
            if stock_id in engine.positions:
                shares = engine.positions[stock_id]["shares"]
                engine.sell(stock_id, price, shares, date, signal["reason"])
        
        # 記錄每日淨值
        engine.record_daily_value(date, {stock_id: price})
    
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
