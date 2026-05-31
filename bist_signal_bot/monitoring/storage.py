from pathlib import Path
from typing import List, Optional
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringSnapshot, PerformanceDecayFinding, ChampionChallengerComparison, MonitoringAlert, MonitoringWatchlistItem, MonitoringReport, MonitoringObjectType

class MonitoringStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

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
