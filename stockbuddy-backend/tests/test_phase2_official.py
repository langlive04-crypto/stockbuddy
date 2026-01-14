"""
V10.41 Phase 2 官方測試腳本

測試 Temporal Fusion Transformer (TFT) 時間序列預測

執行方式:
    cd stockbuddy-backend
    python tests/test_phase2_official.py
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


class TestTFTDependencies:
    """TFT 依賴測試"""

    def test_pytorch_import(self):
        """測試 PyTorch 導入"""
        try:
            import torch
            print(f"✅ PyTorch 版本: {torch.__version__}")
            print(f"   CUDA 可用: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"   GPU: {torch.cuda.get_device_name(0)}")
            return True
        except ImportError:
            print("⚠️ PyTorch 未安裝 (可選依賴)")
            return True

    def test_pytorch_forecasting_import(self):
        """測試 PyTorch Forecasting 導入"""
        try:
            import pytorch_forecasting
            print(f"✅ PyTorch Forecasting 版本: {pytorch_forecasting.__version__}")
            return True
        except ImportError:
            print("⚠️ PyTorch Forecasting 未安裝 (可選依賴)")
            return True


class TestTFTPredictor:
    """TFT 預測器測試"""

    def test_predictor_import(self):
        """測試 TFT 預測器導入"""
        try:
            from app.services.tft_predictor import (
                TFTPredictor,
                TFTPrediction,
                get_tft_predictor,
                predict_stock
            )
            print("✅ TFT 預測器模組導入成功")
            return True
        except ImportError as e:
            print(f"❌ TFT 預測器導入失敗: {e}")
            return False

    def test_predictor_creation(self):
        """測試預測器建立"""
        try:
            from app.services.tft_predictor import TFTPredictor

            predictor = TFTPredictor(model_path=None, prediction_length=5)
            assert predictor is not None
            assert predictor.prediction_length == 5
            print("✅ TFT 預測器建立成功")
            return True

        except Exception as e:
            print(f"❌ TFT 預測器建立失敗: {e}")
            return False

    def test_rule_based_fallback(self):
        """測試規則引擎備案"""
        try:
            from app.services.tft_predictor import predict_stock

            # 準備模擬歷史數據 (60 天)
            history = [
                {"date": f"2024-01-{(i % 28) + 1:02d}", "close": 100 + i * 0.5, "volume": 10000}
                for i in range(60)
            ]

            result = predict_stock(history, stock_id="TEST")

            assert "stock_id" in result
            assert "predictions" in result
            assert "model_version" in result

            # 確認有 5 天預測
            assert "day_1" in result["predictions"]
            assert "day_5" in result["predictions"]

            # 確認每天有區間
            day1 = result["predictions"]["day_1"]
            assert "return" in day1
            assert "lower" in day1
            assert "upper" in day1

            print(f"✅ 規則引擎備案測試通過")
            print(f"   模型版本: {result['model_version']}")
            print(f"   Day 1 預測: {day1['return']:.2f}% [{day1['lower']:.2f}, {day1['upper']:.2f}]")
            return True

        except Exception as e:
            print(f"❌ 規則引擎備案測試失敗: {e}")
            return False

    def test_insufficient_data_handling(self):
        """測試數據不足處理"""
        try:
            from app.services.tft_predictor import predict_stock

            # 僅 10 天數據 (不足 20 天)
            history = [
                {"date": f"2024-01-{i:02d}", "close": 100, "volume": 10000}
                for i in range(1, 11)
            ]

            result = predict_stock(history, stock_id="SHORT")

            assert result["predictions"]["day_1"]["return"] == 0
            assert result["attention"]["method"] == "insufficient_data"
            print("✅ 數據不足處理測試通過 (返回中性預測)")
            return True

        except Exception as e:
            print(f"❌ 數據不足處理測試失敗: {e}")
            return False


class TestTFTPerformance:
    """TFT 效能測試"""

    def test_prediction_speed(self):
        """測試預測速度"""
        try:
            from app.services.tft_predictor import predict_stock

            history = [
                {"date": f"2024-01-{(i % 28) + 1:02d}", "close": 100 + i * 0.5, "volume": 10000}
                for i in range(60)
            ]

            start = time.time()
            for _ in range(10):
                predict_stock(history, stock_id="SPEED_TEST")
            elapsed = time.time() - start

            avg_time = elapsed / 10 * 1000  # ms

            print(f"✅ 預測速度測試通過")
            print(f"   平均單次預測: {avg_time:.1f} ms")

            # 規則引擎應該很快 (< 100ms)
            assert avg_time < 100, f"預測太慢: {avg_time:.1f} ms"
            return True

        except Exception as e:
            print(f"❌ 預測速度測試失敗: {e}")
            return False


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("V10.41 Phase 2 官方驗收測試 - TFT 時間序列預測")
    print("=" * 60 + "\n")

    results = []

    # 依賴測試
    print("【1. 依賴檢查】")
    deps = TestTFTDependencies()
    results.append(("PyTorch 導入", deps.test_pytorch_import()))
    results.append(("PyTorch Forecasting", deps.test_pytorch_forecasting_import()))

    print("\n" + "-" * 60 + "\n")

    # 預測器測試
    print("【2. TFT 預測器測試】")
    predictor_tests = TestTFTPredictor()
    results.append(("預測器導入", predictor_tests.test_predictor_import()))
    results.append(("預測器建立", predictor_tests.test_predictor_creation()))
    results.append(("規則引擎備案", predictor_tests.test_rule_based_fallback()))
    results.append(("數據不足處理", predictor_tests.test_insufficient_data_handling()))

    print("\n" + "-" * 60 + "\n")

    # 效能測試
    print("【3. 效能測試】")
    perf_tests = TestTFTPerformance()
    results.append(("預測速度", perf_tests.test_prediction_speed()))

    # 統計結果
    print("\n" + "=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"Phase 2 測試結果: {passed}/{total} 通過")
    print("=" * 60)

    if passed == total:
        print("✅ Phase 2 驗收通過！")
    else:
        print("⚠️ 部分測試未通過")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
