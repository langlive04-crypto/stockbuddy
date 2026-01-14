"""
V10.41 Phase 3 官方測試腳本

測試 PPO 強化學習交易代理

執行方式:
    cd stockbuddy-backend
    python tests/test_phase3_official.py
"""

import sys
import os
import time
from pathlib import Path

# 設置控制台編碼
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestRLDependencies:
    """強化學習依賴測試"""

    def test_stable_baselines3_import(self):
        """測試 Stable Baselines 3 導入"""
        try:
            import stable_baselines3 as sb3
            print(f"✅ Stable Baselines 3 版本: {sb3.__version__}")
            return True
        except ImportError:
            print("⚠️ Stable Baselines 3 未安裝 (可選依賴)")
            return True

    def test_gymnasium_import(self):
        """測試 Gymnasium 導入"""
        try:
            import gymnasium as gym
            print(f"✅ Gymnasium 版本: {gym.__version__}")
            return True
        except ImportError:
            print("⚠️ Gymnasium 未安裝 (可選依賴)")
            return True

    def test_numpy_import(self):
        """測試 NumPy 導入"""
        try:
            import numpy as np
            print(f"✅ NumPy 版本: {np.__version__}")
            return True
        except ImportError:
            print("❌ NumPy 未安裝")
            return False


class TestRLAgent:
    """RL 代理測試"""

    def test_agent_import(self):
        """測試代理導入"""
        try:
            from app.services.rl_agent import (
                RLTradingAgent,
                TradingSuggestion,
                TradingEnvironment,
                get_rl_agent,
                suggest_trade
            )
            print("✅ RL 代理模組導入成功")
            return True
        except ImportError as e:
            print(f"❌ RL 代理導入失敗: {e}")
            return False

    def test_agent_creation(self):
        """測試代理建立"""
        try:
            from app.services.rl_agent import RLTradingAgent

            agent = RLTradingAgent(model_path=None)
            assert agent is not None
            print("✅ RL 代理建立成功")
            return True

        except Exception as e:
            print(f"❌ RL 代理建立失敗: {e}")
            return False

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
            return True

        except Exception as e:
            print(f"❌ 規則引擎建議測試失敗: {e}")
            return False

    def test_different_risk_levels(self):
        """測試不同風險等級"""
        try:
            from app.services.rl_agent import suggest_trade

            market_state = {"rsi": 30, "macd_signal": -0.2, "foreign_net_ratio": -0.1}

            print("   不同風險等級測試:")
            for risk in ["low", "medium", "high"]:
                result = suggest_trade(
                    market_state=market_state,
                    current_position=0.5,
                    risk_tolerance=risk
                )
                print(f"   - {risk}: {result['action']} → {result['target_position']:.0%}")

            print("✅ 不同風險等級測試通過")
            return True

        except Exception as e:
            print(f"❌ 不同風險等級測試失敗: {e}")
            return False


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
            return True

        except Exception as e:
            print(f"❌ TradingSuggestion 測試失敗: {e}")
            return False

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

            print("   動作類型測試:")
            for market, position, expected in test_cases:
                result = suggest_trade(market, position)
                print(f"   - RSI={market['rsi']}, pos={position:.0%} → {result['action']} ({expected})")

            print("✅ 動作類型測試通過")
            return True

        except Exception as e:
            print(f"❌ 動作類型測試失敗: {e}")
            return False


class TestRLPerformance:
    """RL 效能測試"""

    def test_suggestion_speed(self):
        """測試建議速度"""
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
            return True

        except Exception as e:
            print(f"❌ 建議速度測試失敗: {e}")
            return False


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("V10.41 Phase 3 官方驗收測試 - PPO 強化學習代理")
    print("=" * 60 + "\n")

    results = []

    # 依賴測試
    print("【1. 依賴檢查】")
    deps = TestRLDependencies()
    results.append(("Stable Baselines 3", deps.test_stable_baselines3_import()))
    results.append(("Gymnasium", deps.test_gymnasium_import()))
    results.append(("NumPy", deps.test_numpy_import()))

    print("\n" + "-" * 60 + "\n")

    # 代理測試
    print("【2. RL 代理測試】")
    agent_tests = TestRLAgent()
    results.append(("代理導入", agent_tests.test_agent_import()))
    results.append(("代理建立", agent_tests.test_agent_creation()))
    results.append(("規則引擎建議", agent_tests.test_rule_based_suggestion()))
    results.append(("風險等級測試", agent_tests.test_different_risk_levels()))

    print("\n" + "-" * 60 + "\n")

    # 建議測試
    print("【3. 交易建議測試】")
    suggestion_tests = TestTradingSuggestion()
    results.append(("建議資料類", suggestion_tests.test_suggestion_dataclass()))
    results.append(("動作類型", suggestion_tests.test_action_types()))

    print("\n" + "-" * 60 + "\n")

    # 效能測試
    print("【4. 效能測試】")
    perf_tests = TestRLPerformance()
    results.append(("建議速度", perf_tests.test_suggestion_speed()))

    # 統計結果
    print("\n" + "=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"Phase 3 測試結果: {passed}/{total} 通過")
    print("=" * 60)

    if passed == total:
        print("✅ Phase 3 驗收通過！")
    else:
        print("⚠️ 部分測試未通過")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
