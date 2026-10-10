import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringSnapshot, PerformanceDecayFinding, ChampionChallengerComparison, MonitoringAlert, MonitoringWatchlistItem, MonitoringReport, MonitoringObjectType

class HeartbeatFileStore:
    """Append-only local JSONL heartbeat log (one HeartbeatRecord per line, newest last). Local files only.

    Appends are a single write()+flush+fsync of one full line (O_APPEND), so a crash can at worst leave one partial
    trailing line, which readers skip (never raise). Reads are newest-first.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def append_heartbeat(self, record) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = record.model_dump_json() + "\n"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return self.path

    def load_recent_heartbeats(self, limit: int = 100) -> list:
        from bist_signal_bot.monitoring.models import HeartbeatRecord
        if not self.path.exists():
            return []
        out = []
        for ln in reversed(self.path.read_text(encoding="utf-8", errors="replace").splitlines()):
            if not ln.strip():
                continue
            try:
                out.append(HeartbeatRecord.model_validate_json(ln))
            except ValueError:  # corrupt / partial line: skip, never crash the monitor
                continue
            if len(out) >= limit:
                break
        return out

    def last_heartbeat(self, component=None):
        for r in self.load_recent_heartbeats(limit=10000):
            if component is None or r.component == component:
                return r
        return None

    def is_stale(self, max_age_seconds: float, component=None, now: Optional[datetime] = None) -> bool:
        """True when there is no beat (fail closed) or the newest one is older than max_age_seconds."""
        r = self.last_heartbeat(component)
        if r is None:
            return True
        return ((now or datetime.utcnow()) - r.timestamp).total_seconds() > max_age_seconds


class MonitoringStore:
    def __init__(self, base_dir):
        if not isinstance(base_dir, (str, Path)):  # a Settings object (CLI/diagnostics pass settings)
            from bist_signal_bot.storage.paths import get_monitoring_dir
            base_dir = get_monitoring_dir(base_dir)
        self.base_dir = Path(base_dir)

    @property
    def heartbeats(self) -> HeartbeatFileStore:
        return HeartbeatFileStore(self.base_dir / "heartbeats.jsonl")

    def append_heartbeat(self, record) -> Path:
        return self.heartbeats.append_heartbeat(record)

    def load_recent_heartbeats(self, limit: int = 100) -> list:
        return self.heartbeats.load_recent_heartbeats(limit)

    def load_recent_alerts(self, limit: int = 50) -> list:
        return []

    def load_recent_metrics(self, limit: int = 100) -> list:
        return []

    def append_metrics(self, metrics: List[MonitoringMetric]) -> Path:
        return self.base_dir / "metrics.jsonl"

    def load_metrics(self, object_type: Optional[MonitoringObjectType] = None, object_id: Optional[str] = None, limit: int = 10000) -> List[MonitoringMetric]:
        return []

    def append_snapshot(self, snapshot: MonitoringSnapshot) -> Path:
        return self.base_dir / "snapshots.jsonl"

    def load_snapshots(self, object_type: Optional[MonitoringObjectType] = None, object_id: Optional[str] = None, limit: int = 10000) -> List[MonitoringSnapshot]:
        return []

    def load_latest_snapshot(self, object_type: MonitoringObjectType, object_id: str) -> Optional[MonitoringSnapshot]:
        return None

    def append_decay_findings(self, findings: List[PerformanceDecayFinding]) -> Path:
        return self.base_dir / "decay.jsonl"

    def load_decay_findings(self, object_id: Optional[str] = None, limit: int = 10000) -> List[PerformanceDecayFinding]:
        return []

    def append_champion_challenger(self, comparison: ChampionChallengerComparison) -> Path:
        return self.base_dir / "cc.jsonl"

    def load_champion_challenger(self, limit: int = 10000) -> List[ChampionChallengerComparison]:
        return []

    def append_alerts(self, alerts: List[MonitoringAlert]) -> Path:
        return self.base_dir / "alerts.jsonl"

    def load_alerts(self, object_id: Optional[str] = None, acknowledged: Optional[bool] = None, limit: int = 10000) -> List[MonitoringAlert]:
        return []

    def append_watchlist_item(self, item: MonitoringWatchlistItem) -> Path:
        return self.base_dir / "watchlist.jsonl"

    def load_watchlist(self, limit: int = 10000) -> List[MonitoringWatchlistItem]:
        return []

    def save_report(self, report: MonitoringReport, markdown_text: str) -> dict:
        return {"report": self.base_dir / "report.json", "markdown": self.base_dir / "report.md"}
