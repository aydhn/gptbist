from bist_signal_bot.maintenance_automation.models import RetentionPolicy, MaintenanceArtifactKind

class RetentionPolicyRegistry:
    def default_retention_policies(self) -> list[RetentionPolicy]:
        return [
            RetentionPolicy(retention_id="cache_ret", artifact_kind=MaintenanceArtifactKind.CACHE, path_pattern="*cache*", retention_days=30),
            RetentionPolicy(retention_id="report_ret", artifact_kind=MaintenanceArtifactKind.REPORT, path_pattern="*report*", retention_days=180),
            RetentionPolicy(retention_id="log_ret", artifact_kind=MaintenanceArtifactKind.LOG, path_pattern="*log*", retention_days=30),
        ]

    def validate_retention_policy(self, policy: RetentionPolicy) -> list[str]:
        errors = []
        if policy.retention_days <= 0:
            errors.append("Retention days must be positive")
        return errors
