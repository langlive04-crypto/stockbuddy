"""
database.py - 資料庫連接與模型定義
V10.38: 新增 SQLite + SQLAlchemy 支援
V10.41: 新增 ML 增量學習相關資料表

功能：
- 資料庫連接管理
- 使用者資料模型
- 投資組合模型
- 績效追蹤模型
- ML 訓練樣本與版本管理 (V10.41)
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, text, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 資料庫路徑
DATABASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'stockbuddy.db')}"

# 建立引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=False  # 設為 True 可看 SQL 語句
)

# Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基礎模型類別
Base = declarative_base()


# ===== 資料模型定義 =====

class User(Base):
    """使用者資料表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationHistory", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    """投資組合資料表"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=True)
    shares = Column(Integer, nullable=False, default=0)
    avg_price = Column(Float, nullable=False, default=0.0)
    buy_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    user = relationship("User", back_populates="portfolios")


class Watchlist(Base):
    """自選股清單"""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=True)
    category = Column(String(50), default="default")  # 分類群組
    target_price = Column(Float, nullable=True)  # 目標價
    stop_loss = Column(Float, nullable=True)  # 停損價
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯
    user = relationship("User", back_populates="watchlists")


class RecommendationHistory(Base):
    """AI 推薦歷史記錄（用於追蹤績效）"""
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可為 None (系統推薦)
    stock_id = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=True)
    recommendation_type = Column(String(20), nullable=False)  # ai_pick, hot, volume, dark_horse
    score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    recommendation_date = Column(DateTime, default=datetime.utcnow)

    # 追蹤欄位
    status = Column(String(20), default="active")  # active, closed, expired
    exit_price = Column(Float, nullable=True)
    exit_date = Column(DateTime, nullable=True)
    return_pct = Column(Float, nullable=True)  # 報酬率
    days_held = Column(Integer, nullable=True)  # 持有天數

    # 分析數據（JSON 字串）
    analysis_data = Column(Text, nullable=True)

    # 關聯
    user = relationship("User", back_populates="recommendations")


class DailyPerformance(Base):
    """每日績效統計"""
    __tablename__ = "daily_performance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False, index=True, unique=True)  # YYYY-MM-DD

    # 推薦統計
    total_recommendations = Column(Integer, default=0)
    ai_picks = Column(Integer, default=0)
    hot_stocks = Column(Integer, default=0)
    volume_hot = Column(Integer, default=0)
    dark_horses = Column(Integer, default=0)

    # 績效指標
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    avg_return = Column(Float, default=0.0)
    best_return = Column(Float, default=0.0)
    worst_return = Column(Float, default=0.0)

    # 市場數據
    market_index = Column(Float, nullable=True)  # 加權指數
    market_change_pct = Column(Float, nullable=True)  # 大盤漲跌幅

    created_at = Column(DateTime, default=datetime.utcnow)


class AlertHistory(Base):
    """警示歷史記錄"""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=True)
    alert_type = Column(String(30), nullable=False)  # price_target, stop_loss, volume_spike, etc.
    alert_message = Column(Text, nullable=False)
    trigger_value = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)


# ===== V10.41: ML 增量學習相關資料表 =====

