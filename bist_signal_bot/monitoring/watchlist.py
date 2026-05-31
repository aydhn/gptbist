from datetime import datetime
from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringWatchlistItem, MonitoringObjectType, MonitoringStatus, MonitoringSnapshot

class MonitoringWatchlistManager:
    def add_to_watchlist(self, object_type: MonitoringObjectType, object_id: str, reason: str, save: bool = False) -> MonitoringWatchlistItem:
        return MonitoringWatchlistItem(
            watch_id=f"watch_{object_id}",
            object_type=object_type,
            object_id=object_id,
            added_at=datetime.now(),
            reason=reason,
            status=MonitoringStatus.WATCH
        )

    def remove_from_watchlist(self, watch_id: str, confirm: bool = False) -> MonitoringWatchlistItem:
        return MonitoringWatchlistItem(
            watch_id=watch_id,
            object_type="CUSTOM",
            object_id="custom",
            added_at=datetime.now(),
            reason="Removed",
            status=MonitoringStatus.PASS
        )

    def list_watchlist(self, status: Optional[MonitoringStatus] = None) -> List[MonitoringWatchlistItem]:
        return []

    def update_from_snapshot(self, snapshot: MonitoringSnapshot) -> Optional[MonitoringWatchlistItem]:
        if snapshot.status in [MonitoringStatus.WATCH, MonitoringStatus.DEGRADED]:
            return self.add_to_watchlist(snapshot.object_type, snapshot.object_id, "Degraded performance")
        return None

    def watch_reason(self, snapshot: MonitoringSnapshot) -> Optional[str]:
        if snapshot.status in [MonitoringStatus.WATCH, MonitoringStatus.DEGRADED]:
            return "Degraded performance"
        return None
