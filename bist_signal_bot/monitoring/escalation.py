import uuid
from bist_signal_bot.monitoring.models import MonitoringAlert

class MonitoringEscalationEngine:
    def escalate_if_needed(self, alerts: list[MonitoringAlert], save: bool = False) -> list[MonitoringAlert]:
        escalated = []
        for alert in alerts:
            if self.should_escalate(alert):
                case_id = self.create_review_case_for_alert(alert, save)
                if case_id:
                    alert.review_case_id = case_id
                escalated.append(alert)
        return escalated

    def create_review_case_for_alert(self, alert: MonitoringAlert, save: bool = False) -> str | None:
        if save:
            return f"case_{uuid.uuid4().hex[:8]}"
        return None

    def escalation_reason(self, alert: MonitoringAlert) -> str:
        return f"Alert {alert.alert_id} ({alert.severity}) triggered escalation due to {alert.title}."

    def should_escalate(self, alert: MonitoringAlert) -> bool:
        return alert.severity == "CRITICAL" or alert.status.value == "DEGRADED"
