import uuid
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monitoring.models import (
    MonitoringAlert, MonitoringComponent, AlertSeverity, AlertStatus, DiagnosticCheckResult
)
from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.runtime.models import RuntimePipelineResult

class AlertManager:
    def __init__(self, storage: Optional[MonitoringStore] = None, notifier: Optional[Any] = None, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.storage = storage or MonitoringStore(self.settings)
        self.notifier = notifier
        self.logger = logger or logging.getLogger(__name__)

    def _generate_fingerprint(self, component: MonitoringComponent, severity: AlertSeverity, title: str) -> str:
        raw = f"{component.value}_{severity.value}_{title}".encode('utf-8')
        return hashlib.md5(raw).hexdigest()

    def create_alert(self, component: MonitoringComponent, severity: AlertSeverity, title: str, message: str, runtime_run_id: str | None = None, metadata: dict[str, Any] | None = None) -> MonitoringAlert:
        fingerprint = self._generate_fingerprint(component, severity, title)

        recent_alerts = self.storage.load_recent_alerts(limit=50)
        existing = next((a for a in recent_alerts if a.fingerprint == fingerprint and a.status in [AlertStatus.NEW, AlertStatus.THROTTLED, AlertStatus.FAILED]), None)

        now = datetime.utcnow()
        if existing:
            existing.count += 1
            existing.last_seen_at = now
            existing.message = message
            existing.runtime_run_id = runtime_run_id
            if metadata:
                existing.metadata.update(metadata)

            try:
                self.storage.append_alert(existing)
            except Exception as e:
                self.logger.error(f"Failed to update alert: {e}")
            return existing

        alert = MonitoringAlert(
            alert_id=str(uuid.uuid4()),
            timestamp=now,
            component=component,
            severity=severity,
            status=AlertStatus.NEW,
            title=title,
            message=message,
            fingerprint=fingerprint,
            count=1,
            first_seen_at=now,
            last_seen_at=now,
            runtime_run_id=runtime_run_id,
            metadata=metadata or {}
        )

        try:
            self.storage.append_alert(alert)
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")

        return alert

    def should_throttle(self, alert: MonitoringAlert, recent_alerts: list[MonitoringAlert], throttle_minutes: int) -> bool:
        if throttle_minutes <= 0:
            return False

        cutoff = datetime.utcnow() - timedelta(minutes=throttle_minutes)
        for recent in recent_alerts:
            if recent.fingerprint == alert.fingerprint and recent.status == AlertStatus.SENT:
                if recent.sent_at and recent.sent_at > cutoff:
                    return True
        return False

    def send_alert(self, alert: MonitoringAlert) -> MonitoringAlert:
        recent_alerts = self.storage.load_recent_alerts(limit=100)
        throttle_mins = getattr(self.settings, "MONITORING_ALERT_THROTTLE_MINUTES", 30)

        if self.should_throttle(alert, recent_alerts, throttle_mins):
            alert.status = AlertStatus.THROTTLED
            alert.metadata["throttle_reason"] = f"Sent within {throttle_mins} minutes"
            self.storage.append_alert(alert)
            self.logger.info(f"Alert throttled: {alert.title}")
            return alert

        if not self.notifier or not getattr(self.settings, "ENABLE_TELEGRAM", False):
            alert.status = AlertStatus.THROTTLED
            alert.metadata["throttle_reason"] = "Notifier not available or disabled"
            self.storage.append_alert(alert)
            return alert

        try:
            from bist_signal_bot.notifications.formatter import format_monitoring_alert
            msg = format_monitoring_alert(alert)

            forbidden = ["kesin", "garanti", "risksiz"]
            if any(f in msg.lower() for f in forbidden):
                raise ValueError("Forbidden phrase in alert message")

            if hasattr(self.notifier, "send_message"):
                success = self.notifier.send_message(msg)
                if success is False:
                    raise ValueError("Notifier returned false")

            alert.status = AlertStatus.SENT
            alert.sent_at = datetime.utcnow()
            self.logger.info(f"Alert sent successfully: {alert.title}")

        except Exception as e:
            self.logger.error(f"Failed to send alert '{alert.title}': {e}")
            alert.status = AlertStatus.FAILED
            alert.metadata["send_error"] = str(e)

        self.storage.append_alert(alert)
        return alert

    def resolve_alert(self, alert_id: str, message: str | None = None) -> MonitoringAlert | None:
        recent_alerts = self.storage.load_recent_alerts(limit=500)
        alert = next((a for a in recent_alerts if a.alert_id == alert_id), None)
        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        if message:
            alert.metadata["resolve_message"] = message

        self.storage.append_alert(alert)
        return alert

    def alerts_from_diagnostics(self, checks: list[DiagnosticCheckResult]) -> list[MonitoringAlert]:
        created_alerts = []
        for check in checks:
            if check.status in [DiagnosticCheckStatus.FAIL, DiagnosticCheckStatus.ERROR]:
                alert = self.create_alert(
                    component=check.component,
                    severity=check.severity,
                    title=f"Diagnostic Failure: {check.check_name}",
                    message=check.message,
                    metadata={"details": check.details, "recommendations": check.recommendations}
                )
                created_alerts.append(alert)
        return created_alerts

    def alerts_from_runtime_result(self, result: RuntimePipelineResult) -> list[MonitoringAlert]:
        created_alerts = []
        if result.status.value == "FAILED":
            alert = self.create_alert(
                component=MonitoringComponent.RUNTIME,
                severity=AlertSeverity.ERROR,
                title="Runtime Pipeline Failed",
                message=f"Run {result.run_id} failed.",
                runtime_run_id=result.run_id,
                metadata={"unexpected_error": result.metadata.get("unexpected_error")}
            )
            created_alerts.append(alert)

        if result.scan_report_summary:
            total = result.scan_report_summary.get("total_symbols", 0)
            errors = result.scan_report_summary.get("error_count", 0)
            max_rate = getattr(self.settings, "MONITORING_MAX_SCANNER_ERROR_RATE", 0.30)
            if total > 0 and (errors / total) > max_rate:
                alert = self.create_alert(
                    component=MonitoringComponent.SCANNER,
                    severity=AlertSeverity.WARNING,
                    title="High Scanner Error Rate",
                    message=f"Scanner encountered {errors} errors out of {total} symbols.",
                    runtime_run_id=result.run_id
                )
                created_alerts.append(alert)

        return created_alerts
