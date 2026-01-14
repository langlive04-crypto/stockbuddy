"""
SHAP 解釋性 AI 模組 V10.41

提供 ML 預測的可解釋性分析

安裝位置: stockbuddy-backend/app/services/shap_explainer.py

依賴: pip install shap>=0.44.0
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# 延遲導入，避免啟動時載入
shap = None


def _ensure_shap():
    """確保 SHAP 已導入"""
    global shap
    if shap is None:
        try:
            import shap as _shap
            shap = _shap
            logger.info("[SHAP] SHAP 模組載入成功")
        except ImportError:
            raise ImportError("請安裝 shap: pip install shap>=0.44.0")


@dataclass
class FeatureContribution:
    """特徵貢獻"""
    feature: str
    value: float
    contribution: float
    direction: str  # "positive" or "negative"


@dataclass
class PredictionExplanation:
    """預測解釋"""
    stock_id: str
    prediction: str
    probability: float
    base_value: float
    predicted_value: float
    top_features: List[FeatureContribution]
    total_features: int


class SHAPExplainer:
    """
    SHAP 解釋器

    為 XGBoost 模型提供可解釋性分析
    """

    def __init__(self, model, feature_names: List[str]):
        """
        初始化解釋器

        Args:
            model: 訓練好的 XGBoost 模型
            feature_names: 特徵名稱列表
        """
        _ensure_shap()

        self.model = model
        self.feature_names = feature_names
        self._explainer = None

    def _get_explainer(self):
        """取得或建立 SHAP 解釋器"""
        if self._explainer is None:
            self._explainer = shap.TreeExplainer(self.model)
            logger.info("[SHAP] TreeExplainer 建立完成")
        return self._explainer

    def explain(
        self,
        feature_vector: List[float],
        stock_id: str = "unknown",
        top_n: int = 10
    ) -> PredictionExplanation:
        """
        解釋單筆預測

        Args:
            feature_vector: 特徵向量 (已標準化)
            stock_id: 股票代碼
            top_n: 返回前 N 個重要特徵

        Returns:
            PredictionExplanation 解釋結果
        """
        import numpy as np

        explainer = self._get_explainer()

        # 確保是 2D 陣列
        if len(np.array(feature_vector).shape) == 1:
            feature_vector = [feature_vector]

        # 計算 SHAP 值
        shap_values = explainer.shap_values(feature_vector)

        # 對於二元分類，取上漲類別 (index 1)
        if isinstance(shap_values, list):
            # 多類別輸出
            values = shap_values[1][0]  # 上漲類別
            base = explainer.expected_value[1]
        else:
            # 單一輸出
            values = shap_values[0]
            base = explainer.expected_value

        # 計算預測值
        predicted_value = base + np.sum(values)

        # 整理特徵貢獻
        contributions = []
        for i, name in enumerate(self.feature_names):
            contrib = float(values[i])
            contributions.append(FeatureContribution(
                feature=name,
                value=float(feature_vector[0][i]),
                contribution=contrib,
                direction="positive" if contrib > 0 else "negative"
            ))

        # 按絕對值排序，取 top N
        contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
        top_features = contributions[:top_n]

        # 決定預測結果
        prob = 1 / (1 + np.exp(-predicted_value))  # sigmoid
        if prob > 0.6:
            prediction = "up"
        elif prob < 0.4:
            prediction = "down"
        else:
            prediction = "neutral"

        return PredictionExplanation(
            stock_id=stock_id,
            prediction=prediction,
            probability=float(prob),
            base_value=float(base),
            predicted_value=float(predicted_value),
            top_features=top_features,
            total_features=len(self.feature_names)
        )

    def explain_batch(
        self,
        feature_vectors: List[List[float]],
        stock_ids: List[str],
        top_n: int = 5
    ) -> List[PredictionExplanation]:
        """
        批次解釋多筆預測

        Args:
            feature_vectors: 特徵向量列表
            stock_ids: 股票代碼列表
            top_n: 每筆返回前 N 個重要特徵

        Returns:
            解釋結果列表
        """
        results = []
        for i, (features, stock_id) in enumerate(zip(feature_vectors, stock_ids)):
            try:
                explanation = self.explain(features, stock_id, top_n)
                results.append(explanation)
            except Exception as e:
                logger.warning(f"[SHAP] 解釋 {stock_id} 失敗: {e}")
                continue
        return results

    def get_feature_importance(self) -> Dict[str, float]:
        """
        取得全域特徵重要性

        Returns:
            特徵名稱 -> 平均 |SHAP| 值
        """
        # 需要有訓練數據來計算全域重要性
        # 這裡返回基於模型的特徵重要性
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            return {
                name: float(imp)
                for name, imp in zip(self.feature_names, importance)
            }
        return {}


# 便捷函數
def create_explainer(model, feature_names: List[str]) -> SHAPExplainer:
    """建立 SHAP 解釋器"""
    return SHAPExplainer(model, feature_names)


def explain_prediction(
    model,
    feature_names: List[str],
    feature_vector: List[float],
    stock_id: str = "unknown"
) -> Dict[str, Any]:
    """
    快速解釋單筆預測

    Returns:
        解釋結果字典
    """
    explainer = SHAPExplainer(model, feature_names)
    result = explainer.explain(feature_vector, stock_id)

    # 轉換為字典格式
    return {
        "stock_id": result.stock_id,
        "prediction": result.prediction,
        "probability": result.probability,
        "explanation": {
            "base_value": result.base_value,
            "predicted_value": result.predicted_value,
            "top_features": [
                {
                    "feature": f.feature,
                    "value": f.value,
                    "contribution": f.contribution,
                    "direction": f.direction
                }
                for f in result.top_features
            ]
        }
    }
