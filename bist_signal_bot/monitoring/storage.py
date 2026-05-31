import json
from pathlib import Path
from bist_signal_bot.storage.paths import (
    get_metrics_path,
    get_snapshots_path,
    get_decay_path,
    get_champion_challenger_path,
    get_alerts_path,
    get_watchlist_path,
    get_report_dir
)
from bist_signal_bot.monitoring.models import (
    MonitoringMetric, MonitoringSnapshot, PerformanceDecayFinding,
    ChampionChallengerComparison, MonitoringAlert, MonitoringWatchlistItem,
    MonitoringReport, MonitoringObjectType
)

class MonitoringStore:
    def _append_jsonl(self, path: Path, data: dict):
        # We assume data handles datetime serialization, but let's be safe.
        # Simple local file operations.
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")

    def append_metrics(self, metrics: list[MonitoringMetric]) -> Path:
        path = get_metrics_path()
        for m in metrics:
            self._append_jsonl(path, m.model_dump(mode='json'))
        return path

    def load_metrics(self, object_type: MonitoringObjectType | None = None, object_id: str | None = None, limit: int = 10000) -> list[MonitoringMetric]:
        path = get_metrics_path()
        if not path.exists():
            return []
        res = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if object_type and d.get("object_type") != object_type.value:
                    continue
                if object_id and d.get("object_id") != object_id:
                    continue
                res.append(MonitoringMetric(**d))
        return res[-limit:]

    def append_snapshot(self, snapshot: MonitoringSnapshot) -> Path:
        path = get_snapshots_path()
        self._append_jsonl(path, snapshot.model_dump(mode='json'))
        return path

    def load_snapshots(self, object_type: MonitoringObjectType | None = None, object_id: str | None = None, limit: int = 10000) -> list[MonitoringSnapshot]:
        path = get_snapshots_path()
        if not path.exists():
            return []
        res = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if object_type and d.get("object_type") != object_type.value:
                    continue
                if object_id and d.get("object_id") != object_id:
                    continue
                res.append(MonitoringSnapshot(**d))
        return res[-limit:]

    def load_latest_snapshot(self, object_type: MonitoringObjectType, object_id: str) -> MonitoringSnapshot | None:
        snaps = self.load_snapshots(object_type, object_id, limit=1)
        return snaps[0] if snaps else None

    def append_decay_findings(self, findings: list[PerformanceDecayFinding]) -> Path:
        path = get_decay_path()
        for f in findings:
            self._append_jsonl(path, f.model_dump(mode='json'))
        return path

    def load_decay_findings(self, object_id: str | None = None, limit: int = 10000) -> list[PerformanceDecayFinding]:
        path = get_decay_path()
        if not path.exists():
            return []
        res = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if object_id and d.get("object_id") != object_id:
                    continue
                res.append(PerformanceDecayFinding(**d))
        return res[-limit:]

    def append_champion_challenger(self, comparison: ChampionChallengerComparison) -> Path:
        path = get_champion_challenger_path()
        self._append_jsonl(path, comparison.model_dump(mode='json'))
        return path

    def load_champion_challenger(self, limit: int = 10000) -> list[ChampionChallengerComparison]:
        path = get_champion_challenger_path()
        if not path.exists():
            return []
        res = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                res.append(ChampionChallengerComparison(**d))
        return res[-limit:]

    def append_alerts(self, alerts: list[MonitoringAlert]) -> Path:
        path = get_alerts_path()
        for a in alerts:
            self._append_jsonl(path, a.model_dump(mode='json'))
        return path

    def load_alerts(self, object_id: str | None = None, acknowledged: bool | None = None, limit: int = 10000) -> list[MonitoringAlert]:
        path = get_alerts_path()
        if not path.exists():
            return []
        res = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if object_id and d.get("object_id") != object_id:
                    continue
                if acknowledged is not None and d.get("acknowledged") != acknowledged:
                    continue
                res.append(MonitoringAlert(**d))
        return res[-limit:]

    def append_watchlist_item(self, item: MonitoringWatchlistItem) -> Path:
        path = get_watchlist_path()
        self._append_jsonl(path, item.model_dump(mode='json'))
        return path

    def load_watchlist(self, limit: int = 10000) -> list[MonitoringWatchlistItem]:
        path = get_watchlist_path()
        if not path.exists():
            return []
        res = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                res.append(MonitoringWatchlistItem(**d))
        return res[-limit:]

    def save_report(self, report: MonitoringReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = get_report_dir(date_str)
        md_path = report_dir / "monitoring_report.md"
        json_path = report_dir / "monitoring_report.json"

        with md_path.open("w", encoding="utf-8") as f:
            f.write(markdown_text)

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode='json'), f, default=str, indent=2)

        return {"markdown": md_path, "json": json_path}
