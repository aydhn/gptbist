import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from bist_signal_bot.data.providers_v2.models import ProviderHealthSnapshot, ProviderType, ProviderStatus
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.config.settings import get_settings

class ProviderHealthTracker:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.health_dir = get_data_dir(self.settings) / getattr(self.settings, "DATA_PROVIDER_HEALTH_DIR_NAME", "provider_health")
        self.health_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.health_dir / "provider_health.jsonl"

    def record_snapshot(self, snapshot: ProviderHealthSnapshot) -> Path:
        with open(self.file_path, "a") as f:
            f.write(snapshot.model_dump_json() + "\n")
        return self.file_path

    def load_recent(self, provider_type: Optional[ProviderType] = None, limit: int = 100) -> List[ProviderHealthSnapshot]:
        if not self.file_path.exists():
            return []

        snapshots = []
        with open(self.file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    snapshot = ProviderHealthSnapshot(**data)
                    if provider_type is None or snapshot.provider_type == provider_type:
                        snapshots.append(snapshot)
                except Exception:
                    pass

        return sorted(snapshots, key=lambda x: x.generated_at, reverse=True)[:limit]

    def provider_score(self, snapshot: ProviderHealthSnapshot) -> float:
        total = snapshot.success_count + snapshot.failure_count + snapshot.empty_count
        if total == 0:
            return 100.0 if snapshot.status == ProviderStatus.HEALTHY else 0.0
        return (snapshot.success_count / total) * 100.0

    def summarize_health(self) -> Dict[str, Any]:
        snapshots = self.load_recent()
        summary = {}
        for s in snapshots:
            ptype = s.provider_type.value
            if ptype not in summary:
                summary[ptype] = {
                    "status": s.status.value,
                    "score": self.provider_score(s),
                    "last_error": s.last_error,
                    "last_success_at": s.last_success_at.isoformat() if s.last_success_at else None,
                    "last_failure_at": s.last_failure_at.isoformat() if s.last_failure_at else None,
                }
        return summary
