from typing import Any
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceAction, MaintenanceCadencePolicy, MaintenancePlan, MaintenanceActionResult,
    RetentionPolicy, CleanupCandidate, BackupManifest, MaintenanceRunManifest,
    MaintenanceRun, MaintenanceAutomationReport
)

def action_to_dict(action: MaintenanceAction) -> dict[str, Any]: return action.model_dump()
def cadence_policy_to_dict(policy: MaintenanceCadencePolicy) -> dict[str, Any]: return policy.model_dump()
def plan_to_dict(plan: MaintenancePlan) -> dict[str, Any]: return plan.model_dump()
def action_result_to_dict(result: MaintenanceActionResult) -> dict[str, Any]: return result.model_dump()
def retention_policy_to_dict(policy: RetentionPolicy) -> dict[str, Any]: return policy.model_dump()
def cleanup_candidate_to_dict(candidate: CleanupCandidate) -> dict[str, Any]: return candidate.model_dump()
def backup_manifest_to_dict(manifest: BackupManifest) -> dict[str, Any]: return manifest.model_dump()
def run_manifest_to_dict(manifest: MaintenanceRunManifest) -> dict[str, Any]: return manifest.model_dump()
def run_to_dict(run: MaintenanceRun) -> dict[str, Any]: return run.model_dump()
def report_to_dict(report: MaintenanceAutomationReport) -> dict[str, Any]: return report.model_dump()

def format_policy_text(policy: MaintenanceCadencePolicy) -> str: return f"Policy: {policy.name}"
def format_plan_text(plan: MaintenancePlan) -> str: return f"Plan: {plan.cadence}"
def format_run_text(run: MaintenanceRun) -> str: return f"Run Status: {run.status}"
def format_cleanup_candidates_text(candidates: list[CleanupCandidate]) -> str: return f"Cleanup Candidates: {len(candidates)}"
def format_backup_manifest_text(manifest: BackupManifest) -> str: return f"Backup Manifest Status: {manifest.status}"
def format_maintenance_automation_report_markdown(report: MaintenanceAutomationReport) -> str: return f"# Report\n{report.disclaimer}"
