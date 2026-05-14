import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_monitoring_dir
from bist_signal_bot.monitoring.models import (
    HeartbeatRecord, MonitoringMetric, MonitoringAlert,
    DiagnosticCheckResult, MonitoringSnapshot
)
from bist_signal_bot.core.exceptions import MonitoringStorageError

class MonitoringStore:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.base_dir = get_monitoring_dir(self.settings)

    def get_monitoring_dir(self) -> Path:
        return self.base_dir

    def _append_jsonl(self, file_path: Path, data: dict) -> Path:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to append to {file_path}: {e}")
            raise MonitoringStorageError(f"Failed to append JSONL: {e}")

    def append_heartbeat(self, record: HeartbeatRecord) -> Path:
        path = self.base_dir / "heartbeats.jsonl"
        return self._append_jsonl(path, record.model_dump(mode="json"))

    def append_metric(self, metric: MonitoringMetric) -> Path:
        path = self.base_dir / "metrics.jsonl"
        return self._append_jsonl(path, metric.model_dump(mode="json"))

    def append_alert(self, alert: MonitoringAlert) -> Path:
        path = self.base_dir / "alerts.jsonl"
        return self._append_jsonl(path, alert.model_dump(mode="json"))

    def _load_jsonl(self, file_path: Path, model_cls: Any, limit: int) -> List[Any]:
        if not file_path.exists():
            return []

        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in reversed(lines):
                if len(results) >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    results.append(model_cls(**data))
                except Exception as e:
                    self.logger.warning(f"Skipping malformed JSONL line in {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")

        return results

    def load_recent_heartbeats(self, limit: int = 100) -> List[HeartbeatRecord]:
        path = self.base_dir / "heartbeats.jsonl"
        return self._load_jsonl(path, HeartbeatRecord, limit)

    def load_recent_metrics(self, limit: int = 1000) -> List[MonitoringMetric]:
        path = self.base_dir / "metrics.jsonl"
        return self._load_jsonl(path, MonitoringMetric, limit)

    def load_recent_alerts(self, limit: int = 100) -> List[MonitoringAlert]:
        path = self.base_dir / "alerts.jsonl"
        return self._load_jsonl(path, MonitoringAlert, limit)

    def save_snapshot(self, snapshot: MonitoringSnapshot) -> Path:
        date_str = snapshot.generated_at.strftime("%Y%m%d")
        path = self.base_dir / "snapshots" / date_str / "monitoring_snapshot.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(snapshot.model_dump_json(indent=2))
            return path
        except Exception as e:
            raise MonitoringStorageError(f"Failed to save snapshot: {e}")

    def save_diagnostics(self, checks: List[DiagnosticCheckResult]) -> Path:
        if not checks:
            date_str = datetime.utcnow().strftime("%Y%m%d")
        else:
            date_str = checks[0].generated_at.strftime("%Y%m%d")

        path = self.base_dir / "diagnostics" / date_str / "diagnostics.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [c.model_dump(mode="json") for c in checks]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return path
        except Exception as e:
            raise MonitoringStorageError(f"Failed to save diagnostics: {e}")

    def save_report_markdown(self, snapshot: MonitoringSnapshot) -> Path:
        from bist_signal_bot.monitoring.reporting import format_monitoring_report_markdown
        date_str = snapshot.generated_at.strftime("%Y%m%d")
        path = self.base_dir / "reports" / date_str / "monitoring_report.md"
        path.parent.mkdir(parents=True, exist_ok=True)

        content = format_monitoring_report_markdown(snapshot)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path
        except Exception as e:
            raise MonitoringStorageError(f"Failed to save report markdown: {e}")

    def cleanup_old_monitoring_files(self, retention_days: int) -> dict[str, Any]:
        result = {"removed_files": 0, "errors": 0}
        if retention_days <= 0:
            return result

        now = datetime.utcnow().timestamp()
        max_age_secs = retention_days * 86400

        for root_folder in ["snapshots", "diagnostics", "reports"]:
            dir_path = self.base_dir / root_folder
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    try:
                        if now - file_path.stat().st_mtime > max_age_secs:
                            file_path.unlink()
                            result["removed_files"] += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to delete {file_path}: {e}")
                        result["errors"] += 1

        return result
