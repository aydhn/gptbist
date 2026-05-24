import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config_registry.models import (
    ConfigDefinition,
    ConfigDiffResult,
    ConfigDriftResult,
    ConfigGateResult,
    ConfigSnapshot,
    FeatureFlag,
    RuntimeProfile,
)
from bist_signal_bot.storage.paths import get_config_registry_dir


class ConfigRegistryStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def _get_base_dir(self) -> Path:
        if self.base_dir:
            return self.base_dir
        return get_config_registry_dir(self.settings)

    def _get_schema_file(self) -> Path:
        p = self._get_base_dir() / "schema" / "config_definitions.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _get_flags_file(self) -> Path:
        p = self._get_base_dir() / "flags" / "feature_flags.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _get_profiles_file(self) -> Path:
        p = self._get_base_dir() / "profiles" / "runtime_profiles.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save_schema(self, definitions: list[ConfigDefinition]) -> Path:
        p = self._get_schema_file()
        from bist_signal_bot.config_registry.reporting import config_definition_to_dict
        data = [config_definition_to_dict(d) for d in definitions]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return p

    def load_schema(self) -> list[ConfigDefinition] | None:
        p = self._get_schema_file()
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Detailed parsing can be done by a factory or manager; we just return raw for now or properly map it
        # Real impl would instantiate dataclass from dicts
        return data

    def save_flags(self, flags: list[FeatureFlag]) -> Path:
        p = self._get_flags_file()
        from bist_signal_bot.config_registry.reporting import feature_flag_to_dict
        data = [feature_flag_to_dict(f) for f in flags]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return p

    def load_flags(self) -> list[FeatureFlag] | None:
        p = self._get_flags_file()
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def save_profiles(self, profiles: list[RuntimeProfile]) -> Path:
        p = self._get_profiles_file()
        from bist_signal_bot.config_registry.reporting import runtime_profile_to_dict
        data = [runtime_profile_to_dict(pr) for pr in profiles]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return p

    def load_profiles(self) -> list[RuntimeProfile] | None:
        p = self._get_profiles_file()
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def save_snapshot(self, snapshot: ConfigSnapshot) -> dict[str, Path]:
        date_str = snapshot.created_at.strftime("%Y%m%d")
        p = self._get_base_dir() / "snapshots" / date_str / snapshot.snapshot_id / "config_snapshot.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        from bist_signal_bot.config_registry.reporting import snapshot_to_dict
        data = snapshot_to_dict(snapshot)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"json": p}

    def load_snapshot(self, snapshot_id: str) -> ConfigSnapshot | None:
        # Simple scan
        snapshots_dir = self._get_base_dir() / "snapshots"
        if not snapshots_dir.exists():
            return None
        for date_dir in snapshots_dir.iterdir():
            if date_dir.is_dir():
                target = date_dir / snapshot_id / "config_snapshot.json"
                if target.exists():
                    with open(target, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return self._deserialize_snapshot(data)
        return None

    def load_latest_snapshot(self) -> ConfigSnapshot | None:
        snapshots_dir = self._get_base_dir() / "snapshots"
        if not snapshots_dir.exists():
            return None
        all_snapshots = []
        for date_dir in snapshots_dir.iterdir():
            if date_dir.is_dir():
                for snap_dir in date_dir.iterdir():
                    target = snap_dir / "config_snapshot.json"
                    if target.exists():
                        with open(target, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            all_snapshots.append(data)
        if not all_snapshots:
            return None
        # Sort by created_at
        all_snapshots.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return self._deserialize_snapshot(all_snapshots[0])

    def _deserialize_snapshot(self, data: dict[str, Any]) -> ConfigSnapshot:
        from bist_signal_bot.config_registry.models import ConfigValueRecord, ConfigModule, ConfigValueType, ConfigSafetyLevel, FeatureFlag, FeatureFlagState, RuntimeProfileType

        records = []
        for r in data.get("records", []):
            records.append(ConfigValueRecord(
                key=r["key"],
                value=r.get("value_redacted"), # In snapshot, raw value is not saved
                value_redacted=r.get("value_redacted"),
                source=r.get("source", "UNKNOWN"),
                module=ConfigModule(r["module"]),
                value_type=ConfigValueType(r["value_type"]),
                safety_level=ConfigSafetyLevel(r["safety_level"]),
                is_default=r.get("is_default", False),
                is_secret=r.get("is_secret", False),
                valid=r.get("valid", True),
                warnings=r.get("warnings", []),
                metadata=r.get("metadata", {})
            ))

        flags = []
        for f in data.get("flags", []):
            flags.append(FeatureFlag(
                flag_id=f["flag_id"],
                key=f["key"],
                module=ConfigModule(f["module"]),
                state=FeatureFlagState(f["state"]),
                default_state=FeatureFlagState(f["default_state"]),
                safety_level=ConfigSafetyLevel(f["safety_level"]),
                description=f.get("description", ""),
                dependencies=f.get("dependencies", []),
                conflicts=f.get("conflicts", []),
                requires_confirm=f.get("requires_confirm", False),
                metadata=f.get("metadata", {})
            ))

        ptype = data.get("profile_type")

        return ConfigSnapshot(
            snapshot_id=data["snapshot_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            profile_type=RuntimeProfileType(ptype) if ptype else None,
            app_version=data.get("app_version", "1.0.0"),
            schema_version=data.get("schema_version", "1.0.0"),
            records=records,
            flags=flags,
            redacted=data.get("redacted", True),
            checksum_sha256=data.get("checksum_sha256"),
            warnings=data.get("warnings", []),
            disclaimer=data.get("disclaimer", ""),
            metadata=data.get("metadata", {})
        )

    def save_diff(self, diff: ConfigDiffResult) -> dict[str, Path]:
        date_str = diff.created_at.strftime("%Y%m%d")
        p = self._get_base_dir() / "diffs" / date_str / diff.diff_id / "config_diff.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        from bist_signal_bot.config_registry.reporting import diff_to_dict
        data = diff_to_dict(diff)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"json": p}

    def save_drift(self, result: ConfigDriftResult) -> dict[str, Path]:
        date_str = result.created_at.strftime("%Y%m%d")
        p = self._get_base_dir() / "drift" / date_str / result.drift_id / "config_drift.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        from bist_signal_bot.config_registry.reporting import drift_to_dict
        data = drift_to_dict(result)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"json": p}

    def save_gate(self, result: ConfigGateResult) -> dict[str, Path]:
        now = datetime.now(UTC)
        date_str = now.strftime("%Y%m%d")
        p = self._get_base_dir() / "gates" / date_str / result.gate_id / "config_gate.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        from bist_signal_bot.config_registry.reporting import gate_to_dict
        data = gate_to_dict(result)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"json": p}

    def list_snapshots(self, limit: int = 20) -> list[dict[str, Any]]:
        snapshots_dir = self._get_base_dir() / "snapshots"
        if not snapshots_dir.exists():
            return []
        all_snapshots = []
        for date_dir in snapshots_dir.iterdir():
            if date_dir.is_dir():
                for snap_dir in date_dir.iterdir():
                    target = snap_dir / "config_snapshot.json"
                    if target.exists():
                        try:
                            with open(target, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                all_snapshots.append({
                                    "snapshot_id": data.get("snapshot_id"),
                                    "created_at": data.get("created_at"),
                                    "profile_type": data.get("profile_type"),
                                    "checksum": data.get("checksum_sha256")
                                })
                        except Exception:
                            pass
        all_snapshots.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return all_snapshots[:limit]
