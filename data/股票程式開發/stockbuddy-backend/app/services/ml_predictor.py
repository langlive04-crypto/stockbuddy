"""
ML 預測引擎 V10.41

提供股票走勢預測功能，支援 XGBoost 模型和規則引擎備案

V10.41 更新:
- 整合 MLTrainingManager 版本管理
- 新增增量學習 (incremental_train)
- 訓練樣本持久化到資料庫
- 支援經驗回放防止災難性遺忘
- 模型版本不再覆蓋，保留歷史

V10.40 更新:
- ModelTrainer 整合 ml_feature_engine 完整 55 特徵
- 新增 use_full_features 參數控制特徵模式
- 改進模型參數 (n_estimators=200, max_depth=5)
- 新增測試集評估 (test_accuracy, test_f1)
- 自動跳過低品質數據 (缺失 > 50%)

V10.38 更新:
- 支援完整 50+ 特徵
- 同時支援 pkl 和 json 格式的 metadata
- 改進模型載入邏輯
- 整合 ml_feature_engine 特徵萃取

功能：
- 使用 XGBoost 機器學習預測
- 規則引擎備案（無模型或數據不足時使用）
- 模型訓練與版本管理
- 增量學習與經驗累積 (V10.41)
"""

import os
import json
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# 設定日誌
logger = logging.getLogger(__name__)

# 模型存放路徑
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_FILE = MODEL_DIR / "stock_predictor.pkl"
SCALER_FILE = MODEL_DIR / "feature_scaler.pkl"
META_FILE = MODEL_DIR / "model_meta.pkl"
META_JSON_FILE = MODEL_DIR / "model_meta.json"


@dataclass
class PredictionResult:
    """預測結果"""
    stock_id: str
    prediction: str          # "up", "down", "neutral"
    probability: float       # 上漲機率 (0-1)
    confidence: str          # "high", "medium", "low"
    expected_return: Optional[float]  # 預期報酬率 (%)
    model_version: str       # 模型版本
    features_used: int       # 使用的特徵數量
    timestamp: str           # 預測時間


