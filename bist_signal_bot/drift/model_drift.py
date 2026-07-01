import logging
import pandas as pd
import numpy as np
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import (
    ModelDriftResult, DriftMetric, DriftTestType, DriftDomain,
    DriftStatus, DriftSeverity, DriftAction, CalibrationReport,
    FeatureDriftResult
)
from bist_signal_bot.drift.statistics import DriftStatistics
from bist_signal_bot.drift.feature_drift import FeatureDriftDetector

logger = logging.getLogger(__name__)

class ModelDriftDetector:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.feature_detector = FeatureDriftDetector(self.settings)

    def detect_model_drift(self,
                           model_id: str | None,
                           reference_predictions: pd.DataFrame,
                           current_predictions: pd.DataFrame,
                           feature_reference: pd.DataFrame | None = None,
                           feature_current: pd.DataFrame | None = None) -> ModelDriftResult:

        result = ModelDriftResult(model_id=model_id)

        if 'prediction' not in reference_predictions.columns or 'prediction' not in current_predictions.columns:
            result.status = DriftStatus.ERROR
            result.warnings.append("Missing 'prediction' column in inputs.")
            return result

        ref_preds = reference_predictions['prediction']
        cur_preds = current_predictions['prediction']

        dist_metrics = self.score_distribution_drift(ref_preds, cur_preds)
        result.score_distribution_metrics = dist_metrics

        threshold = 50.0 if ref_preds.max() > 1.0 else 0.5
        rate_metrics = self.prediction_rate_drift(ref_preds, cur_preds, threshold)
        result.prediction_rate_metrics = rate_metrics

        if feature_reference is not None and feature_current is not None:
             feat_results = self.feature_detector.detect(feature_reference, feature_current)
             result.feature_drift_results = feat_results

        status = DriftStatus.STABLE
        severity = DriftSeverity.LOW

        all_metrics = dist_metrics + rate_metrics
        for m in all_metrics:
            if m.status in [DriftStatus.SEVERE_DRIFT, DriftStatus.DRIFTING, DriftStatus.WATCH]:
                if self._severity_val(m.severity) > self._severity_val(severity):
                    severity = m.severity
                    status = m.status

        if len(result.feature_drift_results) > 0:
            drifting_features = sum(1 for f in result.feature_drift_results if f.status in [DriftStatus.DRIFTING, DriftStatus.SEVERE_DRIFT])
            if drifting_features > len(result.feature_drift_results) * 0.3:
                 if self._severity_val(DriftSeverity.HIGH) > self._severity_val(severity):
                     severity = DriftSeverity.HIGH
                     status = DriftStatus.DRIFTING

        result.status = status
        result.severity = severity
        result.recommended_actions = self.build_recommended_actions(status)

        return result

    def score_distribution_drift(self, reference_predictions: pd.Series, current_predictions: pd.Series) -> list[DriftMetric]:
        ref_vals = reference_predictions.dropna().tolist()
        cur_vals = current_predictions.dropna().tolist()

        psi_val = DriftStatistics.population_stability_index(ref_vals, cur_vals)
        ks_val = DriftStatistics.ks_statistic(ref_vals, cur_vals)

        metrics = []

        psi_status = DriftStatus.STABLE
        psi_severity = DriftSeverity.LOW
        if psi_val is not None:
             if self.settings.DRIFT_MODEL_SCORE_PSI_FAIL is not None and psi_val >= self.settings.DRIFT_MODEL_SCORE_PSI_FAIL:
                 psi_status = DriftStatus.DRIFTING
                 psi_severity = DriftSeverity.HIGH
             elif self.settings.DRIFT_MODEL_SCORE_PSI_WARN is not None and psi_val >= self.settings.DRIFT_MODEL_SCORE_PSI_WARN:
                 psi_status = DriftStatus.WATCH
                 psi_severity = DriftSeverity.MEDIUM

        metrics.append(DriftMetric(
            metric_name="score_psi",
            test_type=DriftTestType.PSI,
            domain=DriftDomain.MODEL_SCORE,
            value=psi_val,
            threshold_warn=self.settings.DRIFT_MODEL_SCORE_PSI_WARN,
            threshold_fail=self.settings.DRIFT_MODEL_SCORE_PSI_FAIL,
            status=psi_status,
            severity=psi_severity,
            sample_count_reference=len(ref_vals),
            sample_count_current=len(cur_vals)
        ))

        metrics.append(DriftMetric(
            metric_name="score_ks",
            test_type=DriftTestType.KS_TEST,
            domain=DriftDomain.MODEL_SCORE,
            value=ks_val,
            sample_count_reference=len(ref_vals),
            sample_count_current=len(cur_vals)
        ))

        return metrics

    def prediction_rate_drift(self, reference_predictions: pd.Series, current_predictions: pd.Series, threshold: float = 0.5) -> list[DriftMetric]:
        ref_vals = reference_predictions.dropna()
        cur_vals = current_predictions.dropna()

        ref_rate = float(np.mean(ref_vals >= threshold)) if len(ref_vals) > 0 else None
        cur_rate = float(np.mean(cur_vals >= threshold)) if len(cur_vals) > 0 else None

        rate_change = DriftStatistics.rate_change(ref_rate, cur_rate)

        status = DriftStatus.STABLE
        severity = DriftSeverity.LOW

        if rate_change is not None:
            abs_change = abs(rate_change)
            if self.settings.DRIFT_MODEL_POSITIVE_RATE_CHANGE_FAIL is not None and abs_change >= self.settings.DRIFT_MODEL_POSITIVE_RATE_CHANGE_FAIL:
                status = DriftStatus.DRIFTING
                severity = DriftSeverity.HIGH
            elif self.settings.DRIFT_MODEL_POSITIVE_RATE_CHANGE_WARN is not None and abs_change >= self.settings.DRIFT_MODEL_POSITIVE_RATE_CHANGE_WARN:
                status = DriftStatus.WATCH
                severity = DriftSeverity.MEDIUM

        return [DriftMetric(
            metric_name="positive_rate_change",
            test_type=DriftTestType.RATE_CHANGE,
            domain=DriftDomain.MODEL_SCORE,
            value=rate_change,
            threshold_warn=self.settings.DRIFT_MODEL_POSITIVE_RATE_CHANGE_WARN,
            threshold_fail=self.settings.DRIFT_MODEL_POSITIVE_RATE_CHANGE_FAIL,
            status=status,
            severity=severity,
            sample_count_reference=len(ref_vals),
            sample_count_current=len(cur_vals),
            metadata={"ref_rate": ref_rate, "cur_rate": cur_rate}
        )]

    def build_recommended_actions(self, status: DriftStatus, calibration_report: CalibrationReport | None = None) -> list[DriftAction]:
        actions = set()

        if status == DriftStatus.SEVERE_DRIFT:
            actions.add(DriftAction.RETRAIN_MODEL)
            actions.add(DriftAction.WATCH)
        elif status == DriftStatus.DRIFTING:
            actions.add(DriftAction.WATCH)
            actions.add(DriftAction.REFRESH_FEATURES)
            actions.add(DriftAction.REVIEW_MANUALLY)
        elif status == DriftStatus.WATCH:
            actions.add(DriftAction.WATCH)

        if calibration_report and calibration_report.status in [DriftStatus.DRIFTING, DriftStatus.SEVERE_DRIFT]:
             actions.add(DriftAction.REDUCE_CONFIDENCE)

        if not actions:
             actions.add(DriftAction.NO_ACTION)

        return list(actions)

    def _severity_val(self, severity: DriftSeverity) -> int:
        mapping = {
            DriftSeverity.CRITICAL: 4,
            DriftSeverity.HIGH: 3,
            DriftSeverity.MEDIUM: 2,
            DriftSeverity.LOW: 1,
            DriftSeverity.UNKNOWN: 0
        }
        return mapping.get(severity, 0)
