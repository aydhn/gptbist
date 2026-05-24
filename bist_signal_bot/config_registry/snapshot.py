import hashlib
import json
import copy
import uuid
from datetime import datetime, UTC

from bist_signal_bot.config_registry.models import ConfigSnapshot, RuntimeProfileType
from bist_signal_bot.config_registry.registry import ConfigRegistry
from bist_signal_bot.config_registry.flags import FeatureFlagManager
from bist_signal_bot.config_registry.storage import ConfigRegistryStore


class ConfigSnapshotManager:
    def __init__(self, registry: ConfigRegistry, flag_manager: FeatureFlagManager, store: ConfigRegistryStore | None = None):
        self.registry = registry
        self.flag_manager = flag_manager
        self.store = store

    def create_snapshot(self, profile_type: RuntimeProfileType | None = None, save: bool = True) -> ConfigSnapshot:
        records = self.registry.list_records()
        flags = self.flag_manager.load_flags()

        # Redact raw secrets before calculating checksum
        redacted_records = []
        for r in records:

            r_copy = copy.deepcopy(r)
            if r_copy.is_secret:
                r_copy.value = r_copy.value_redacted  # Ensure raw secret is not stored
            redacted_records.append(r_copy)

        snapshot = ConfigSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.now(UTC),
            profile_type=profile_type,
            records=redacted_records,
            flags=[copy.deepcopy(f) for f in flags],
            redacted=True
        )

        snapshot.checksum_sha256 = self.snapshot_checksum(snapshot)

        if save and self.store:
            self.store.save_snapshot(snapshot)

        return snapshot

    def snapshot_checksum(self, snapshot: ConfigSnapshot) -> str:
        # Simple deterministic checksum based on keys and redacted values + flags
        data = []
        for r in sorted(snapshot.records, key=lambda x: x.key):
            data.append(f"{r.key}:{r.value_redacted}")
        for f in sorted(snapshot.flags, key=lambda x: x.key):
            data.append(f"{f.key}:{f.state.value}")

        raw = "|".join(data)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def load_snapshot(self, snapshot_id: str) -> ConfigSnapshot | None:
        if not self.store:
            return None
        return self.store.load_snapshot(snapshot_id)

    def load_latest_snapshot(self) -> ConfigSnapshot | None:
        if not self.store:
            return None
        return self.store.load_latest_snapshot()

    def list_snapshots(self, limit: int = 20) -> list[dict[str, str]]:
        if not self.store:
            return []
        return self.store.list_snapshots(limit=limit)
