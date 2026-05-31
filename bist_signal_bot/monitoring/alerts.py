from datetime import datetime
from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringAlert, MonitoringSnapshot, PerformanceDecayFinding, ChampionChallengerComparison, MonitoringAlertType, MonitoringStatus

class MonitoringAlertRouter:
    def create_alerts(self, snapshot: MonitoringSnapshot, decay_findings: Optional[List[PerformanceDecayFinding]] = None) -> List[MonitoringAlert]:
        alerts = []
        if decay_findings:
            for f in decay_findings:
                alerts.append(self.alert_from_decay(f))
        return alerts

    def alert_from_decay(self, finding: PerformanceDecayFinding) -> MonitoringAlert:
        return MonitoringAlert(
            alert_id=f"alert_{finding.decay_id}",
            alert_type=MonitoringAlertType.STRATEGY_DEGRADED,
            object_type=finding.object_type,
            object_id=finding.object_id,
            severity="HIGH" if finding.status == MonitoringStatus.DEGRADED else "MEDIUM",
            status=finding.status,
            created_at=datetime.now(),
            title=f"Decay detected in {finding.metric_name}",
            message=finding.message,
            routed_to=["reports", "review_workflow"]
        )

    def alert_from_champion_challenger(self, comparison: ChampionChallengerComparison) -> Optional[MonitoringAlert]:
        return None

    def route_alert(self, alert: MonitoringAlert) -> MonitoringAlert:
        alert.routed_to = ["reports", "review_workflow"]
        return alert

    def acknowledge_alert(self, alert_id: str, note: Optional[str] = None) -> MonitoringAlert:
        return MonitoringAlert(
            alert_id=alert_id,
            alert_type=MonitoringAlertType.CUSTOM,
            object_type="CUSTOM",
            object_id="custom",
            severity="LOW",
            status="PASS",
            created_at=datetime.now(),
            title="Ack",
            message="Acked",
            acknowledged=True
        )
