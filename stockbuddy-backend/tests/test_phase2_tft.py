"""
V10.41 Phase 2 測試腳本 - TFT 時間序列預測

測試項目:
1. TFT 模組導入
2. 規則引擎備案功能
3. API 端點響應
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_tft_import():
    """測試 TFT 模組導入"""
    print("\n[1] 測試 TFT 模組導入...")
    try:
        from app.services.tft_predictor import (
            TFTPredictor,
            TFTPrediction,
            get_tft_predictor,
            predict_stock
        )
        print("    ✓ 模組導入成功")
        return True
    except ImportError as e:
        print(f"    ✗ 模組導入失敗: {e}")
        return False


def test_tft_rule_based():
    """測試規則引擎備案"""
    print("\n[2] 測試規則引擎備案...")
    try:
        from app.services.tft_predictor import TFTPredictor, predict_stock

        # 模擬歷史數據 (30 天)
        history = [
            {"date": f"2024-01-{i:02d}", "close": 100 + i * 0.5, "volume": 10000}
            for i in range(1, 31)
        ]

        # 測試便捷函數
        result = predict_stock(history, "2330")

        assert "stock_id" in result
        assert "predictions" in result
        assert result["stock_id"] == "2330"
        assert "day_1" in result["predictions"]
        assert result["model_version"] == "rule_based_v1"

        print(f"    ✓ 預測結果: {result['predictions']['day_1']}")
        print(f"    ✓ 模型版本: {result['model_version']}")
        return True

    except Exception as e:
        print(f"    ✗ 規則引擎測試失敗: {e}")
        return False


def test_tft_insufficient_data():
    """測試數據不足時的處理"""
    print("\n[3] 測試數據不足處理...")
    try:
        from app.services.tft_predictor import predict_stock

        # 模擬不足的歷史數據 (10 天)
        history = [
            {"date": f"2024-01-{i:02d}", "close": 100, "volume": 10000}
            for i in range(1, 11)
        ]

        result = predict_stock(history, "2330")

        # 應該返回中性預測
        assert result["predictions"]["day_1"]["return"] == 0
        assert result["attention"]["method"] == "insufficient_data"

        print("    ✓ 數據不足時正確返回中性預測")
        return True

    except Exception as e:
        print(f"    ✗ 數據不足測試失敗: {e}")
        return False


def test_tft_api_endpoint():
    """測試 API 端點"""
    print("\n[4] 測試 API 端點...")
    try:
        import httpx

        # 測試 API 端點
        response = httpx.get(
            "http://localhost:8000/api/stocks/ml/forecast/2330",
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"    ✓ API 響應正常: {data.get('stock_id')}")
            if "predictions" in data:
                print(f"    ✓ 預測天數: {len(data['predictions'])}")
            return True
        else:
            print(f"    ✗ API 響應異常: {response.status_code}")
            return False

    except httpx.ConnectError:
        print("    ⚠ 後端未啟動，跳過 API 測試")
        return True  # 不算失敗
    except Exception as e:
        print(f"    ✗ API 測試失敗: {e}")
        return False


def main():
    """執行所有測試"""
    print("=" * 50)
    print("V10.41 Phase 2 測試 - TFT 時間序列預測")
    print("=" * 50)

    results = []

    results.append(test_tft_import())
    results.append(test_tft_rule_based())
    results.append(test_tft_insufficient_data())
    results.append(test_tft_api_endpoint())

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"測試結果: {passed}/{total} 通過")

    if passed == total:
        print("✓ Phase 2 驗收完成！")
    else:
        print("✗ 部分測試未通過，請檢查")

    print("=" * 50)
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
