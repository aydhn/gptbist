import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import ModelDriftFinding, ModelDriftType, ModelGovernanceStatus


class ModelDriftDetector:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

    def drift_score(self, baseline: list[float], current: list[float]) -> float | None:
        if not baseline or not current:
            return None

        min_sample = getattr(self.settings, "MODEL_DRIFT_MIN_SAMPLE", 30)
        if len(baseline) < min_sample or len(current) < min_sample:
            return None

        # Extremely simplified drift score for the registry MVP
        # e.g. Absolute difference in means scaled by std, mapped to 0-100
        import statistics
        try:
            mean_b = statistics.mean(baseline)
            std_b = statistics.stdev(baseline) if len(baseline) > 1 else 1.0
            if std_b == 0:
                std_b = 1.0

            mean_c = statistics.mean(current)

            # z-score difference
            z_diff = abs(mean_c - mean_b) / std_b

            # Map z_diff to 0-100 (e.g. z=0 -> 0, z=3 -> 100)
            score = min(100.0, z_diff * 33.3)
            return score
        except Exception as e:
            self.logger.warning(f"Error calculating drift score: {e}")
            return None

    def classify_drift(self, score: float | None) -> ModelGovernanceStatus:
        if score is None:
            return ModelGovernanceStatus.INSUFFICIENT_DATA

        warn_thresh = getattr(self.settings, "MODEL_DRIFT_SCORE_WARN", 60.0)
        fail_thresh = warn_thresh + 20.0

        if score >= fail_thresh:
            return ModelGovernanceStatus.FAIL
        elif score >= warn_thresh:
            return ModelGovernanceStatus.WATCH
        return ModelGovernanceStatus.PASS

    def detect_prediction_drift(self, model_id: str, baseline_predictions: list[float],
                                current_predictions: list[float], baseline_window: str = "train",
                                current_window: str = "recent") -> list[ModelDriftFinding]:

        if not getattr(self.settings, "MODEL_DRIFT_ENABLED", True):
            return []

        score = self.drift_score(baseline_predictions, current_predictions)
        status = self.classify_drift(score)

        # Optional: Return empty if no finding (e.g., status in [PASS, INSUFFICIENT_DATA]),
        # but for tracking, we return a finding regardless of status.

        finding = ModelDriftFinding(
            drift_id=f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            drift_type=ModelDriftType.PREDICTION_DISTRIBUTION_SHIFT,
            baseline_window=baseline_window,
            current_window=current_window,
            drift_score=score,
            status=status,
            message=f"Prediction distribution shift score: {score:.1f}" if score is not None else "Insufficient data for prediction drift"
        )
        return [finding]

    def detect_performance_decay(self, model_id: str, baseline_metric: float | None,
                                 current_metric: float | None, metric_name: str,
                                 baseline_window: str = "validation", current_window: str = "live") -> ModelDriftFinding | None:

        if not getattr(self.settings, "MODEL_DRIFT_ENABLED", True):
            return None

        if baseline_metric is None or current_metric is None:
            return None

        decay_warn = getattr(self.settings, "MODEL_PERFORMANCE_DECAY_WARN", 0.10)

        # Simple ratio
        # Assuming higher is better. If metric is loss, it should be reversed, but we simplify here.
        if baseline_metric == 0:
            return None

        decay = (baseline_metric - current_metric) / baseline_metric
        status = ModelGovernanceStatus.PASS
        if decay >= decay_warn + 0.10:
            status = ModelGovernanceStatus.FAIL
        elif decay >= decay_warn:
            status = ModelGovernanceStatus.WATCH

        finding = ModelDriftFinding(
            drift_id=f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            drift_type=ModelDriftType.PERFORMANCE_DECAY,
            baseline_window=baseline_window,
            current_window=current_window,
            baseline_value=baseline_metric,
            current_value=current_metric,
            drift_score=decay * 100, # as percentage
            status=status,
            message=f"Performance decay on {metric_name}: {decay*100:.1f}%"
        )
        return finding

    def detect_calibration_decay(self, model_id: str, baseline_ece: float | None,
                                 current_ece: float | None,
                                 baseline_window: str = "validation", current_window: str = "live") -> ModelDriftFinding | None:

        if not getattr(self.settings, "MODEL_DRIFT_ENABLED", True):
            return None

        if baseline_ece is None or current_ece is None:
            return None

        decay_warn = getattr(self.settings, "MODEL_CALIBRATION_DECAY_WARN", 0.05)

        # ECE: lower is better, so increase is decay
        increase = current_ece - baseline_ece
        status = ModelGovernanceStatus.PASS
        if increase >= decay_warn + 0.05:
            status = ModelGovernanceStatus.FAIL
        elif increase >= decay_warn:
            status = ModelGovernanceStatus.WATCH

        finding = ModelDriftFinding(
            drift_id=f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            drift_type=ModelDriftType.CALIBRATION_DECAY,
            baseline_window=baseline_window,
            current_window=current_window,
            baseline_value=baseline_ece,
            current_value=current_ece,
            drift_score=increase * 100, # as points
            status=status,
            message=f"Calibration ECE increased by {increase:.3f}"
        )
        return finding

    def detect_feature_drift_linked(self, model_id: str, feature_drift_findings: list[Any]) -> list[ModelDriftFinding]:
        if not getattr(self.settings, "MODEL_DRIFT_ENABLED", True):
            return []

        findings = []
        for fd in feature_drift_findings:
            # Assuming FeatureDriftFinding has drift_score, status, feature_name etc.
            status = ModelGovernanceStatus.PASS
            # Map FeatureQualityStatus to ModelGovernanceStatus
            if hasattr(fd, "status"):
                if fd.status.value == "FAIL":
                    status = ModelGovernanceStatus.FAIL
                elif fd.status.value == "WATCH":
                    status = ModelGovernanceStatus.WATCH

            findings.append(ModelDriftFinding(
                drift_id=f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
                model_id=model_id,
                drift_type=ModelDriftType.FEATURE_DRIFT,
                baseline_window="feature_store_baseline",
                current_window="feature_store_current",
                drift_score=fd.drift_score if hasattr(fd, "drift_score") else None,
                status=status,
                message=f"Linked feature drift on {getattr(fd, 'feature_name', 'unknown')}: {getattr(fd, 'message', '')}"
            ))
        return findings
