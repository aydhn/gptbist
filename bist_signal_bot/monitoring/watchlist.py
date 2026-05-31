import uuid
from datetime import datetime
from bist_signal_bot.monitoring.models import MonitoringWatchlistItem, MonitoringObjectType, MonitoringStatus, MonitoringSnapshot

class MonitoringWatchlistManager:
    def add_to_watchlist(self, object_type: MonitoringObjectType, object_id: str, reason: str, save: bool = False) -> MonitoringWatchlistItem:
        item = MonitoringWatchlistItem(
            watch_id=str(uuid.uuid4()),
            object_type=object_type,
            object_id=object_id,
            added_at=datetime.now(),
            reason=reason,
            status=MonitoringStatus.WATCH
        )
        if save:
            pass # Save logic would be in storage
        return item

    def remove_from_watchlist(self, watch_id: str, confirm: bool = False) -> MonitoringWatchlistItem:
        if not confirm:
            raise ValueError("Removal requires explicit confirmation.")
        return MonitoringWatchlistItem(
            watch_id=watch_id,
            object_type=MonitoringObjectType.CUSTOM,
            object_id="removed",
            added_at=datetime.now(),
            reason="Removed",
            status=MonitoringStatus.PASS
        )

    def list_watchlist(self, status: MonitoringStatus | None = None) -> list[MonitoringWatchlistItem]:
        return []

    def update_from_snapshot(self, snapshot: MonitoringSnapshot) -> MonitoringWatchlistItem | None:
        if snapshot.status in [MonitoringStatus.DEGRADED, MonitoringStatus.WATCH]:
            reason = self.watch_reason(snapshot)
            if reason:
                return self.add_to_watchlist(snapshot.object_type, snapshot.object_id, reason)
        return None

    def watch_reason(self, snapshot: MonitoringSnapshot) -> str | None:
        if snapshot.status == MonitoringStatus.DEGRADED:
            return "Health score indicates degraded state."
        if snapshot.status == MonitoringStatus.WATCH:
            return "Health score indicates watch state."
        return None
