"""
歷史績效追蹤服務 V10.36

追蹤 AI 推薦股票的後續表現，評估推薦準確性

功能：
- 記錄每次推薦的股票和推薦時價格
- 追蹤推薦後的價格變化
- 計算推薦準確率和平均報酬率
- 生成績效報告
- V10.36 新增：按週期/訊號/評分區間統計
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path

# 資料存儲路徑
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRACKER_FILE = DATA_DIR / "performance_tracker.json"


class PerformanceTracker:
    """
    績效追蹤器

    追蹤 AI 推薦股票的歷史表現
    """

    def __init__(self):
        self._data: Dict[str, Any] = self._load_data()

    def _load_data(self) -> Dict:
        """載入追蹤資料"""
        try:
            if TRACKER_FILE.exists():
                with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"載入追蹤資料失敗: {e}")

        return {
            "recommendations": [],  # 推薦記錄
            "performance": {},      # 績效記錄（按日期）
            "statistics": {},       # 統計資料
        }

    def _save_data(self):
        """儲存追蹤資料"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(TRACKER_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存追蹤資料失敗: {e}")

    def record_recommendation(self, stock_id: str, name: str, price: float,
                               signal: str, confidence: int, reason: str = None) -> Dict:
        """
        記錄一次推薦

        Args:
            stock_id: 股票代號
            name: 股票名稱
            price: 推薦時價格
            signal: 推薦信號（買進/觀望等）
            confidence: 信心分數
            reason: 推薦理由

        Returns:
            記錄結果
        """
        today = datetime.now().strftime("%Y-%m-%d")

        record = {
            "id": f"{today}_{stock_id}",
            "date": today,
            "timestamp": datetime.now().isoformat(),
            "stock_id": stock_id,
            "name": name,
            "entry_price": price,
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "status": "active",  # active, closed, expired
            "current_price": None,
            "return_percent": None,
            "days_held": 0,
            "updates": [],
        }

        # 避免同一天重複記錄同一檔股票
        existing = next(
            (r for r in self._data["recommendations"]
             if r["date"] == today and r["stock_id"] == stock_id),
            None
        )

        if existing:
            # 更新現有記錄
            existing.update({
                "entry_price": price,
                "signal": signal,
                "confidence": confidence,
                "reason": reason,
            })
        else:
            self._data["recommendations"].append(record)

        self._save_data()

        return {
            "success": True,
            "message": f"已記錄 {name} ({stock_id}) 推薦",
            "record": record,
        }

    def update_price(self, stock_id: str, current_price: float) -> Dict:
        """
        更新股票當前價格

        Args:
            stock_id: 股票代號
            current_price: 當前價格

        Returns:
            更新結果
        """
        updated = []

        for record in self._data["recommendations"]:
            if record["stock_id"] == stock_id and record["status"] == "active":
                record["current_price"] = current_price
                record["return_percent"] = round(
                    (current_price - record["entry_price"]) / record["entry_price"] * 100, 2
                )

                entry_date = datetime.strptime(record["date"], "%Y-%m-%d")
                record["days_held"] = (datetime.now() - entry_date).days

                # 記錄更新歷史
                record["updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "price": current_price,
                    "return_percent": record["return_percent"],
                })

                # 只保留最近 30 天的更新記錄
                record["updates"] = record["updates"][-30:]

                updated.append(record["stock_id"])

        if updated:
            self._save_data()

        return {
            "success": True,
            "updated": updated,
            "count": len(updated),
        }

    def close_position(self, stock_id: str, exit_price: float, reason: str = "手動關閉") -> Dict:
        """
        關閉推薦追蹤

        Args:
            stock_id: 股票代號
            exit_price: 出場價格
            reason: 關閉原因

        Returns:
            關閉結果
        """
        closed = []

        for record in self._data["recommendations"]:
            if record["stock_id"] == stock_id and record["status"] == "active":
                record["status"] = "closed"
                record["exit_price"] = exit_price
                record["exit_date"] = datetime.now().strftime("%Y-%m-%d")
                record["final_return_percent"] = round(
                    (exit_price - record["entry_price"]) / record["entry_price"] * 100, 2
                )
                record["close_reason"] = reason

                closed.append({
                    "stock_id": stock_id,
                    "name": record["name"],
                    "entry_price": record["entry_price"],
                    "exit_price": exit_price,
                    "return_percent": record["final_return_percent"],
                    "days_held": record["days_held"],
                })

        if closed:
            self._save_data()

        return {
            "success": len(closed) > 0,
            "closed": closed,
        }

    def get_active_recommendations(self) -> List[Dict]:
        """取得所有進行中的推薦"""
        active = [
            r for r in self._data["recommendations"]
            if r["status"] == "active"
        ]

        # 依報酬率排序
        active.sort(key=lambda x: x.get("return_percent") or 0, reverse=True)

        return active

    def get_closed_recommendations(self, limit: int = 50) -> List[Dict]:
        """取得已關閉的推薦"""
        closed = [
            r for r in self._data["recommendations"]
            if r["status"] == "closed"
        ]

        # 依日期排序（最新在前）
        closed.sort(key=lambda x: x.get("exit_date", ""), reverse=True)

        return closed[:limit]

    def get_statistics(self) -> Dict:
        """
        計算績效統計

        Returns:
            統計資料
        """
        recommendations = self._data["recommendations"]

        if not recommendations:
            return {
                "total_recommendations": 0,
                "active_count": 0,
                "closed_count": 0,
                "win_rate": 0,
                "avg_return": 0,
                "best_return": 0,
                "worst_return": 0,
            }

        active = [r for r in recommendations if r["status"] == "active"]
        closed = [r for r in recommendations if r["status"] == "closed"]

        # 計算已關閉推薦的績效
        closed_returns = [r.get("final_return_percent", 0) for r in closed if r.get("final_return_percent") is not None]
        wins = [r for r in closed_returns if r > 0]

        # 計算進行中推薦的帳面績效
        active_returns = [r.get("return_percent", 0) for r in active if r.get("return_percent") is not None]

        all_returns = closed_returns + active_returns

        return {
            "total_recommendations": len(recommendations),
            "active_count": len(active),
            "closed_count": len(closed),
            "win_rate": round(len(wins) / len(closed_returns) * 100, 1) if closed_returns else 0,
            "avg_return": round(sum(all_returns) / len(all_returns), 2) if all_returns else 0,
            "best_return": round(max(all_returns), 2) if all_returns else 0,
            "worst_return": round(min(all_returns), 2) if all_returns else 0,
            "total_profit_loss": round(sum(all_returns), 2),
            "active_avg_return": round(sum(active_returns) / len(active_returns), 2) if active_returns else 0,
            "closed_avg_return": round(sum(closed_returns) / len(closed_returns), 2) if closed_returns else 0,
        }

    def get_recommendation_history(self, stock_id: str) -> List[Dict]:
        """取得特定股票的推薦歷史"""
        history = [
            r for r in self._data["recommendations"]
            if r["stock_id"] == stock_id
        ]
        history.sort(key=lambda x: x["date"], reverse=True)
        return history

    def get_daily_performance(self, days: int = 30) -> List[Dict]:
        """取得每日績效摘要"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        daily_data = {}

        for record in self._data["recommendations"]:
            date = record["date"]
            if date < cutoff_str:
                continue

            if date not in daily_data:
                daily_data[date] = {
                    "date": date,
                    "recommendations": 0,
                    "winners": 0,
                    "losers": 0,
                    "avg_return": 0,
                    "returns": [],
                }

            daily_data[date]["recommendations"] += 1

            ret = record.get("return_percent") or record.get("final_return_percent")
            if ret is not None:
                daily_data[date]["returns"].append(ret)
                if ret > 0:
                    daily_data[date]["winners"] += 1
                elif ret < 0:
                    daily_data[date]["losers"] += 1

        # 計算平均報酬
        for date, data in daily_data.items():
            if data["returns"]:
                data["avg_return"] = round(sum(data["returns"]) / len(data["returns"]), 2)
            del data["returns"]

        # 排序並返回
        result = list(daily_data.values())
        result.sort(key=lambda x: x["date"], reverse=True)
        return result

    def export_report(self) -> Dict:
        """匯出完整績效報告"""
        return {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "active_recommendations": self.get_active_recommendations(),
            "recent_closed": self.get_closed_recommendations(20),
            "daily_performance": self.get_daily_performance(30),
        }

    def cleanup_expired(self, max_days: int = 90):
        """
        清理過期的推薦記錄

        Args:
            max_days: 最大保留天數
        """
        cutoff = datetime.now() - timedelta(days=max_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        # 將過期的 active 記錄標記為 expired
        for record in self._data["recommendations"]:
            if record["status"] == "active" and record["date"] < cutoff_str:
                record["status"] = "expired"

        # 移除非常舊的記錄（超過 180 天）
        very_old = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        self._data["recommendations"] = [
            r for r in self._data["recommendations"]
            if r["date"] >= very_old
        ]

        self._save_data()

    # ============================================================
    # V10.36 新增：進階統計功能
    # ============================================================

    def get_stats_by_period(self, periods: List[int] = [7, 30, 90]) -> Dict[str, Any]:
        """
        按追蹤週期取得統計

        Args:
            periods: 追蹤週期天數列表，預設 [7, 30, 90]

        Returns:
            各週期的勝率和報酬統計
        """
        recommendations = self._data["recommendations"]
        today = datetime.now()

        results = {}

        for period in periods:
            # 篩選至少追蹤了指定天數的推薦
            cutoff_date = (today - timedelta(days=period)).strftime("%Y-%m-%d")

            eligible = [
                r for r in recommendations
                if r["date"] <= cutoff_date and r.get("return_percent") is not None
            ]

            if not eligible:
                results[f"{period}d"] = {
                    "period_days": period,
                    "total": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                    "max_return": 0,
                    "min_return": 0,
                }
                continue

            returns = [r.get("return_percent", 0) or r.get("final_return_percent", 0) for r in eligible]
            wins = [r for r in returns if r > 0]
            losses = [r for r in returns if r < 0]

            results[f"{period}d"] = {
                "period_days": period,
                "total": len(eligible),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": round(len(wins) / len(eligible) * 100, 1) if eligible else 0,
                "avg_return": round(sum(returns) / len(returns), 2) if returns else 0,
                "max_return": round(max(returns), 2) if returns else 0,
                "min_return": round(min(returns), 2) if returns else 0,
            }

        return {
            "generated_at": today.isoformat(),
            "periods": results,
        }

    def get_stats_by_signal(self) -> Dict[str, Any]:
        """
        按訊號類型統計

        Returns:
            各訊號類型的勝率和報酬統計
        """
        recommendations = self._data["recommendations"]

        # 分組
        signal_groups: Dict[str, List] = {}
        for rec in recommendations:
            signal = rec.get("signal", "未知")
            if signal not in signal_groups:
                signal_groups[signal] = []
            signal_groups[signal].append(rec)

        results = {}

        for signal, recs in signal_groups.items():
            # 取得有報酬數據的推薦
            with_returns = [
                r for r in recs
                if r.get("return_percent") is not None or r.get("final_return_percent") is not None
            ]

            if not with_returns:
                results[signal] = {
                    "signal": signal,
                    "total": len(recs),
                    "tracked": 0,
                    "wins": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                }
                continue

            returns = [
                r.get("return_percent") or r.get("final_return_percent", 0)
                for r in with_returns
            ]
            wins = [r for r in returns if r > 0]

            results[signal] = {
                "signal": signal,
                "total": len(recs),
                "tracked": len(with_returns),
                "wins": len(wins),
                "win_rate": round(len(wins) / len(with_returns) * 100, 1),
                "avg_return": round(sum(returns) / len(returns), 2),
                "max_return": round(max(returns), 2),
                "min_return": round(min(returns), 2),
            }

        # 按勝率排序
        sorted_results = dict(
            sorted(results.items(), key=lambda x: x[1].get("win_rate", 0), reverse=True)
        )

        return {
            "generated_at": datetime.now().isoformat(),
            "by_signal": sorted_results,
        }

    def get_stats_by_score_range(self) -> Dict[str, Any]:
        """
        按評分區間統計

        Returns:
            各評分區間的勝率和報酬統計
        """
        recommendations = self._data["recommendations"]

        # 定義評分區間
        score_ranges = [
            ("80+", 80, 100),
            ("70-79", 70, 79),
            ("60-69", 60, 69),
            ("50-59", 50, 59),
            ("<50", 0, 49),
        ]

        results = {}

        for label, min_score, max_score in score_ranges:
            # 篩選該分數區間的推薦
            in_range = [
                r for r in recommendations
                if min_score <= (r.get("confidence", 0) or 0) <= max_score
            ]

            # 取得有報酬數據的推薦
            with_returns = [
                r for r in in_range
                if r.get("return_percent") is not None or r.get("final_return_percent") is not None
            ]

            if not with_returns:
                results[label] = {
                    "range": label,
                    "min_score": min_score,
                    "max_score": max_score,
                    "total": len(in_range),
                    "tracked": 0,
                    "wins": 0,
                    "win_rate": 0,
                    "avg_return": 0,
                }
                continue

            returns = [
                r.get("return_percent") or r.get("final_return_percent", 0)
                for r in with_returns
            ]
            wins = [r for r in returns if r > 0]

            results[label] = {
                "range": label,
                "min_score": min_score,
                "max_score": max_score,
                "total": len(in_range),
                "tracked": len(with_returns),
                "wins": len(wins),
                "win_rate": round(len(wins) / len(with_returns) * 100, 1),
                "avg_return": round(sum(returns) / len(returns), 2),
                "max_return": round(max(returns), 2),
                "min_return": round(min(returns), 2),
            }

        return {
            "generated_at": datetime.now().isoformat(),
            "by_score_range": results,
        }

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        取得綜合統計報告（含週期、訊號、評分區間）

        Returns:
            完整的統計報告
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "basic": self.get_statistics(),
            "by_period": self.get_stats_by_period()["periods"],
            "by_signal": self.get_stats_by_signal()["by_signal"],
            "by_score_range": self.get_stats_by_score_range()["by_score_range"],
        }


# 全域實例
_tracker: Optional[PerformanceTracker] = None


def get_performance_tracker() -> PerformanceTracker:
    """取得追蹤器實例"""
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker
