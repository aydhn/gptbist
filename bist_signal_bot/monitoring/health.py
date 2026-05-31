from datetime import datetime
from typing import List, Optional, Dict
from bist_signal_bot.monitoring.models import MonitoringSnapshot, MonitoringObjectType, MonitoringMetric, PerformanceDecayFinding, MonitoringStatus

class MonitoringHealthEngine:
    def build_snapshot(self, object_type: MonitoringObjectType, object_id: str, as_of: Optional[datetime] = None) -> MonitoringSnapshot:
        return MonitoringSnapshot(
            snapshot_id="snap_1",
            object_type=object_type,
            object_id=object_id,
            as_of=as_of or datetime.now(),
            metrics=[],
            status=MonitoringStatus.PASS,
            health_score=100.0
        )

    def health_score(self, metrics: List[MonitoringMetric], decay_findings: Optional[List[PerformanceDecayFinding]] = None) -> Optional[float]:
        if not metrics:
            return None
        score = 100.0
        if decay_findings:
            score -= len(decay_findings) * 10.0
        return max(0.0, score)

    def status_from_health(self, score: Optional[float], metrics: List[MonitoringMetric], decay_findings: Optional[List[PerformanceDecayFinding]] = None) -> MonitoringStatus:
        if score is None:
            return MonitoringStatus.UNKNOWN
        if score < 50.0:
            return MonitoringStatus.DEGRADED
        elif score < 65.0:
            return MonitoringStatus.WATCH
        return MonitoringStatus.PASS

    def key_findings(self, metrics: List[MonitoringMetric], decay_findings: Optional[List[PerformanceDecayFinding]] = None) -> List[str]:
        return []

    def build_many(self, objects: List[Dict[str, str]]) -> List[MonitoringSnapshot]:
        return []
