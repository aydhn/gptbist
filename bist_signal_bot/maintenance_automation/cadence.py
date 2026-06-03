from typing import List, Optional, Any, Dict
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceCadencePolicy,
    MaintenanceCadenceKind,
    MaintenanceAction,
    MaintenanceActionType
)

class MaintenanceCadenceRegistry:
    def __init__(self):
        self._policies: Dict[str, MaintenanceCadencePolicy] = {}
        for p in self.default_policies():
            self._policies[p.policy_id] = p

    def default_policies(self) -> List[MaintenanceCadencePolicy]:
        return [
            MaintenanceCadencePolicy(
                policy_id="daily_operator_self_audit_v1",
                name="Daily Operator Self-Audit",
                cadence=MaintenanceCadenceKind.DAILY,
                actions=[
                    MaintenanceAction(
                        action_id="healthcheck",
                        action_type=MaintenanceActionType.HEALTHCHECK,
                        name="Run Healthcheck",
                    ),
                    MaintenanceAction(
                        action_id="doctor",
                        action_type=MaintenanceActionType.DOCTOR,
                        name="Run Doctor",
                    ),
                    MaintenanceAction(
                        action_id="ops_readiness",
                        action_type=MaintenanceActionType.OPS_READINESS,
                        name="Run Ops Readiness",
                    ),
                    MaintenanceAction(
                        action_id="reports_daily_dry_run",
                        action_type=MaintenanceActionType.CUSTOM,
                        name="Reports Daily (Dry-Run)",
                        command="python -m bist_signal_bot reports daily --dry-run"
                    )
                ]
            ),
            MaintenanceCadencePolicy(
                policy_id="weekly_quality_and_performance_v1",
                name="Weekly Quality and Performance",
                cadence=MaintenanceCadenceKind.WEEKLY,
                actions=[
                    MaintenanceAction(
                        action_id="qa_release_gate",
                        action_type=MaintenanceActionType.QA_GATE,
                        name="Run QA Release Gate",
                    ),
                    MaintenanceAction(
                        action_id="performance_benchmark",
                        action_type=MaintenanceActionType.PERFORMANCE_BENCHMARK,
                        name="Run Performance Benchmark",
                    ),
                    MaintenanceAction(
                        action_id="synthetic_smoke",
                        action_type=MaintenanceActionType.SYNTHETIC_SMOKE,
                        name="Run Synthetic Smoke",
                    ),
                    MaintenanceAction(
                        action_id="data_import_check",
                        action_type=MaintenanceActionType.DATA_IMPORT_CHECK,
                        name="Data Import Check",
                    ),
                    MaintenanceAction(
                        action_id="market_registry_check",
                        action_type=MaintenanceActionType.MARKET_REGISTRY_CHECK,
                        name="Market Registry Check",
                    ),
                    MaintenanceAction(
                        action_id="explainability_check",
                        action_type=MaintenanceActionType.EXPLAINABILITY_CHECK,
                        name="Explainability Check",
                    ),
                    MaintenanceAction(
                        action_id="report_template_check",
                        action_type=MaintenanceActionType.REPORT_TEMPLATE_CHECK,
                        name="Report Template Check",
                    )
                ]
            ),
            MaintenanceCadencePolicy(
                policy_id="monthly_cleanup_and_rotation_v1",
                name="Monthly Cleanup and Rotation",
                cadence=MaintenanceCadenceKind.MONTHLY,
                actions=[
                    MaintenanceAction(
                        action_id="cache_cleanup_dry_run",
                        action_type=MaintenanceActionType.CACHE_CLEANUP,
                        name="Cache Cleanup (Dry-Run)",
                        destructive=True,
                        requires_confirm=True
                    ),
                    MaintenanceAction(
                        action_id="report_rotation_dry_run",
                        action_type=MaintenanceActionType.REPORT_ROTATION,
                        name="Report Rotation (Dry-Run)",
                        destructive=True,
                        requires_confirm=True
                    ),
                    MaintenanceAction(
                        action_id="log_rotation_dry_run",
                        action_type=MaintenanceActionType.LOG_ROTATION,
                        name="Log Rotation (Dry-Run)",
                        destructive=True,
                        requires_confirm=True
                    ),
                    MaintenanceAction(
                        action_id="backup_manifest",
                        action_type=MaintenanceActionType.BACKUP_MANIFEST,
                        name="Backup Manifest",
                    ),
                    MaintenanceAction(
                        action_id="final_audit_run",
                        action_type=MaintenanceActionType.FINAL_AUDIT,
                        name="Final Audit Run",
                    )
                ]
            ),
            MaintenanceCadencePolicy(
                policy_id="quarterly_release_readiness_review_v1",
                name="Quarterly Release Readiness Review",
                cadence=MaintenanceCadenceKind.QUARTERLY,
                actions=[
                    MaintenanceAction(
                        action_id="final_audit",
                        action_type=MaintenanceActionType.FINAL_AUDIT,
                        name="Final Audit",
                    ),
                    MaintenanceAction(
                        action_id="final_handoff",
                        action_type=MaintenanceActionType.CUSTOM,
                        name="Final Handoff Check",
                    ),
                    MaintenanceAction(
                        action_id="docs_hub_coverage",
                        action_type=MaintenanceActionType.CUSTOM,
                        name="Docs Hub Coverage Check",
                    ),
                    MaintenanceAction(
                        action_id="release_pack_check",
                        action_type=MaintenanceActionType.CUSTOM,
                        name="Release Pack Check",
                    ),
                    MaintenanceAction(
                        action_id="roadmap_review",
                        action_type=MaintenanceActionType.CUSTOM,
                        name="Roadmap Review",
                    )
                ]
            ),
            MaintenanceCadencePolicy(
                policy_id="on_demand_safe_cleanup_v1",
                name="On-Demand Safe Cleanup",
                cadence=MaintenanceCadenceKind.ON_DEMAND,
                actions=[
                    MaintenanceAction(
                        action_id="stale_artifact_check",
                        action_type=MaintenanceActionType.STALE_ARTIFACT_CHECK,
                        name="Stale Artifact Check",
                    )
                ]
            ),
            MaintenanceCadencePolicy(
                policy_id="on_demand_backup_manifest_v1",
                name="On-Demand Backup Manifest",
                cadence=MaintenanceCadenceKind.ON_DEMAND,
                actions=[
                    MaintenanceAction(
                        action_id="backup_manifest",
                        action_type=MaintenanceActionType.BACKUP_MANIFEST,
                        name="Backup Manifest",
                    )
                ]
            )
        ]

    def get_policy(self, policy_id_or_name: str) -> Optional[MaintenanceCadencePolicy]:
        if policy_id_or_name in self._policies:
            return self._policies[policy_id_or_name]
        for p in self._policies.values():
            if p.name == policy_id_or_name:
                return p
        return None

    def policies_by_cadence(self, cadence: MaintenanceCadenceKind) -> List[MaintenanceCadencePolicy]:
        return [p for p in self._policies.values() if p.cadence == cadence]

    def validate_policy(self, policy: MaintenanceCadencePolicy) -> List[str]:
        errors = []
        for action in policy.actions:
            errors.extend(action.validate_action())
        if not policy.disclaimer or "not investment advice" not in policy.disclaimer.lower():
            errors.append("Policy disclaimer must clearly state it is not investment advice.")
        return errors

    def policy_summary(self, policy: MaintenanceCadencePolicy) -> Dict[str, Any]:
        return {
            "policy_id": policy.policy_id,
            "name": policy.name,
            "cadence": policy.cadence.value,
            "action_count": len(policy.actions),
            "destructive_count": sum(1 for a in policy.actions if a.destructive),
            "enabled": policy.enabled,
            "warnings": policy.warnings
        }
