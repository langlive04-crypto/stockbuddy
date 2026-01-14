"""
V10.41: ML 訓練管理器

統一管理 ML 訓練、版本控制、數據累積

功能：
- 訓練數據管理：保存/載入訓練樣本
- 模型版本管理：保存/載入/回滾版本
- 訓練策略：完整訓練/增量訓練/混合訓練
- 經驗回放：防止災難性遺忘
"""

import os
import json
import shutil
import logging
import pickle
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# 路徑配置
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
CURRENT_DIR = os.path.join(MODELS_DIR, "current")
VERSIONS_DIR = os.path.join(MODELS_DIR, "versions")
TRAINING_DATA_DIR = os.path.join(MODELS_DIR, "training_data")


class MLTrainingManager:
    """
    ML 訓練管理器 - 統一管理訓練、版本、數據

    使用方式：
        manager = get_training_manager()

        # 保存訓練樣本
        manager.save_training_samples(X, y, features_list, metadata)

        # 保存模型版本
        manager.save_model_version(model, scaler, metrics, config)

        # 增量訓練
        manager.incremental_train(new_X, new_y)
    """

    def __init__(self):
        self._ensure_directories()

    def _ensure_directories(self):
        """確保所有必要目錄存在"""
        for dir_path in [CURRENT_DIR, VERSIONS_DIR, TRAINING_DATA_DIR]:
            os.makedirs(dir_path, exist_ok=True)

    # ===== 訓練數據管理 =====

    def save_training_samples(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        保存訓練樣本到資料庫

        Args:
            X: 特徵矩陣 (n_samples, n_features)
            y: 標籤向量 (n_samples,)
            feature_names: 特徵名稱列表
            metadata: 元數據 {stock_ids, dates, returns, source, quality_scores}

        Returns:
            保存結果統計
        """
        from app.database import SessionLocal, TrainingSample

        db = SessionLocal()
        saved_count = 0
        skipped_count = 0

        try:
            stock_ids = metadata.get("stock_ids", [])
            dates = metadata.get("dates", [])
            returns = metadata.get("returns", [])
            source = metadata.get("source", "historical")
            quality_scores = metadata.get("quality_scores", [])
            predict_days = metadata.get("predict_days", 5)

            for i in range(len(X)):
                # 檢查是否已存在相同的樣本
                stock_id = stock_ids[i] if i < len(stock_ids) else f"unknown_{i}"
                sample_date = dates[i] if i < len(dates) else date.today()

                # 轉換日期格式
                if isinstance(sample_date, str):
                    sample_date = datetime.strptime(sample_date, "%Y-%m-%d").date()
                elif isinstance(sample_date, datetime):
                    sample_date = sample_date.date()

                # 檢查重複
                existing = db.query(TrainingSample).filter(
                    TrainingSample.stock_id == stock_id,
                    TrainingSample.sample_date == sample_date,
                    TrainingSample.source == source
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                # 建立特徵字典
                features_dict = {
                    name: float(X[i, j]) if not np.isnan(X[i, j]) else None
                    for j, name in enumerate(feature_names)
                }

                # 建立樣本記錄
                sample = TrainingSample(
                    stock_id=stock_id,
                    sample_date=sample_date,
                    features=features_dict,
                    feature_count=len(feature_names),
                    label=int(y[i]),
                    actual_return=float(returns[i]) if i < len(returns) else None,
                    source=source,
                    quality_score=float(quality_scores[i]) if i < len(quality_scores) else 0.6,
                    predict_days=predict_days,
                )

                db.add(sample)
                saved_count += 1

                # 每 1000 筆 commit 一次
                if saved_count % 1000 == 0:
                    db.commit()

            db.commit()

            logger.info(f"[MLManager] 保存訓練樣本: {saved_count} 筆, 跳過: {skipped_count} 筆")

            return {
                "success": True,
                "saved": saved_count,
                "skipped": skipped_count,
                "total": len(X),
            }

        except Exception as e:
            db.rollback()
            logger.error(f"[MLManager] 保存訓練樣本失敗: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def load_training_samples(
        self,
        sources: Optional[List[str]] = None,
        min_quality: float = 0.6,
        limit: Optional[int] = None,
        random_sample: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        從資料庫載入訓練樣本

        Args:
            sources: 數據來源 ["historical", "performance"]，None 表示全部
            min_quality: 最低品質分數
            limit: 最大樣本數
            random_sample: 是否隨機抽樣

        Returns:
            (X, y, feature_names)
        """
        from app.database import SessionLocal, TrainingSample

        db = SessionLocal()

        try:
            query = db.query(TrainingSample).filter(
                TrainingSample.quality_score >= min_quality
            )

            if sources:
                query = query.filter(TrainingSample.source.in_(sources))

            if random_sample and limit:
                # SQLite 不支援 ORDER BY RANDOM() 效能好的實現
                # 先取全部 ID，再隨機選擇
                all_ids = [s.id for s in query.all()]
                if len(all_ids) > limit:
                    import random
                    selected_ids = random.sample(all_ids, limit)
                    query = db.query(TrainingSample).filter(
                        TrainingSample.id.in_(selected_ids)
                    )
            elif limit:
                query = query.limit(limit)

            samples = query.all()

            if not samples:
                return np.array([]), np.array([]), []

            # 取得特徵名稱 (從第一個樣本)
            feature_names = list(samples[0].features.keys())

            # 建構矩陣
            X = []
            y = []

            for sample in samples:
                feature_vector = [
                    sample.features.get(name, 0.0) or 0.0
                    for name in feature_names
                ]
                X.append(feature_vector)
                y.append(sample.label)

            logger.info(f"[MLManager] 載入訓練樣本: {len(samples)} 筆")

            return np.array(X), np.array(y), feature_names

        finally:
            db.close()

    def get_training_stats(self) -> Dict[str, Any]:
        """取得訓練數據統計"""
        from app.database import SessionLocal, TrainingSample

        db = SessionLocal()

        try:
            total = db.query(TrainingSample).count()
            historical = db.query(TrainingSample).filter(
                TrainingSample.source == "historical"
            ).count()
            performance = db.query(TrainingSample).filter(
                TrainingSample.source == "performance"
            ).count()

            # 品質分布
            high_quality = db.query(TrainingSample).filter(
                TrainingSample.quality_score >= 0.8
            ).count()
            medium_quality = db.query(TrainingSample).filter(
                TrainingSample.quality_score >= 0.6,
                TrainingSample.quality_score < 0.8
            ).count()

            # 類別分布
            positive = db.query(TrainingSample).filter(
                TrainingSample.label == 1
            ).count()
            negative = db.query(TrainingSample).filter(
                TrainingSample.label == 0
            ).count()

            return {
                "total_samples": total,
                "by_source": {
                    "historical": historical,
                    "performance": performance,
                },
                "by_quality": {
                    "high": high_quality,
                    "medium": medium_quality,
                },
                "by_label": {
                    "positive": positive,
                    "negative": negative,
                }
            }
        finally:
            db.close()

    # ===== 模型版本管理 =====

    def save_model_version(
        self,
        model,
        scaler,
        metrics: Dict[str, float],
        config: Dict[str, Any],
        set_as_current: bool = True,
    ) -> Dict[str, Any]:
        """
        保存新的模型版本

        Args:
            model: 訓練好的模型 (XGBClassifier)
            scaler: 特徵縮放器 (StandardScaler)
            metrics: 性能指標 {accuracy, f1, precision, recall}
            config: 訓練配置 {training_method, samples_count, predict_days, ...}
            set_as_current: 是否設為當前版本

        Returns:
            版本資訊
        """
        from app.database import SessionLocal, ModelVersion, TrainingHistory

        # 生成版本號
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        method_short = config.get("training_method", "full")[:3]
        version = f"v{timestamp}_{method_short}"

        # 創建版本目錄
        version_dir = os.path.join(VERSIONS_DIR, version)
        os.makedirs(version_dir, exist_ok=True)

        # 保存模型文件
        model_path = os.path.join(version_dir, "model.pkl")
        scaler_path = os.path.join(version_dir, "scaler.pkl")
        meta_path = os.path.join(version_dir, "meta.json")

        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        with open(scaler_path, "wb") as f:
            pickle.dump(scaler, f)

        meta = {
            "version": version,
            "created_at": datetime.now().isoformat(),
            "metrics": metrics,
            "config": config,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 保存到資料庫
        db = SessionLocal()

        try:
            # 如果設為當前版本，先取消其他版本的 is_current
            if set_as_current:
                db.query(ModelVersion).filter(
                    ModelVersion.is_current == True
                ).update({"is_current": False})

            # 建立版本記錄
            model_version = ModelVersion(
                version=version,
                training_method=config.get("training_method", "full"),
                samples_count=config.get("samples_count", 0),
                feature_count=config.get("feature_count", 55),
                predict_days=config.get("predict_days", 5),
                cv_accuracy=metrics.get("cv_accuracy"),
                test_accuracy=metrics.get("accuracy", 0),
                test_f1=metrics.get("f1", 0),
                test_precision=metrics.get("precision"),
                test_recall=metrics.get("recall"),
                class_distribution=config.get("class_distribution"),
                model_path=version_dir,
                is_current=set_as_current,
                base_version=config.get("base_version"),
            )
            db.add(model_version)

            # 建立訓練歷史
            training_history = TrainingHistory(
                version=version,
                training_type=config.get("training_method", "full"),
                base_version=config.get("base_version"),
                data_sources=config.get("data_sources", ["historical"]),
                stock_count=config.get("stock_count"),
                date_range=config.get("date_range"),
                total_samples=config.get("samples_count", 0),
                samples_added=config.get("samples_added"),
                high_quality_samples=config.get("high_quality_samples"),
                rejected_samples=config.get("rejected_samples"),
                improvement=config.get("improvement"),
                training_duration=config.get("training_duration"),
                notes=config.get("notes"),
            )
            db.add(training_history)

            db.commit()

            # 如果設為當前版本，複製到 current 目錄
            if set_as_current:
                self._copy_to_current(version_dir)

            logger.info(f"[MLManager] 模型版本保存成功: {version}")

            return {
                "success": True,
                "version": version,
                "path": version_dir,
                "is_current": set_as_current,
                "metrics": metrics,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"[MLManager] 保存模型版本失敗: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def _copy_to_current(self, version_dir: str):
        """複製版本到 current 目錄"""
        # 清空 current 目錄
        for f in os.listdir(CURRENT_DIR):
            path = os.path.join(CURRENT_DIR, f)
            if os.path.isfile(path):
                os.remove(path)

        # 複製文件
        for f in ["model.pkl", "scaler.pkl", "meta.json"]:
            src = os.path.join(version_dir, f)
            dst = os.path.join(CURRENT_DIR, f)
            if os.path.exists(src):
                shutil.copy2(src, dst)

    def list_versions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """列出所有模型版本"""
        from app.database import SessionLocal, ModelVersion

        db = SessionLocal()

        try:
            versions = db.query(ModelVersion).order_by(
                ModelVersion.created_at.desc()
            ).limit(limit).all()

            return [
                {
                    "version": v.version,
                    "training_method": v.training_method,
                    "samples_count": v.samples_count,
                    "test_accuracy": v.test_accuracy,
                    "test_f1": v.test_f1,
                    "is_current": v.is_current,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ]
        finally:
            db.close()

    def load_version(self, version: str) -> Tuple[Any, Any, Dict]:
        """載入指定版本的模型"""
        from app.database import SessionLocal, ModelVersion

        db = SessionLocal()

        try:
            model_version = db.query(ModelVersion).filter(
                ModelVersion.version == version
            ).first()

            if not model_version:
                raise ValueError(f"版本不存在: {version}")

            version_dir = model_version.model_path

            # 載入模型
            model_path = os.path.join(version_dir, "model.pkl")
            scaler_path = os.path.join(version_dir, "scaler.pkl")
            meta_path = os.path.join(version_dir, "meta.json")

            with open(model_path, "rb") as f:
                model = pickle.load(f)

            with open(scaler_path, "rb") as f:
                scaler = pickle.load(f)

            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            return model, scaler, meta

        finally:
            db.close()

    def get_current_version(self) -> Optional[str]:
        """取得當前使用的版本"""
        from app.database import SessionLocal, ModelVersion

        db = SessionLocal()

        try:
            current = db.query(ModelVersion).filter(
                ModelVersion.is_current == True
            ).first()

            return current.version if current else None
        finally:
            db.close()

    def set_current_version(self, version: str) -> Dict[str, Any]:
        """設置當前使用版本"""
        from app.database import SessionLocal, ModelVersion

        db = SessionLocal()

        try:
            # 檢查版本是否存在
            target = db.query(ModelVersion).filter(
                ModelVersion.version == version
            ).first()

            if not target:
                return {"success": False, "error": f"版本不存在: {version}"}

            # 取消其他版本的 is_current
            db.query(ModelVersion).filter(
                ModelVersion.is_current == True
            ).update({"is_current": False})

            # 設置目標版本
            target.is_current = True
            db.commit()

            # 複製到 current 目錄
            self._copy_to_current(target.model_path)

            logger.info(f"[MLManager] 當前版本已切換到: {version}")

            return {"success": True, "version": version}

        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def compare_versions(
        self,
        version1: str,
        version2: str,
    ) -> Dict[str, Any]:
        """比較兩個版本的性能"""
        from app.database import SessionLocal, ModelVersion

        db = SessionLocal()

        try:
            v1 = db.query(ModelVersion).filter(ModelVersion.version == version1).first()
            v2 = db.query(ModelVersion).filter(ModelVersion.version == version2).first()

            if not v1 or not v2:
                return {"success": False, "error": "版本不存在"}

            return {
                "success": True,
                "comparison": {
                    "version1": {
                        "version": v1.version,
                        "accuracy": v1.test_accuracy,
                        "f1": v1.test_f1,
                        "samples": v1.samples_count,
                    },
                    "version2": {
                        "version": v2.version,
                        "accuracy": v2.test_accuracy,
                        "f1": v2.test_f1,
                        "samples": v2.samples_count,
                    },
                    "difference": {
                        "accuracy": v2.test_accuracy - v1.test_accuracy,
                        "f1": v2.test_f1 - v1.test_f1,
                        "samples": v2.samples_count - v1.samples_count,
                    }
                }
            }
        finally:
            db.close()

    # ===== 訓練策略 =====

    def sample_for_replay(
        self,
        size: int,
        sources: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        經驗回放：從歷史數據中隨機抽樣

        用於增量訓練時防止災難性遺忘
        """
        X, y, _ = self.load_training_samples(
            sources=sources,
            limit=size,
            random_sample=True,
        )
        return X, y


# 單例
_manager = None


def get_training_manager() -> MLTrainingManager:
    """取得訓練管理器單例"""
    global _manager
    if _manager is None:
        _manager = MLTrainingManager()
    return _manager