class MLPredictor:
    """
    ML 預測器

    支援 XGBoost 模型預測，並提供規則引擎備案
    """

    def __init__(self):
        self._model = None
        self._scaler = None
        self._meta = None
        self._model_loaded = False

    def _ensure_model_dir(self):
        """確保模型目錄存在"""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

    def _load_model(self) -> bool:
        """
        V10.38: 載入已訓練的模型

        支援 pkl 和 json 格式的 metadata
        """
        if self._model_loaded:
            return self._model is not None

        try:
            if MODEL_FILE.exists() and SCALER_FILE.exists():
                with open(MODEL_FILE, 'rb') as f:
                    self._model = pickle.load(f)
                with open(SCALER_FILE, 'rb') as f:
                    self._scaler = pickle.load(f)

                # V10.38: 優先讀取 JSON，其次 pkl
                if META_JSON_FILE.exists():
                    with open(META_JSON_FILE, 'r', encoding='utf-8') as f:
                        self._meta = json.load(f)
                    logger.info(f"[MLPredictor] 載入模型 (JSON metadata): {self._meta.get('version')}")
                elif META_FILE.exists():
                    with open(META_FILE, 'rb') as f:
                        self._meta = pickle.load(f)
                    logger.info(f"[MLPredictor] 載入模型 (PKL metadata): {self._meta.get('version')}")
                else:
                    self._meta = {"version": "unknown", "feature_names": []}

                self._model_loaded = True

                # 記錄模型資訊
                metrics = self._meta.get("metrics", {})
                logger.info(f"[MLPredictor] 模型版本: {self._meta.get('model_version', 'N/A')}")
                logger.info(f"[MLPredictor] 訓練時間: {self._meta.get('trained_at', 'N/A')}")
                logger.info(f"[MLPredictor] 特徵數量: {self._meta.get('feature_count', len(self._meta.get('feature_names', [])))}")
                logger.info(f"[MLPredictor] CV Accuracy: {metrics.get('cv_accuracy', 'N/A')}")
                logger.info(f"[MLPredictor] Test F1: {metrics.get('test_f1', 'N/A')}")

                return True

        except Exception as e:
            logger.warning(f"[MLPredictor] 載入模型失敗: {e}")

        self._model_loaded = True  # 標記已嘗試載入
        return False

    def _get_model_version(self) -> str:
        """取得模型版本"""
        if self._meta and "version" in self._meta:
            return self._meta["version"]
        return "rule_based_v1"

    def predict(
        self,
        stock_id: str,
        features: Optional[Dict[str, float]] = None,
        stock_data: Optional[Dict] = None
    ) -> PredictionResult:
        """
        預測股票走勢

        Args:
            stock_id: 股票代碼
            features: 特徵字典 (若已計算)
            stock_data: 原始股票數據 (若無特徵則從此計算)

        Returns:
            PredictionResult 預測結果
        """
        timestamp = datetime.now().isoformat()

        # 嘗試載入模型
        has_model = self._load_model()

        # 決定使用 ML 模型還是規則引擎
        if has_model and features is not None:
            return self._ml_prediction(stock_id, features, timestamp)
        else:
            return self._rule_based_prediction(stock_id, stock_data, timestamp)

    def _ml_prediction(
        self,
        stock_id: str,
        features: Dict[str, float],
        timestamp: str
    ) -> PredictionResult:
        """
        V10.38: 使用 ML 模型預測

        Args:
            stock_id: 股票代碼
            features: 特徵字典
            timestamp: 預測時間

        Returns:
            PredictionResult
        """
        try:
            # 準備特徵向量
            feature_names = self._meta.get("feature_names", [])

            # V10.38: 確保特徵順序正確
            feature_vector = []
            missing_features = []
            for name in feature_names:
                value = features.get(name, 0)
                if value is None:
                    value = 0
                    missing_features.append(name)
                feature_vector.append(float(value))

            if missing_features and len(missing_features) <= 5:
                logger.debug(f"[MLPredictor] 缺少特徵: {missing_features}")

            # 標準化
            if self._scaler:
                feature_vector = self._scaler.transform([feature_vector])[0]

            # 預測
            prob = self._model.predict_proba([feature_vector])[0]

            # 取得上漲機率 (假設 class 1 是上漲)
            up_prob = float(prob[1]) if len(prob) > 1 else float(prob[0])

            # 邊界處理
            up_prob = max(0.0, min(1.0, up_prob))

            # 決定預測結果
            if up_prob > 0.6:
                prediction = "up"
            elif up_prob < 0.4:
                prediction = "down"
            else:
                prediction = "neutral"

            # 決定信心等級
            confidence = self._get_confidence(up_prob)

            # V10.38: 改進預期報酬率估算
            # 根據歷史數據調整 (假設平均報酬率約 5-10%)
            expected_return = round((up_prob - 0.5) * 15, 2)

            return PredictionResult(
                stock_id=stock_id,
                prediction=prediction,
                probability=round(up_prob, 4),
                confidence=confidence,
                expected_return=expected_return,
                model_version=self._get_model_version(),
                features_used=len(feature_names) - len(missing_features),
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"[MLPredictor] ML 預測失敗: {e}")
            # 降級到規則引擎
            return self._rule_based_prediction(stock_id, None, timestamp)

    def _rule_based_prediction(
        self,
        stock_id: str,
        stock_data: Optional[Dict],
        timestamp: str
    ) -> PredictionResult:
        """
        使用規則引擎預測

        基於技術指標和籌碼面的簡單規則進行預測

        Args:
            stock_id: 股票代碼
            stock_data: 股票數據
            timestamp: 預測時間

        Returns:
            PredictionResult
        """
        score = 50  # 基礎分數
        features_used = 0

        if stock_data:
            # 技術面規則
            # RSI
            rsi = stock_data.get("rsi", stock_data.get("rsi_14"))
            if rsi is not None:
                features_used += 1
                if rsi < 30:
                    score += 15  # 超賣，看漲
                elif rsi > 70:
                    score -= 15  # 超買，看跌
                elif rsi < 50:
                    score += 5
                else:
                    score -= 5

            # 價格相對於 MA
            price = stock_data.get("close", stock_data.get("price"))
            ma5 = stock_data.get("ma5")
            ma20 = stock_data.get("ma20")
            ma60 = stock_data.get("ma60")

            if price and ma5:
                features_used += 1
                if price > ma5:
                    score += 5
                else:
                    score -= 5

            if price and ma20:
                features_used += 1
                if price > ma20:
                    score += 8
                else:
                    score -= 8

            if price and ma60:
                features_used += 1
                if price > ma60:
                    score += 5
                else:
                    score -= 5

            # 均線排列
            if ma5 and ma20 and ma60:
                features_used += 1
                if ma5 > ma20 > ma60:
                    score += 10  # 多頭排列
                elif ma5 < ma20 < ma60:
                    score -= 10  # 空頭排列

            # 成交量
            volume = stock_data.get("volume")
            avg_volume = stock_data.get("avg_volume", stock_data.get("volume_ma20"))
            if volume and avg_volume and avg_volume > 0:
                features_used += 1
                volume_ratio = volume / avg_volume
                if volume_ratio > 1.5:
                    score += 5  # 量增
                elif volume_ratio < 0.5:
                    score -= 3  # 量縮

            # 籌碼面規則
            foreign_net = stock_data.get("foreign_net", stock_data.get("foreign_buy"))
            if foreign_net is not None:
                features_used += 1
                if foreign_net > 0:
                    score += 8
                else:
                    score -= 5

            trust_net = stock_data.get("trust_net", stock_data.get("trust_buy"))
            if trust_net is not None:
                features_used += 1
                if trust_net > 0:
                    score += 5
                else:
                    score -= 3

            # AI 評分 (若有)
            ai_score = stock_data.get("ai_score")
            if ai_score is not None:
                features_used += 1
                if ai_score >= 80:
                    score += 15
                elif ai_score >= 70:
                    score += 10
                elif ai_score >= 60:
                    score += 5
                elif ai_score < 50:
                    score -= 5

        # 限制分數範圍
        score = max(0, min(100, score))

        # 轉換為機率
        probability = score / 100

        # 決定預測結果
        if probability > 0.6:
            prediction = "up"
        elif probability < 0.4:
            prediction = "down"
        else:
            prediction = "neutral"

        # 決定信心等級
        confidence = self._get_confidence(probability)

        # 預期報酬率
        expected_return = round((probability - 0.5) * 20, 2)

        return PredictionResult(
            stock_id=stock_id,
            prediction=prediction,
            probability=round(probability, 4),
            confidence=confidence,
            expected_return=expected_return,
            model_version="rule_based_v1",
            features_used=features_used,
            timestamp=timestamp,
        )

    def _get_confidence(self, probability: float) -> str:
        """
        根據機率決定信心等級

        Args:
            probability: 預測機率

        Returns:
            信心等級字串
        """
        # 計算與中性 (0.5) 的距離
        distance = abs(probability - 0.5)

        if distance > 0.2:
            return "high"
        elif distance > 0.1:
            return "medium"
        else:
            return "low"

    def predict_batch(
        self,
        stocks: List[Dict]
    ) -> List[PredictionResult]:
        """
        批次預測多檔股票

        Args:
            stocks: 股票數據列表

        Returns:
            預測結果列表
        """
        results = []
        for stock in stocks:
            stock_id = stock.get("stock_id", stock.get("id", "unknown"))
            result = self.predict(stock_id, stock_data=stock)
            results.append(result)
        return results


