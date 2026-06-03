from typing import List, Optional, Dict
from bist_signal_bot.maintenance_automation.models import RetentionPolicy, MaintenanceArtifactKind

class RetentionPolicyRegistry:
    def __init__(self):
        self._policies: Dict[str, RetentionPolicy] = {}
        for p in self.default_retention_policies():
            self._policies[p.retention_id] = p

    def default_retention_policies(self) -> List[RetentionPolicy]:
        return [
            RetentionPolicy(
                retention_id="cache_default_v1",
                artifact_kind=MaintenanceArtifactKind.CACHE,
                path_pattern="data/cache/**/*",
                retention_days=30,
                max_total_mb=1024.0,
                archive_before_delete=False
            ),
            RetentionPolicy(
                retention_id="reports_default_v1",
                artifact_kind=MaintenanceArtifactKind.REPORT,
                path_pattern="data/reports/**/*",
                retention_days=180,
                archive_before_delete=True
            ),
            RetentionPolicy(
                retention_id="logs_default_v1",
                artifact_kind=MaintenanceArtifactKind.LOG,
                path_pattern="logs/**/*",
                retention_days=30,
                archive_before_delete=True
            ),
            RetentionPolicy(
                retention_id="temp_files_default_v1",
                artifact_kind=MaintenanceArtifactKind.TEMP_FILE,
                path_pattern="data/temp/**/*",
                retention_days=7,
                archive_before_delete=False
            ),
            RetentionPolicy(
                retention_id="exports_default_v1",
                artifact_kind=MaintenanceArtifactKind.EXPORT,
                path_pattern="data/exports/**/*",
                retention_days=90,
                archive_before_delete=True
            ),
            RetentionPolicy(
                retention_id="manifests_default_v1",
                artifact_kind=MaintenanceArtifactKind.MANIFEST,
                path_pattern="data/manifests/**/*",
                retention_days=365,
                archive_before_delete=True
            ),
            RetentionPolicy(
                retention_id="backups_default_v1",
                artifact_kind=MaintenanceArtifactKind.BACKUP,
                path_pattern="data/backups/**/*",
                retention_days=365,
                archive_before_delete=False
            )
        ]

    def get_policy(self, retention_id: str) -> Optional[RetentionPolicy]:
        return self._policies.get(retention_id)

    def policy_for_artifact_kind(self, kind: MaintenanceArtifactKind) -> Optional[RetentionPolicy]:
        for p in self._policies.values():
            if p.artifact_kind == kind:
                return p
        return None

    def validate_retention_policy(self, policy: RetentionPolicy) -> List[str]:
        errors = []
        if policy.retention_days <= 0:
            errors.append("retention_days must be greater than 0.")
        if policy.max_total_mb is not None and policy.max_total_mb <= 0:
            errors.append("max_total_mb must be greater than 0.")
        return errors
