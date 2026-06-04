import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from bist_signal_bot.release_policy.models import (
    VersionSnapshot, VersionBumpType, ChangeRequest, ChangeType
)
from bist_signal_bot.config.settings import get_settings

class VersionGovernanceEngine:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_version_snapshot(self) -> VersionSnapshot:
        return VersionSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            project_version=self.settings.RELEASE_POLICY_PROJECT_VERSION or "1.0.0",
            schema_version=self.settings.RELEASE_POLICY_SCHEMA_VERSION or "1.0.0",
            config_version=self.settings.RELEASE_POLICY_CONFIG_VERSION or "1.0.0",
            cli_contract_version=self.settings.RELEASE_POLICY_CLI_CONTRACT_VERSION or "1.0.0",
            data_contract_version=self.settings.RELEASE_POLICY_DATA_CONTRACT_VERSION or "1.0.0",
            plugin_contract_version=self.settings.RELEASE_POLICY_PLUGIN_CONTRACT_VERSION or "1.0.0"
        )

    def validate_version_snapshot(self, snapshot: VersionSnapshot) -> List[str]:
        errors = []
        versions = [
            ("project_version", snapshot.project_version),
            ("schema_version", snapshot.schema_version),
            ("config_version", snapshot.config_version),
            ("cli_contract_version", snapshot.cli_contract_version),
            ("data_contract_version", snapshot.data_contract_version)
        ]
        for name, ver in versions:
            if not self.is_valid_semver(ver):
                errors.append(f"{name} '{ver}' is not a valid semver.")

        if snapshot.plugin_contract_version and not self.is_valid_semver(snapshot.plugin_contract_version):
             errors.append(f"plugin_contract_version '{snapshot.plugin_contract_version}' is not a valid semver.")
        return errors

    def suggest_version_bump(self, changes: List[ChangeRequest]) -> VersionBumpType:
        bump = VersionBumpType.NONE
        for change in changes:
            if change.change_type == ChangeType.BREAKING:
                return VersionBumpType.MAJOR
            elif change.change_type in [ChangeType.FEATURE, ChangeType.DEPRECATION]:
                if bump not in [VersionBumpType.MAJOR]:
                    bump = VersionBumpType.MINOR
            elif change.change_type in [ChangeType.BUGFIX, ChangeType.SECURITY, ChangeType.PERFORMANCE]:
                if bump == VersionBumpType.NONE:
                    bump = VersionBumpType.PATCH
        return bump

    def parse_semver(self, version: str) -> Optional[Dict[str, int]]:
        match = re.match(r"^([0-9]+)\.([0-9]+)\.([0-9]+)(?:-[a-zA-Z0-9\.]+)?(?:\+[a-zA-Z0-9\.]+)?$", version)
        if match:
            return {
                "major": int(match.group(1)),
                "minor": int(match.group(2)),
                "patch": int(match.group(3))
            }
        return None

    def is_valid_semver(self, version: str) -> bool:
        return self.parse_semver(version) is not None

    def compare_versions(self, a: str, b: str) -> int:
        va = self.parse_semver(a)
        vb = self.parse_semver(b)
        if not va or not vb:
            return 0
        for part in ["major", "minor", "patch"]:
            if va[part] > vb[part]: return 1
            if va[part] < vb[part]: return -1
        return 0

    def version_summary(self, snapshot: VersionSnapshot) -> Dict[str, Any]:
        return {
            "project_version": snapshot.project_version,
            "schema_version": snapshot.schema_version,
            "config_version": snapshot.config_version,
            "cli_contract_version": snapshot.cli_contract_version,
            "data_contract_version": snapshot.data_contract_version
        }
