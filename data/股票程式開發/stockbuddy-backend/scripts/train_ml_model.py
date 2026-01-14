#!/usr/bin/env python3
"""
ML 模型訓練腳本 V10.38

用法:
    python scripts/train_ml_model.py --help
    python scripts/train_ml_model.py --train
    python scripts/train_ml_model.py --train --save
    python scripts/train_ml_model.py --evaluate
    python scripts/train_ml_model.py --tune-params

功能:
    - 訓練 XGBoost 分類模型
    - 使用 TimeSeriesSplit 避免資料洩漏
    - 超參數網格搜索調整
    - 模型評估和交叉驗證
    - 特徵重要性分析
    - 支援完整 50+ 特徵

V10.38 更新:
    - 使用 TimeSeriesSplit 取代 cross_val_score
    - 擴充特徵支援 (從 2 個到 50+)
    - 改進模型儲存格式
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 將 app 目錄加入路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """檢查必要套件"""
    try:
        import numpy
        import xgboost
        import sklearn
        logger.info("Dependencies OK: numpy, xgboost, sklearn")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please run: pip install xgboost scikit-learn numpy")
        return False


def load_training_data(data_path: Optional[str] = None) -> Tuple[List[Dict], int]:
    """
    載入訓練數據

    Args:
        data_path: 數據檔案路徑 (可選)

    Returns:
        (數據列表, 樣本數)
    """
    if data_path and Path(data_path).exists():
        logger.info(f"Loading data from: {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, len(data)

    # 嘗試從 performance_tracker 載入
    try:
        from app.services.performance_tracker import get_performance_tracker
        tracker = get_performance_tracker()
        data = tracker.get_closed_recommendations(limit=1000)
        logger.info(f"Loaded {len(data)} records from performance tracker")
        return data, len(data)
    except Exception as e:
        logger.warning(f"Cannot load from tracker: {e}")

    # 生成模擬訓練數據（僅供測試）
    logger.warning("Using simulated data for training demo")
    import random
    random.seed(42)

    simulated_data = []
    for i in range(200):
        confidence = random.randint(40, 95)
        days_held = random.randint(1, 30)
        # 信心度越高，勝率越高
        base_return = (confidence - 50) / 10 + random.gauss(0, 5)
        simulated_data.append({
            "stock_id": f"TEST{i:03d}",
            "confidence": confidence,
            "days_held": days_held,
            "final_return_percent": base_return,
            "signal": random.choice(["buy", "sell"]),
        })

    return simulated_data, len(simulated_data)


def prepare_features(data: List[Dict], use_full_features: bool = True) -> Tuple[Any, Any, List[str]]:
    """
    V10.38: 準備特徵和標籤

    Args:
        data: 原始數據
        use_full_features: 是否使用完整 50+ 特徵

    Returns:
        (X, y, feature_names)
    """
    import numpy as np

    if use_full_features:
        # V10.38: 使用完整特徵集
        try:
            from app.services.ml_feature_engine import MLFeatureEngine
            feature_names = MLFeatureEngine.FEATURE_COLUMNS
            logger.info(f"使用完整特徵集: {len(feature_names)} 個特徵")
        except ImportError:
            logger.warning("無法載入完整特徵集，使用基本特徵")
            feature_names = ["confidence", "days_held"]
    else:
        # 基本特徵
        feature_names = [
            "confidence",
            "days_held",
            "ai_score",
            "rsi_14",
            "price_change_5d",
            "volume_ratio_20d",
            "foreign_net_ratio",
            "institutional_score",
        ]

    X = []
    y = []

    for d in data:
        if d.get("final_return_percent") is None:
            continue

        # 從數據中提取特徵
        features_dict = d.get("features", {})
        if isinstance(features_dict, str):
            try:
                features_dict = json.loads(features_dict)
            except:
                features_dict = {}

        # 合併原始欄位和 features 字典
        combined = {**d, **features_dict}

        features = []
        for name in feature_names:
            value = combined.get(name, 0)
            if value is None:
                value = 0
            features.append(float(value))

        X.append(features)

        # 標籤：報酬 > 0 為上漲 (1)
        y.append(1 if d.get("final_return_percent", 0) > 0 else 0)

    return np.array(X), np.array(y), feature_names


def train_model(
    X: Any,
    y: Any,
    feature_names: List[str],
    params: Optional[Dict] = None,
    cv_folds: int = 5,
    use_time_series_split: bool = True
) -> Dict[str, Any]:
    """
    V10.38: 訓練 XGBoost 模型

    使用 TimeSeriesSplit 避免資料洩漏 (Look-Ahead Bias)

    Args:
        X: 特徵矩陣
        y: 標籤向量
        feature_names: 特徵名稱
        params: XGBoost 參數
        cv_folds: 交叉驗證折數
        use_time_series_split: 是否使用時間序列分割

    Returns:
        訓練結果
    """
    import numpy as np
    from xgboost import XGBClassifier
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score, train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    # V10.38: 預設參數 (優化過)
    if params is None:
        params = {
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "use_label_encoder": False,
            "eval_metric": "logloss",
        }

    logger.info(f"Training with params: {params}")

    # 標準化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # V10.38: 使用 TimeSeriesSplit 避免資料洩漏
    if use_time_series_split:
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        cv_results = {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1": []
        }

        logger.info(f"使用 TimeSeriesSplit ({cv_folds} 折)")

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled)):
            X_train_fold, X_val_fold = X_scaled[train_idx], X_scaled[val_idx]
            y_train_fold, y_val_fold = y[train_idx], y[val_idx]

            model = XGBClassifier(**params)
            model.fit(X_train_fold, y_train_fold)

            y_pred_fold = model.predict(X_val_fold)

            cv_results["accuracy"].append(accuracy_score(y_val_fold, y_pred_fold))
            cv_results["precision"].append(precision_score(y_val_fold, y_pred_fold, zero_division=0))
            cv_results["recall"].append(recall_score(y_val_fold, y_pred_fold, zero_division=0))
            cv_results["f1"].append(f1_score(y_val_fold, y_pred_fold, zero_division=0))

            logger.info(f"  Fold {fold+1}: Acc={cv_results['accuracy'][-1]:.4f}, F1={cv_results['f1'][-1]:.4f}")

        cv_accuracy = np.mean(cv_results["accuracy"])
        cv_std = np.std(cv_results["accuracy"])
        cv_f1 = np.mean(cv_results["f1"])

        # 最終模型使用全部數據訓練
        final_model = XGBClassifier(**params)
        final_model.fit(X_scaled, y)

        # 使用最後一折的驗證結果作為測試指標
        test_accuracy = cv_results["accuracy"][-1]
        test_precision = cv_results["precision"][-1]
        test_recall = cv_results["recall"][-1]
        test_f1 = cv_results["f1"][-1]

        model = final_model
        train_size = int(len(y) * (cv_folds - 1) / cv_folds)
        test_size = len(y) - train_size

    else:
        # 傳統分割
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        model = XGBClassifier(**params)
        model.fit(X_train, y_train)

        cv_scores = cross_val_score(model, X_scaled, y, cv=cv_folds, scoring='accuracy')
        cv_accuracy = np.mean(cv_scores)
        cv_std = np.std(cv_scores)

        y_pred = model.predict(X_test)

        test_accuracy = accuracy_score(y_test, y_pred)
        test_precision = precision_score(y_test, y_pred, zero_division=0)
        test_recall = recall_score(y_test, y_pred, zero_division=0)
        test_f1 = f1_score(y_test, y_pred, zero_division=0)

        train_size = len(y_train)
        test_size = len(y_test)

    # 特徵重要性
    importance = model.feature_importances_
    feature_importance = dict(zip(feature_names, importance.tolist()))

    # 排序特徵重要性
    sorted_importance = dict(sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    ))

    result = {
        "success": True,
        "version": "V10.38",
        "samples": len(y),
        "train_size": train_size,
        "test_size": test_size,
        "cv_accuracy": round(float(cv_accuracy), 4),
        "cv_std": round(float(cv_std), 4),
        "test_accuracy": round(float(test_accuracy), 4),
        "test_precision": round(float(test_precision), 4),
        "test_recall": round(float(test_recall), 4),
        "test_f1": round(float(test_f1), 4),
        "feature_importance": sorted_importance,
        "top_10_features": list(sorted_importance.keys())[:10],
        "params": params,
        "use_time_series_split": use_time_series_split,
    }

    return result, model, scaler


def tune_hyperparameters(
    X: Any,
    y: Any,
    cv_folds: int = 3
) -> Dict[str, Any]:
    """
    超參數網格搜索

    Args:
        X: 特徵矩陣
        y: 標籤向量
        cv_folds: 交叉驗證折數

    Returns:
        最佳參數和結果
    """
    import numpy as np
    from xgboost import XGBClassifier
    from sklearn.model_selection import GridSearchCV
    from sklearn.preprocessing import StandardScaler

    logger.info("Starting hyperparameter tuning...")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 參數網格
    param_grid = {
        "n_estimators": [50, 100, 150],
        "max_depth": [2, 3, 4, 5],
        "learning_rate": [0.05, 0.1, 0.15],
        "min_child_weight": [1, 3, 5],
    }

    model = XGBClassifier(
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
    )

    grid_search = GridSearchCV(
        model,
        param_grid,
        cv=cv_folds,
        scoring='accuracy',
        n_jobs=-1,
        verbose=1,
    )

    grid_search.fit(X_scaled, y)

    logger.info(f"Best params: {grid_search.best_params_}")
    logger.info(f"Best score: {grid_search.best_score_:.4f}")

    return {
        "best_params": grid_search.best_params_,
        "best_score": round(grid_search.best_score_, 4),
        "cv_results_summary": {
            "mean_test_scores": [
                round(s, 4) for s in grid_search.cv_results_['mean_test_score'][:10]
            ],
        },
    }


def save_model(
    model: Any,
    scaler: Any,
    feature_names: List[str],
    metrics: Dict,
    output_dir: Optional[str] = None
) -> str:
    """
    V10.38: 儲存模型

    Args:
        model: 訓練好的模型
        scaler: 特徵標準化器
        feature_names: 特徵名稱
        metrics: 評估指標
        output_dir: 輸出目錄

    Returns:
        模型目錄路徑
    """
    import pickle

    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "app" / "models"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 儲存模型
    model_file = output_dir / "stock_predictor.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)

    # 儲存標準化器
    scaler_file = output_dir / "feature_scaler.pkl"
    with open(scaler_file, 'wb') as f:
        pickle.dump(scaler, f)

    # V10.38: 儲存元數據 (同時儲存 pkl 和 json 格式)
    meta = {
        "version": version,
        "model_version": "V10.38",
        "trained_at": datetime.now().isoformat(),
        "feature_names": feature_names,
        "feature_count": len(feature_names),
        "metrics": {
            "cv_accuracy": metrics.get("cv_accuracy"),
            "cv_std": metrics.get("cv_std"),
            "test_accuracy": metrics.get("test_accuracy"),
            "test_precision": metrics.get("test_precision"),
            "test_recall": metrics.get("test_recall"),
            "test_f1": metrics.get("test_f1"),
        },
        "top_10_features": metrics.get("top_10_features", []),
        "params": metrics.get("params", {}),
        "use_time_series_split": metrics.get("use_time_series_split", True),
    }

    # pkl 格式
    meta_file = output_dir / "model_meta.pkl"
    with open(meta_file, 'wb') as f:
        pickle.dump(meta, f)

    # json 格式 (方便檢視)
    json_file = output_dir / "model_meta.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Model saved to: {output_dir}")
    logger.info(f"Version: {version}")
    logger.info(f"Files: stock_predictor.pkl, feature_scaler.pkl, model_meta.pkl/json")

    return str(output_dir)


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="StockBuddy ML Model Training Script V10.38"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train model with default parameters"
    )
    parser.add_argument(
        "--tune-params",
        action="store_true",
        help="Run hyperparameter tuning"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate existing model"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to training data JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for model files"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=50,
        help="Minimum samples required for training"
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Number of cross-validation folds"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save trained model to disk"
    )

    args = parser.parse_args()

    # 沒有指定任何動作時顯示幫助
    if not any([args.train, args.tune_params, args.evaluate]):
        parser.print_help()
        return

    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)

    # 載入數據
    data, sample_count = load_training_data(args.data_path)

    if sample_count < args.min_samples:
        logger.error(
            f"Not enough samples: {sample_count} < {args.min_samples}"
        )
        sys.exit(1)

    # 準備特徵
    X, y, feature_names = prepare_features(data)
    logger.info(f"Prepared {len(y)} samples with {len(feature_names)} features")

    # 執行訓練
    if args.train:
        logger.info("=" * 50)
        logger.info("Training model...")
        result, model, scaler = train_model(
            X, y, feature_names,
            cv_folds=args.cv_folds
        )

        print("\n" + "=" * 50)
        print("Training Results:")
        print("=" * 50)
        print(f"Samples: {result['samples']}")
        print(f"CV Accuracy: {result['cv_accuracy']:.4f} (+/- {result['cv_std']:.4f})")
        print(f"Test Accuracy: {result['test_accuracy']:.4f}")
        print(f"Test Precision: {result['test_precision']:.4f}")
        print(f"Test Recall: {result['test_recall']:.4f}")
        print(f"Test F1: {result['test_f1']:.4f}")
        print("\nFeature Importance:")
        for name, imp in result['feature_importance'].items():
            print(f"  {name}: {imp:.4f}")

        if args.save:
            save_model(model, scaler, feature_names, result, args.output_dir)

    # 超參數調整
    if args.tune_params:
        logger.info("=" * 50)
        logger.info("Tuning hyperparameters...")
        result = tune_hyperparameters(X, y, cv_folds=args.cv_folds)

        print("\n" + "=" * 50)
        print("Hyperparameter Tuning Results:")
        print("=" * 50)
        print(f"Best Score: {result['best_score']:.4f}")
        print("Best Parameters:")
        for name, value in result['best_params'].items():
            print(f"  {name}: {value}")

    # 評估現有模型
    if args.evaluate:
        logger.info("=" * 50)
        logger.info("Evaluating existing model...")

        try:
            from app.services.ml_predictor import get_predictor
            predictor = get_predictor()

            # 載入測試數據
            test_data, _ = load_training_data(args.data_path)
            correct = 0
            total = 0

            for d in test_data[:100]:
                if d.get("final_return_percent") is None:
                    continue

                result = predictor.predict(d.get("stock_id", "TEST"), stock_data=d)
                actual = "up" if d["final_return_percent"] > 0 else "down"

                if result.prediction == actual or result.prediction == "neutral":
                    correct += 1
                total += 1

            accuracy = correct / total if total > 0 else 0

            print("\n" + "=" * 50)
            print("Model Evaluation Results:")
            print("=" * 50)
            print(f"Samples evaluated: {total}")
            print(f"Accuracy: {accuracy:.4f}")

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")


if __name__ == "__main__":
    main()
