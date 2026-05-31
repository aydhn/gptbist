import uuid
from datetime import datetime
from bist_signal_bot.monitoring.models import MonitoringAlert, MonitoringSnapshot, PerformanceDecayFinding, ChampionChallengerComparison, MonitoringAlertType, MonitoringStatus

class MonitoringAlertRouter:
    def __init__(self, route_to_review: bool = True, route_to_reports: bool = True):
        self.route_to_review = route_to_review
        self.route_to_reports = route_to_reports

    def create_alerts(self, snapshot: MonitoringSnapshot, decay_findings: list[PerformanceDecayFinding] | None = None) -> list[MonitoringAlert]:
        alerts = []
        if decay_findings:
            for f in decay_findings:
                if f.status in [MonitoringStatus.DEGRADED, MonitoringStatus.WATCH]:
                    alerts.append(self.alert_from_decay(f))

        if snapshot.status in [MonitoringStatus.DEGRADED, MonitoringStatus.BLOCKED_RESEARCH]:
            alert_type = MonitoringAlertType.STRATEGY_DEGRADED if snapshot.object_type.value == "STRATEGY" else MonitoringAlertType.MODEL_DEGRADED
            alerts.append(MonitoringAlert(
                alert_id=str(uuid.uuid4()),
                alert_type=alert_type,
                object_type=snapshot.object_type,
                object_id=snapshot.object_id,
                severity="CRITICAL" if snapshot.status == MonitoringStatus.BLOCKED_RESEARCH else "HIGH",
                status=snapshot.status,
                created_at=datetime.now(),
                title=f"{snapshot.object_type.value} {snapshot.status.value}",
                message=f"Health score dropped to {snapshot.health_score}",
                evidence_refs=[snapshot.snapshot_id],
                routed_to=[]
            ))

        return [self.route_alert(a) for a in alerts]

    def alert_from_decay(self, finding: PerformanceDecayFinding) -> MonitoringAlert:
        alert_type = MonitoringAlertType.CALIBRATION_DECAY if finding.decay_type.value == "CALIBRATION_DECAY" else MonitoringAlertType.CUSTOM
        if finding.decay_type.value == "PERFORMANCE_DECAY":
            alert_type = MonitoringAlertType.STRATEGY_DEGRADED if finding.object_type.value == "STRATEGY" else MonitoringAlertType.MODEL_DEGRADED

        severity = "HIGH" if finding.status == MonitoringStatus.DEGRADED else "MEDIUM"

        return MonitoringAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            object_type=finding.object_type,
            object_id=finding.object_id,
            severity=severity,
            status=finding.status,
            created_at=datetime.now(),
            title=f"Decay Detected: {finding.metric_name}",
            message=finding.message,
            evidence_refs=[finding.decay_id],
            routed_to=[]
        )

    def alert_from_champion_challenger(self, comparison: ChampionChallengerComparison) -> MonitoringAlert | None:
        if comparison.decision == "PROMOTE_CHALLENGER_RESEARCH":
            alert = MonitoringAlert(
                alert_id=str(uuid.uuid4()),
                alert_type=MonitoringAlertType.CHAMPION_CHALLENGER_CHANGE,
                object_type=comparison.object_type,
                object_id=comparison.champion_id,
                severity="INFO",
                status=MonitoringStatus.PASS,
                created_at=datetime.now(),
                title="Challenger Promotion Suggested",
                message=f"Challenger {comparison.challenger_id} outperformed Champion {comparison.champion_id}.",
                evidence_refs=[comparison.comparison_id],
                routed_to=[]
            )
            return self.route_alert(alert)
        return None

    def route_alert(self, alert: MonitoringAlert) -> MonitoringAlert:
        routes = []
        if self.route_to_review:
            routes.append("review_workflow")
        if self.route_to_reports:
            routes.append("reports")

        if alert.object_type.value == "STRATEGY":
            routes.append("strategy_registry")
        elif alert.object_type.value == "MODEL":
            routes.append("model_registry")

        alert.routed_to = routes
        return alert

    def acknowledge_alert(self, alert_id: str, note: str | None = None) -> MonitoringAlert:
        # Mocked acknowledgment for the core engine
        return MonitoringAlert(
            alert_id=alert_id,
            alert_type=MonitoringAlertType.CUSTOM,
            object_type=MonitoringObjectType.CUSTOM,
            object_id="mock",
            severity="INFO",
            status=MonitoringStatus.PASS,
            created_at=datetime.now(),
            title="Ack",
            message="Ack",
            acknowledged=True,
            metadata={"note": note} if note else {}
        )
