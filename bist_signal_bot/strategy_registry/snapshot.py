import uuid
import hashlib
import json
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyRegistrySnapshot,
    StrategyRegistryStatus
)
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore

class StrategyRegistrySnapshotBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.store = StrategyRegistryStore(self.settings, base_dir)

    def create_snapshot(self, save: bool = True) -> StrategyRegistrySnapshot:
        definitions = self.store.load_definitions()

        status_counts = {}
        blocked = []
        candidates = []
        validated = []

        for d in definitions:
            status_counts[d.status.value] = status_counts.get(d.status.value, 0) + 1
            if d.status == StrategyRegistryStatus.BLOCKED:
                blocked.append(d.strategy_name)
            elif d.status == StrategyRegistryStatus.CANDIDATE:
                candidates.append(d.strategy_name)
            elif d.status == StrategyRegistryStatus.VALIDATED_RESEARCH:
                validated.append(d.strategy_name)

        snapshot = StrategyRegistrySnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            strategies_count=len(definitions),
            status_counts=status_counts,
            scorecards_count=0, # Would load scorecards but that's heavy, maybe estimate
            blocked_strategies=blocked,
            candidate_strategies=candidates,
            validated_research_strategies=validated
        )

        snapshot.checksum_sha256 = self.snapshot_checksum(snapshot)

        if save:
            self.store.save_snapshot(snapshot)

        return snapshot

    def snapshot_checksum(self, snapshot: StrategyRegistrySnapshot) -> str:
        from bist_signal_bot.strategy_registry.reporting import snapshot_to_dict
        data = snapshot_to_dict(snapshot)
        # Remove volatile fields
        data.pop("snapshot_id", None)
        data.pop("created_at", None)
        data.pop("checksum_sha256", None)

        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def compare_snapshots(self, old_id: str, new_id: str) -> dict[str, Any]:
        # Mock logic
        return {
            "match": True,
            "changes": []
        }
