import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.models import ModelCalibrationSummary, ModelGovernanceStatus


class ModelCalibrationGovernance:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)

    def check_sample_count(self, sample_count: int | None) -> list[str]:
        issues = []
        min_sample = getattr(self.settings, "MODEL_CALIBRATION_MIN_SAMPLE", 100)
        if sample_count is None:
            issues.append("Calibration sample count is missing")
        elif sample_count < min_sample:
            issues.append(f"Calibration sample count {sample_count} is below minimum {min_sample}")
        return issues

    def check_reliability(self, reliability_score: float | None) -> list[str]:
        issues = []
        if reliability_score is None:
            return issues

        min_rel = getattr(self.settings, "MODEL_CALIBRATION_MIN_RELIABILITY_SCORE", 60.0)
        if reliability_score < min_rel:
            issues.append(f"Reliability score {reliability_score:.2f} is below minimum {min_rel:.2f}")
        return issues

    def check_ece(self, ece: float | None) -> list[str]:
        issues = []
        if ece is None:
            return issues

        max_ece = getattr(self.settings, "MODEL_CALIBRATION_MAX_ECE_WARN", 0.15)
        if ece > max_ece:
            issues.append(f"Expected Calibration Error (ECE) {ece:.3f} exceeds warning threshold {max_ece:.3f}")
        return issues

    def status_from_calibration(self, reliability_score: float | None, brier_score: float | None,
                                expected_calibration_error: float | None, sample_count: int | None) -> ModelGovernanceStatus:

        rel_issues = self.check_reliability(reliability_score)
        ece_issues = self.check_ece(expected_calibration_error)
        sample_issues = self.check_sample_count(sample_count)

        if sample_issues:
            return ModelGovernanceStatus.INSUFFICIENT_DATA

        if rel_issues or ece_issues:
            # If reliability is extremely low, maybe FAIL. Otherwise WATCH.
            if reliability_score is not None and reliability_score < getattr(self.settings, "MODEL_CALIBRATION_MIN_RELIABILITY_SCORE", 60.0) - 20:
                return ModelGovernanceStatus.FAIL
            return ModelGovernanceStatus.WATCH

        if reliability_score is not None:
            return ModelGovernanceStatus.PASS

        return ModelGovernanceStatus.UNKNOWN

    def validate_summary(self, summary: ModelCalibrationSummary) -> list[str]:
        issues = []
        if not summary.calibration_method:
            issues.append("calibration_method is empty")
        return issues

    def summarize_calibration(self, model_id: str, calibration_result: Any | None = None,
                              reliability_score: float | None = None,
                              brier_score: float | None = None,
                              expected_calibration_error: float | None = None,
                              calibration_bucket_count: int | None = None,
                              sample_count: int | None = None,
                              calibration_method: str = "isotonic") -> ModelCalibrationSummary:
        warnings = []
        warnings.extend(self.check_sample_count(sample_count))
        warnings.extend(self.check_reliability(reliability_score))
        warnings.extend(self.check_ece(expected_calibration_error))

        status = self.status_from_calibration(reliability_score, brier_score, expected_calibration_error, sample_count)

        summary = ModelCalibrationSummary(
            calibration_id=f"cal_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            model_id=model_id,
            created_at=datetime.now(timezone.utc),
            calibration_method=calibration_method,
            reliability_score=reliability_score,
            brier_score=brier_score,
            expected_calibration_error=expected_calibration_error,
            calibration_bucket_count=calibration_bucket_count,
            sample_count=sample_count,
            status=status,
            warnings=warnings
        )

        val_issues = self.validate_summary(summary)
        summary.warnings.extend(val_issues)

        return summary
