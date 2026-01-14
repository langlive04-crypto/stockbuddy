"""
A/B 測試框架 V10.38

支援推薦算法的 A/B 測試，比較不同版本的表現

功能:
- 實驗分組
- 流量分配
- 結果追蹤
- 統計顯著性檢驗
"""

import hashlib
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

# 實驗配置檔案
EXPERIMENTS_FILE = Path(__file__).parent.parent / "data" / "ab_experiments.json"


@dataclass
class ExperimentVariant:
    """實驗變體"""
    id: str
    name: str
    description: str
    traffic_ratio: float  # 0-1 流量佔比
    config: Dict = field(default_factory=dict)


@dataclass
class Experiment:
    """A/B 實驗"""
    id: str
    name: str
    description: str
    status: str  # draft, running, paused, completed
    created_at: str
    variants: List[ExperimentVariant]
    default_variant: str
    metrics: List[str] = field(default_factory=list)
    results: Dict = field(default_factory=dict)


@dataclass
class ExperimentAssignment:
    """用戶實驗分配"""
    user_id: str
    experiment_id: str
    variant_id: str
    assigned_at: str


class ABTestingFramework:
    """
    A/B 測試框架

    管理實驗、分配流量、追蹤結果
    """

    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.assignments: Dict[str, Dict[str, ExperimentAssignment]] = {}
        self._load_experiments()

    def _ensure_data_dir(self):
        """確保數據目錄存在"""
        EXPERIMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_experiments(self):
        """載入實驗配置"""
        self._ensure_data_dir()
        if EXPERIMENTS_FILE.exists():
            try:
                with open(EXPERIMENTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for exp_data in data.get("experiments", []):
                    variants = [
                        ExperimentVariant(**v)
                        for v in exp_data.get("variants", [])
                    ]
                    exp = Experiment(
                        id=exp_data["id"],
                        name=exp_data["name"],
                        description=exp_data.get("description", ""),
                        status=exp_data.get("status", "draft"),
                        created_at=exp_data.get("created_at", datetime.now().isoformat()),
                        variants=variants,
                        default_variant=exp_data.get("default_variant", "control"),
                        metrics=exp_data.get("metrics", []),
                        results=exp_data.get("results", {}),
                    )
                    self.experiments[exp.id] = exp

                logger.info(f"Loaded {len(self.experiments)} experiments")
            except Exception as e:
                logger.error(f"Failed to load experiments: {e}")

    def _save_experiments(self):
        """儲存實驗配置"""
        self._ensure_data_dir()
        data = {
            "experiments": [
                {
                    "id": exp.id,
                    "name": exp.name,
                    "description": exp.description,
                    "status": exp.status,
                    "created_at": exp.created_at,
                    "variants": [asdict(v) for v in exp.variants],
                    "default_variant": exp.default_variant,
                    "metrics": exp.metrics,
                    "results": exp.results,
                }
                for exp in self.experiments.values()
            ],
            "updated_at": datetime.now().isoformat(),
        }

        with open(EXPERIMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str = "",
        variants: Optional[List[Dict]] = None,
        metrics: Optional[List[str]] = None
    ) -> Experiment:
        """
        建立新實驗

        Args:
            experiment_id: 實驗 ID
            name: 實驗名稱
            description: 描述
            variants: 變體列表
            metrics: 追蹤指標

        Returns:
            新建立的實驗
        """
        if experiment_id in self.experiments:
            raise ValueError(f"Experiment '{experiment_id}' already exists")

        # 預設變體：control (50%) vs treatment (50%)
        if variants is None:
            variants = [
                {"id": "control", "name": "Control", "description": "原始版本", "traffic_ratio": 0.5},
                {"id": "treatment", "name": "Treatment", "description": "新版本", "traffic_ratio": 0.5},
            ]

        # 預設指標
        if metrics is None:
            metrics = ["win_rate", "avg_return", "sharpe_ratio"]

        # 驗證流量比例總和為 1
        total_ratio = sum(v.get("traffic_ratio", 0) for v in variants)
        if abs(total_ratio - 1.0) > 0.01:
            raise ValueError(f"Traffic ratios must sum to 1.0, got {total_ratio}")

        exp_variants = [
            ExperimentVariant(
                id=v["id"],
                name=v["name"],
                description=v.get("description", ""),
                traffic_ratio=v["traffic_ratio"],
                config=v.get("config", {}),
            )
            for v in variants
        ]

        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            status="draft",
            created_at=datetime.now().isoformat(),
            variants=exp_variants,
            default_variant=exp_variants[0].id,
            metrics=metrics,
            results={},
        )

        self.experiments[experiment_id] = experiment
        self._save_experiments()

        logger.info(f"Created experiment: {experiment_id}")
        return experiment

    def start_experiment(self, experiment_id: str) -> bool:
        """啟動實驗"""
        if experiment_id not in self.experiments:
            return False

        exp = self.experiments[experiment_id]
        exp.status = "running"
        self._save_experiments()

        logger.info(f"Started experiment: {experiment_id}")
        return True

    def pause_experiment(self, experiment_id: str) -> bool:
        """暫停實驗"""
        if experiment_id not in self.experiments:
            return False

        exp = self.experiments[experiment_id]
        exp.status = "paused"
        self._save_experiments()

        logger.info(f"Paused experiment: {experiment_id}")
        return True

    def complete_experiment(self, experiment_id: str) -> bool:
        """結束實驗"""
        if experiment_id not in self.experiments:
            return False

        exp = self.experiments[experiment_id]
        exp.status = "completed"
        self._save_experiments()

        logger.info(f"Completed experiment: {experiment_id}")
        return True

    def get_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[ExperimentVariant]:
        """
        取得用戶的實驗變體

        使用 deterministic hashing 確保同一用戶總是分到同一組

        Args:
            experiment_id: 實驗 ID
            user_id: 用戶 ID

        Returns:
            分配的變體，若實驗不存在或未運行則返回 None
        """
        if experiment_id not in self.experiments:
            return None

        exp = self.experiments[experiment_id]

        # 只有運行中的實驗才分配
        if exp.status != "running":
            # 返回預設變體
            return next(
                (v for v in exp.variants if v.id == exp.default_variant),
                exp.variants[0] if exp.variants else None
            )

        # 檢查是否已有分配
        user_assignments = self.assignments.get(user_id, {})
        if experiment_id in user_assignments:
            variant_id = user_assignments[experiment_id].variant_id
            return next(
                (v for v in exp.variants if v.id == variant_id),
                None
            )

        # 使用 hash 決定分組（確保 deterministic）
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 10000) / 10000  # 0-1 之間的值

        # 根據流量比例分配
        cumulative = 0
        selected_variant = exp.variants[-1]  # 預設最後一個

        for variant in exp.variants:
            cumulative += variant.traffic_ratio
            if bucket < cumulative:
                selected_variant = variant
                break

        # 記錄分配
        assignment = ExperimentAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=selected_variant.id,
            assigned_at=datetime.now().isoformat(),
        )

        if user_id not in self.assignments:
            self.assignments[user_id] = {}
        self.assignments[user_id][experiment_id] = assignment

        return selected_variant

    def record_event(
        self,
        experiment_id: str,
        user_id: str,
        event_type: str,
        event_data: Dict
    ):
        """
        記錄實驗事件

        Args:
            experiment_id: 實驗 ID
            user_id: 用戶 ID
            event_type: 事件類型 (impression, click, conversion, etc.)
            event_data: 事件數據
        """
        if experiment_id not in self.experiments:
            return

        # 取得用戶的變體
        variant = self.get_variant(experiment_id, user_id)
        if not variant:
            return

        exp = self.experiments[experiment_id]

        # 初始化結果結構
        if variant.id not in exp.results:
            exp.results[variant.id] = {
                "impressions": 0,
                "conversions": 0,
                "total_return": 0,
                "events": [],
            }

        # 更新計數
        results = exp.results[variant.id]
        if event_type == "impression":
            results["impressions"] += 1
        elif event_type == "conversion":
            results["conversions"] += 1
            results["total_return"] += event_data.get("return_pct", 0)

        # 記錄事件（限制數量）
        if len(results["events"]) < 1000:
            results["events"].append({
                "type": event_type,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "data": event_data,
            })

        self._save_experiments()

    def analyze_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        分析實驗結果

        Args:
            experiment_id: 實驗 ID

        Returns:
            分析結果，包含統計顯著性檢驗
        """
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}

        exp = self.experiments[experiment_id]

        if not exp.results:
            return {"error": "No results yet"}

        analysis = {
            "experiment_id": experiment_id,
            "name": exp.name,
            "status": exp.status,
            "variants": {},
            "winner": None,
            "statistical_significance": False,
        }

        variant_stats = []

        for variant in exp.variants:
            results = exp.results.get(variant.id, {})
            impressions = results.get("impressions", 0)
            conversions = results.get("conversions", 0)
            total_return = results.get("total_return", 0)

            conversion_rate = conversions / impressions if impressions > 0 else 0
            avg_return = total_return / conversions if conversions > 0 else 0

            stats = {
                "variant_id": variant.id,
                "variant_name": variant.name,
                "impressions": impressions,
                "conversions": conversions,
                "conversion_rate": round(conversion_rate, 4),
                "avg_return": round(avg_return, 2),
            }

            analysis["variants"][variant.id] = stats
            variant_stats.append(stats)

        # 找出最佳變體
        if len(variant_stats) >= 2:
            sorted_variants = sorted(
                variant_stats,
                key=lambda x: (x["conversion_rate"], x["avg_return"]),
                reverse=True
            )

            best = sorted_variants[0]
            second = sorted_variants[1]

            analysis["winner"] = best["variant_id"]

            # 簡易統計顯著性檢驗（樣本數足夠大）
            if best["impressions"] >= 100 and second["impressions"] >= 100:
                # 使用 Z-test 近似
                p1 = best["conversion_rate"]
                p2 = second["conversion_rate"]
                n1 = best["impressions"]
                n2 = second["impressions"]

                if p1 > p2:
                    pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)
                    if pooled_p > 0 and pooled_p < 1:
                        se = (pooled_p * (1 - pooled_p) * (1/n1 + 1/n2)) ** 0.5
                        if se > 0:
                            z_score = (p1 - p2) / se
                            # Z > 1.96 表示 95% 顯著性
                            analysis["statistical_significance"] = z_score > 1.96
                            analysis["z_score"] = round(z_score, 2)

        return analysis

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """取得實驗詳情"""
        if experiment_id not in self.experiments:
            return None
        return asdict(self.experiments[experiment_id])

    def list_experiments(self, status: Optional[str] = None) -> List[Dict]:
        """列出所有實驗"""
        experiments = []
        for exp in self.experiments.values():
            if status is None or exp.status == status:
                experiments.append({
                    "id": exp.id,
                    "name": exp.name,
                    "status": exp.status,
                    "variants_count": len(exp.variants),
                    "created_at": exp.created_at,
                })
        return experiments


# 全域實例
_framework: Optional[ABTestingFramework] = None


def get_ab_framework() -> ABTestingFramework:
    """取得 A/B 測試框架實例"""
    global _framework
    if _framework is None:
        _framework = ABTestingFramework()
    return _framework
