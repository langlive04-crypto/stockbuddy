"""
V10.41 Phase 2 測試腳本

測試 Temporal Fusion Transformer (TFT) 時間序列預測

執行方式:
    cd stockbuddy-backend
    python -m pytest ../V10.41-AI升級包/測試腳本/test_phase2.py -v
"""

import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent.parent.parent / "10.40驗證與開發" / "股票程式開發" / "stockbuddy-backend"
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
        except ImportError:
            print("❌ PyTorch 未安裝，請執行: pip install torch>=2.1.0")
            raise

    def test_pytorch_forecasting_import(self):
        """測試 PyTorch Forecasting 導入"""
        try:
            import pytorch_forecasting
            print(f"✅ PyTorch Forecasting 版本: {pytorch_forecasting.__version__}")
        except ImportError:
            print("❌ PyTorch Forecasting 未安裝，請執行: pip install pytorch-forecasting>=1.0.0")
            raise

    def test_pytorch_lightning_import(self):
        """測試 PyTorch Lightning 導入"""
        try:
            import pytorch_lightning
            print(f"✅ PyTorch Lightning 版本: {pytorch_lightning.__version__}")
        except ImportError:
            print("❌ PyTorch Lightning 未安裝，請執行: pip install pytorch-lightning>=2.1.0")
            raise


class TestTFTPredictor:
    """TFT 預測器測試"""

    def test_predictor_import(self):
        """測試 TFT 預測器導入"""
        try:
            from app.services.tft_predictor import TFTPredictor, get_tft_predictor
            print("✅ TFT 預測器模組導入成功")
        except ImportError as e:
            print(f"❌ TFT 預測器導入失敗: {e}")
            raise

    def test_predictor_creation(self):
        """測試預測器建立"""
        try:
            from app.services.tft_predictor import TFTPredictor

            predictor = TFTPredictor(model_path=None, prediction_length=5)
            assert predictor is not None
            assert predictor.prediction_length == 5
            print("✅ TFT 預測器建立成功")

        except Exception as e:
            print(f"❌ TFT 預測器建立失敗: {e}")
            raise

    def test_rule_based_fallback(self):
        """測試規則引擎備案"""
        try:
            from app.services.tft_predictor import predict_stock

            # 準備模擬歷史數據
            history = [
                {"date": f"2024-01-{i:02d}", "close": 100 + i * 0.5, "volume": 10000}
                for i in range(1, 61)
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

        except Exception as e:
            print(f"❌ 規則引擎備案測試失敗: {e}")
            raise

    def test_insufficient_data_handling(self):
        """測試數據不足處理"""
        try:
            from app.services.tft_predictor import predict_stock

            # 僅 5 天數據 (不足 20 天)
            history = [
                {"date": f"2024-01-{i:02d}", "close": 100, "volume": 10000}
                for i in range(1, 6)
            ]

            result = predict_stock(history, stock_id="SHORT")

            assert result["predictions"]["day_1"]["return"] == 0
            print("✅ 數據不足處理測試通過 (返回中性預測)")

        except Exception as e:
            print(f"❌ 數據不足處理測試失敗: {e}")
            raise


class TestTFTDataPrep:
    """TFT 數據準備測試"""

    def test_dataframe_preparation(self):
        """測試 DataFrame 準備"""
        try:
            from app.services.tft_predictor import TFTPredictor
            import pandas as pd

            predictor = TFTPredictor()

            history = [
                {"date": "2024-01-01", "close": 100, "volume": 10000},
                {"date": "2024-01-02", "close": 101, "volume": 11000},
                {"date": "2024-01-03", "close": 102, "volume": 12000},
            ]

            df = predictor._prepare_dataframe(history, "TEST")

            assert "time_idx" in df.columns
            assert "day_of_week" in df.columns
            assert "month" in df.columns
            assert "stock_id" in df.columns

            print("✅ DataFrame 準備測試通過")
            print(f"   欄位: {list(df.columns)}")

        except Exception as e:
            print(f"❌ DataFrame 準備測試失敗: {e}")
            raise


class TestTFTPerformance:
    """TFT 效能測試"""

    def test_prediction_speed(self):
        """測試預測速度"""
        import time

        try:
            from app.services.tft_predictor import predict_stock

            history = [
                {"date": f"2024-01-{i:02d}", "close": 100 + i * 0.5, "volume": 10000}
                for i in range(1, 61)
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

        except Exception as e:
            print(f"❌ 預測速度測試失敗: {e}")
            raise


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 50)
    print("V10.41 Phase 2 測試 - TFT 時間序列預測")
    print("=" * 50 + "\n")

    # 依賴測試
    print("【依賴檢查】")
    deps = TestTFTDependencies()
    deps.test_pytorch_import()
    deps.test_pytorch_forecasting_import()
    deps.test_pytorch_lightning_import()

    print("\n" + "-" * 50 + "\n")

    # 預測器測試
    print("【TFT 預測器測試】")
    predictor_tests = TestTFTPredictor()
    predictor_tests.test_predictor_import()
    predictor_tests.test_predictor_creation()
    predictor_tests.test_rule_based_fallback()
    predictor_tests.test_insufficient_data_handling()

    print("\n" + "-" * 50 + "\n")

    # 數據準備測試
    print("【數據準備測試】")
    data_tests = TestTFTDataPrep()
    data_tests.test_dataframe_preparation()

    print("\n" + "-" * 50 + "\n")

    # 效能測試
    print("【效能測試】")
    perf_tests = TestTFTPerformance()
    perf_tests.test_prediction_speed()

    print("\n" + "=" * 50)
    print("Phase 2 測試完成！")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
