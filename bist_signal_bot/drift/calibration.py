import uuid
import numpy as np
from typing import Any
import logging

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import CalibrationReport, CalibrationBin, DriftStatus

logger = logging.getLogger(__name__)

class CalibrationMonitor:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def build_calibration_report(self, predictions: list[float], outcomes: list[int], model_id: str | None = None, bins: int = 10) -> CalibrationReport:
        if len(predictions) == 0 or len(outcomes) == 0 or len(predictions) != len(outcomes):
            return CalibrationReport(
                report_id=str(uuid.uuid4()),
                model_id=model_id,
                status=DriftStatus.INSUFFICIENT_DATA,
                warnings=["Mismatched or empty predictions/outcomes."]
            )

        norm_preds = []
        for p in predictions:
            if p > 1.0:
                norm_preds.append(p / 100.0)
            else:
                norm_preds.append(p)

        cal_bins = self.bin_predictions(norm_preds, outcomes, bins)
        ece = self.expected_calibration_error(cal_bins)
        mce = self.maximum_calibration_error(cal_bins)
        brier = self.brier_score(norm_preds, outcomes)

        status = self.classify_calibration(ece, brier)

        return CalibrationReport(
            report_id=str(uuid.uuid4()),
            model_id=model_id,
            bins=cal_bins,
            expected_calibration_error=ece,
            maximum_calibration_error=mce,
            brier_score=brier,
            status=status
        )

    def bin_predictions(self, predictions: list[float], outcomes: list[int], bins: int) -> list[CalibrationBin]:
        bin_edges = np.linspace(0.0, 1.0, bins + 1)
        cal_bins = []

        for i in range(bins):
            lower = float(bin_edges[i])
            upper = float(bin_edges[i+1])

            if i == bins - 1:
                indices = [j for j, p in enumerate(predictions) if lower <= p <= upper]
            else:
                indices = [j for j, p in enumerate(predictions) if lower <= p < upper]

            count = len(indices)
            if count > 0:
                bin_preds = [predictions[j] for j in indices]
                bin_outs = [outcomes[j] for j in indices]

                avg_pred = float(np.mean(bin_preds))
                obs_rate = float(np.mean(bin_outs))
                cal_err = abs(avg_pred - obs_rate)
            else:
                avg_pred = None
                obs_rate = None
                cal_err = None

            cal_bins.append(CalibrationBin(
                bin_id=f"bin_{i}",
                lower_bound=lower,
                upper_bound=upper,
                sample_count=count,
                average_prediction=avg_pred,
                observed_rate=obs_rate,
                calibration_error=cal_err
            ))

        return cal_bins

    def expected_calibration_error(self, bins: list[CalibrationBin]) -> float | None:
        total_samples = sum(b.sample_count for b in bins)
        if total_samples == 0:
            return None

        ece = 0.0
        for b in bins:
            if b.sample_count > 0 and b.calibration_error is not None:
                weight = b.sample_count / total_samples
                ece += weight * b.calibration_error

        return ece

    def maximum_calibration_error(self, bins: list[CalibrationBin]) -> float | None:
        errors = [b.calibration_error for b in bins if b.calibration_error is not None]
        if not errors:
            return None
        return max(errors)

    def brier_score(self, predictions: list[float], outcomes: list[int]) -> float | None:
        if len(predictions) == 0:
            return None
        preds = np.array(predictions)
        outs = np.array(outcomes)
        return float(np.mean((preds - outs) ** 2))

    def classify_calibration(self, ece: float | None, brier: float | None) -> DriftStatus:
        if ece is None:
            return DriftStatus.INSUFFICIENT_DATA

        if ece >= self.settings.DRIFT_ECE_FAIL:
            return DriftStatus.DRIFTING
        if ece >= self.settings.DRIFT_ECE_WARN:
            return DriftStatus.WATCH

        if brier is not None and brier >= self.settings.DRIFT_BRIER_WARN:
             return DriftStatus.WATCH

        return DriftStatus.STABLE
