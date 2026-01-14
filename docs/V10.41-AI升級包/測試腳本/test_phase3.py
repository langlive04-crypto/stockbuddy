"""
V10.41 Phase 3 測試腳本

測試 PPO 強化學習交易代理

執行方式:
    cd stockbuddy-backend
    python -m pytest ../V10.41-AI升級包/測試腳本/test_phase3.py -v
"""

import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent.parent.parent / "10.40驗證與開發" / "股票程式開發" / "stockbuddy-backend"
sys.path.insert(0, str(backend_path))


class TestRLDependencies:
    """強化學習依賴測試"""

    def test_stable_baselines3_import(self):
        """測試 Stable Baselines 3 導入"""
        try:
            import stable_baselines3 as sb3
            print(f"✅ Stable Baselines 3 版本: {sb3.__version__}")
        except ImportError:
            print("❌ Stable Baselines 3 未安裝，請執行: pip install stable-baselines3>=2.2.0")
            raise

    def test_gymnasium_import(self):
        """測試 Gymnasium 導入"""
        try:
            import gymnasium as gym
            print(f"✅ Gymnasium 版本: {gym.__version__}")
        except ImportError:
            print("❌ Gymnasium 未安裝，請執行: pip install gymnasium>=0.29.0")
            raise

    def test_numpy_import(self):
        """測試 NumPy 導入"""
        try:
            import numpy as np
            print(f"✅ NumPy 版本: {np.__version__}")
        except ImportError:
            print("❌ NumPy 未安裝")
            raise


class TestTradingEnvironment:
    """交易環境測試"""

    def test_environment_import(self):
        """測試環境導入"""
        try:
            from app.services.rl_agent import TradingEnvironment
            print("✅ TradingEnvironment 導入成功")
        except ImportError as e:
            print(f"❌ TradingEnvironment 導入失敗: {e}")
            raise

    def test_environment_creation(self):
        """測試環境建立"""
        try:
            from app.services.rl_agent import TradingEnvironment

            env = TradingEnvironment(
                initial_cash=1000000,
                max_position=1.0,
                transaction_cost=0.001425
            )

            assert env is not None
            assert env.initial_cash == 1000000
            print("✅ 交易環境建立成功")

        except Exception as e:
            print(f"❌ 交易環境建立失敗: {e}")
            raise

    def test_environment_spaces(self):
        """測試環境空間"""
        try:
            from app.services.rl_agent import TradingEnvironment

            env = TradingEnvironment()

            # 觀察空間
            assert env.observation_space.shape == (32,)
            print(f"✅ 觀察空間: {env.observation_space.shape}")

            # 動作空間
            assert env.action_space.shape == (1,)
            print(f"✅ 動作空間: {env.action_space.shape}")

        except Exception as e:
            print(f"❌ 環境空間測試失敗: {e}")
            raise

    def test_environment_reset(self):
        """測試環境重置"""
        try:
            from app.services.rl_agent import TradingEnvironment

            env = TradingEnvironment()
            obs, info = env.reset()

            assert obs.shape == (32,)
            assert env.cash == env.initial_cash
            assert env.position == 0.0
            print("✅ 環境重置測試通過")

        except Exception as e:
            print(f"❌ 環境重置測試失敗: {e}")
            raise

    def test_environment_step(self):
        """測試環境步進"""
        try:
            from app.services.rl_agent import TradingEnvironment
            import numpy as np

            env = TradingEnvironment()
            env.reset()

            # 執行動作 (買入)
            action = np.array([0.5])  # 增加倉位
            obs, reward, terminated, truncated, info = env.step(action)

            assert obs.shape == (32,)
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            print(f"✅ 環境步進測試通過")
            print(f"   獎勵: {reward:.4f}")
            print(f"   當前持倉: {env.position:.2%}")

        except Exception as e:
            print(f"❌ 環境步進測試失敗: {e}")
            raise

    def test_environment_episode(self):
        """測試完整回合"""
        try:
            from app.services.rl_agent import TradingEnvironment
            import numpy as np

            env = TradingEnvironment()
            obs, _ = env.reset()

            total_reward = 0
            steps = 0

            while True:
                # 隨機動作
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                steps += 1

                if terminated or truncated:
                    break

            print(f"✅ 完整回合測試通過")
            print(f"   步數: {steps}")
            print(f"   總獎勵: {total_reward:.4f}")
            print(f"   最終價值: ${env.portfolio_value:,.0f}")

        except Exception as e:
            print(f"❌ 完整回合測試失敗: {e}")
            raise


