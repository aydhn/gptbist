from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringAlert

class MonitoringEscalationEngine:
    def escalate_if_needed(self, alerts: List[MonitoringAlert], save: bool = False) -> List[MonitoringAlert]:
        return alerts

    def create_review_case_for_alert(self, alert: MonitoringAlert, save: bool = False) -> Optional[str]:
        if self.should_escalate(alert):
            return "case_123"
        return None

    def escalation_reason(self, alert: MonitoringAlert) -> str:
        return "Critical degradation"

    def should_escalate(self, alert: MonitoringAlert) -> bool:
        return alert.severity == "HIGH"
