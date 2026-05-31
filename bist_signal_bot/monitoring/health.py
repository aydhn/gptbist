import uuid
from datetime import datetime
from bist_signal_bot.monitoring.models import MonitoringObjectType, MonitoringSnapshot, MonitoringMetric, PerformanceDecayFinding, MonitoringStatus

class MonitoringHealthEngine:
    def __init__(self, degraded_threshold: float = 50.0, watch_threshold: float = 65.0):
        self.degraded_threshold = degraded_threshold
        self.watch_threshold = watch_threshold

    def build_snapshot(self, object_type: MonitoringObjectType, object_id: str, as_of: datetime | None = None) -> MonitoringSnapshot:
        as_of = as_of or datetime.now()

        # Typically would collect metrics and detect decay here
        metrics = []
        decay_findings = []

        score = self.health_score(metrics, decay_findings)
        status = self.status_from_health(score, metrics, decay_findings)
        findings = self.key_findings(metrics, decay_findings)

        sample_count = max([m.sample_count for m in metrics if m.sample_count is not None] + [0])

        return MonitoringSnapshot(
            snapshot_id=str(uuid.uuid4()),
            object_type=object_type,
            object_id=object_id,
            as_of=as_of,
            metrics=metrics,
            status=status,
            health_score=score,
            sample_count=sample_count if metrics else None,
            key_findings=findings
        )

    def health_score(self, metrics: list[MonitoringMetric], decay_findings: list[PerformanceDecayFinding] | None = None) -> float | None:
        if not metrics and not decay_findings:
            return None

        score = 100.0

        if decay_findings:
            for f in decay_findings:
                if f.status == MonitoringStatus.DEGRADED:
                    score -= 20.0
                elif f.status == MonitoringStatus.WATCH:
                    score -= 10.0

        for m in metrics:
            if m.status == MonitoringStatus.DEGRADED:
                score -= 10.0
            elif m.status == MonitoringStatus.WATCH:
                score -= 5.0

        return max(0.0, min(100.0, score))

    def status_from_health(self, score: float | None, metrics: list[MonitoringMetric], decay_findings: list[PerformanceDecayFinding] | None = None) -> MonitoringStatus:
        if score is None:
            return MonitoringStatus.UNKNOWN

        if decay_findings:
            if any(f.status == MonitoringStatus.BLOCKED_RESEARCH for f in decay_findings):
                return MonitoringStatus.BLOCKED_RESEARCH

        if score < self.degraded_threshold:
            return MonitoringStatus.DEGRADED
        elif score < self.watch_threshold:
            return MonitoringStatus.WATCH

        return MonitoringStatus.PASS

    def key_findings(self, metrics: list[MonitoringMetric], decay_findings: list[PerformanceDecayFinding] | None = None) -> list[str]:
        findings = []
        if decay_findings:
            for f in decay_findings:
                findings.append(f"Decay: {f.message}")

        for m in metrics:
            if m.status in [MonitoringStatus.DEGRADED, MonitoringStatus.WATCH]:
                findings.append(f"Metric Issue: {m.metric_name} is {m.status.value} (Value: {m.value})")

        if not findings:
            findings.append("No critical issues found.")

        return findings

    def build_many(self, objects: list[dict[str, str]]) -> list[MonitoringSnapshot]:
        snapshots = []
        for obj in objects:
            obj_type = MonitoringObjectType(obj["object_type"])
            obj_id = obj["object_id"]
            snapshots.append(self.build_snapshot(obj_type, obj_id))
        return snapshots
