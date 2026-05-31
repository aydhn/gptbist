from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringSnapshot, MonitoringMetric, PerformanceDecayFinding, DecayType, MonitoringStatus

class PerformanceDecayDetector:
    def detect_decay(self, snapshot: MonitoringSnapshot, baseline_metrics: Optional[List[MonitoringMetric]] = None) -> List[PerformanceDecayFinding]:
        if not baseline_metrics:
            return []
        findings = []
        for m in snapshot.metrics:
            f = self.detect_metric_decay(m)
            if f:
                findings.append(f)
        return findings

    def detect_metric_decay(self, metric: MonitoringMetric) -> Optional[PerformanceDecayFinding]:
        if metric.baseline_value is None or metric.value is None:
            return None

        score = self.decay_score(metric.value, metric.baseline_value, metric.metric_name)
        status = self.classify_decay(score, metric.sample_count)

        if status in [MonitoringStatus.PASS, MonitoringStatus.UNKNOWN]:
            return None

        return PerformanceDecayFinding(
            decay_id=f"decay_{metric.metric_id}",
            object_type=metric.object_type,
            object_id=metric.object_id,
            decay_type=DecayType.PERFORMANCE_DECAY,
            metric_name=metric.metric_name,
            baseline_value=metric.baseline_value,
            current_value=metric.value,
            decay_score=score,
            status=status,
            message=f"Decay detected in {metric.metric_name}",
            evidence_refs=[]
        )

    def decay_score(self, current: Optional[float], baseline: Optional[float], metric_name: str) -> Optional[float]:
        if current is None or baseline is None or baseline == 0:
            return None
        return (baseline - current) / abs(baseline) * 100.0

    def classify_decay(self, score: Optional[float], sample_count: Optional[int]) -> MonitoringStatus:
        if sample_count is None or sample_count < 30:
            return MonitoringStatus.INSUFFICIENT_DATA
        if score is None:
            return MonitoringStatus.UNKNOWN

        if score > 15.0:
            return MonitoringStatus.DEGRADED
        elif score > 5.0:
            return MonitoringStatus.WATCH
        return MonitoringStatus.PASS

    def detect_calibration_decay(self, metrics: List[MonitoringMetric]) -> List[PerformanceDecayFinding]:
        return []

    def detect_feature_or_model_linked_decay(self, snapshot: MonitoringSnapshot) -> List[PerformanceDecayFinding]:
        return []
