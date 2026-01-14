"""
weight_optimizer.py - 評分權重優化服務
V10.38: 基於歷史數據分析最佳權重配置

功能：
- 分析歷史推薦績效
- 計算不同權重組合的回測效果
- 使用 Grid Search 尋找最優權重
- 生成權重調整建議
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import itertools

# 資料路徑
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRACKER_FILE = DATA_DIR / "performance_tracker.json"
OPTIMIZER_FILE = DATA_DIR / "weight_optimization.json"


class WeightOptimizer:
    """評分權重優化器"""

    # 預設權重搜索範圍
    WEIGHT_RANGES = {
        "technical": [0.30, 0.35, 0.40, 0.45, 0.50, 0.55],
        "fundamental": [0.15, 0.20, 0.25, 0.30, 0.35],
        "chip": [0.10, 0.15, 0.20, 0.25, 0.30],
        "news": [0.05, 0.10, 0.15],
    }

    # 評估指標權重
    METRIC_WEIGHTS = {
        "win_rate": 0.35,        # 勝率
        "avg_return": 0.30,      # 平均報酬
        "sharpe_ratio": 0.20,    # 風險調整報酬
        "max_drawdown": 0.15,    # 最大回撤
    }

    def __init__(self):
        self._history = self._load_history()
        self._optimization_results: Dict = {}

    def _load_history(self) -> List[Dict]:
        """載入歷史推薦數據"""
        try:
            if TRACKER_FILE.exists():
                with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("recommendations", [])
        except Exception as e:
            print(f"載入歷史數據失敗: {e}")
        return []

    def _save_results(self):
        """儲存優化結果"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(OPTIMIZER_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._optimization_results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存優化結果失敗: {e}")

    def analyze_current_performance(self) -> Dict[str, Any]:
        """
        分析當前權重設定的績效

        Returns:
            績效分析結果
        """
        if not self._history:
            return {"error": "無歷史數據", "recommendations_count": 0}

        # 篩選已結束的推薦（有報酬率數據）
        completed = [
            r for r in self._history
            if r.get("return_percent") is not None and r.get("status") == "closed"
        ]

        if not completed:
            # 如果沒有已結束的，使用活躍的計算
            completed = [
                r for r in self._history
                if r.get("return_percent") is not None
            ]

        if not completed:
            return {"error": "無已完成的推薦數據", "recommendations_count": len(self._history)}

        # 計算績效指標
        returns = [r["return_percent"] for r in completed]
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r <= 0]

        win_rate = len(wins) / len(returns) * 100 if returns else 0
        avg_return = sum(returns) / len(returns) if returns else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        # 計算最大回撤 (簡化版)
        max_drawdown = min(returns) if returns else 0

        # 計算 Sharpe Ratio (簡化版，假設無風險利率 2%)
        if len(returns) > 1:
            import statistics
            std_dev = statistics.stdev(returns)
            sharpe_ratio = (avg_return - 0.02) / std_dev if std_dev > 0 else 0
        else:
            sharpe_ratio = 0

        # 按信號類型分析
        by_signal = {}
        for r in completed:
            signal = r.get("signal", "unknown")
            if signal not in by_signal:
                by_signal[signal] = {"count": 0, "returns": [], "wins": 0}
            by_signal[signal]["count"] += 1
            by_signal[signal]["returns"].append(r["return_percent"])
            if r["return_percent"] > 0:
                by_signal[signal]["wins"] += 1

        signal_stats = {}
        for signal, data in by_signal.items():
            signal_stats[signal] = {
                "count": data["count"],
                "win_rate": data["wins"] / data["count"] * 100 if data["count"] > 0 else 0,
                "avg_return": sum(data["returns"]) / len(data["returns"]) if data["returns"] else 0,
            }

        # 按信心分數區間分析
        by_confidence = {"high": [], "medium": [], "low": []}
        for r in completed:
            conf = r.get("confidence", 0)
            if conf >= 80:
                by_confidence["high"].append(r["return_percent"])
            elif conf >= 60:
                by_confidence["medium"].append(r["return_percent"])
            else:
                by_confidence["low"].append(r["return_percent"])

        confidence_stats = {}
        for level, rets in by_confidence.items():
            if rets:
                wins_count = len([r for r in rets if r > 0])
                confidence_stats[level] = {
                    "count": len(rets),
                    "win_rate": wins_count / len(rets) * 100,
                    "avg_return": sum(rets) / len(rets),
                }

        return {
            "total_recommendations": len(self._history),
            "completed_recommendations": len(completed),
            "overall": {
                "win_rate": round(win_rate, 2),
                "avg_return": round(avg_return, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "max_drawdown": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe_ratio, 3),
            },
            "by_signal": signal_stats,
            "by_confidence": confidence_stats,
            "analysis_date": datetime.now().isoformat(),
        }

    def _generate_weight_combinations(self) -> List[Dict[str, float]]:
        """
        生成所有有效的權重組合（總和為 1.0）

        Returns:
            權重組合列表
        """
        combinations = []

        for t in self.WEIGHT_RANGES["technical"]:
            for f in self.WEIGHT_RANGES["fundamental"]:
                for c in self.WEIGHT_RANGES["chip"]:
                    for n in self.WEIGHT_RANGES["news"]:
                        total = t + f + c + n
                        # 允許 ±0.01 的誤差
                        if 0.99 <= total <= 1.01:
                            combinations.append({
                                "technical": t,
                                "fundamental": f,
                                "chip": c,
                                "news": n,
                            })

        return combinations

    def _simulate_with_weights(self, weights: Dict[str, float],
                                recommendations: List[Dict]) -> Dict[str, float]:
        """
        使用指定權重模擬績效

        注意：這是簡化版模擬，假設權重變化會線性影響結果

        Args:
            weights: 權重配置
            recommendations: 推薦記錄

        Returns:
            模擬績效指標
        """
        if not recommendations:
            return {"win_rate": 0, "avg_return": 0, "sharpe_ratio": 0, "max_drawdown": 0}

        # 簡化模擬：假設各維度得分對報酬率的影響
        # 實際上應該重新計算每檔股票的分數，但這需要原始數據
        # 這裡使用近似方法

        # 基準權重（當前設定）
        base_weights = {
            "technical": 0.50,
            "fundamental": 0.25,
            "chip": 0.15,
            "news": 0.10,
        }

        # 計算權重調整因子
        adjustment = {}
        for key in weights:
            adjustment[key] = weights[key] / base_weights[key] if base_weights[key] > 0 else 1

        # 模擬調整後的報酬率
        adjusted_returns = []
        for r in recommendations:
            if r.get("return_percent") is not None:
                base_return = r["return_percent"]

                # 簡化假設：技術面權重增加會放大波動
                # 基本面權重增加會減少波動但降低報酬
                # 籌碼面權重增加對趨勢股有利
                tech_factor = 1 + (adjustment["technical"] - 1) * 0.3
                fund_factor = 1 + (adjustment["fundamental"] - 1) * 0.1
                chip_factor = 1 + (adjustment["chip"] - 1) * 0.2
                news_factor = 1 + (adjustment["news"] - 1) * 0.1

                combined_factor = (tech_factor + fund_factor + chip_factor + news_factor) / 4
                adjusted_return = base_return * combined_factor

                adjusted_returns.append(adjusted_return)

        if not adjusted_returns:
            return {"win_rate": 0, "avg_return": 0, "sharpe_ratio": 0, "max_drawdown": 0}

        # 計算績效指標
        wins = [r for r in adjusted_returns if r > 0]
        win_rate = len(wins) / len(adjusted_returns) * 100

        avg_return = sum(adjusted_returns) / len(adjusted_returns)
        max_drawdown = min(adjusted_returns)

        # Sharpe Ratio
        if len(adjusted_returns) > 1:
            import statistics
            std_dev = statistics.stdev(adjusted_returns)
            sharpe_ratio = (avg_return - 0.02) / std_dev if std_dev > 0 else 0
        else:
            sharpe_ratio = 0

        return {
            "win_rate": round(win_rate, 2),
            "avg_return": round(avg_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "max_drawdown": round(max_drawdown, 2),
        }

    def _calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """
        計算綜合評分

        Args:
            metrics: 績效指標

        Returns:
            綜合評分 (0-100)
        """
        # 標準化各指標
        normalized = {
            "win_rate": metrics["win_rate"] / 100,  # 0-1
            "avg_return": min(max(metrics["avg_return"] / 10, -1), 1) / 2 + 0.5,  # 標準化到 0-1
            "sharpe_ratio": min(max(metrics["sharpe_ratio"] / 2, -1), 1) / 2 + 0.5,  # 標準化到 0-1
            "max_drawdown": 1 - min(abs(metrics["max_drawdown"]) / 20, 1),  # 回撤越小越好
        }

        # 加權計算
        score = 0
        for metric, weight in self.METRIC_WEIGHTS.items():
            score += normalized.get(metric, 0.5) * weight

        return round(score * 100, 2)

    def optimize_weights(self, min_samples: int = 30) -> Dict[str, Any]:
        """
        優化權重配置

        Args:
            min_samples: 最少樣本數

        Returns:
            優化結果
        """
        # 取得有報酬率的推薦記錄
        completed = [
            r for r in self._history
            if r.get("return_percent") is not None
        ]

        if len(completed) < min_samples:
            return {
                "error": f"樣本數不足，需要至少 {min_samples} 筆，目前只有 {len(completed)} 筆",
                "current_count": len(completed),
                "required_count": min_samples,
            }

        # 生成權重組合
        combinations = self._generate_weight_combinations()

        if not combinations:
            return {"error": "無法生成有效的權重組合"}

        # 評估每個組合
        results = []
        for weights in combinations:
            metrics = self._simulate_with_weights(weights, completed)
            score = self._calculate_composite_score(metrics)

            results.append({
                "weights": weights,
                "metrics": metrics,
                "composite_score": score,
            })

        # 排序找出最佳組合
        results.sort(key=lambda x: x["composite_score"], reverse=True)

        # 取得前 5 名
        top_5 = results[:5]

        # 當前權重的績效
        current_weights = {
            "technical": 0.50,
            "fundamental": 0.25,
            "chip": 0.15,
            "news": 0.10,
        }
        current_metrics = self._simulate_with_weights(current_weights, completed)
        current_score = self._calculate_composite_score(current_metrics)

        # 計算最佳權重相對於當前的改善幅度
        best = top_5[0]
        improvement = best["composite_score"] - current_score

        # 生成建議
        recommendations = self._generate_recommendations(best["weights"], current_weights, improvement)

        result = {
            "optimization_date": datetime.now().isoformat(),
            "samples_used": len(completed),
            "combinations_tested": len(combinations),
            "current": {
                "weights": current_weights,
                "metrics": current_metrics,
                "composite_score": current_score,
            },
            "best": best,
            "top_5": top_5,
            "improvement": round(improvement, 2),
            "recommendations": recommendations,
        }

        # 儲存結果
        self._optimization_results = result
        self._save_results()

        return result

    def _generate_recommendations(self, best_weights: Dict[str, float],
                                   current_weights: Dict[str, float],
                                   improvement: float) -> List[str]:
        """
        生成權重調整建議

        Args:
            best_weights: 最佳權重
            current_weights: 當前權重
            improvement: 改善幅度

        Returns:
            建議列表
        """
        recommendations = []

        # 檢查改善幅度
        if improvement < 1:
            recommendations.append("當前權重配置已接近最優，無需大幅調整")
            return recommendations

        # 分析各維度的變化
        for dim in ["technical", "fundamental", "chip", "news"]:
            diff = best_weights[dim] - current_weights[dim]
            if abs(diff) >= 0.05:  # 差異超過 5%
                direction = "增加" if diff > 0 else "減少"
                dim_names = {
                    "technical": "技術面",
                    "fundamental": "基本面",
                    "chip": "籌碼面",
                    "news": "新聞情緒",
                }
                recommendations.append(
                    f"建議{direction}{dim_names[dim]}權重 {abs(diff)*100:.0f}%"
                )

        # 整體建議
        if improvement >= 5:
            recommendations.append(f"預估可提升綜合評分 {improvement:.1f} 分")
        elif improvement >= 2:
            recommendations.append(f"預估可小幅提升綜合評分 {improvement:.1f} 分")

        return recommendations

    def get_weight_analysis_by_market_condition(self) -> Dict[str, Any]:
        """
        根據市場狀況分析最適權重

        Returns:
            不同市場狀況的最適權重分析
        """
        if not self._history:
            return {"error": "無歷史數據"}

        completed = [r for r in self._history if r.get("return_percent") is not None]

        if len(completed) < 50:
            return {"error": "樣本數不足，需要至少 50 筆"}

        # 按市場狀況分類（這裡簡化使用報酬率作為市場指標）
        # 實際應該使用大盤指數數據
        bull_market = []  # 多頭（大部分股票上漲）
        bear_market = []  # 空頭（大部分股票下跌）
        sideways = []     # 盤整

        # 按週分組
        from collections import defaultdict
        weekly_groups = defaultdict(list)
        for r in completed:
            week = r["date"][:10][:7]  # YYYY-MM
            weekly_groups[week].append(r)

        for week, records in weekly_groups.items():
            if len(records) < 3:
                continue
            avg_return = sum(r["return_percent"] for r in records) / len(records)
            if avg_return > 3:
                bull_market.extend(records)
            elif avg_return < -3:
                bear_market.extend(records)
            else:
                sideways.extend(records)

        # 分析各市場狀況的最適權重
        analysis = {}

        for market_name, records in [
            ("bull_market", bull_market),
            ("bear_market", bear_market),
            ("sideways", sideways)
        ]:
            if len(records) >= 10:
                # 簡化分析：計算該市場狀況下的最佳權重傾向
                high_return_records = [r for r in records if r["return_percent"] > 0]
                if high_return_records:
                    # 分析成功推薦的共同特徵
                    avg_confidence = sum(r.get("confidence", 50) for r in high_return_records) / len(high_return_records)

                    # 根據市場狀況建議權重調整
                    if market_name == "bull_market":
                        suggested = {
                            "technical": 0.55,  # 多頭市場技術面更重要
                            "fundamental": 0.20,
                            "chip": 0.15,
                            "news": 0.10,
                        }
                        advice = "多頭市場建議增加技術面權重，順勢操作"
                    elif market_name == "bear_market":
                        suggested = {
                            "technical": 0.35,  # 空頭市場基本面更重要
                            "fundamental": 0.35,
                            "chip": 0.15,
                            "news": 0.15,
                        }
                        advice = "空頭市場建議增加基本面權重，注重防禦"
                    else:
                        suggested = {
                            "technical": 0.40,  # 盤整市場籌碼面更重要
                            "fundamental": 0.25,
                            "chip": 0.25,
                            "news": 0.10,
                        }
                        advice = "盤整市場建議增加籌碼面權重，跟隨主力"

                    analysis[market_name] = {
                        "sample_count": len(records),
                        "win_rate": len(high_return_records) / len(records) * 100,
                        "avg_return": sum(r["return_percent"] for r in records) / len(records),
                        "suggested_weights": suggested,
                        "advice": advice,
                    }

        return {
            "analysis_date": datetime.now().isoformat(),
            "total_samples": len(completed),
            "market_conditions": analysis,
        }

    def get_score_threshold_analysis(self) -> Dict[str, Any]:
        """
        分析最佳分數閾值

        Returns:
            閾值分析結果
        """
        if not self._history:
            return {"error": "無歷史數據"}

        completed = [r for r in self._history if r.get("return_percent") is not None]

        if len(completed) < 30:
            return {"error": "樣本數不足"}

        # 按信心分數區間統計
        thresholds = [50, 55, 60, 65, 70, 75, 80, 85, 90]
        threshold_stats = []

        for threshold in thresholds:
            filtered = [r for r in completed if r.get("confidence", 0) >= threshold]
            if filtered:
                wins = [r for r in filtered if r["return_percent"] > 0]
                win_rate = len(wins) / len(filtered) * 100
                avg_return = sum(r["return_percent"] for r in filtered) / len(filtered)

                threshold_stats.append({
                    "threshold": threshold,
                    "count": len(filtered),
                    "win_rate": round(win_rate, 2),
                    "avg_return": round(avg_return, 2),
                    # 計算綜合分數 (考慮數量和品質的平衡)
                    "quality_score": round(win_rate * 0.6 + (avg_return + 10) * 2, 2),
                })

        # 找出最佳閾值
        if threshold_stats:
            # 使用綜合分數排序
            best = max(threshold_stats, key=lambda x: x["quality_score"])

            # 找出最佳平衡點 (數量和品質)
            balanced = max(
                [t for t in threshold_stats if t["count"] >= 10],
                key=lambda x: x["quality_score"],
                default=best
            )

            return {
                "analysis_date": datetime.now().isoformat(),
                "total_samples": len(completed),
                "threshold_stats": threshold_stats,
                "recommended_threshold": balanced["threshold"],
                "best_quality_threshold": best["threshold"],
                "recommendation": f"建議使用 {balanced['threshold']} 分作為買進閾值，"
                                  f"可獲得 {balanced['win_rate']:.1f}% 勝率和 {balanced['avg_return']:.1f}% 平均報酬",
            }

        return {"error": "無法進行閾值分析"}


# 全局實例
_optimizer_instance = None


def get_weight_optimizer() -> WeightOptimizer:
    """取得權重優化器實例"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = WeightOptimizer()
    return _optimizer_instance
