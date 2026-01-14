"""
Temporal Fusion Transformer 預測模組 V10.41

使用 TFT 進行時間序列股價預測

安裝位置: stockbuddy-backend/app/services/tft_predictor.py

依賴:
    pip install pytorch-forecasting>=1.0.0 pytorch-lightning>=2.1.0 torch>=2.1.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# 延遲導入
torch = None
pytorch_forecasting = None
pandas = None
numpy = None


def _ensure_dependencies():
    """確保依賴已導入"""
    global torch, pytorch_forecasting, pandas, numpy
    if torch is None:
        try:
            import torch as _torch
            import pytorch_forecasting as _pf
            import pandas as _pd
            import numpy as _np
            torch = _torch
            pytorch_forecasting = _pf
            pandas = _pd
            numpy = _np
            logger.info("[TFT] 依賴載入成功")
        except ImportError as e:
            raise ImportError(
                "請安裝依賴: pip install pytorch-forecasting>=1.0.0 "
                "pytorch-lightning>=2.1.0 torch>=2.1.0"
            ) from e


@dataclass
class TFTPrediction:
    """TFT 預測結果"""
    stock_id: str
    predictions: Dict[str, Dict[str, float]]  # day_1: {return, lower, upper}
    attention: Dict[str, Any]  # 注意力權重
    model_version: str


class TFTPredictor:
    """
    Temporal Fusion Transformer 預測器

    特點:
    - 捕捉長期時間依賴
    - 提供預測區間
    - 注意力機制可解釋

    使用方式:
    ```python
    predictor = TFTPredictor("path/to/model.ckpt")
    result = predictor.predict(history_data)
    ```
    """

    # 預設特徵配置
    DEFAULT_FEATURES = {
        "time_varying_known_reals": ["day_of_week", "month"],
        "time_varying_unknown_reals": [
            "close", "volume", "rsi", "macd",
            "foreign_net", "trust_net"
        ],
        "static_categoricals": ["stock_id", "industry"],
        "static_reals": ["market_cap"]
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        prediction_length: int = 5,
        device: str = "auto"
    ):
        """
        初始化 TFT 預測器

        Args:
            model_path: 模型檔案路徑 (None 則使用規則引擎備案)
            prediction_length: 預測天數
            device: 裝置 ("auto", "cpu", "cuda")
        """
        _ensure_dependencies()

        self.model_path = model_path
        self.prediction_length = prediction_length

        # 自動選擇裝置
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model = None
        self._loaded = False

    def _load_model(self):
        """載入 TFT 模型"""
        if self._loaded:
            return

        if self.model_path and Path(self.model_path).exists():
            logger.info(f"[TFT] 載入模型: {self.model_path}")
            self._model = pytorch_forecasting.TemporalFusionTransformer.load_from_checkpoint(
                self.model_path
            )
            self._model.to(self.device)
            self._model.eval()
            self._loaded = True
            logger.info(f"[TFT] 模型載入完成 (device: {self.device})")
        else:
            logger.warning("[TFT] 模型不存在，將使用規則引擎備案")
            self._loaded = True

    def predict(
        self,
        history: List[Dict],
        stock_id: str = "unknown"
    ) -> TFTPrediction:
        """
        預測未來走勢

        Args:
            history: 歷史 K 線數據 (至少 60 天)
            stock_id: 股票代碼

        Returns:
            TFTPrediction 預測結果
        """
        self._load_model()

        if self._model is None:
            # 使用規則引擎備案
            return self._rule_based_prediction(history, stock_id)

        # 準備數據
        df = self._prepare_dataframe(history, stock_id)

        # 建立 TimeSeriesDataSet
        dataset = self._create_dataset(df)

        # 預測
        with torch.no_grad():
            predictions = self._model.predict(dataset)

        # 解析預測結果
        return self._parse_predictions(predictions, stock_id)

    def _prepare_dataframe(
        self,
        history: List[Dict],
        stock_id: str
    ) -> 'pandas.DataFrame':
        """將歷史數據轉換為 DataFrame"""
        df = pandas.DataFrame(history)

        # 確保必要欄位
        required_cols = ["date", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"缺少必要欄位: {col}")

        # 添加時間特徵
        df["date"] = pandas.to_datetime(df["date"])
        df["day_of_week"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["time_idx"] = range(len(df))
        df["stock_id"] = stock_id

        # 填補缺失值
        df = df.fillna(method="ffill").fillna(0)

        return df

    def _create_dataset(self, df: 'pandas.DataFrame'):
        """建立 TimeSeriesDataSet"""
        from pytorch_forecasting import TimeSeriesDataSet

        training_cutoff = df["time_idx"].max() - self.prediction_length

        dataset = TimeSeriesDataSet(
            df[df["time_idx"] <= training_cutoff],
            time_idx="time_idx",
            target="close",
            group_ids=["stock_id"],
            max_encoder_length=60,
            max_prediction_length=self.prediction_length,
            time_varying_known_reals=["day_of_week", "month"],
            time_varying_unknown_reals=["close", "volume"],
            allow_missing_timesteps=True
        )

        return dataset

    def _parse_predictions(
        self,
        predictions: torch.Tensor,
        stock_id: str
    ) -> TFTPrediction:
        """解析預測結果"""
        preds = predictions.numpy()

        # 假設預測的是報酬率
        result_dict = {}
        for i in range(self.prediction_length):
            day_key = f"day_{i + 1}"
            pred_value = float(preds[0, i]) if len(preds.shape) > 1 else float(preds[i])

            # 估算信賴區間 (假設 ±30% 範圍)
            result_dict[day_key] = {
                "return": round(pred_value, 2),
                "lower": round(pred_value - abs(pred_value) * 0.3, 2),
                "upper": round(pred_value + abs(pred_value) * 0.3, 2)
            }

        return TFTPrediction(
            stock_id=stock_id,
            predictions=result_dict,
            attention={"note": "注意力權重需進一步解析"},
            model_version="tft_v1"
        )

    def _rule_based_prediction(
        self,
        history: List[Dict],
        stock_id: str
    ) -> TFTPrediction:
        """
        規則引擎備案

        當 TFT 模型不可用時，使用簡單趨勢外推
        """
        if len(history) < 20:
            # 數據不足，返回中性預測
            return TFTPrediction(
                stock_id=stock_id,
                predictions={
                    f"day_{i}": {"return": 0, "lower": -2, "upper": 2}
                    for i in range(1, self.prediction_length + 1)
                },
                attention={"method": "insufficient_data"},
                model_version="rule_based_v1"
            )

        # 計算近期趨勢
        closes = [h.get("close", 0) for h in history[-20:]]
        if closes[-1] > 0 and closes[0] > 0:
            trend = (closes[-1] - closes[0]) / closes[0] * 100 / 20  # 每日平均漲幅
        else:
            trend = 0

        # 線性外推
        result_dict = {}
        for i in range(1, self.prediction_length + 1):
            expected = trend * i
            result_dict[f"day_{i}"] = {
                "return": round(expected, 2),
                "lower": round(expected - 2, 2),
                "upper": round(expected + 2, 2)
            }

        return TFTPrediction(
            stock_id=stock_id,
            predictions=result_dict,
            attention={"method": "linear_extrapolation", "daily_trend": round(trend, 4)},
            model_version="rule_based_v1"
        )


# 全域實例
_predictor: Optional[TFTPredictor] = None


def get_tft_predictor(model_path: Optional[str] = None) -> TFTPredictor:
    """取得 TFT 預測器實例"""
    global _predictor
    if _predictor is None:
        _predictor = TFTPredictor(model_path)
    return _predictor


def predict_stock(
    history: List[Dict],
    stock_id: str = "unknown"
) -> Dict[str, Any]:
    """
    便捷函數：預測股票走勢

    Returns:
        {
            "stock_id": "2330",
            "predictions": {
                "day_1": {"return": 0.8, "lower": -0.5, "upper": 2.1},
                ...
            },
            "attention": {...},
            "model_version": "..."
        }
    """
    predictor = get_tft_predictor()
    result = predictor.predict(history, stock_id)

    return {
        "stock_id": result.stock_id,
        "predictions": result.predictions,
        "attention": result.attention,
        "model_version": result.model_version
    }
