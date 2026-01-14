"""
V10.41: ML 預測 API 路由
從 stocks.py 拆分出來，提高可維護性

V10.41: 新增增量學習 API、版本管理 API
V10.40: 新增 train-historical 歷史數據訓練功能
V10.40: 新增 stock-presets 預設股票清單 API
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/stocks/ml", tags=["ml"])


# ===== Pydantic Models =====

class VersionCompareRequest(BaseModel):
    version1: str
    version2: str


@router.get("/stock-presets")
async def get_stock_presets():
    """
    V10.40: 取得可用的預設股票清單

    Returns:
        各種預設股票清單及其描述、股票數量、預估訓練時間
    """
    try:
        from app.config.stock_lists import get_all_presets
        presets = get_all_presets()
        return {
            "success": True,
            "presets": presets
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/stock-presets/{preset_key}")
async def get_preset_stock_list(preset_key: str):
    """
    V10.40: 取得指定預設清單的股票代碼

    Args:
        preset_key: 預設清單 key (top50, top100, electronics50, etc.)
    """
    try:
        from app.config.stock_lists import STOCK_PRESETS

        if preset_key not in STOCK_PRESETS:
            return {
                "success": False,
                "error": f"找不到預設清單: {preset_key}",
                "available_keys": list(STOCK_PRESETS.keys())
            }

        preset = STOCK_PRESETS[preset_key]
        return {
            "success": True,
            "preset_key": preset_key,
            "name": preset["name"],
            "description": preset["description"],
            "count": len(preset["stocks"]),
            "stocks": preset["stocks"]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/predict/{stock_id}")
async def ml_predict_stock(stock_id: str):
    """
    V10.36: ML 預測股票走勢

    使用機器學習模型或規則引擎預測股票未來走勢

    Returns:
        - prediction: "up" / "down" / "neutral"
        - probability: 上漲機率 (0-1)
        - confidence: "high" / "medium" / "low"
        - model_version: 使用的模型版本
    """
    try:
        from app.services.ml_predictor import predict_stock

        # 嘗試取得股票數據作為預測依據
        stock_data = {}
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{stock_id}.TW")
            hist = ticker.history(period="60d")

            if not hist.empty and len(hist) >= 20:
                close = hist['Close']
                stock_data = {
                    "close": float(close.iloc[-1]),
                    "ma5": float(close.rolling(5).mean().iloc[-1]),
                    "ma20": float(close.rolling(20).mean().iloc[-1]),
                    "volume": float(hist['Volume'].iloc[-1]),
                    "avg_volume": float(hist['Volume'].rolling(20).mean().iloc[-1]),
                }

                # 計算 RSI
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                stock_data["rsi"] = float(rsi.iloc[-1]) if not rsi.empty else None

        except Exception:
            # 即使取得數據失敗，仍可使用規則引擎預測
            pass

        result = predict_stock(stock_id, stock_data)
        return {"success": True, **result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/predict/batch")
async def ml_predict_batch(stock_ids: List[str]):
    """
    V10.36: 批次 ML 預測多檔股票
    """
    try:
        from app.services.ml_predictor import predict_stock

        results = []
        for stock_id in stock_ids[:20]:  # 限制最多 20 檔
            try:
                result = predict_stock(stock_id, {})
                results.append(result)
            except Exception as e:
                results.append({
                    "stock_id": stock_id,
                    "error": str(e)
                })

        return {
            "success": True,
            "count": len(results),
            "predictions": results
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/train")
async def train_ml_model(
    min_samples: int = Query(100, ge=10, description="最少訓練樣本數"),
    use_full_features: bool = Query(True, description="使用完整 55 特徵 (預設 True)")
):
    """
    V10.40: 訓練 ML 模型

    使用歷史績效追蹤數據訓練預測模型

    Args:
        min_samples: 最少訓練樣本數 (預設 100)
        use_full_features: 是否使用完整 55 特徵 (預設 True)
            - True: 使用 ml_feature_engine 的 55 個特徵
            - False: 使用基礎 2 特徵 (confidence, days_held)

    前置條件: 需要至少 min_samples 筆有完整報酬追蹤的推薦數據
    """
    try:
        from app.services.ml_predictor import ModelTrainer

        result = ModelTrainer.train_from_history(
            min_samples=min_samples,
            use_full_features=use_full_features
        )
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/train-historical")
async def train_ml_model_from_historical(
    period: str = Query("1y", description="歷史數據期間 (6mo, 1y, 2y, 5y)"),
    predict_days: int = Query(5, ge=1, le=30, description="預測天數 (標籤: N天後是否上漲)"),
    min_samples: int = Query(100, ge=10, description="最少訓練樣本數"),
    preset: Optional[str] = Query(None, description="預設股票清單 (top50, top100, electronics50, electronics100, financials30, traditional50, dividend30)"),
    stock_ids: Optional[str] = Query(None, description="自訂股票代碼 (逗號分隔，如: 2330,2317,2454)")
):
    """
    V10.40: 從歷史股價數據訓練 ML 模型

    使用 Yahoo Finance 的歷史數據自動生成訓練樣本，無需等待績效追蹤。

    Args:
        period: 歷史數據期間
            - "6mo": 6 個月
            - "1y": 1 年 (預設)
            - "2y": 2 年
            - "5y": 5 年
        predict_days: 預測天數 (1-30)，模型將學習預測 N 天後是否上漲
        min_samples: 最少訓練樣本數
        preset: 預設股票清單 (優先使用)
            - "top50": 市值 TOP 50
            - "top100": 市值 TOP 100 (推薦)
            - "electronics50": 電子 TOP 50
            - "electronics100": 電子 TOP 100
            - "financials30": 金融 TOP 30
            - "traditional50": 傳產 TOP 50
            - "dividend30": 高股息 TOP 30
        stock_ids: 自訂股票代碼 (當 preset 為空時使用)

    Returns:
        訓練結果，包含準確率、F1 分數、樣本數等資訊
    """
    try:
        from app.services.ml_predictor import ModelTrainer

        # 解析股票代碼：優先使用 preset
        parsed_stock_ids = None

        if preset:
            # 使用預設清單
            from app.config.stock_lists import get_preset_stocks
            parsed_stock_ids = get_preset_stocks(preset)
        elif stock_ids:
            # 使用自訂清單
            parsed_stock_ids = [s.strip() for s in stock_ids.split(",") if s.strip()]

        result = ModelTrainer.train_from_historical(
            stock_ids=parsed_stock_ids,
            period=period,
            predict_days=predict_days,
            min_samples=min_samples
        )
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/model-info")
async def get_ml_model_info():
    """
    V10.36: 取得 ML 模型資訊
    """
    try:
        from app.services.ml_predictor import get_predictor

        predictor = get_predictor()

        # 嘗試載入模型資訊
        predictor._load_model()

        if predictor._meta:
            return {
                "success": True,
                "has_model": True,
                "model_info": predictor._meta
            }
        else:
            return {
                "success": True,
                "has_model": False,
                "message": "尚未訓練模型，使用規則引擎預測",
                "model_version": "rule_based_v1"
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== V10.41: 增量學習與版本管理 API =====

@router.post("/train-incremental")
async def train_incremental(
    data_source: str = Query("performance", description="新數據來源 (performance, historical)"),
    replay_ratio: float = Query(0.3, ge=0, le=1, description="經驗回放比例"),
    base_version: Optional[str] = Query(None, description="基礎版本 (預設使用當前版本)"),
    min_new_samples: int = Query(50, ge=10, description="最少新樣本數"),
):
    """
    V10.41: 增量訓練

    在現有模型基礎上繼續訓練，使用經驗回放防止災難性遺忘。

    Args:
        data_source: 新數據來源 ("performance" 使用績效追蹤數據, "historical" 使用歷史數據)
        replay_ratio: 經驗回放比例 (從舊數據抽樣的比例，0.3 表示新數據的 30%)
        base_version: 基礎版本 ID (可選，預設使用當前版本)
        min_new_samples: 最少新樣本數

    Returns:
        訓練結果，包含新版本 ID、改進幅度等
    """
    try:
        from app.services.ml_predictor import ModelTrainer

        result = ModelTrainer.incremental_train(
            new_data_source=data_source,
            replay_ratio=replay_ratio,
            base_version=base_version,
            min_new_samples=min_new_samples,
        )
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/train-hybrid")
async def train_hybrid(
    min_samples: int = Query(100, ge=10, description="最少樣本數"),
):
    """
    V10.41: 混合訓練

    結合歷史數據和績效追蹤數據進行完整訓練。

    Args:
        min_samples: 最少樣本數

    Returns:
        訓練結果
    """
    try:
        from app.services.ml_predictor import ModelTrainer

        result = ModelTrainer.hybrid_train(min_samples=min_samples)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/versions")
async def list_model_versions(
    limit: int = Query(10, ge=1, le=50, description="最大返回數量"),
):
    """
    V10.41: 列出所有模型版本

    Returns:
        版本列表，按建立時間降序排列
    """
    try:
        from app.services.ml_training_manager import get_training_manager

        manager = get_training_manager()
        versions = manager.list_versions(limit=limit)

        return {
            "success": True,
            "count": len(versions),
            "versions": versions,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/versions/{version_id}")
async def get_model_version(version_id: str):
    """
    V10.41: 取得指定版本詳情

    Args:
        version_id: 版本 ID

    Returns:
        版本詳細資訊
    """
    try:
        from app.database import SessionLocal, ModelVersion

        db = SessionLocal()

        try:
            version = db.query(ModelVersion).filter(
                ModelVersion.version == version_id
            ).first()

            if not version:
                return {
                    "success": False,
                    "error": f"版本不存在: {version_id}"
                }

            return {
                "success": True,
                "version": {
                    "version": version.version,
                    "training_method": version.training_method,
                    "samples_count": version.samples_count,
                    "feature_count": version.feature_count,
                    "predict_days": version.predict_days,
                    "cv_accuracy": version.cv_accuracy,
                    "test_accuracy": version.test_accuracy,
                    "test_f1": version.test_f1,
                    "test_precision": version.test_precision,
                    "test_recall": version.test_recall,
                    "class_distribution": version.class_distribution,
                    "is_current": version.is_current,
                    "base_version": version.base_version,
                    "model_path": version.model_path,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                }
            }
        finally:
            db.close()

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/versions/{version_id}/activate")
async def activate_model_version(version_id: str):
    """
    V10.41: 設置指定版本為當前使用版本

    Args:
        version_id: 版本 ID

    Returns:
        操作結果
    """
    try:
        from app.services.ml_training_manager import get_training_manager

        manager = get_training_manager()
        result = manager.set_current_version(version_id)

        if result["success"]:
            # 重置預測器以載入新版本
            from app.services.ml_predictor import get_predictor
            global _predictor
            _predictor = None

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/versions/compare")
async def compare_model_versions(request: VersionCompareRequest):
    """
    V10.41: 比較兩個版本的性能

    Args:
        request: 包含 version1 和 version2 的請求體

    Returns:
        比較結果
    """
    try:
        from app.services.ml_training_manager import get_training_manager

        manager = get_training_manager()
        result = manager.compare_versions(request.version1, request.version2)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/training-data/stats")
async def get_training_data_stats():
    """
    V10.41: 取得訓練數據統計

    Returns:
        訓練數據的統計資訊
    """
    try:
        from app.services.ml_training_manager import get_training_manager

        manager = get_training_manager()
        stats = manager.get_training_stats()

        return {
            "success": True,
            "stats": stats,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/versions/{version_id}")
async def delete_model_version(version_id: str):
    """
    V10.41: 刪除指定版本

    注意：無法刪除當前使用中的版本

    Args:
        version_id: 版本 ID

    Returns:
        操作結果
    """
    try:
        from app.database import SessionLocal, ModelVersion
        import shutil

        db = SessionLocal()

        try:
            version = db.query(ModelVersion).filter(
                ModelVersion.version == version_id
            ).first()

            if not version:
                return {
                    "success": False,
                    "error": f"版本不存在: {version_id}"
                }

            if version.is_current:
                return {
                    "success": False,
                    "error": "無法刪除當前使用中的版本，請先切換到其他版本"
                }

            # 刪除模型文件
            import os
            if version.model_path and os.path.exists(version.model_path):
                shutil.rmtree(version.model_path)

            # 刪除資料庫記錄
            db.delete(version)
            db.commit()

            return {
                "success": True,
                "message": f"版本 {version_id} 已刪除"
            }

        finally:
            db.close()

    except Exception as e:
        return {"success": False, "error": str(e)}
