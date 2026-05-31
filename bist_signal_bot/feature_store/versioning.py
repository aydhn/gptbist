from datetime import datetime, timezone
import uuid
import hashlib
import json
from typing import Any
from bist_signal_bot.feature_store.models import FeatureDefinition, FeatureContract, FeatureVersion, FeatureStatus

class FeatureVersionManager:
    def __init__(self):
        self._versions: dict[str, list[FeatureVersion]] = {}

    def create_version(self, feature: FeatureDefinition, contract: FeatureContract | None = None, change_summary: str = "") -> FeatureVersion:
        now = datetime.now(timezone.utc)
        contract_id = contract.contract_id if contract else None

        history = self._versions.get(feature.feature_name, [])
        if not history:
            ver_str = "1.0"
        else:
            last_ver = history[-1].version
            parts = last_ver.split(".")
            if len(parts) == 2:
                ver_str = f"{parts[0]}.{int(parts[1]) + 1}"
            else:
                ver_str = f"{last_ver}.1"

        version = FeatureVersion(
            version_id=f"ver_{uuid.uuid4().hex[:8]}",
            feature_name=feature.feature_name,
            version=ver_str,
            created_at=now,
            contract_id=contract_id,
            compute_hash=self.compute_contract_hash(contract),
            change_summary=change_summary,
            status=FeatureStatus.ACTIVE
        )

        if feature.feature_name not in self._versions:
            self._versions[feature.feature_name] = []
        self._versions[feature.feature_name].append(version)

        return version

    def latest_version(self, feature_name: str) -> FeatureVersion | None:
        history = self._versions.get(feature_name, [])
        return history[-1] if history else None

    def version_history(self, feature_name: str) -> list[FeatureVersion]:
        return self._versions.get(feature_name, [])

    def compare_versions(self, feature_name: str, old_version: str, new_version: str) -> dict[str, Any]:
        history = self._versions.get(feature_name, [])
        old_v = next((v for v in history if v.version == old_version), None)
        new_v = next((v for v in history if v.version == new_version), None)

        return {
            "feature_name": feature_name,
            "old_version": old_v.version if old_v else None,
            "new_version": new_v.version if new_v else None,
            "hash_changed": old_v.compute_hash != new_v.compute_hash if (old_v and new_v) else None
        }

    def compute_contract_hash(self, contract: FeatureContract | None) -> str | None:
        if not contract:
            return None
        data = f"{contract.feature_name}:{contract.version}:{contract.dtype.value}"
        return hashlib.sha256(data.encode()).hexdigest()