class TrainingSample(Base):
    """
    ML 訓練樣本表

    保存所有用於訓練的特徵向量和標籤，支持：
    - 經驗累積：所有訓練數據持久化
    - 增量學習：可選擇性載入數據
    - 數據來源追蹤：區分歷史數據 vs 績效追蹤數據
    """
    __tablename__ = "training_samples"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True)
    sample_date = Column(Date, nullable=False, index=True)

    # 特徵 (55 維特徵向量，存為 JSON)
    features = Column(JSON, nullable=False)  # {"price_change_1d": 0.5, ...}
    feature_count = Column(Integer, nullable=False)  # 實際特徵數量

    # 標籤
    label = Column(Integer, nullable=False)  # 1=上漲, 0=下跌
    actual_return = Column(Float, nullable=True)  # 實際報酬率 (%)

    # 元數據
    source = Column(String(20), nullable=False, index=True)  # "historical" or "performance"
    quality_score = Column(Float, nullable=False)  # 特徵完整度 0-1
    feature_version = Column(String(20), default="v55")  # 特徵版本
    predict_days = Column(Integer, default=5)  # 預測天數

    created_at = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    """
    ML 模型版本表

    保存所有訓練過的模型版本，支持：
    - 版本管理：不覆蓋舊模型
    - 性能比較：追蹤每個版本的指標
    - 版本回滾：可切換到任意歷史版本
    """
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False, index=True)

    # 訓練配置
    training_method = Column(String(50), nullable=False)  # "full", "incremental", "hybrid"
    samples_count = Column(Integer, nullable=False)  # 訓練樣本數
    feature_count = Column(Integer, default=55)  # 特徵數量
    predict_days = Column(Integer, default=5)  # 預測天數

    # 性能指標
    cv_accuracy = Column(Float, nullable=True)  # 交叉驗證準確率
    test_accuracy = Column(Float, nullable=False)  # 測試集準確率
    test_f1 = Column(Float, nullable=False)  # F1 分數
    test_precision = Column(Float, nullable=True)  # 精確率
    test_recall = Column(Float, nullable=True)  # 召回率

    # 類別分布
    class_distribution = Column(JSON, nullable=True)  # {"0": 5000, "1": 5000}

    # 路徑與狀態
    model_path = Column(String(200), nullable=False)  # 模型文件路徑
    is_current = Column(Boolean, default=False, index=True)  # 是否為當前使用版本

    # 基礎版本（增量學習時使用）
    base_version = Column(String(50), nullable=True)  # 增量訓練的基礎版本

    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯
    training_history = relationship("TrainingHistory", back_populates="model_version", cascade="all, delete-orphan")


class TrainingHistory(Base):
    """
    訓練歷史表

    記錄每次訓練的詳細過程，支持：
    - 訓練追蹤：記錄數據來源、樣本數
    - 改進追蹤：相對基礎版本的改進幅度
    - 問題診斷：記錄訓練過程中的統計數據
    """
    __tablename__ = "training_history"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), ForeignKey("model_versions.version"), nullable=False)

    # 訓練類型
    training_type = Column(String(20), nullable=False)  # "full", "incremental", "hybrid"
    base_version = Column(String(50), nullable=True)  # 增量學習的基礎版本

    # 數據來源
    data_sources = Column(JSON, nullable=False)  # ["historical", "performance"]
    stock_count = Column(Integer, nullable=True)  # 股票數量
    date_range = Column(String(50), nullable=True)  # "2025-01-01 ~ 2026-01-01"

    # 樣本統計
    total_samples = Column(Integer, nullable=False)
    samples_added = Column(Integer, nullable=True)  # 增量訓練時新增的樣本
    high_quality_samples = Column(Integer, nullable=True)  # 高品質樣本數
    rejected_samples = Column(Integer, nullable=True)  # 被拒絕的樣本數

    # 訓練結果
    improvement = Column(Float, nullable=True)  # 相對基礎版本的改進 (%)
    training_duration = Column(Float, nullable=True)  # 訓練耗時 (秒)

    # 備註
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 關聯
    model_version = relationship("ModelVersion", back_populates="training_history")


# ===== 資料庫操作函數 =====

def init_db():
    """初始化資料庫（建立所有表格）"""
    Base.metadata.create_all(bind=engine)
    # 使用 logging 而非 print，避免編碼問題


def get_db():
    """取得資料庫 Session（用於依賴注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all_tables():
    """刪除所有表格（僅用於開發/測試）"""
    Base.metadata.drop_all(bind=engine)
    # 使用 logging 而非 print，避免編碼問題


# ===== 資料庫狀態檢查 =====

def check_db_status():
    """檢查資料庫狀態"""
    try:
        db = SessionLocal()
        # 測試連接 (SQLAlchemy 2.0 語法)
        db.execute(text("SELECT 1"))

        # 統計資料
        user_count = db.query(User).count()
        portfolio_count = db.query(Portfolio).count()
        watchlist_count = db.query(Watchlist).count()
        recommendation_count = db.query(RecommendationHistory).count()

        # V10.41: ML 訓練相關統計
        training_sample_count = db.query(TrainingSample).count()
        model_version_count = db.query(ModelVersion).count()
        current_model = db.query(ModelVersion).filter(ModelVersion.is_current == True).first()

        db.close()

        return {
            "status": "connected",
            "database_url": DATABASE_URL,
            "statistics": {
                "users": user_count,
                "portfolios": portfolio_count,
                "watchlists": watchlist_count,
                "recommendations": recommendation_count,
            },
            "ml_statistics": {
                "training_samples": training_sample_count,
                "model_versions": model_version_count,
                "current_model": current_model.version if current_model else None,
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
