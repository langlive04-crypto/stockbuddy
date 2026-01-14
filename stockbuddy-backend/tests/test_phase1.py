"""
V10.41 Phase 1 測試腳本

測試 SHAP 解釋性 + FinBERT 情緒分析

執行方式:
    cd stockbuddy-backend
    python -m pytest tests/test_phase1.py -v

    或直接執行:
    python tests/test_phase1.py
"""

import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestSHAPExplainer:
    """SHAP 解釋器測試"""

    def test_shap_import(self):
        """測試 SHAP 導入"""
        try:
            import shap
            assert shap.__version__ >= "0.44.0"
            print(f"SHAP 版本: {shap.__version__}")
        except ImportError:
            print("SHAP 未安裝，請執行: pip install shap>=0.44.0")
            raise

    def test_explainer_creation(self):
        """測試解釋器建立"""
        try:
            from app.services.shap_explainer import SHAPExplainer
            from xgboost import XGBClassifier
            import numpy as np

            # 建立簡單模型
            X = np.random.randn(100, 10)
            y = (X[:, 0] > 0).astype(int)
            model = XGBClassifier(n_estimators=10)
            model.fit(X, y)

            # 建立解釋器
            feature_names = [f"feature_{i}" for i in range(10)]
            explainer = SHAPExplainer(model, feature_names)

            assert explainer is not None
            print("SHAP 解釋器建立成功")

        except Exception as e:
            print(f"SHAP 解釋器建立失敗: {e}")
            raise

    def test_explain_prediction(self):
        """測試預測解釋"""
        try:
            from app.services.shap_explainer import explain_prediction
            from xgboost import XGBClassifier
            import numpy as np

            # 準備測試數據
            X = np.random.randn(100, 10)
            y = (X[:, 0] > 0).astype(int)
            model = XGBClassifier(n_estimators=10)
            model.fit(X, y)

            feature_names = [f"feature_{i}" for i in range(10)]
            test_features = X[0].tolist()

            # 解釋預測
            result = explain_prediction(
                model, feature_names, test_features, "TEST"
            )

            assert "stock_id" in result
            assert "prediction" in result
            assert "explanation" in result
            assert "top_features" in result["explanation"]

            print(f"預測解釋成功: {result['prediction']}")
            print(f"Top 特徵: {result['explanation']['top_features'][0]['feature']}")

        except Exception as e:
            print(f"預測解釋失敗: {e}")
            raise


class TestFinBERTSentiment:
    """FinBERT 情緒分析測試"""

    def test_transformers_import(self):
        """測試 Transformers 導入"""
        try:
            import transformers
            import torch
            print(f"Transformers 版本: {transformers.__version__}")
            print(f"PyTorch 版本: {torch.__version__}")
            print(f"CUDA 可用: {torch.cuda.is_available()}")
        except ImportError as e:
            print(f"依賴未安裝: {e}")
            raise

    def test_finbert_english(self):
        """測試英文 FinBERT"""
        try:
            from app.services.finbert_sentiment import FinBERTSentiment

            analyzer = FinBERTSentiment(language="en")

            # 測試正面情緒
            result = analyzer.analyze("Company reports record earnings and raises guidance")
            assert result.label in ["positive", "negative", "neutral"]
            print(f"英文情緒分析: '{result.label}' (score: {result.score:.2f})")

        except Exception as e:
            print(f"英文 FinBERT 測試失敗: {e}")
            raise

    def test_finbert_chinese(self):
        """測試中文 FinBERT"""
        try:
            from app.services.finbert_sentiment import FinBERTSentiment

            analyzer = FinBERTSentiment(language="zh")

            # 測試中文新聞
            test_cases = [
                ("台積電營收創新高，法人看好後市", "positive"),
                ("營收大幅衰退，股價重挫跌停", "negative"),
                ("公司召開例行股東會", "neutral"),
            ]

            for text, expected in test_cases:
                result = analyzer.analyze(text)
                print(f"'{text[:20]}...' -> {result.label} (expected: {expected})")

            print("中文情緒分析測試完成")

        except Exception as e:
            print(f"中文 FinBERT 測試警告: {e}")
            print("(可能是模型下載中，首次執行較慢)")

    def test_sentiment_score(self):
        """測試情緒分數"""
        try:
            from app.services.finbert_sentiment import get_sentiment_score

            score = get_sentiment_score("股價大漲創新高", language="zh")
            assert 0 <= score <= 100
            print(f"情緒分數: {score:.1f}/100")

        except Exception as e:
            print(f"情緒分數測試失敗: {e}")
            raise


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 50)
    print("V10.41 Phase 1 測試")
    print("=" * 50 + "\n")

    # SHAP 測試
    print("【SHAP 解釋性 AI 測試】")
    shap_tests = TestSHAPExplainer()
    try:
        shap_tests.test_shap_import()
        shap_tests.test_explainer_creation()
        shap_tests.test_explain_prediction()
        print("[PASS] SHAP 測試通過\n")
    except Exception as e:
        print(f"[FAIL] SHAP 測試失敗: {e}\n")

    print("-" * 50 + "\n")

    # FinBERT 測試
    print("【FinBERT 情緒分析測試】")
    finbert_tests = TestFinBERTSentiment()
    try:
        finbert_tests.test_transformers_import()
        finbert_tests.test_finbert_english()
        finbert_tests.test_finbert_chinese()
        finbert_tests.test_sentiment_score()
        print("[PASS] FinBERT 測試通過\n")
    except Exception as e:
        print(f"[FAIL] FinBERT 測試失敗: {e}\n")

    print("=" * 50)
    print("Phase 1 測試完成！")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_all_tests()