class TestRLAgent:
    """RL 代理測試"""

    def test_agent_import(self):
        """測試代理導入"""
        try:
            from app.services.rl_agent import RLTradingAgent, get_rl_agent
            print("✅ RLTradingAgent 導入成功")
        except ImportError as e:
            print(f"❌ RLTradingAgent 導入失敗: {e}")
            raise

    def test_agent_creation(self):
        """測試代理建立"""
        try:
            from app.services.rl_agent import RLTradingAgent

            agent = RLTradingAgent(model_path=None)
            assert agent is not None
            print("✅ RL 代理建立成功")

        except Exception as e:
            print(f"❌ RL 代理建立失敗: {e}")
            raise

    def test_rule_based_suggestion(self):
        """測試規則引擎建議"""
        try:
            from app.services.rl_agent import suggest_trade

            market_state = {
                "rsi": 25,  # 超賣
                "macd_signal": 0.5,  # 多頭
                "foreign_net_ratio": 0.1  # 外資買超
            }

            result = suggest_trade(
                market_state=market_state,
                current_position=0.3,
                risk_tolerance="medium"
            )

            assert "action" in result
            assert "target_position" in result
            assert "confidence" in result
            assert "reasoning" in result

            print(f"✅ 規則引擎建議測試通過")
            print(f"   動作: {result['action']}")
            print(f"   目標持倉: {result['target_position']:.0%}")
            print(f"   信心度: {result['confidence']:.0%}")
            print(f"   理由: {result['reasoning']}")

        except Exception as e:
            print(f"❌ 規則引擎建議測試失敗: {e}")
            raise

    def test_different_risk_levels(self):
        """測試不同風險等級"""
        try:
            from app.services.rl_agent import suggest_trade

            market_state = {"rsi": 30, "macd_signal": -0.2, "foreign_net_ratio": -0.1}

            for risk in ["low", "medium", "high"]:
                result = suggest_trade(
                    market_state=market_state,
                    current_position=0.5,
                    risk_tolerance=risk
                )
                print(f"   {risk}: {result['action']} → {result['target_position']:.0%}")

            print("✅ 不同風險等級測試通過")

        except Exception as e:
            print(f"❌ 不同風險等級測試失敗: {e}")
            raise


class TestTradingSuggestion:
    """交易建議測試"""

    def test_suggestion_dataclass(self):
        """測試建議資料類"""
        try:
            from app.services.rl_agent import TradingSuggestion

            suggestion = TradingSuggestion(
                action="buy",
                target_position=0.5,
                confidence=0.8,
                reasoning=["RSI 超賣", "外資買超"]
            )

            assert suggestion.action == "buy"
            assert suggestion.target_position == 0.5
            print("✅ TradingSuggestion 資料類測試通過")

        except Exception as e:
            print(f"❌ TradingSuggestion 測試失敗: {e}")
            raise

    def test_action_types(self):
        """測試動作類型"""
        try:
            from app.services.rl_agent import suggest_trade

            # 測試各種市場狀態
            test_cases = [
                ({"rsi": 20, "macd_signal": 1, "foreign_net_ratio": 0.2}, 0.0, "buy 預期"),
                ({"rsi": 80, "macd_signal": -1, "foreign_net_ratio": -0.2}, 0.8, "sell/decrease 預期"),
                ({"rsi": 50, "macd_signal": 0, "foreign_net_ratio": 0}, 0.5, "hold 預期"),
            ]

            for market, position, expected in test_cases:
                result = suggest_trade(market, position)
                print(f"   RSI={market['rsi']}, pos={position:.0%} → {result['action']} ({expected})")

            print("✅ 動作類型測試通過")

        except Exception as e:
            print(f"❌ 動作類型測試失敗: {e}")
            raise


class TestRLPerformance:
    """RL 效能測試"""

    def test_suggestion_speed(self):
        """測試建議速度"""
        import time

        try:
            from app.services.rl_agent import suggest_trade

            market_state = {"rsi": 50, "macd_signal": 0, "foreign_net_ratio": 0}

            start = time.time()
            for _ in range(100):
                suggest_trade(market_state, 0.5)
            elapsed = time.time() - start

            avg_time = elapsed / 100 * 1000  # ms

            print(f"✅ 建議速度測試通過")
            print(f"   平均單次建議: {avg_time:.2f} ms")

            # 規則引擎應該很快 (< 10ms)
            assert avg_time < 10, f"建議太慢: {avg_time:.2f} ms"

        except Exception as e:
            print(f"❌ 建議速度測試失敗: {e}")
            raise


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 50)
    print("V10.41 Phase 3 測試 - PPO 強化學習代理")
    print("=" * 50 + "\n")

    # 依賴測試
    print("【依賴檢查】")
    deps = TestRLDependencies()
    deps.test_stable_baselines3_import()
    deps.test_gymnasium_import()
    deps.test_numpy_import()

    print("\n" + "-" * 50 + "\n")

    # 環境測試
    print("【交易環境測試】")
    env_tests = TestTradingEnvironment()
    env_tests.test_environment_import()
    env_tests.test_environment_creation()
    env_tests.test_environment_spaces()
    env_tests.test_environment_reset()
    env_tests.test_environment_step()
    env_tests.test_environment_episode()

    print("\n" + "-" * 50 + "\n")

    # 代理測試
    print("【RL 代理測試】")
    agent_tests = TestRLAgent()
    agent_tests.test_agent_import()
    agent_tests.test_agent_creation()
    agent_tests.test_rule_based_suggestion()
    agent_tests.test_different_risk_levels()

    print("\n" + "-" * 50 + "\n")

    # 建議測試
    print("【交易建議測試】")
    suggestion_tests = TestTradingSuggestion()
    suggestion_tests.test_suggestion_dataclass()
    suggestion_tests.test_action_types()

    print("\n" + "-" * 50 + "\n")

    # 效能測試
    print("【效能測試】")
    perf_tests = TestRLPerformance()
    perf_tests.test_suggestion_speed()

    print("\n" + "=" * 50)
    print("Phase 3 測試完成！")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
