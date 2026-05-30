import uuid
import numpy as np
from typing import Any
from bist_signal_bot.feature_store.models import (
    FeatureDriftFinding, FeatureDriftType, FeatureQualityStatus, FeatureFrame
)

class FeatureDriftDetector:
    def detect_drift(self, feature_name: str, baseline_values: list[float], current_values: list[float]) -> list[FeatureDriftFinding]:
        findings = []
        if len(baseline_values) < 30 or len(current_values) < 30:
            return findings

        ms = self.mean_shift(feature_name, baseline_values, current_values)
        if ms: findings.append(ms)

        vs = self.variance_shift(feature_name, baseline_values, current_values)
        if vs: findings.append(vs)

        return findings

    def detect_frame_drift(self, baseline_frame: FeatureFrame, current_frame: FeatureFrame) -> list[FeatureDriftFinding]:
        findings = []
        for feature in baseline_frame.feature_names:
            base_vals = [r.get(feature) for r in baseline_frame.rows if isinstance(r.get(feature), (int, float))]
            curr_vals = [r.get(feature) for r in current_frame.rows if isinstance(r.get(feature), (int, float))]
            findings.extend(self.detect_drift(feature, base_vals, curr_vals))
        return findings

    def mean_shift(self, feature_name: str, baseline: list[float], current: list[float]) -> FeatureDriftFinding | None:
        if not baseline or not current:
            return None
        base_mean = float(np.mean(baseline))
        curr_mean = float(np.mean(current))
        base_std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 1.0

        if base_std == 0:
            base_std = 1.0

        z_score = abs(curr_mean - base_mean) / base_std
        if z_score > 2.0:
            return FeatureDriftFinding(
                drift_id=str(uuid.uuid4()),
                feature_name=feature_name,
                drift_type=FeatureDriftType.MEAN_SHIFT,
                baseline_window="baseline",
                current_window="current",
                baseline_value=base_mean,
                current_value=curr_mean,
                drift_score=z_score,
                status=FeatureQualityStatus.WATCH,
                message=f"Mean shift detected (z-score: {z_score:.2f})"
            )
        return None

    def variance_shift(self, feature_name: str, baseline: list[float], current: list[float]) -> FeatureDriftFinding | None:
        if len(baseline) < 2 or len(current) < 2:
            return None
        base_var = float(np.var(baseline, ddof=1))
        curr_var = float(np.var(current, ddof=1))

        if base_var == 0:
            return None

        ratio = curr_var / base_var if curr_var > base_var else base_var / curr_var
        if ratio > 2.0:
            return FeatureDriftFinding(
                drift_id=str(uuid.uuid4()),
                feature_name=feature_name,
                drift_type=FeatureDriftType.VARIANCE_SHIFT,
                baseline_window="baseline",
                current_window="current",
                baseline_value=base_var,
                current_value=curr_var,
                drift_score=ratio,
                status=FeatureQualityStatus.WATCH,
                message=f"Variance shift detected (ratio: {ratio:.2f})"
            )
        return None

    def missing_ratio_shift(self, feature_name: str, baseline: list[Any], current: list[Any]) -> FeatureDriftFinding | None:
        if not baseline or not current:
            return None
        base_missing = sum(1 for v in baseline if v is None) / len(baseline)
        curr_missing = sum(1 for v in current if v is None) / len(current)

        diff = curr_missing - base_missing
        if diff > 0.10:
            return FeatureDriftFinding(
                drift_id=str(uuid.uuid4()),
                feature_name=feature_name,
                drift_type=FeatureDriftType.MISSING_RATIO_SHIFT,
                baseline_window="baseline",
                current_window="current",
                baseline_value=base_missing,
                current_value=curr_missing,
                drift_score=diff,
                status=FeatureQualityStatus.WATCH,
                message=f"Missing ratio increased by {diff:.2f}"
            )
        return None

    def distribution_shift_score(self, baseline: list[float], current: list[float]) -> float | None:
        if not baseline or not current:
            return None
        # Simple heuristic for distribution shift without SciPy
        base_mean = float(np.mean(baseline))
        curr_mean = float(np.mean(current))
        base_std = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 1.0
        if base_std == 0: base_std = 1.0
        return abs(curr_mean - base_mean) / base_std

    def classify_drift(self, score: float | None) -> FeatureQualityStatus:
        if score is None:
            return FeatureQualityStatus.INSUFFICIENT_DATA
        if score > 3.0:
            return FeatureQualityStatus.FAIL
        if score > 2.0:
            return FeatureQualityStatus.WATCH
        return FeatureQualityStatus.PASS