class ModelTrainer:
    """
    模型訓練器 V10.40

    從歷史數據訓練 XGBoost 模型
    V10.40: 整合 ml_feature_engine 完整 55 特徵
    """

    @staticmethod
    def train_from_history(
        min_samples: int = 100,
        history_data: Optional[List[Dict]] = None,
        use_full_features: bool = True
    ) -> Dict[str, Any]:
        """
        V10.40: 從歷史數據訓練模型（支援完整 55 特徵）

        Args:
            min_samples: 最少樣本數
            history_data: 歷史數據 (若無則從追蹤器取得)
            use_full_features: 是否使用完整 55 特徵 (預設 True)

        Returns:
            訓練結果
        """
        try:
            # 延遲匯入，避免啟動時就需要這些套件
            import numpy as np

            try:
                from xgboost import XGBClassifier
                from sklearn.model_selection import cross_val_score, train_test_split
                from sklearn.preprocessing import StandardScaler
                from sklearn.metrics import f1_score, classification_report
            except ImportError as e:
                return {
                    "success": False,
                    "error": f"缺少必要套件: {e}. 請執行 pip install xgboost scikit-learn"
                }

            # V10.40: 導入特徵工程引擎
            feature_engine = None
            if use_full_features:
                try:
                    from .ml_feature_engine import get_feature_engine
                    feature_engine = get_feature_engine()
                    logger.info("[ModelTrainer] 使用完整 55 特徵訓練")
                except ImportError as e:
                    logger.warning(f"[ModelTrainer] 無法載入特徵引擎: {e}，降級為基礎特徵")
                    use_full_features = False

            # 取得歷史數據
            if history_data is None:
                from .performance_tracker import get_performance_tracker
                tracker = get_performance_tracker()
                history_data = tracker.get_closed_recommendations(limit=500)

            # 過濾有完整報酬數據的記錄
            valid_data = [
                d for d in history_data
                if d.get("final_return_percent") is not None
            ]

            if len(valid_data) < min_samples:
                return {
                    "success": False,
                    "error": f"數據不足，需要至少 {min_samples} 筆，目前只有 {len(valid_data)} 筆"
                }

            # V10.40: 準備特徵和標籤
            if use_full_features and feature_engine:
                # 使用完整 55 特徵
                feature_names = feature_engine.FEATURE_COLUMNS
                X = []
                y = []
                skipped = 0

                for d in valid_data:
                    try:
                        # 萃取完整特徵
                        feature_set = feature_engine.extract_features(d)
                        feature_vector = feature_engine.get_feature_vector(feature_set)

                        # 檢查特徵品質 (缺失不超過 50%)
                        if feature_set.missing_count <= len(feature_names) * 0.5:
                            X.append(feature_vector)
                            y.append(1 if d.get("final_return_percent", 0) > 0 else 0)
                        else:
                            skipped += 1
                    except Exception as e:
                        logger.debug(f"[ModelTrainer] 特徵萃取失敗: {e}")
                        skipped += 1

                if skipped > 0:
                    logger.info(f"[ModelTrainer] 跳過 {skipped} 筆低品質數據")

            else:
                # 基礎特徵模式
                feature_names = ["confidence", "days_held"]
                X = []
                y = []

                for d in valid_data:
                    features = [
                        d.get("confidence", 50),
                        d.get("days_held", 0),
                    ]
                    X.append(features)
                    y.append(1 if d.get("final_return_percent", 0) > 0 else 0)

            # 檢查數據量
            if len(X) < min_samples:
                return {
                    "success": False,
                    "error": f"有效數據不足，需要至少 {min_samples} 筆，目前只有 {len(X)} 筆"
                }

            X = np.array(X)
            y = np.array(y)

            logger.info(f"[ModelTrainer] 訓練數據: {len(X)} 筆, 特徵數: {len(feature_names)}")

            # 標準化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # V10.40: 分割訓練/測試集
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )

            # V10.40: 調整模型參數 (適應更多特徵)
            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )

            # 交叉驗證
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')

            # 完整訓練
            model.fit(X_train, y_train)

            # V10.40: 測試集評估
            y_pred = model.predict(X_test)
            test_accuracy = float(np.mean(y_pred == y_test))
            test_f1 = float(f1_score(y_test, y_pred, zero_division=0))

            logger.info(f"[ModelTrainer] 測試集準確率: {test_accuracy:.4f}, F1: {test_f1:.4f}")

            # 儲存模型
            MODEL_DIR.mkdir(parents=True, exist_ok=True)

            version = f"v{datetime.now().strftime('%Y%m%d')}"
            model_version = f"{version}_{'full' if use_full_features else 'basic'}_{len(feature_names)}f"

            with open(MODEL_FILE, 'wb') as f:
                pickle.dump(model, f)

            with open(SCALER_FILE, 'wb') as f:
                pickle.dump(scaler, f)

            # V10.40: 擴充 metadata
            meta = {
                "version": version,
                "model_version": model_version,
                "trained_at": datetime.now().isoformat(),
                "samples": len(X),
                "feature_count": len(feature_names),
                "feature_names": feature_names,
                "use_full_features": use_full_features,
                "metrics": {
                    "cv_accuracy": float(np.mean(cv_scores)),
                    "cv_std": float(np.std(cv_scores)),
                    "test_accuracy": test_accuracy,
                    "test_f1": test_f1,
                },
                "model_params": {
                    "n_estimators": 200,
                    "max_depth": 5,
                    "learning_rate": 0.05,
                },
            }

            # 同時儲存 pkl 和 json 格式
            with open(META_FILE, 'wb') as f:
                pickle.dump(meta, f)

            with open(META_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            logger.info(f"[ModelTrainer] 模型訓練完成: {model_version}")

            return {
                "success": True,
                "version": version,
                "model_version": model_version,
                "samples": len(X),
                "feature_count": len(feature_names),
                "use_full_features": use_full_features,
                "cv_accuracy": round(float(np.mean(cv_scores)), 4),
                "cv_std": round(float(np.std(cv_scores)), 4),
                "test_accuracy": round(test_accuracy, 4),
                "test_f1": round(test_f1, 4),
                "model_path": str(MODEL_DIR),
            }

        except Exception as e:
            logger.error(f"[ModelTrainer] 模型訓練失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    # V10.40: 歷史訓練專用特徵 (27 個，全部可從 Yahoo Finance 計算)
    HISTORICAL_FEATURES = [
        # 價格特徵 (9)
        "price_change_1d",      # 單日漲跌幅
        "price_change_5d",      # 5日漲跌幅
        "price_change_20d",     # 20日漲跌幅
        "price_vs_ma5",         # 價格相對 MA5
        "price_vs_ma20",        # 價格相對 MA20
        "price_vs_ma60",        # 價格相對 MA60
        "ma5_vs_ma20",          # MA5 相對 MA20
        "ma20_vs_ma60",         # MA20 相對 MA60
        "upper_shadow_ratio",   # 上影線比例

        # 動能指標 (6)
        "rsi_14",               # RSI(14)
        "rsi_position",         # RSI 位置 (超買/超賣)
        "macd",                 # MACD
        "macd_signal",          # MACD 信號線
        "macd_hist",            # MACD 柱狀
        "momentum_10d",         # 10日動能

        # 成交量 (5)
        "volume_ratio",         # 量比 (今量/20日均量)
        "volume_change_5d",     # 5日量能變化
        "volume_trend",         # 量能趨勢
        "price_volume_corr",    # 價量相關性
        "obv_trend",            # OBV 趨勢

        # 波動率 (5)
        "volatility_20d",       # 20日波動率
        "atr_ratio",            # ATR 比例
        "bb_position",          # 布林帶位置
        "bb_width",             # 布林帶寬度
        "high_low_range",       # 振幅

        # 趨勢 (2)
        "trend_strength",       # 趨勢強度
        "consecutive_days",     # 連漲/連跌天數
    ]

    @staticmethod
    def _extract_historical_features(hist, i: int) -> Optional[List[float]]:
        """
        V10.40: 從歷史數據提取特徵 (專用於 Yahoo Finance 數據)

        Args:
            hist: pandas DataFrame 歷史數據
            i: 當前索引

        Returns:
            特徵向量 (27 維) 或 None
        """
        import numpy as np

        try:
            row = hist.iloc[i]
            features = []

            # 基本數據
            close = row['Close']
            high = row['High']
            low = row['Low']
            open_price = row['Open']
            volume = row['Volume']

            # ===== 價格特徵 (9) =====

            # 單日漲跌幅
            prev_close = hist.iloc[i-1]['Close'] if i > 0 else close
            price_change_1d = (close - prev_close) / prev_close * 100 if prev_close > 0 else 0
            features.append(price_change_1d)

            # 5日漲跌幅
            price_5d_ago = hist.iloc[i-5]['Close'] if i >= 5 else close
            price_change_5d = (close - price_5d_ago) / price_5d_ago * 100 if price_5d_ago > 0 else 0
            features.append(price_change_5d)

            # 20日漲跌幅
            price_20d_ago = hist.iloc[i-20]['Close'] if i >= 20 else close
            price_change_20d = (close - price_20d_ago) / price_20d_ago * 100 if price_20d_ago > 0 else 0
            features.append(price_change_20d)

            # 價格相對均線
            ma5 = row['MA5'] if not np.isnan(row['MA5']) else close
            ma20 = row['MA20'] if not np.isnan(row['MA20']) else close
            ma60 = row['MA60'] if not np.isnan(row['MA60']) else close

            features.append((close / ma5 - 1) * 100 if ma5 > 0 else 0)   # price_vs_ma5
            features.append((close / ma20 - 1) * 100 if ma20 > 0 else 0) # price_vs_ma20
            features.append((close / ma60 - 1) * 100 if ma60 > 0 else 0) # price_vs_ma60
            features.append((ma5 / ma20 - 1) * 100 if ma20 > 0 else 0)   # ma5_vs_ma20
            features.append((ma20 / ma60 - 1) * 100 if ma60 > 0 else 0)  # ma20_vs_ma60

            # 上影線比例
            body = abs(close - open_price)
            upper_shadow = high - max(close, open_price)
            upper_shadow_ratio = upper_shadow / body * 100 if body > 0 else 0
            features.append(min(upper_shadow_ratio, 500))  # 限制極端值

            # ===== 動能指標 (6) =====

            # RSI
            rsi = row['RSI'] if not np.isnan(row['RSI']) else 50
            features.append(rsi)

            # RSI 位置 (超買=1, 正常=0, 超賣=-1)
            rsi_position = 1 if rsi > 70 else (-1 if rsi < 30 else 0)
            features.append(rsi_position)

            # MACD
            ema12 = hist['Close'].iloc[:i+1].ewm(span=12).mean().iloc[-1]
            ema26 = hist['Close'].iloc[:i+1].ewm(span=26).mean().iloc[-1]
            macd = ema12 - ema26
            macd_signal = hist['Close'].iloc[:i+1].ewm(span=12).mean().ewm(span=9).mean().iloc[-1] - \
                          hist['Close'].iloc[:i+1].ewm(span=26).mean().ewm(span=9).mean().iloc[-1]
            macd_hist = macd - macd_signal

            features.append(macd / close * 100 if close > 0 else 0)          # MACD (標準化)
            features.append(macd_signal / close * 100 if close > 0 else 0)   # MACD Signal
            features.append(macd_hist / close * 100 if close > 0 else 0)     # MACD Histogram

            # 10日動能
            price_10d_ago = hist.iloc[i-10]['Close'] if i >= 10 else close
            momentum_10d = (close - price_10d_ago) / price_10d_ago * 100 if price_10d_ago > 0 else 0
            features.append(momentum_10d)

            # ===== 成交量 (5) =====

            volume_ma20 = row['Volume_MA20'] if not np.isnan(row['Volume_MA20']) else volume

            # 量比
            volume_ratio = volume / volume_ma20 if volume_ma20 > 0 else 1
            features.append(min(volume_ratio, 10))  # 限制極端值

            # 5日量能變化
            vol_5d_ago = hist.iloc[i-5]['Volume'] if i >= 5 else volume
            volume_change_5d = (volume - vol_5d_ago) / vol_5d_ago * 100 if vol_5d_ago > 0 else 0
            features.append(np.clip(volume_change_5d, -200, 500))

            # 量能趨勢 (過去5天平均量 vs 過去20天平均量)
            vol_5d_avg = hist['Volume'].iloc[max(0,i-4):i+1].mean()
            vol_20d_avg = hist['Volume'].iloc[max(0,i-19):i+1].mean()
            volume_trend = (vol_5d_avg / vol_20d_avg - 1) * 100 if vol_20d_avg > 0 else 0
            features.append(np.clip(volume_trend, -100, 200))

            # 價量相關性 (過去20天)
            if i >= 20:
                price_series = hist['Close'].iloc[i-19:i+1].values
                vol_series = hist['Volume'].iloc[i-19:i+1].values
                if np.std(price_series) > 0 and np.std(vol_series) > 0:
                    corr = np.corrcoef(price_series, vol_series)[0, 1]
                    features.append(corr if not np.isnan(corr) else 0)
                else:
                    features.append(0)
            else:
                features.append(0)

            # OBV 趨勢
            obv_trend = 0
            if i >= 5:
                for j in range(i-4, i+1):
                    if hist.iloc[j]['Close'] > hist.iloc[j-1]['Close']:
                        obv_trend += 1
                    elif hist.iloc[j]['Close'] < hist.iloc[j-1]['Close']:
                        obv_trend -= 1
            features.append(obv_trend)

            # ===== 波動率 (5) =====

            # 20日波動率
            volatility = row['Volatility'] if not np.isnan(row['Volatility']) else 0
            features.append(volatility)

            # ATR 比例
            atr = hist['High'].iloc[max(0,i-13):i+1].max() - hist['Low'].iloc[max(0,i-13):i+1].min()
            atr_ratio = atr / close * 100 if close > 0 else 0
            features.append(atr_ratio)

            # 布林帶
            bb_std = hist['Close'].iloc[max(0,i-19):i+1].std()
            bb_upper = ma20 + 2 * bb_std
            bb_lower = ma20 - 2 * bb_std
            bb_width = (bb_upper - bb_lower) / ma20 * 100 if ma20 > 0 else 0
            bb_position = (close - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

            features.append(np.clip(bb_position, 0, 1))  # 布林帶位置 (0-1)
            features.append(bb_width)                     # 布林帶寬度

            # 振幅
            high_low_range = (high - low) / close * 100 if close > 0 else 0
            features.append(high_low_range)

            # ===== 趨勢 (2) =====

            # 趨勢強度 (ADX 簡化版)
            if ma5 > ma20 > ma60:
                trend_strength = 1  # 強上升趨勢
            elif ma5 < ma20 < ma60:
                trend_strength = -1  # 強下降趨勢
            else:
                trend_strength = 0  # 盤整
            features.append(trend_strength)

            # 連漲/連跌天數
            consecutive = 0
            for j in range(i, max(0, i-10), -1):
                if hist.iloc[j]['Close'] > hist.iloc[j-1]['Close']:
                    if consecutive >= 0:
                        consecutive += 1
                    else:
                        break
                elif hist.iloc[j]['Close'] < hist.iloc[j-1]['Close']:
                    if consecutive <= 0:
                        consecutive -= 1
                    else:
                        break
                else:
                    break
            features.append(consecutive)

            return features

        except Exception as e:
            logger.debug(f"[ModelTrainer] 特徵提取失敗: {e}")
            return None

    @staticmethod
    def train_from_historical(
        stock_ids: Optional[List[str]] = None,
        period: str = "1y",
        predict_days: int = 5,
        min_samples: int = 100,
    ) -> Dict[str, Any]:
        """
        V10.40: 從歷史股價數據訓練模型

        使用過去的股價數據自動生成訓練樣本，無需等待績效追蹤。
        使用專用的 27 維特徵集，100% 可從 Yahoo Finance 計算。

        Args:
            stock_ids: 股票代碼列表 (None 則使用預設熱門股)
            period: 歷史數據期間 ("6mo", "1y", "2y", "5y")
            predict_days: 預測天數 (標籤: N天後是否上漲)
            min_samples: 最少樣本數

        Returns:
            訓練結果
        """
        try:
            import numpy as np

            try:
                import yfinance as yf
                from xgboost import XGBClassifier
                from sklearn.model_selection import cross_val_score, train_test_split
                from sklearn.preprocessing import StandardScaler
                from sklearn.metrics import f1_score
            except ImportError as e:
                return {
                    "success": False,
                    "error": f"缺少必要套件: {e}. 請執行 pip install yfinance xgboost scikit-learn"
                }

            # 預設熱門台股
            if stock_ids is None:
                stock_ids = [
                    "2330", "2317", "2454", "2308", "2382",  # 電子
                    "2881", "2882", "2884", "2886", "2891",  # 金融
                    "1301", "1303", "1326", "2002", "2912",  # 傳產
                    "3008", "3034", "2357", "2379", "6505",  # 其他
                ]

            logger.info(f"[ModelTrainer] 從歷史數據訓練，股票數: {len(stock_ids)}, 期間: {period}")

            # 使用完整 55 特徵引擎 + 數據補齊器
            try:
                from .ml_feature_engine import get_feature_engine
                from .historical_data_enricher import get_enricher

                feature_engine = get_feature_engine()
                enricher = get_enricher()
            except ImportError as ie:
                return {"success": False, "error": f"無法載入模組: {ie}"}

            feature_names = feature_engine.FEATURE_COLUMNS
            logger.info(f"[ModelTrainer] 使用完整 {len(feature_names)} 特徵架構")

            # 預先載入大盤數據 (所有股票共用)
            market_hist = enricher.get_market_data(period)
            if market_hist is not None:
                logger.info(f"[ModelTrainer] 大盤數據載入: {len(market_hist)} 筆")

            X = []
            y = []
            processed_stocks = 0
            skipped_stocks = 0
            total_samples = 0
            quality_stats = {"high": 0, "medium": 0, "low": 0, "rejected": 0}

            for stock_id in stock_ids:
                try:
                    # 取得歷史數據
                    ticker = yf.Ticker(f"{stock_id}.TW")
                    hist = ticker.history(period=period)

                    if hist.empty or len(hist) < 60 + predict_days:
                        logger.debug(f"[ModelTrainer] {stock_id} 數據不足，跳過")
                        skipped_stocks += 1
                        continue

                    # 計算技術指標
                    hist['MA5'] = hist['Close'].rolling(5).mean()
                    hist['MA20'] = hist['Close'].rolling(20).mean()
                    hist['MA60'] = hist['Close'].rolling(60).mean()
                    hist['Volume_MA20'] = hist['Volume'].rolling(20).mean()

                    # RSI
                    delta = hist['Close'].diff()
                    gain = delta.where(delta > 0, 0).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss
                    hist['RSI'] = 100 - (100 / (1 + rs))

                    # 波動率
                    hist['Volatility'] = hist['Close'].rolling(20).std() / hist['Close'].rolling(20).mean() * 100

                    # 獲取基本面數據 (每檔股票查一次)
                    fundamental = enricher.get_fundamental_data(stock_id)

                    stock_samples = 0

                    # 生成訓練樣本（從第60天開始，到倒數第predict_days天）
                    for i in range(60, len(hist) - predict_days):
                        row = hist.iloc[i]
                        future_price = hist.iloc[i + predict_days]['Close']
                        current_price = row['Close']

                        # 標籤: N天後是否上漲
                        label = 1 if future_price > current_price else 0

                        # 使用數據補齊器準備完整數據
                        stock_data = enricher.enrich_stock_data(
                            stock_id=stock_id,
                            hist_row=row,
                            hist_df=hist,
                            row_index=i,
                            market_hist=market_hist,
                            fundamental=fundamental,
                        )

                        # 準備歷史數據
                        history_data = enricher.prepare_history_for_features(hist, i)

                        # 使用完整 55 特徵引擎萃取特徵
                        try:
                            feature_set = feature_engine.extract_features(stock_data, history=history_data)
                            missing_ratio = feature_set.missing_count / len(feature_names)

                            # 品質分級
                            if missing_ratio <= 0.2:
                                quality_stats["high"] += 1
                            elif missing_ratio <= 0.4:
                                quality_stats["medium"] += 1
                            elif missing_ratio <= 0.6:
                                quality_stats["low"] += 1
                            else:
                                quality_stats["rejected"] += 1
                                continue  # 超過 60% 缺失則跳過

                            feature_vector = feature_engine.get_feature_vector(feature_set)
                            X.append(feature_vector)
                            y.append(label)
                            stock_samples += 1

                        except Exception as fe:
                            logger.debug(f"[ModelTrainer] 特徵萃取失敗: {fe}")
                            continue

                    processed_stocks += 1
                    total_samples += stock_samples
                    if stock_samples > 0:
                        logger.info(f"[ModelTrainer] {stock_id} 完成: {stock_samples} 樣本，累計: {len(X)}")

                except Exception as e:
                    logger.warning(f"[ModelTrainer] {stock_id} 處理失敗: {e}")
                    skipped_stocks += 1
                    continue

            # 輸出品質統計
            logger.info(f"[ModelTrainer] 數據準備完成: {len(X)} 樣本, {processed_stocks} 股票成功, {skipped_stocks} 跳過")
            logger.info(f"[ModelTrainer] 品質分佈: 高品質={quality_stats['high']}, 中品質={quality_stats['medium']}, 低品質={quality_stats['low']}, 拒絕={quality_stats['rejected']}")

            if len(X) < min_samples:
                return {
                    "success": False,
                    "error": f"有效樣本不足，需要 {min_samples} 筆，目前只有 {len(X)} 筆",
                    "quality_stats": quality_stats,
                    "stocks_processed": processed_stocks,
                    "stocks_skipped": skipped_stocks,
                }

            X = np.array(X)
            y = np.array(y)

            # 檢查類別分佈
            up_ratio = np.mean(y)
            logger.info(f"[ModelTrainer] 類別分佈: 上漲 {up_ratio:.2%}, 下跌 {1-up_ratio:.2%}")

            # 標準化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # 分割訓練/測試集
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )

            # 訓練模型
            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )

            # 交叉驗證
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')

            # 完整訓練
            model.fit(X_train, y_train)

            # 測試集評估
            y_pred = model.predict(X_test)
            test_accuracy = float(np.mean(y_pred == y_test))
            test_f1 = float(f1_score(y_test, y_pred, zero_division=0))

            logger.info(f"[ModelTrainer] 測試集: accuracy={test_accuracy:.4f}, f1={test_f1:.4f}")

            # 計算品質比例
            total_quality = sum(quality_stats.values())
            quality_ratio = {
                "high": round(quality_stats["high"] / total_quality, 4) if total_quality > 0 else 0,
                "medium": round(quality_stats["medium"] / total_quality, 4) if total_quality > 0 else 0,
                "low": round(quality_stats["low"] / total_quality, 4) if total_quality > 0 else 0,
            }

            # V10.41: 使用 MLTrainingManager 進行版本管理
            try:
                from .ml_training_manager import get_training_manager
                manager = get_training_manager()

                # 準備訓練樣本的元數據 (用於保存到資料庫)
                sample_metadata = {
                    "stock_ids": stock_ids[:len(X)] if stock_ids else [],
                    "dates": [],  # 歷史訓練不追蹤具體日期
                    "returns": [],
                    "source": "historical",
                    "quality_scores": [
                        0.9 if i < quality_stats["high"] else
                        0.7 if i < quality_stats["high"] + quality_stats["medium"] else 0.5
                        for i in range(len(X))
                    ],
                    "predict_days": predict_days,
                }

                # 保存訓練樣本
                save_result = manager.save_training_samples(
                    X, y, feature_names, sample_metadata
                )
                logger.info(f"[ModelTrainer] 訓練樣本保存: {save_result}")

                # 使用版本管理保存模型
                metrics = {
                    "cv_accuracy": float(np.mean(cv_scores)),
                    "accuracy": test_accuracy,
                    "f1": test_f1,
                }

                config = {
                    "training_method": "full",  # 完整訓練
                    "samples_count": len(X),
                    "feature_count": len(feature_names),
                    "predict_days": predict_days,
                    "data_sources": ["historical"],
                    "stock_count": processed_stocks,
                    "high_quality_samples": quality_stats["high"],
                    "rejected_samples": quality_stats["rejected"],
                    "class_distribution": {"0": int(sum(y == 0)), "1": int(sum(y == 1))},
                }

                version_result = manager.save_model_version(
                    model, scaler, metrics, config, set_as_current=True
                )

                if version_result["success"]:
                    model_version = version_result["version"]
                    logger.info(f"[ModelTrainer] 模型版本保存成功: {model_version}")
                else:
                    logger.warning(f"[ModelTrainer] 版本管理失敗，使用舊方式保存")
                    raise Exception(version_result.get("error", "Unknown error"))

            except Exception as manager_error:
                logger.warning(f"[ModelTrainer] 版本管理失敗: {manager_error}，降級為傳統保存")

                # 降級: 使用舊的保存方式
                MODEL_DIR.mkdir(parents=True, exist_ok=True)

                version = f"v{datetime.now().strftime('%Y%m%d')}"
                model_version = f"{version}_hist_{len(stock_ids)}stocks_{predict_days}d"

                with open(MODEL_FILE, 'wb') as f:
                    pickle.dump(model, f)

                with open(SCALER_FILE, 'wb') as f:
                    pickle.dump(scaler, f)

                meta = {
                    "version": version,
                    "model_version": model_version,
                    "trained_at": datetime.now().isoformat(),
                    "training_method": "historical_enriched",
                    "samples": len(X),
                    "stocks_used": processed_stocks,
                    "stocks_skipped": skipped_stocks,
                    "period": period,
                    "predict_days": predict_days,
                    "feature_count": len(feature_names),
                    "feature_names": feature_names,
                    "class_distribution": {"up": float(up_ratio), "down": float(1 - up_ratio)},
                    "quality_stats": quality_stats,
                    "quality_ratio": quality_ratio,
                    "metrics": {
                        "cv_accuracy": float(np.mean(cv_scores)),
                        "cv_std": float(np.std(cv_scores)),
                        "test_accuracy": test_accuracy,
                        "test_f1": test_f1,
                    },
                }

                with open(META_FILE, 'wb') as f:
                    pickle.dump(meta, f)

                with open(META_JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

            logger.info(f"[ModelTrainer] 歷史數據訓練完成: {model_version}")

            # 重置預測器以載入新模型
            global _predictor
            _predictor = None

            return {
                "success": True,
                "version": model_version.split("_")[0] if "_" in model_version else model_version,
                "model_version": model_version,
                "training_method": "full",
                "samples": len(X),
                "stocks_used": processed_stocks,
                "stocks_skipped": skipped_stocks,
                "period": period,
                "predict_days": predict_days,
                "feature_count": len(feature_names),
                "class_distribution": {"up": round(up_ratio, 4), "down": round(1 - up_ratio, 4)},
                "quality_stats": quality_stats,
                "quality_ratio": quality_ratio,
                "cv_accuracy": round(float(np.mean(cv_scores)), 4),
                "cv_std": round(float(np.std(cv_scores)), 4),
                "test_accuracy": round(test_accuracy, 4),
                "test_f1": round(test_f1, 4),
                "model_path": str(MODEL_DIR),
            }

        except Exception as e:
            logger.error(f"[ModelTrainer] 歷史數據訓練失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def incremental_train(
        new_data_source: str = "performance",
        replay_ratio: float = 0.3,
        base_version: Optional[str] = None,
        min_new_samples: int = 50,
    ) -> Dict[str, Any]:
        """
        V10.41: 增量訓練

        在現有模型基礎上繼續訓練，使用經驗回放防止災難性遺忘。

        Args:
            new_data_source: 新數據來源 ("performance" 或 "historical")
            replay_ratio: 經驗回放比例 (舊數據 / 新數據)
            base_version: 基礎版本 (None 則使用當前版本)
            min_new_samples: 最少新樣本數

        Returns:
            訓練結果
        """
        try:
            import numpy as np
            from datetime import datetime
            import time

            try:
                from xgboost import XGBClassifier
                from sklearn.preprocessing import StandardScaler
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import f1_score
            except ImportError as e:
                return {
                    "success": False,
                    "error": f"缺少必要套件: {e}"
                }

            from .ml_training_manager import get_training_manager
            manager = get_training_manager()

            start_time = time.time()

            # 1. 載入新數據
            X_new, y_new, feature_names = manager.load_training_samples(
                sources=[new_data_source],
                min_quality=0.6,
            )

            if len(X_new) < min_new_samples:
                return {
                    "success": False,
                    "error": f"新數據不足，需要 {min_new_samples} 筆，目前只有 {len(X_new)} 筆"
                }

            logger.info(f"[ModelTrainer] 增量訓練: 新數據 {len(X_new)} 筆")

            # 2. 經驗回放：從歷史數據抽樣
            replay_size = int(len(X_new) * replay_ratio)
            if replay_size > 0:
                X_old, y_old = manager.sample_for_replay(
                    size=replay_size,
                    sources=["historical"] if new_data_source == "performance" else ["performance"]
                )
                logger.info(f"[ModelTrainer] 經驗回放: {len(X_old)} 筆舊數據")
            else:
                X_old, y_old = np.array([]), np.array([])

            # 3. 合併數據 (新數據權重更高)
            if len(X_old) > 0:
                X_combined = np.vstack([X_new, X_old])
                y_combined = np.hstack([y_new, y_old])

                # 樣本權重: 新數據 1.5, 舊數據 1.0
                sample_weights = np.hstack([
                    np.ones(len(X_new)) * 1.5,
                    np.ones(len(X_old)) * 1.0
                ])
            else:
                X_combined = X_new
                y_combined = y_new
                sample_weights = np.ones(len(X_new))

            logger.info(f"[ModelTrainer] 合併數據: {len(X_combined)} 筆")

            # 4. 載入基礎模型
            if base_version:
                base_model, base_scaler, base_meta = manager.load_version(base_version)
            else:
                current_version = manager.get_current_version()
                if current_version:
                    base_model, base_scaler, base_meta = manager.load_version(current_version)
                    base_version = current_version
                else:
                    return {
                        "success": False,
                        "error": "沒有基礎模型可用於增量訓練，請先執行完整訓練"
                    }

            logger.info(f"[ModelTrainer] 基礎版本: {base_version}")

            # 5. 標準化 (使用基礎模型的 scaler 或重新擬合)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_combined)

            # 6. 分割訓練/測試集
            X_train, X_test, y_train, y_test, w_train, _ = train_test_split(
                X_scaled, y_combined, sample_weights,
                test_size=0.2, random_state=42, stratify=y_combined
            )

            # 7. 增量訓練 (使用較小的學習率和較少的樹)
            new_model = XGBClassifier(
                n_estimators=50,      # 較少的新樹
                learning_rate=0.02,   # 較小的學習率
                max_depth=4,          # 較淺的樹
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )

            # XGBoost 增量訓練: 在舊模型基礎上繼續
            new_model.fit(
                X_train, y_train,
                sample_weight=w_train,
                xgb_model=base_model.get_booster() if hasattr(base_model, 'get_booster') else None,
            )

            # 8. 評估
            y_pred = new_model.predict(X_test)
            test_accuracy = float(np.mean(y_pred == y_test))
            test_f1 = float(f1_score(y_test, y_pred, zero_division=0))

            training_duration = time.time() - start_time

            logger.info(f"[ModelTrainer] 增量訓練完成: accuracy={test_accuracy:.4f}, f1={test_f1:.4f}")

            # 9. 計算改進幅度
            base_accuracy = base_meta.get("metrics", {}).get("test_accuracy", 0)
            improvement = (test_accuracy - base_accuracy) * 100

            # 10. 保存新版本
            metrics = {
                "accuracy": test_accuracy,
                "f1": test_f1,
            }

            config = {
                "training_method": "incremental",
                "samples_count": len(X_combined),
                "samples_added": len(X_new),
                "feature_count": len(feature_names),
                "predict_days": base_meta.get("config", {}).get("predict_days", 5),
                "data_sources": [new_data_source, "replay"],
                "base_version": base_version,
                "improvement": improvement,
                "training_duration": training_duration,
                "replay_ratio": replay_ratio,
            }

            version_result = manager.save_model_version(
                new_model, scaler, metrics, config, set_as_current=True
            )

            if not version_result["success"]:
                return version_result

            # 重置預測器
            global _predictor
            _predictor = None

            return {
                "success": True,
                "version": version_result["version"],
                "training_method": "incremental",
                "base_version": base_version,
                "new_samples": len(X_new),
                "replay_samples": len(X_old),
                "total_samples": len(X_combined),
                "test_accuracy": round(test_accuracy, 4),
                "test_f1": round(test_f1, 4),
                "improvement": round(improvement, 2),
                "training_duration": round(training_duration, 2),
            }

        except Exception as e:
            logger.error(f"[ModelTrainer] 增量訓練失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def hybrid_train(
        historical_ratio: float = 0.7,
        performance_ratio: float = 0.3,
        min_samples: int = 100,
    ) -> Dict[str, Any]:
        """
        V10.41: 混合訓練

        結合歷史數據和績效追蹤數據進行訓練。

        Args:
            historical_ratio: 歷史數據比例
            performance_ratio: 績效追蹤數據比例
            min_samples: 最少樣本數

        Returns:
            訓練結果
        """
        try:
            import numpy as np
            import time

            try:
                from xgboost import XGBClassifier
                from sklearn.preprocessing import StandardScaler
                from sklearn.model_selection import cross_val_score, train_test_split
                from sklearn.metrics import f1_score
            except ImportError as e:
                return {
                    "success": False,
                    "error": f"缺少必要套件: {e}"
                }

            from .ml_training_manager import get_training_manager
            manager = get_training_manager()

            start_time = time.time()

            # 載入所有數據
            X_all, y_all, feature_names = manager.load_training_samples(
                sources=["historical", "performance"],
                min_quality=0.6,
            )

            if len(X_all) < min_samples:
                return {
                    "success": False,
                    "error": f"數據不足，需要 {min_samples} 筆，目前只有 {len(X_all)} 筆"
                }

            logger.info(f"[ModelTrainer] 混合訓練: 共 {len(X_all)} 筆數據")

            # 標準化
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_all)

            # 分割訓練/測試集
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_all, test_size=0.2, random_state=42, stratify=y_all
            )

            # 訓練模型
            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )

            # 交叉驗證
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')

            # 完整訓練
            model.fit(X_train, y_train)

            # 測試集評估
            y_pred = model.predict(X_test)
            test_accuracy = float(np.mean(y_pred == y_test))
            test_f1 = float(f1_score(y_test, y_pred, zero_division=0))

            training_duration = time.time() - start_time

            logger.info(f"[ModelTrainer] 混合訓練完成: accuracy={test_accuracy:.4f}, f1={test_f1:.4f}")

            # 保存版本
            metrics = {
                "cv_accuracy": float(np.mean(cv_scores)),
                "accuracy": test_accuracy,
                "f1": test_f1,
            }

            config = {
                "training_method": "hybrid",
                "samples_count": len(X_all),
                "feature_count": len(feature_names),
                "data_sources": ["historical", "performance"],
                "training_duration": training_duration,
            }

            version_result = manager.save_model_version(
                model, scaler, metrics, config, set_as_current=True
            )

            if not version_result["success"]:
                return version_result

            # 重置預測器
            global _predictor
            _predictor = None

            return {
                "success": True,
                "version": version_result["version"],
                "training_method": "hybrid",
                "total_samples": len(X_all),
                "feature_count": len(feature_names),
                "cv_accuracy": round(float(np.mean(cv_scores)), 4),
                "test_accuracy": round(test_accuracy, 4),
                "test_f1": round(test_f1, 4),
                "training_duration": round(training_duration, 2),
            }

        except Exception as e:
            logger.error(f"[ModelTrainer] 混合訓練失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }


# 全域預測器實例
_predictor: Optional[MLPredictor] = None


def get_predictor() -> MLPredictor:
    """取得預測器實例"""
    global _predictor
    if _predictor is None:
        _predictor = MLPredictor()
    return _predictor


def predict_stock(stock_id: str, stock_data: Dict = None) -> Dict:
    """預測單檔股票"""
    predictor = get_predictor()
    result = predictor.predict(stock_id, stock_data=stock_data)
    return asdict(result)


def predict_stocks_batch(stocks: List[Dict]) -> List[Dict]:
    """批次預測"""
    predictor = get_predictor()
    results = predictor.predict_batch(stocks)
    return [asdict(r) for r in results]
