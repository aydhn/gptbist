import uuid
import logging
from typing import Any
import numpy as np

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import (
    PortfolioDriftReport, DriftMetric, DriftTestType, DriftDomain,
    DriftStatus, DriftSeverity, DriftAction
)
from bist_signal_bot.drift.statistics import DriftStatistics

logger = logging.getLogger(__name__)

class PortfolioDriftAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def analyze(self, reference_snapshot: Any | None, current_snapshot: Any | None,
                reference_stress: Any | None = None, current_stress: Any | None = None) -> PortfolioDriftReport:

        report = PortfolioDriftReport(
            report_id=str(uuid.uuid4())
        )

        if reference_snapshot is None or current_snapshot is None:
             report.status = DriftStatus.INSUFFICIENT_DATA
             report.warnings.append("Missing reference or current portfolio snapshot.")
             return report

        report.reference_snapshot_id = getattr(reference_snapshot, "id", None) or getattr(reference_snapshot, "snapshot_id", None)
        report.current_snapshot_id = getattr(current_snapshot, "id", None) or getattr(current_snapshot, "snapshot_id", None)

        ref_exp = getattr(reference_snapshot, "exposures", []) if not isinstance(reference_snapshot, dict) else reference_snapshot.get("exposures", [])
        cur_exp = getattr(current_snapshot, "exposures", []) if not isinstance(current_snapshot, dict) else current_snapshot.get("exposures", [])

        report.exposure_drift_metrics = self.exposure_drift(ref_exp, cur_exp)

        report.concentration_change = self.concentration_change(reference_snapshot, current_snapshot)
        report.correlation_change = self.correlation_change(reference_snapshot, current_snapshot)

        if reference_stress and current_stress:
             ref_rating = getattr(reference_stress, "stress_rating", None) if not isinstance(reference_stress, dict) else reference_stress.get("stress_rating")
             cur_rating = getattr(current_stress, "stress_rating", None) if not isinstance(current_stress, dict) else current_stress.get("stress_rating")
             if ref_rating and cur_rating and ref_rating != cur_rating:
                 report.stress_rating_change = f"{ref_rating} -> {cur_rating}"

        status, severity = self.classify_portfolio_drift(report.exposure_drift_metrics, report.concentration_change, report.correlation_change)

        if report.stress_rating_change and "CRITICAL" in report.stress_rating_change:
             severity = DriftSeverity.HIGH
             status = DriftStatus.DRIFTING

        report.status = status
        report.severity = severity

        actions = set()
        if status in [DriftStatus.DRIFTING, DriftStatus.SEVERE_DRIFT]:
             actions.add(DriftAction.WATCH)
             actions.add(DriftAction.REVIEW_MANUALLY)
        elif status == DriftStatus.WATCH:
             actions.add(DriftAction.WATCH)

        report.recommended_actions = list(actions) if actions else [DriftAction.NO_ACTION]

        return report

    def exposure_drift(self, reference_exposures: list[Any], current_exposures: list[Any]) -> list[DriftMetric]:
        ref_weights = {e.get('symbol', 'unknown'): e.get('weight', 0.0) for e in reference_exposures if isinstance(e, dict)}
        cur_weights = {e.get('symbol', 'unknown'): e.get('weight', 0.0) for e in current_exposures if isinstance(e, dict)}

        if not ref_weights or not cur_weights:
            return []

        metrics = []
        all_symbols = set(ref_weights.keys()).union(set(cur_weights.keys()))

        shift_sum = sum(abs(cur_weights.get(s, 0.0) - ref_weights.get(s, 0.0)) for s in all_symbols)
        normalized_shift = float(shift_sum / 2.0)

        status = DriftStatus.STABLE
        severity = DriftSeverity.LOW
        if normalized_shift >= self.settings.DRIFT_EXPOSURE_CHANGE_WARN:
             status = DriftStatus.WATCH
             severity = DriftSeverity.MEDIUM

        metrics.append(DriftMetric(
             metric_name="exposure_shift",
             test_type=DriftTestType.CATEGORY_SHIFT,
             domain=DriftDomain.PORTFOLIO_RESEARCH,
             value=normalized_shift,
             threshold_warn=self.settings.DRIFT_EXPOSURE_CHANGE_WARN,
             status=status,
             severity=severity
        ))

        return metrics

    def concentration_change(self, reference_snapshot: Any, current_snapshot: Any) -> float | None:
        def get_conc(snap):
             if isinstance(snap, dict):
                  return snap.get("metrics", {}).get("concentration_index")
             if hasattr(snap, "metrics") and isinstance(snap.metrics, dict):
                  return snap.metrics.get("concentration_index")
             return None

        ref_c = get_conc(reference_snapshot)
        cur_c = get_conc(current_snapshot)

        if ref_c is not None and cur_c is not None:
             return float(cur_c - ref_c)
        return None

    def correlation_change(self, reference_snapshot: Any, current_snapshot: Any) -> float | None:
        def get_corr(snap):
             if isinstance(snap, dict):
                  return snap.get("metrics", {}).get("average_correlation")
             if hasattr(snap, "metrics") and isinstance(snap.metrics, dict):
                  return snap.metrics.get("average_correlation")
             return None

        ref_c = get_corr(reference_snapshot)
        cur_c = get_corr(current_snapshot)

        if ref_c is not None and cur_c is not None:
             return float(cur_c - ref_c)
        return None

    def classify_portfolio_drift(self, metrics: list[DriftMetric], concentration_change: float | None, correlation_change: float | None) -> tuple[DriftStatus, DriftSeverity]:
        severities = {
            DriftSeverity.CRITICAL: 4,
            DriftSeverity.HIGH: 3,
            DriftSeverity.MEDIUM: 2,
            DriftSeverity.LOW: 1,
            DriftSeverity.UNKNOWN: 0
        }

        max_sev = DriftSeverity.LOW
        status = DriftStatus.STABLE

        for m in metrics:
             if m.status in [DriftStatus.SEVERE_DRIFT, DriftStatus.DRIFTING, DriftStatus.WATCH]:
                  if severities[m.severity] > severities[max_sev]:
                       max_sev = m.severity
                       status = m.status

        if concentration_change is not None and concentration_change >= self.settings.DRIFT_CONCENTRATION_CHANGE_WARN:
             if severities[DriftSeverity.MEDIUM] > severities[max_sev]:
                  max_sev = DriftSeverity.MEDIUM
                  status = DriftStatus.WATCH

        if correlation_change is not None and correlation_change >= self.settings.DRIFT_CORRELATION_CHANGE_WARN:
             if severities[DriftSeverity.MEDIUM] > severities[max_sev]:
                  max_sev = DriftSeverity.MEDIUM
                  status = DriftStatus.WATCH

        return status, max_sev
