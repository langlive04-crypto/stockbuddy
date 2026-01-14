"""
時序交叉驗證模組 V10.38

提供專為金融時序數據設計的交叉驗證方法，
避免前向偏差 (Look-ahead Bias)

驗證方法:
- TimeSeriesSplit: 標準時序分割
- WalkForwardValidation: 滾動窗口驗證
- PurgedKFold: 帶清除緩衝的 K-Fold
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Iterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """驗證結果"""
    fold: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_size: int
    test_size: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float


class TimeSeriesValidator:
    """
    時序驗證器

    專為金融時序數據設計，確保訓練集永遠早於測試集
    """

    def __init__(
        self,
        n_splits: int = 5,
        gap: int = 0,
        test_size: Optional[int] = None,
        min_train_size: int = 30,
    ):
        """
        Args:
            n_splits: 分割數
            gap: 訓練集與測試集間的間隔天數（避免資訊洩漏）
            test_size: 每個測試集大小（None 則自動計算）
            min_train_size: 最小訓練集大小
        """
        self.n_splits = n_splits
        self.gap = gap
        self.test_size = test_size
        self.min_train_size = min_train_size

    def time_series_split(
        self,
        data: List[Dict],
        date_field: str = "date"
    ) -> Iterator[Tuple[List[Dict], List[Dict]]]:
        """
        時序分割

        確保訓練集總是早於測試集

        Args:
            data: 依日期排序的數據
            date_field: 日期欄位名稱

        Yields:
            (訓練集, 測試集) 元組
        """
        n = len(data)
        if n < self.min_train_size + self.n_splits:
            logger.warning(f"Data too small: {n} samples")
            return

        # 計算測試集大小
        if self.test_size is None:
            test_size = n // (self.n_splits + 1)
        else:
            test_size = self.test_size

        # 逐步增加訓練集
        for i in range(self.n_splits):
            # 計算分割點
            train_end = self.min_train_size + i * test_size
            test_start = train_end + self.gap
            test_end = test_start + test_size

            if test_end > n:
                break

            train_data = data[:train_end]
            test_data = data[test_start:test_end]

            yield train_data, test_data

    def walk_forward_split(
        self,
        data: List[Dict],
        train_window: int = 60,
        test_window: int = 20,
        step: int = 10,
    ) -> Iterator[Tuple[List[Dict], List[Dict]]]:
        """
        滾動窗口驗證

        使用固定大小的訓練窗口向前滾動

        Args:
            data: 依日期排序的數據
            train_window: 訓練窗口大小
            test_window: 測試窗口大小
            step: 每次滾動步長

        Yields:
            (訓練集, 測試集) 元組
        """
        n = len(data)
        start = 0

        while start + train_window + self.gap + test_window <= n:
            train_end = start + train_window
            test_start = train_end + self.gap
            test_end = test_start + test_window

            train_data = data[start:train_end]
            test_data = data[test_start:test_end]

            yield train_data, test_data

            start += step

    def purged_kfold_split(
        self,
        data: List[Dict],
        purge_gap: int = 5,
    ) -> Iterator[Tuple[List[Dict], List[Dict]]]:
        """
        帶清除緩衝的 K-Fold

        在每個 fold 的邊界設置清除區，避免資訊洩漏

        Args:
            data: 依日期排序的數據
            purge_gap: 清除區大小

        Yields:
            (訓練集, 測試集) 元組
        """
        n = len(data)
        fold_size = n // self.n_splits

        for i in range(self.n_splits):
            test_start = i * fold_size
            test_end = (i + 1) * fold_size if i < self.n_splits - 1 else n

            # 建立訓練集（排除測試集及其前後的清除區）
            train_data = []
            for j, d in enumerate(data):
                # 跳過測試區
                if test_start <= j < test_end:
                    continue
                # 跳過測試區前的清除區
                if test_start - purge_gap <= j < test_start:
                    continue
                # 跳過測試區後的清除區
                if test_end <= j < test_end + purge_gap:
                    continue
                train_data.append(d)

            test_data = data[test_start:test_end]

            if len(train_data) >= self.min_train_size:
                yield train_data, test_data


class ModelEvaluator:
    """
    模型評估器

    使用時序驗證評估模型性能
    """

    def __init__(
        self,
        validator: Optional[TimeSeriesValidator] = None
    ):
        self.validator = validator or TimeSeriesValidator()
        self.results: List[ValidationResult] = []

    def evaluate_time_series(
        self,
        model_class: Any,
        model_params: Dict,
        data: List[Dict],
        feature_extractor: Any,
        label_field: str = "final_return_percent",
        validation_method: str = "time_series"
    ) -> Dict[str, Any]:
        """
        使用時序驗證評估模型

        Args:
            model_class: 模型類別
            model_params: 模型參數
            data: 訓練數據
            feature_extractor: 特徵萃取器
            label_field: 標籤欄位
            validation_method: 驗證方法 (time_series, walk_forward, purged_kfold)

        Returns:
            評估結果
        """
        try:
            import numpy as np
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            from sklearn.preprocessing import StandardScaler
        except ImportError as e:
            return {"error": f"Missing dependency: {e}"}

        self.results = []

        # 選擇分割方法
        if validation_method == "walk_forward":
            splits = self.validator.walk_forward_split(data)
        elif validation_method == "purged_kfold":
            splits = self.validator.purged_kfold_split(data)
        else:
            splits = self.validator.time_series_split(data)

        fold = 0
        for train_data, test_data in splits:
            fold += 1

            # 準備特徵
            X_train, y_train = self._prepare_data(train_data, feature_extractor, label_field)
            X_test, y_test = self._prepare_data(test_data, feature_extractor, label_field)

            if len(X_train) == 0 or len(X_test) == 0:
                continue

            X_train = np.array(X_train)
            X_test = np.array(X_test)
            y_train = np.array(y_train)
            y_test = np.array(y_test)

            # 標準化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # 訓練模型
            model = model_class(**model_params)
            model.fit(X_train_scaled, y_train)

            # 預測
            y_pred = model.predict(X_test_scaled)

            # 計算指標
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)

            # 記錄結果
            result = ValidationResult(
                fold=fold,
                train_start=train_data[0].get("date", ""),
                train_end=train_data[-1].get("date", ""),
                test_start=test_data[0].get("date", ""),
                test_end=test_data[-1].get("date", ""),
                train_size=len(train_data),
                test_size=len(test_data),
                accuracy=round(accuracy, 4),
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1_score=round(f1, 4),
            )
            self.results.append(result)

            logger.info(
                f"Fold {fold}: train={len(train_data)}, test={len(test_data)}, "
                f"accuracy={accuracy:.4f}, f1={f1:.4f}"
            )

        # 彙總結果
        if not self.results:
            return {"error": "No valid folds"}

        avg_accuracy = np.mean([r.accuracy for r in self.results])
        avg_precision = np.mean([r.precision for r in self.results])
        avg_recall = np.mean([r.recall for r in self.results])
        avg_f1 = np.mean([r.f1_score for r in self.results])

        std_accuracy = np.std([r.accuracy for r in self.results])

        return {
            "n_folds": len(self.results),
            "validation_method": validation_method,
            "avg_accuracy": round(float(avg_accuracy), 4),
            "std_accuracy": round(float(std_accuracy), 4),
            "avg_precision": round(float(avg_precision), 4),
            "avg_recall": round(float(avg_recall), 4),
            "avg_f1": round(float(avg_f1), 4),
            "fold_results": [
                {
                    "fold": r.fold,
                    "train_period": f"{r.train_start} to {r.train_end}",
                    "test_period": f"{r.test_start} to {r.test_end}",
                    "train_size": r.train_size,
                    "test_size": r.test_size,
                    "accuracy": r.accuracy,
                    "f1_score": r.f1_score,
                }
                for r in self.results
            ],
        }

    def _prepare_data(
        self,
        data: List[Dict],
        feature_extractor: Any,
        label_field: str
    ) -> Tuple[List[List[float]], List[int]]:
        """準備訓練數據"""
        X = []
        y = []

        for d in data:
            label_value = d.get(label_field)
            if label_value is None:
                continue

            # 萃取特徵
            if feature_extractor:
                features = feature_extractor.extract_features(d)
                feature_vector = list(features.features.values())
            else:
                feature_vector = [
                    d.get("confidence", 50),
                    d.get("days_held", 0),
                ]

            X.append(feature_vector)
            y.append(1 if label_value > 0 else 0)

        return X, y


def validate_model_with_time_series(
    data: List[Dict],
    n_splits: int = 5,
    gap: int = 5,
    validation_method: str = "time_series"
) -> Dict[str, Any]:
    """
    使用時序驗證評估模型（便捷函數）

    Args:
        data: 訓練數據
        n_splits: 分割數
        gap: 間隔天數
        validation_method: 驗證方法

    Returns:
        評估結果
    """
    try:
        from xgboost import XGBClassifier
    except ImportError:
        return {"error": "XGBoost not installed"}

    try:
        from .ml_feature_engine import get_feature_engine
        feature_extractor = get_feature_engine()
    except ImportError:
        feature_extractor = None

    validator = TimeSeriesValidator(n_splits=n_splits, gap=gap)
    evaluator = ModelEvaluator(validator)

    model_params = {
        "n_estimators": 100,
        "max_depth": 3,
        "learning_rate": 0.1,
        "random_state": 42,
        "use_label_encoder": False,
        "eval_metric": "logloss",
    }

    return evaluator.evaluate_time_series(
        model_class=XGBClassifier,
        model_params=model_params,
        data=data,
        feature_extractor=feature_extractor,
        validation_method=validation_method,
    )
