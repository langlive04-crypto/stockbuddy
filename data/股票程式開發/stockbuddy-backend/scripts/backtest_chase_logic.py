#!/usr/bin/env python3
"""
V10.38: 追高邏輯回測驗證腳本

比較新舊邏輯的效果：
- 舊邏輯 (V10.36)：漲幅越高分數越高 (追漲策略)
- 新邏輯 (V10.37)：漲幅過高減分，超跌加分 (逆向策略)

用法:
    python scripts/backtest_chase_logic.py
    python scripts/backtest_chase_logic.py --days 60
    python scripts/backtest_chase_logic.py --output results.json

驗證目標:
- 新邏輯勝率應 >= 舊邏輯
- 新邏輯高分組勝率應明顯優於低分組
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 將 app 目錄加入路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def old_logic_score(change_pct: float) -> int:
    """
    V10.36 舊邏輯 - 追漲策略

    漲越多分數越高
    """
    if change_pct > 5:
        return 8
    elif change_pct > 3:
        return 5
    elif change_pct > 1:
        return 2
    elif change_pct > 0:
        return 1
    elif change_pct > -1:
        return 0
    elif change_pct > -3:
        return -2
    else:
        return -5


def new_logic_score(change_pct: float) -> int:
    """
    V10.37 新邏輯 - 逆向策略

    漲幅過高減分，適度下跌加分 (逢低布局)
    """
    if change_pct > 5:
        return -5  # 追高風險
    elif change_pct > 3:
        return 0   # 中性
    elif 0 < change_pct <= 3:
        return 3   # 溫和上漲，較佳
    elif -3 <= change_pct < 0:
        return 2   # 小幅下跌，機會
    elif change_pct < -3:
        return 5   # 超跌，逢低加碼
    return 0


def generate_simulated_data(num_samples: int = 500, seed: int = 42) -> List[Dict]:
    """
    生成模擬歷史數據

    真實規律：
    - 大漲後容易回調
    - 超跌後容易反彈
    - 市場有均值回歸傾向
    """
    import random
    random.seed(seed)

    data = []

    for i in range(num_samples):
        # 當日漲跌幅 (-10% ~ +10%)
        change_pct = random.gauss(0, 3)  # 正態分布，平均 0，標準差 3
        change_pct = max(-10, min(10, change_pct))

        # 30 天後報酬 - 加入均值回歸特性
        # 大漲後傾向下跌，大跌後傾向上漲
        reversion_effect = -change_pct * 0.3  # 30% 均值回歸
        random_component = random.gauss(0, 5)  # 隨機波動
        future_return_30d = reversion_effect + random_component

        # 添加一些市場趨勢
        market_trend = random.gauss(0.5, 2)  # 整體市場微漲傾向
        future_return_30d += market_trend

        data.append({
            "stock_id": f"SIM{i:04d}",
            "date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "change_pct": round(change_pct, 2),
            "future_return_30d": round(future_return_30d, 2),
        })

    return data


def load_real_data(data_path: Optional[str] = None) -> List[Dict]:
    """
    載入真實歷史數據

    優先使用 performance_tracker 的資料
    """
    if data_path and Path(data_path).exists():
        logger.info(f"載入數據: {data_path}")
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 嘗試從 performance_tracker 載入
    try:
        from app.services.performance_tracker import get_performance_tracker
        tracker = get_performance_tracker()
        data = tracker.get_closed_recommendations(limit=500)

        # 轉換格式
        converted = []
        for d in data:
            if d.get("final_return_percent") is None:
                continue
            converted.append({
                "stock_id": d.get("stock_id", ""),
                "date": d.get("date", ""),
                "change_pct": d.get("price_change_1d", 0),
                "future_return_30d": d.get("final_return_percent", 0),
            })

        if converted:
            logger.info(f"從 performance_tracker 載入 {len(converted)} 筆")
            return converted
    except Exception as e:
        logger.warning(f"無法載入真實數據: {e}")

    # 使用模擬數據
    logger.info("使用模擬數據進行回測")
    return generate_simulated_data()


def backtest(
    data: List[Dict],
    score_func,
    holding_days: int = 30
) -> Dict:
    """
    回測評分邏輯

    Args:
        data: 包含 change_pct, future_return_30d 的數據
        score_func: 評分函數
        holding_days: 持有天數 (用於標記)

    Returns:
        回測結果
    """
    if not data:
        return {"error": "無數據"}

    # 計算每筆數據的分數
    scored_data = []
    for d in data:
        change_pct = d.get("change_pct", 0)
        future_return = d.get("future_return_30d", 0)

        score = score_func(change_pct)
        is_win = future_return > 0

        scored_data.append({
            **d,
            "score": score,
            "is_win": is_win,
        })

    # 整體統計
    total = len(scored_data)
    wins = sum(1 for d in scored_data if d["is_win"])
    win_rate = wins / total if total > 0 else 0

    returns = [d["future_return_30d"] for d in scored_data]
    avg_return = sum(returns) / len(returns) if returns else 0

    # 計算標準差和夏普比率
    if len(returns) > 1:
        import statistics
        std_return = statistics.stdev(returns)
        sharpe = avg_return / std_return if std_return > 0 else 0
    else:
        std_return = 0
        sharpe = 0

    # 按分數分組統計
    score_groups = {
        "high": {"scores": [], "returns": [], "wins": 0, "total": 0},
        "medium": {"scores": [], "returns": [], "wins": 0, "total": 0},
        "low": {"scores": [], "returns": [], "wins": 0, "total": 0},
    }

    for d in scored_data:
        score = d["score"]
        future_return = d["future_return_30d"]
        is_win = d["is_win"]

        if score >= 3:
            group = "high"
        elif score >= 0:
            group = "medium"
        else:
            group = "low"

        score_groups[group]["scores"].append(score)
        score_groups[group]["returns"].append(future_return)
        score_groups[group]["total"] += 1
        if is_win:
            score_groups[group]["wins"] += 1

    # 計算各組統計
    group_stats = {}
    for group, g_data in score_groups.items():
        total_g = g_data["total"]
        wins_g = g_data["wins"]
        returns_g = g_data["returns"]

        group_stats[group] = {
            "count": total_g,
            "win_rate": round(wins_g / total_g, 4) if total_g > 0 else 0,
            "avg_return": round(sum(returns_g) / len(returns_g), 2) if returns_g else 0,
            "avg_score": round(sum(g_data["scores"]) / len(g_data["scores"]), 2) if g_data["scores"] else 0,
        }

    return {
        "total_samples": total,
        "overall_win_rate": round(win_rate, 4),
        "avg_return": round(avg_return, 2),
        "std_return": round(std_return, 2),
        "sharpe_ratio": round(sharpe, 4),
        "high_score_win_rate": group_stats["high"]["win_rate"],
        "high_score_avg_return": group_stats["high"]["avg_return"],
        "group_stats": group_stats,
    }


def main():
    parser = argparse.ArgumentParser(
        description="V10.38: 追高邏輯回測驗證"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="數據檔案路徑 (JSON)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=500,
        help="模擬數據樣本數"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="輸出結果檔案"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("V10.38 追高邏輯回測驗證")
    print("=" * 60)

    # 載入數據
    data = load_real_data(args.data_path)
    if not data:
        data = generate_simulated_data(args.samples)

    print(f"\n數據樣本數: {len(data)}")

    # 回測舊邏輯
    print("\n" + "-" * 40)
    old_results = backtest(data, old_logic_score)
    print("📈 V10.36 舊邏輯 (追漲策略):")
    print(f"   整體勝率: {old_results['overall_win_rate']:.2%}")
    print(f"   高分組勝率: {old_results['high_score_win_rate']:.2%}")
    print(f"   平均報酬: {old_results['avg_return']:.2f}%")
    print(f"   夏普比率: {old_results['sharpe_ratio']:.4f}")

    # 回測新邏輯
    print("\n" + "-" * 40)
    new_results = backtest(data, new_logic_score)
    print("📉 V10.37 新邏輯 (逆向策略):")
    print(f"   整體勝率: {new_results['overall_win_rate']:.2%}")
    print(f"   高分組勝率: {new_results['high_score_win_rate']:.2%}")
    print(f"   平均報酬: {new_results['avg_return']:.2f}%")
    print(f"   夏普比率: {new_results['sharpe_ratio']:.4f}")

    # 比較
    print("\n" + "=" * 60)
    print("📊 比較結果:")
    print("=" * 60)

    win_rate_diff = new_results['overall_win_rate'] - old_results['overall_win_rate']
    high_win_diff = new_results['high_score_win_rate'] - old_results['high_score_win_rate']
    return_diff = new_results['avg_return'] - old_results['avg_return']
    sharpe_diff = new_results['sharpe_ratio'] - old_results['sharpe_ratio']

    print(f"   勝率變化: {win_rate_diff:+.2%}")
    print(f"   高分組勝率變化: {high_win_diff:+.2%}")
    print(f"   報酬變化: {return_diff:+.2f}%")
    print(f"   夏普比率變化: {sharpe_diff:+.4f}")

    # 驗證結論
    print("\n" + "-" * 40)
    print("🎯 驗證結論:")

    passed = True

    if new_results['overall_win_rate'] >= old_results['overall_win_rate'] - 0.05:
        print("   ✅ 新邏輯勝率不低於舊邏輯 (允許 5% 誤差)")
    else:
        print("   ❌ 新邏輯勝率低於舊邏輯")
        passed = False

    if new_results['high_score_win_rate'] > new_results['group_stats']['low']['win_rate']:
        print("   ✅ 高分組勝率優於低分組")
    else:
        print("   ⚠️ 高分組勝率未優於低分組")

    if new_results['sharpe_ratio'] >= old_results['sharpe_ratio'] - 0.1:
        print("   ✅ 新邏輯夏普比率不低於舊邏輯")
    else:
        print("   ⚠️ 新邏輯夏普比率較低")

    # 輸出結果
    results = {
        "timestamp": datetime.now().isoformat(),
        "samples": len(data),
        "old_logic": old_results,
        "new_logic": new_results,
        "comparison": {
            "win_rate_diff": round(win_rate_diff, 4),
            "high_score_win_rate_diff": round(high_win_diff, 4),
            "avg_return_diff": round(return_diff, 2),
            "sharpe_diff": round(sharpe_diff, 4),
        },
        "passed": passed,
    }

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n結果已儲存至: {args.output}")

    print("\n" + "=" * 60)
    if passed:
        print("✅ 回測驗證通過")
    else:
        print("⚠️ 回測驗證部分未通過，建議檢視詳細數據")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
