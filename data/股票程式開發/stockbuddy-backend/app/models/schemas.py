"""
Pydantic 資料模型
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class StockInfo(BaseModel):
    """股票基本資訊"""
    stock_id: str
    name: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_percent: float


class StockHistory(BaseModel):
    """歷史K線資料"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float


class TechnicalIndicators(BaseModel):
    """技術指標"""
    ma5: Optional[float]
    ma20: Optional[float]
    ma60: Optional[float]
    rsi: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]


class InstitutionalData(BaseModel):
    """三大法人資料"""
    stock_id: str
    name: str
    foreign_net: int
    investment_net: int
    dealer_net: int
    total_net: int


class StockAnalysis(BaseModel):
    """股票分析結果"""
    stock_id: str
    name: str
    current_price: float
    change_percent: float
    
    # AI 評估
    confidence: int  # 0-100
    signal: str  # 買進/持有/觀望/賣出
    reason: str
    action: str
    
    # 關鍵價位
    stop_loss: float
    target: float
    
    # 技術細節（可選展開）
    technical: Optional[Dict[str, Any]] = None
    fundamental: Optional[Dict[str, Any]] = None
    news: Optional[Dict[str, Any]] = None
    chip: Optional[Dict[str, Any]] = None


class MarketSummary(BaseModel):
    """大盤概況"""
    date: str
    taiex_value: float
    taiex_change: float
    taiex_change_percent: float
    mood: str
    ai_comment: str


class RecommendationResponse(BaseModel):
    """推薦回應"""
    market: MarketSummary
    recommendations: List[StockAnalysis]
    updated_at: datetime


class StockDetailResponse(BaseModel):
    """個股詳情回應"""
    info: StockInfo
    history: List[StockHistory]
    technical: Dict[str, Any]
    institutional: Optional[InstitutionalData]
    analysis: StockAnalysis
