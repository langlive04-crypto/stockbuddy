"""
PPO 強化學習交易代理 V10.41

使用 PPO 算法進行動態倉位配置

安裝位置: stockbuddy-backend/app/services/rl_agent.py

依賴:
    pip install stable-baselines3>=2.2.0 gymnasium>=0.29.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# 延遲導入
numpy = None
gymnasium = None
stable_baselines3 = None


def _ensure_dependencies():
    """確保依賴已導入 (可選)"""
    global numpy, gymnasium, stable_baselines3
    if numpy is None:
        try:
            import numpy as _np
            numpy = _np
        except ImportError:
            pass

        try:
            import gymnasium as _gym
            import stable_baselines3 as _sb3
            gymnasium = _gym
            stable_baselines3 = _sb3
            logger.info("[RL] RL 依賴載入成功")
            return True
        except ImportError:
            logger.warning("[RL] RL 依賴未安裝，將使用規則引擎備案")
            return False
    return gymnasium is not None


def _has_full_dependencies():
    """檢查是否有完整 RL 依賴"""
    return gymnasium is not None and stable_baselines3 is not None


@dataclass
class TradingSuggestion:
    """交易建議"""
    action: str           # "buy", "sell", "hold", "increase", "decrease"
    target_position: float  # 目標持倉比例 (0-1)
    confidence: float     # 信心度 (0-1)
    reasoning: List[str]  # 決策理由


class TradingEnvironment:
    """
    交易環境 (Gymnasium 格式)

    State: [market_features(20), portfolio_state(10), cash_ratio, risk_budget]
    Action: position_change (-1 to +1)
    Reward: sharpe_ratio (風險調整後收益)
    """

    def __init__(
        self,
        initial_cash: float = 1000000,
        max_position: float = 1.0,
        transaction_cost: float = 0.001425,  # 台股手續費
        risk_free_rate: float = 0.02
    ):
        """
        初始化交易環境

        Args:
            initial_cash: 初始資金
            max_position: 最大持倉比例
            transaction_cost: 交易成本
            risk_free_rate: 無風險利率 (年化)
        """
        _ensure_dependencies()

        self.initial_cash = initial_cash
        self.max_position = max_position
        self.transaction_cost = transaction_cost
        self.risk_free_rate = risk_free_rate

        # 狀態空間: 32 維
        self.observation_space = gymnasium.spaces.Box(
            low=-numpy.inf,
            high=numpy.inf,
            shape=(32,),
            dtype=numpy.float32
        )

        # 動作空間: 連續 (-1 到 +1)
        self.action_space = gymnasium.spaces.Box(
            low=-1,
            high=1,
            shape=(1,),
            dtype=numpy.float32
        )

        self.reset()

    def reset(self, seed=None):
        """重置環境"""
        self.cash = self.initial_cash
        self.position = 0.0
        self.portfolio_value = self.initial_cash
        self.returns_history = []
        self.step_count = 0

        return self._get_observation(), {}

    def step(self, action):
        """
        執行一步

        Args:
            action: 倉位變化 (-1 到 +1)

        Returns:
            observation, reward, terminated, truncated, info
        """
        # 解析動作
        position_change = float(action[0])

        # 更新持倉
        new_position = numpy.clip(
            self.position + position_change * 0.1,  # 每步最多變化 10%
            0,
            self.max_position
        )

        # 計算交易成本
        trade_amount = abs(new_position - self.position) * self.portfolio_value
        cost = trade_amount * self.transaction_cost

        self.position = new_position
        self.cash -= cost

        # 模擬收益 (這裡需要接入真實市場數據)
        daily_return = numpy.random.normal(0.0005, 0.02)  # 模擬
        self.portfolio_value *= (1 + daily_return * self.position)

        # 記錄收益
        self.returns_history.append(daily_return * self.position)

        # 計算獎勵 (Sharpe Ratio)
        reward = self._calculate_reward()

        self.step_count += 1
        terminated = self.step_count >= 252  # 一年交易日
        truncated = False

        return self._get_observation(), reward, terminated, truncated, {}

    def _get_observation(self) -> numpy.ndarray:
        """取得當前狀態"""
        # 這裡簡化為隨機特徵，實際應接入真實市場數據
        market_features = numpy.random.randn(20).astype(numpy.float32)
        portfolio_state = numpy.array([
            self.position,
            self.cash / self.initial_cash,
            self.portfolio_value / self.initial_cash,
            len(self.returns_history),
            numpy.mean(self.returns_history[-20:]) if self.returns_history else 0,
            numpy.std(self.returns_history[-20:]) if len(self.returns_history) > 1 else 0,
            0, 0, 0, 0  # 其他狀態
        ], dtype=numpy.float32)
        other = numpy.array([self.step_count / 252, 0], dtype=numpy.float32)

        return numpy.concatenate([market_features, portfolio_state, other])

    def _calculate_reward(self) -> float:
        """計算獎勵 (Sharpe Ratio)"""
        if len(self.returns_history) < 2:
            return 0

        returns = numpy.array(self.returns_history[-20:])
        mean_return = numpy.mean(returns) * 252  # 年化
        std_return = numpy.std(returns) * numpy.sqrt(252) + 1e-6

        sharpe = (mean_return - self.risk_free_rate) / std_return
        return float(numpy.clip(sharpe, -5, 5))


class RLTradingAgent:
    """
    PPO 交易代理

    使用方式:
    ```python
    agent = RLTradingAgent()
    suggestion = agent.suggest(market_state, current_position)
    ```
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        初始化 RL 代理

        Args:
            model_path: 模型檔案路徑
        """
        self._has_deps = _ensure_dependencies()

        self.model_path = model_path
        self._model = None
        self._loaded = False

    def _load_model(self):
        """載入模型"""
        if self._loaded:
            return

        if not self._has_deps:
            logger.warning("[RL] RL 依賴未安裝，將使用規則引擎備案")
            self._loaded = True
            return

        if self.model_path and Path(self.model_path).exists():
            logger.info(f"[RL] 載入模型: {self.model_path}")
            self._model = stable_baselines3.PPO.load(self.model_path)
            self._loaded = True
            logger.info("[RL] 模型載入完成")
        else:
            logger.warning("[RL] 模型不存在，將使用規則引擎備案")
            self._loaded = True

    def suggest(
        self,
        market_state: Dict[str, float],
        current_position: float,
        cash_available: float = 100000,
        risk_tolerance: str = "medium"
    ) -> TradingSuggestion:
        """
        生成交易建議

        Args:
            market_state: 市場狀態 (技術指標等)
            current_position: 目前持倉比例 (0-1)
            cash_available: 可用資金
            risk_tolerance: 風險容忍度 ("low", "medium", "high")

        Returns:
            TradingSuggestion 交易建議
        """
        self._load_model()

        if self._model is None:
            return self._rule_based_suggestion(
                market_state, current_position, risk_tolerance
            )

        # 準備觀察向量
        obs = self._prepare_observation(market_state, current_position)

        # 模型預測
        action, _ = self._model.predict(obs, deterministic=True)
        position_change = float(action[0])

        # 計算目標持倉
        target_position = numpy.clip(current_position + position_change * 0.1, 0, 1)

        # 決定動作類型
        if position_change > 0.1:
            action_type = "increase" if current_position > 0 else "buy"
        elif position_change < -0.1:
            action_type = "decrease" if current_position > 0.1 else "sell"
        else:
            action_type = "hold"

        # 生成理由
        reasoning = self._generate_reasoning(market_state, action_type)

        return TradingSuggestion(
            action=action_type,
            target_position=round(target_position, 2),
            confidence=0.7,  # 可從模型 value function 估算
            reasoning=reasoning
        )

    def _prepare_observation(
        self,
        market_state: Dict[str, float],
        current_position: float
    ) -> numpy.ndarray:
        """準備觀察向量"""
        # 市場特徵
        market_features = numpy.array([
            market_state.get("rsi", 50) / 100,
            market_state.get("macd_signal", 0),
            market_state.get("price_vs_ma20", 0) / 100,
            market_state.get("volume_ratio", 1),
            market_state.get("foreign_net_ratio", 0),
            # ... 其他特徵
        ] + [0] * 15, dtype=numpy.float32)[:20]

        # 持倉狀態
        portfolio_state = numpy.array([
            current_position,
            1 - current_position,  # 現金比例
            0, 0, 0, 0, 0, 0, 0, 0
        ], dtype=numpy.float32)

        # 其他
        other = numpy.array([0.5, 0], dtype=numpy.float32)

        return numpy.concatenate([market_features, portfolio_state, other])

    def _rule_based_suggestion(
        self,
        market_state: Dict[str, float],
        current_position: float,
        risk_tolerance: str
    ) -> TradingSuggestion:
        """
        規則引擎備案
        """
        # 風險係數
        risk_factor = {"low": 0.5, "medium": 1.0, "high": 1.5}.get(risk_tolerance, 1.0)

        # 技術指標分析
        rsi = market_state.get("rsi", 50)
        macd = market_state.get("macd_signal", 0)
        foreign = market_state.get("foreign_net_ratio", 0)

        # 計算信號
        signal = 0
        reasoning = []

        if rsi < 30:
            signal += 0.3
            reasoning.append("RSI 處於超賣區間")
        elif rsi > 70:
            signal -= 0.3
            reasoning.append("RSI 處於超買區間")

        if macd > 0:
            signal += 0.2
            reasoning.append("MACD 呈現多頭")
        elif macd < 0:
            signal -= 0.2
            reasoning.append("MACD 呈現空頭")

        if foreign > 0:
            signal += 0.2
            reasoning.append("外資淨買超")
        elif foreign < 0:
            signal -= 0.1
            reasoning.append("外資淨賣超")

        # 調整風險
        signal *= risk_factor

        # 決定目標持倉
        target = current_position + signal * 0.2
        target = max(0, min(1, target))  # clip without numpy

        # 決定動作
        if signal > 0.2:
            action = "increase" if current_position > 0 else "buy"
        elif signal < -0.2:
            action = "decrease" if current_position > 0.2 else "sell"
        else:
            action = "hold"
            reasoning.append("信號不明顯，建議觀望")

        return TradingSuggestion(
            action=action,
            target_position=round(target, 2),
            confidence=min(abs(signal) + 0.3, 0.9),
            reasoning=reasoning if reasoning else ["綜合評估後的建議"]
        )

    def _generate_reasoning(
        self,
        market_state: Dict[str, float],
        action: str
    ) -> List[str]:
        """生成決策理由"""
        reasoning = []

        rsi = market_state.get("rsi", 50)
        if rsi < 35:
            reasoning.append("RSI 處於超賣區間")
        elif rsi > 65:
            reasoning.append("RSI 處於超買區間")

        if market_state.get("foreign_net_ratio", 0) > 0:
            reasoning.append("外資呈現買超趨勢")

        if market_state.get("volume_ratio", 1) > 1.5:
            reasoning.append("成交量明顯放大")

        if not reasoning:
            reasoning.append("綜合技術指標分析")

        return reasoning


# 全域實例
_agent: Optional[RLTradingAgent] = None


def get_rl_agent(model_path: Optional[str] = None) -> RLTradingAgent:
    """取得 RL 代理實例"""
    global _agent
    if _agent is None:
        _agent = RLTradingAgent(model_path)
    return _agent


def suggest_trade(
    market_state: Dict[str, float],
    current_position: float,
    risk_tolerance: str = "medium"
) -> Dict[str, Any]:
    """
    便捷函數：取得交易建議

    Returns:
        {
            "action": "increase",
            "target_position": 0.45,
            "confidence": 0.78,
            "reasoning": [...]
        }
    """
    agent = get_rl_agent()
    result = agent.suggest(market_state, current_position, risk_tolerance=risk_tolerance)

    return {
        "action": result.action,
        "target_position": result.target_position,
        "confidence": result.confidence,
        "reasoning": result.reasoning
    }
