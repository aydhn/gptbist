import uuid
import logging
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.models import (
    SignalDecayReport, DriftMetric, DriftTestType, DriftDomain,
    DriftStatus, DriftSeverity, DriftAction
)
from bist_signal_bot.drift.statistics import DriftStatistics

logger = logging.getLogger(__name__)

class SignalDecayAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def analyze(self, reference_signals: list[Any], current_signals: list[Any]) -> SignalDecayReport:
        ref_count = len(reference_signals)
        cur_count = len(current_signals)

        report = SignalDecayReport(
            report_id=str(uuid.uuid4()),
            domain=DriftDomain.SIGNAL_OUTCOME,
            signal_count_reference=ref_count,
            signal_count_current=cur_count
        )

        if ref_count < self.settings.DRIFT_MIN_SAMPLES or cur_count < self.settings.DRIFT_MIN_SAMPLES:
            report.status = DriftStatus.INSUFFICIENT_DATA
            report.warnings.append("Insufficient signals for robust decay analysis.")
            return report

        ref_alert = self.alert_rate(reference_signals)
        cur_alert = self.alert_rate(current_signals)

        ref_outcome = self.positive_outcome_rate(reference_signals)
        cur_outcome = self.positive_outcome_rate(current_signals)

        ref_muted = self.muted_alert_rate(reference_signals)
        cur_muted = self.muted_alert_rate(current_signals)

        ref_inv = self.invalidation_rate(reference_signals)
        cur_inv = self.invalidation_rate(current_signals)

        report.alert_rate_change_pct = DriftStatistics.rate_change(ref_alert, cur_alert)
        report.outcome_rate_change_pct = DriftStatistics.rate_change(ref_outcome, cur_outcome)
        report.muted_alert_rate_change_pct = DriftStatistics.rate_change(ref_muted, cur_muted)
        report.invalidation_rate_change_pct = DriftStatistics.rate_change(ref_inv, cur_inv)

        report.average_score_change = DriftStatistics.mean_shift(
            [s.get('score', 0) if isinstance(s, dict) else getattr(s, 'score', 0) for s in reference_signals],
            [s.get('score', 0) if isinstance(s, dict) else getattr(s, 'score', 0) for s in current_signals]
        )

        report.average_confidence_change = DriftStatistics.mean_shift(
            [s.get('confidence', 0) if isinstance(s, dict) else getattr(s, 'confidence', 0) for s in reference_signals],
            [s.get('confidence', 0) if isinstance(s, dict) else getattr(s, 'confidence', 0) for s in current_signals]
        )

        metrics = []
        if report.outcome_rate_change_pct is not None:
             drop_val = -report.outcome_rate_change_pct

             status = DriftStatus.STABLE
             severity = DriftSeverity.LOW
             if drop_val >= self.settings.DRIFT_SIGNAL_OUTCOME_DROP_FAIL:
                 status = DriftStatus.DRIFTING
                 severity = DriftSeverity.HIGH
             elif drop_val >= self.settings.DRIFT_SIGNAL_OUTCOME_DROP_WARN:
                 status = DriftStatus.WATCH
                 severity = DriftSeverity.MEDIUM

             metrics.append(DriftMetric(
                 metric_name="outcome_drop_pct",
                 test_type=DriftTestType.RATE_CHANGE,
                 domain=DriftDomain.SIGNAL_OUTCOME,
                 value=drop_val,
                 threshold_warn=self.settings.DRIFT_SIGNAL_OUTCOME_DROP_WARN,
                 threshold_fail=self.settings.DRIFT_SIGNAL_OUTCOME_DROP_FAIL,
                 status=status,
                 severity=severity,
                 sample_count_reference=ref_count,
                 sample_count_current=cur_count
             ))

        if report.muted_alert_rate_change_pct is not None:
             val = report.muted_alert_rate_change_pct
             status = DriftStatus.STABLE
             severity = DriftSeverity.LOW
             if val >= self.settings.DRIFT_MUTED_ALERT_RATE_WARN:
                 status = DriftStatus.WATCH
                 severity = DriftSeverity.MEDIUM

             metrics.append(DriftMetric(
                 metric_name="muted_rate_increase_pct",
                 test_type=DriftTestType.RATE_CHANGE,
                 domain=DriftDomain.SIGNAL_OUTCOME,
                 value=val,
                 threshold_warn=self.settings.DRIFT_MUTED_ALERT_RATE_WARN,
                 status=status,
                 severity=severity,
                 sample_count_reference=ref_count,
                 sample_count_current=cur_count
             ))

        report.metrics = metrics
        status, severity = self.classify_decay(metrics)
        report.status = status
        report.severity = severity

        actions = set()
        if status in [DriftStatus.DRIFTING, DriftStatus.SEVERE_DRIFT]:
             actions.add(DriftAction.WATCH)
             actions.add(DriftAction.REVIEW_MANUALLY)
             actions.add(DriftAction.RUN_OPTIMIZATION)
        elif status == DriftStatus.WATCH:
             actions.add(DriftAction.WATCH)

        if cur_inv is not None and cur_inv > 50.0:
             actions.add(DriftAction.RUN_BACKTEST)

        report.recommended_actions = list(actions) if actions else [DriftAction.NO_ACTION]

        return report

    def alert_rate(self, signals: list[Any]) -> float | None:
        if not signals: return None
        alerts = sum(1 for s in signals if (s.get('alert_sent', False) if isinstance(s, dict) else getattr(s, 'alert_sent', False)))
        return float(alerts / len(signals))

    def positive_outcome_rate(self, signals: list[Any]) -> float | None:
        if not signals: return None
        outcomes = [s.get('outcome_positive') if isinstance(s, dict) else getattr(s, 'outcome_positive', None) for s in signals]
        valid = [o for o in outcomes if o is not None]
        if not valid: return None
        return float(sum(1 for o in valid if o) / len(valid))

    def muted_alert_rate(self, signals: list[Any]) -> float | None:
        if not signals: return None
        muted = sum(1 for s in signals if (s.get('muted', False) if isinstance(s, dict) else getattr(s, 'muted', False)))
        return float(muted / len(signals))

    def invalidation_rate(self, signals: list[Any]) -> float | None:
        if not signals: return None
        invalidated = sum(1 for s in signals if (s.get('invalidated', False) if isinstance(s, dict) else getattr(s, 'invalidated', False)))
        return float(invalidated / len(signals))

    def classify_decay(self, metrics: list[DriftMetric]) -> tuple[DriftStatus, DriftSeverity]:
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

        return status, max_sev
