from bist_signal_bot.calibration.models import (
    CalibrationResult, ThresholdOptimizationResult, OutcomeCohort, CalibrationStatus, ErrorCase, ErrorCaseType
)
from bist_signal_bot.config.settings import Settings

class CalibrationScorer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def score_calibration(self, result: CalibrationResult) -> float | None:
        if result.status == CalibrationStatus.INSUFFICIENT_DATA:
            return None

        base_score = 100.0

        if result.reliability_curve and result.reliability_curve.expected_calibration_error is not None:
            penalty = min(50.0, result.reliability_curve.expected_calibration_error * 200) # e.g. 0.10 ECE -> -20 pts
            base_score -= penalty

        if result.reliability_curve and result.reliability_curve.max_calibration_error is not None:
            penalty = min(30.0, result.reliability_curve.max_calibration_error * 100)
            base_score -= penalty

        return max(0.0, base_score)

    def score_threshold_result(self, result: ThresholdOptimizationResult) -> float | None:
        if result.status == CalibrationStatus.INSUFFICIENT_DATA or not result.selected_threshold:
            return None

        quality = result.selected_threshold.expected_quality_change.get("net_return_quality")
        if quality is None:
            return 50.0

        return max(0.0, min(100.0, 50.0 + (quality * 10.0)))

    def score_cohorts(self, cohorts: list[OutcomeCohort]) -> float | None:
        if not cohorts:
            return None

        weak_count = sum(1 for c in cohorts if c.status in [CalibrationStatus.FAIL, CalibrationStatus.WATCH])
        penalty = min(80.0, weak_count * 10.0)
        return 100.0 - penalty

    def overall_status(self, results: list[CalibrationResult], errors: list[ErrorCase]) -> CalibrationStatus:
        if not results:
            return CalibrationStatus.INSUFFICIENT_DATA

        has_fail = any(r.status == CalibrationStatus.FAIL for r in results)
        has_watch = any(r.status == CalibrationStatus.WATCH for r in results)

        high_conf_failures = sum(1 for e in errors if e.error_type == ErrorCaseType.HIGH_CONFIDENCE_FAILURE)
        if high_conf_failures > 10:
            has_fail = True
        elif high_conf_failures > 5:
            has_watch = True

        if has_fail:
            return CalibrationStatus.FAIL
        elif has_watch:
            return CalibrationStatus.WATCH
        return CalibrationStatus.PASS
