from typing import Any
from datetime import datetime, timezone

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import (
    AdaptivePolicy,
    AdaptiveEvidence,
    ModelRefreshRecommendation
)

class ModelRefreshPlanner:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings

    def recommend_model_refresh(self, model_artifacts: list[Any], evidence_items: list[AdaptiveEvidence], policy: AdaptivePolicy) -> list[ModelRefreshRecommendation]:
        recommendations = []
        ml_evidence = [e for e in evidence_items if e.evidence_type.value == "ML_MODEL"]

        for ev in ml_evidence:
            metrics = ev.metrics
            created_at = ev.generated_at
            age_days = self.calculate_model_age_days(created_at)
            drift_score = self.calculate_simple_drift_score(metrics, {})

            should_retrain = False
            reasons = []

            if age_days > policy.max_model_age_days:
                should_retrain = True
                reasons.append(f"Model age ({age_days:.1f} days) exceeds limit ({policy.max_model_age_days})")

            if drift_score and drift_score > 0.3:
                should_retrain = True
                reasons.append(f"High drift score detected ({drift_score:.2f})")

            if metrics.get("accuracy", 1.0) * 100 < policy.min_ml_score:
                should_retrain = True
                reasons.append(f"Model accuracy ({metrics.get('accuracy', 0)*100:.1f}%) below minimum ({policy.min_ml_score}%)")

            if should_retrain:
                recommendations.append(
                    ModelRefreshRecommendation(
                        model_id=ev.metadata.get("model_id", "unknown"),
                        model_type="classification",
                        target_col="target_1d",
                        should_retrain=True,
                        reason="; ".join(reasons),
                        model_age_days=age_days,
                        drift_score=drift_score,
                        recommended_command=self.build_retrain_command([ev.symbol] if ev.symbol else ["ALL"], "classification", "target_1d")
                    )
                )

        if policy.mode.value != "DISABLED" and not ml_evidence and "ml_filter" in [e.strategy_name for e in evidence_items]:
             recommendations.append(
                ModelRefreshRecommendation(
                    should_retrain=True,
                    reason="ML Filter is active but no models found",
                    recommended_command=self.build_retrain_command(["ALL"], "classification", "target_1d")
                )
            )

        return recommendations

    def calculate_model_age_days(self, created_at: datetime) -> float:
        now = datetime.now(timezone.utc)
        delta = now - created_at
        return delta.total_seconds() / (24 * 3600)

    def calculate_simple_drift_score(self, reference_metrics: dict[str, Any], recent_metrics: dict[str, Any]) -> float | None:
        if not reference_metrics or not recent_metrics:
            return None
        ref_acc = reference_metrics.get("accuracy", 0.0)
        rec_acc = recent_metrics.get("accuracy", 0.0)
        if ref_acc > 0:
            return max(0.0, (ref_acc - rec_acc) / ref_acc)
        return None

    def build_retrain_command(self, symbols: list[str], model_type: str, target_col: str) -> list[str]:
        base = ["python", "-m", "bist_signal_bot", "ml-train", "train"]
        if symbols and symbols != ["ALL"]:
            base.extend(["--symbols"] + symbols)
        return base
