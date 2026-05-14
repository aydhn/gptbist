import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monitoring.models import HeartbeatRecord, MonitoringComponent, HealthLevel
from bist_signal_bot.monitoring.storage import MonitoringStore

class HeartbeatManager:
    def __init__(self, storage: Optional[MonitoringStore] = None, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.storage = storage or MonitoringStore(self.settings)
        self.logger = logger or logging.getLogger(__name__)

    def record(self, component: MonitoringComponent, status: HealthLevel, message: str, runtime_run_id: str | None = None, metadata: dict[str, Any] | None = None) -> HeartbeatRecord:
        record = HeartbeatRecord(
            heartbeat_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            component=component,
            status=status,
            message=message,
            runtime_run_id=runtime_run_id,
            scheduler_active=False,
            metadata=metadata or {}
        )

        if component == MonitoringComponent.SCHEDULER and status == HealthLevel.HEALTHY:
            record.scheduler_active = True

        try:
            self.storage.append_heartbeat(record)
        except Exception as e:
            self.logger.error(f"Failed to save heartbeat: {e}")

        return record

    def latest(self, component: MonitoringComponent | None = None) -> HeartbeatRecord | None:
        try:
            records = self.storage.load_recent_heartbeats(limit=100)
            if not records:
                return None

            if component:
                filtered = [r for r in records if r.component == component]
                return filtered[0] if filtered else None

            return records[0]
        except Exception as e:
            self.logger.error(f"Failed to load latest heartbeat: {e}")
            return None

    def is_stale(self, record: HeartbeatRecord, max_age_seconds: int) -> bool:
        age_seconds = (datetime.utcnow() - record.timestamp).total_seconds()
        return age_seconds > max_age_seconds

    def component_health_from_heartbeat(self, component: MonitoringComponent, max_age_seconds: int) -> HealthLevel:
        latest_record = self.latest(component)
        if not latest_record:
            return HealthLevel.UNKNOWN

        if self.is_stale(latest_record, max_age_seconds):
            return HealthLevel.DEGRADED if latest_record.status == HealthLevel.HEALTHY else HealthLevel.UNHEALTHY

        return latest_record.status

    def heartbeat_summary(self) -> dict[str, Any]:
        components_to_check = [MonitoringComponent.RUNTIME, MonitoringComponent.SCHEDULER]
        summary = {}
        max_age = getattr(self.settings, "MONITORING_HEARTBEAT_MAX_AGE_SECONDS", 1800)

        for comp in components_to_check:
            latest = self.latest(comp)
            if latest:
                is_stale = self.is_stale(latest, max_age)
                summary[comp.value] = {
                    "latest_timestamp": latest.timestamp.isoformat(),
                    "status": latest.status.value,
                    "is_stale": is_stale,
                    "message": latest.message
                }
            else:
                summary[comp.value] = {
                    "latest_timestamp": None,
                    "status": HealthLevel.UNKNOWN.value,
                    "is_stale": True,
                    "message": "No heartbeat found"
                }

        return summary
