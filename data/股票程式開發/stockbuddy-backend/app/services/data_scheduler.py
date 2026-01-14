"""
資料排程更新服務 V10.23
自動在背景更新重要資料

功能：
- 盤中自動更新（每分鐘更新熱門股票）
- 盤後批次更新（每日收盤後批次更新所有追蹤股票）
- 手動觸發更新（API 端點）
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
from .cache_service import is_trading_hours, SmartTTL, StockCache

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataScheduler:
    """
    資料排程更新器

    在盤中時段自動更新熱門股票資料
    """

    # 預設熱門股票清單（台股50成分股前20大）
    HOT_STOCKS = [
        "2330", "2317", "2454", "2308", "2382",  # 台積電、鴻海、聯發科、台達電、廣達
        "2881", "2882", "2891", "2886", "2884",  # 富邦金、國泰金、中信金、兆豐金、玉山金
        "2412", "3711", "2303", "2892", "2002",  # 中華電、日月光、聯電、第一金、中鋼
        "1303", "1301", "3008", "2912", "1216",  # 南亞、台塑、大立光、統一超、統一
    ]

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_update: Dict[str, datetime] = {}
        self._update_callbacks: Dict[str, Callable] = {}
        self._update_interval = 60  # 盤中更新間隔（秒）
        self._tracked_stocks: List[str] = list(self.HOT_STOCKS)
        self._update_count = 0
        self._error_count = 0

    def register_callback(self, data_type: str, callback: Callable):
        """註冊更新回調函數"""
        self._update_callbacks[data_type] = callback

    def add_tracked_stock(self, stock_id: str):
        """添加追蹤股票"""
        if stock_id not in self._tracked_stocks:
            self._tracked_stocks.append(stock_id)

    def remove_tracked_stock(self, stock_id: str):
        """移除追蹤股票"""
        if stock_id in self._tracked_stocks and stock_id not in self.HOT_STOCKS:
            self._tracked_stocks.remove(stock_id)

    def get_tracked_stocks(self) -> List[str]:
        """取得追蹤股票清單"""
        return list(self._tracked_stocks)

    async def start(self):
        """啟動排程器"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("📅 DataScheduler 已啟動")

    async def stop(self):
        """停止排程器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 DataScheduler 已停止")

    async def _scheduler_loop(self):
        """排程主迴圈"""
        while self._running:
            try:
                if is_trading_hours():
                    await self._update_during_trading()
                else:
                    # 盤後每 30 分鐘檢查一次
                    await asyncio.sleep(1800)

            except Exception as e:
                self._error_count += 1
                logger.error(f"排程更新錯誤: {e}")
                await asyncio.sleep(60)

    async def _update_during_trading(self):
        """盤中更新邏輯"""
        logger.info(f"📊 盤中更新開始 ({len(self._tracked_stocks)} 檔股票)")

        # 批次更新熱門股票
        batch_size = 5  # 每批次更新 5 檔
        for i in range(0, len(self._tracked_stocks), batch_size):
            batch = self._tracked_stocks[i:i + batch_size]

            tasks = []
            for stock_id in batch:
                if "stock_info" in self._update_callbacks:
                    tasks.append(self._safe_update("stock_info", stock_id))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # 避免請求過於頻繁
            await asyncio.sleep(2)

        self._update_count += 1
        logger.info(f"✅ 盤中更新完成 (第 {self._update_count} 次)")

        # 等待下一次更新
        await asyncio.sleep(self._update_interval)

    async def _safe_update(self, data_type: str, stock_id: str):
        """安全執行更新（捕捉異常）"""
        try:
            callback = self._update_callbacks.get(data_type)
            if callback:
                await callback(stock_id)
                self._last_update[f"{data_type}:{stock_id}"] = datetime.now()
        except Exception as e:
            logger.warning(f"更新 {data_type}:{stock_id} 失敗: {e}")

    async def force_update(self, stock_id: str = None) -> Dict:
        """
        強制更新資料

        Args:
            stock_id: 指定股票代號，None 表示更新所有追蹤股票

        Returns:
            更新結果
        """
        stocks_to_update = [stock_id] if stock_id else self._tracked_stocks
        updated = []
        failed = []

        for sid in stocks_to_update:
            try:
                for data_type, callback in self._update_callbacks.items():
                    await callback(sid)
                updated.append(sid)
            except Exception as e:
                failed.append({"stock_id": sid, "error": str(e)})

        return {
            "success": True,
            "updated": updated,
            "failed": failed,
            "timestamp": datetime.now().isoformat(),
        }

    def get_status(self) -> Dict:
        """取得排程器狀態"""
        return {
            "running": self._running,
            "is_trading_hours": is_trading_hours(),
            "market_status": "盤中" if is_trading_hours() else "盤後",
            "tracked_stocks_count": len(self._tracked_stocks),
            "update_interval_seconds": self._update_interval,
            "total_updates": self._update_count,
            "error_count": self._error_count,
            "last_updates": {
                k: v.isoformat() for k, v in list(self._last_update.items())[-10:]
            },
        }


# 全域排程器實例
_scheduler: Optional[DataScheduler] = None


def get_scheduler() -> DataScheduler:
    """取得排程器實例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataScheduler()
    return _scheduler


# ============================================================
# V10.23: 資料更新狀態追蹤
# ============================================================

class DataUpdateTracker:
    """
    資料更新狀態追蹤器

    追蹤每個資料的最後更新時間和狀態
    """

    def __init__(self):
        self._updates: Dict[str, Dict] = {}

    def record_update(self, data_type: str, stock_id: str = None, success: bool = True, error: str = None):
        """記錄更新狀態"""
        key = f"{data_type}:{stock_id}" if stock_id else data_type
        self._updates[key] = {
            "data_type": data_type,
            "stock_id": stock_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error": error,
        }

    def get_update_status(self, data_type: str, stock_id: str = None) -> Optional[Dict]:
        """取得更新狀態"""
        key = f"{data_type}:{stock_id}" if stock_id else data_type
        return self._updates.get(key)

    def get_all_status(self) -> Dict:
        """取得所有更新狀態"""
        return {
            "updates": self._updates,
            "total_count": len(self._updates),
            "success_count": sum(1 for u in self._updates.values() if u["success"]),
            "error_count": sum(1 for u in self._updates.values() if not u["success"]),
        }

    def get_stale_data(self, max_age_minutes: int = 30) -> List[Dict]:
        """取得過期資料清單"""
        stale = []
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        for key, update in self._updates.items():
            update_time = datetime.fromisoformat(update["timestamp"])
            if update_time < cutoff:
                stale.append({
                    **update,
                    "age_minutes": int((datetime.now() - update_time).total_seconds() / 60),
                })

        return stale


# 全域追蹤器實例
_update_tracker: Optional[DataUpdateTracker] = None


def get_update_tracker() -> DataUpdateTracker:
    """取得追蹤器實例"""
    global _update_tracker
    if _update_tracker is None:
        _update_tracker = DataUpdateTracker()
    return _update_tracker
