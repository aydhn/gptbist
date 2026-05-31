import uuid
from bist_signal_bot.monitoring.models import MonitoringSnapshot, MonitoringMetric, PerformanceDecayFinding, DecayType, MonitoringStatus, MonitoringObjectType

class PerformanceDecayDetector:
    def __init__(self, performance_threshold: float = 0.15, calibration_threshold: float = 0.10):
        self.performance_threshold = performance_threshold
        self.calibration_threshold = calibration_threshold

    def detect_decay(self, snapshot: MonitoringSnapshot, baseline_metrics: list[MonitoringMetric] | None = None) -> list[PerformanceDecayFinding]:
        findings = []
        if baseline_metrics is None:
            baseline_metrics = []

        baseline_map = {m.metric_name: m.value for m in baseline_metrics if m.value is not None}

        for metric in snapshot.metrics:
            # Prefer baseline from argument, fallback to metric.baseline_value
            base_val = baseline_map.get(metric.metric_name, metric.baseline_value)
            metric_with_base = metric.model_copy(update={'baseline_value': base_val})
            finding = self.detect_metric_decay(metric_with_base)
            if finding:
                findings.append(finding)

        # Also check calibration decay
        calib_findings = self.detect_calibration_decay(snapshot.metrics)
        findings.extend(calib_findings)

        # Check feature/model drift linked decay
        drift_findings = self.detect_feature_or_model_linked_decay(snapshot)
        findings.extend(drift_findings)

        return findings

    def detect_metric_decay(self, metric: MonitoringMetric) -> PerformanceDecayFinding | None:
        if metric.value is None:
            return None

        if metric.baseline_value is None:
            return PerformanceDecayFinding(
                decay_id=str(uuid.uuid4()),
                object_type=metric.object_type,
                object_id=metric.object_id,
                decay_type=DecayType.UNKNOWN,
                metric_name=metric.metric_name,
                baseline_value=None,
                current_value=metric.value,
                decay_score=None,
                status=MonitoringStatus.INSUFFICIENT_DATA,
                message=f"No baseline available for {metric.metric_name}",
                warnings=["Cannot compute decay without baseline"]
            )

        score = self.decay_score(metric.value, metric.baseline_value, metric.metric_name)
        if score is None:
            return None

        status = self.classify_decay(score, metric.sample_count)

        if status in [MonitoringStatus.PASS, MonitoringStatus.UNKNOWN]:
            return None

        decay_type = DecayType.PERFORMANCE_DECAY
        if metric.metric_name == "win_rate":
            decay_type = DecayType.WIN_RATE_DECAY
        elif metric.metric_name == "expectancy":
            decay_type = DecayType.EXPECTANCY_DECAY

        return PerformanceDecayFinding(
            decay_id=str(uuid.uuid4()),
            object_type=metric.object_type,
            object_id=metric.object_id,
            decay_type=decay_type,
            metric_name=metric.metric_name,
            baseline_value=metric.baseline_value,
            current_value=metric.value,
            decay_score=score,
            status=status,
            message=f"Detected {status.value} decay in {metric.metric_name} (Score: {score:.2f})",
            warnings=[f"Metric {metric.metric_name} decayed by {score:.2f}%"]
        )

    def decay_score(self, current: float | None, baseline: float | None, metric_name: str) -> float | None:
        if current is None or baseline is None or baseline == 0:
            return None

        # Assuming higher is better for these metrics. If max_drawdown, lower is better.
        if metric_name == "max_drawdown":
            if current > baseline:
                return ((current - baseline) / baseline) * 100.0
            return 0.0

        if current < baseline:
            return ((baseline - current) / abs(baseline)) * 100.0
        return 0.0

    def classify_decay(self, score: float | None, sample_count: int | None) -> MonitoringStatus:
        if sample_count is not None and sample_count < 30:
            return MonitoringStatus.INSUFFICIENT_DATA

        if score is None:
            return MonitoringStatus.UNKNOWN

        if score >= self.performance_threshold * 100 * 1.5: # 1.5x threshold = FAIL/DEGRADED
            return MonitoringStatus.DEGRADED
        elif score >= self.performance_threshold * 100:
            return MonitoringStatus.WATCH

        return MonitoringStatus.PASS

    def detect_calibration_decay(self, metrics: list[MonitoringMetric]) -> list[PerformanceDecayFinding]:
        findings = []
        for m in metrics:
            if m.metric_name == "calibration_reliability":
                if m.baseline_value is not None and m.value is not None:
                    if m.value < m.baseline_value * (1 - self.calibration_threshold):
                        findings.append(PerformanceDecayFinding(
                            decay_id=str(uuid.uuid4()),
                            object_type=m.object_type,
                            object_id=m.object_id,
                            decay_type=DecayType.CALIBRATION_DECAY,
                            metric_name="calibration_reliability",
                            baseline_value=m.baseline_value,
                            current_value=m.value,
                            decay_score=self.decay_score(m.value, m.baseline_value, "calibration_reliability"),
                            status=MonitoringStatus.WATCH,
                            message="Calibration reliability has degraded below threshold.",
                            warnings=["Calibration decay detected."]
                        ))
        return findings

    def detect_feature_or_model_linked_decay(self, snapshot: MonitoringSnapshot) -> list[PerformanceDecayFinding]:
        # Placeholder for complex drift logic linking model/feature drift to outcome decay
        return []
