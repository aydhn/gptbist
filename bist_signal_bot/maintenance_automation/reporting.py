from typing import Any, Dict, List
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceAction, MaintenanceCadencePolicy, MaintenancePlan,
    MaintenanceActionResult, RetentionPolicy, CleanupCandidate,
    BackupManifest, MaintenanceRunManifest, MaintenanceRun,
    MaintenanceAutomationReport
)

def action_to_dict(action: MaintenanceAction) -> Dict[str, Any]:
    return action.model_dump(mode='json')

def cadence_policy_to_dict(policy: MaintenanceCadencePolicy) -> Dict[str, Any]:
    return policy.model_dump(mode='json')

def plan_to_dict(plan: MaintenancePlan) -> Dict[str, Any]:
    return plan.model_dump(mode='json')

def action_result_to_dict(result: MaintenanceActionResult) -> Dict[str, Any]:
    return result.model_dump(mode='json')

def retention_policy_to_dict(policy: RetentionPolicy) -> Dict[str, Any]:
    return policy.model_dump(mode='json')

def cleanup_candidate_to_dict(candidate: CleanupCandidate) -> Dict[str, Any]:
    return candidate.model_dump(mode='json')

def backup_manifest_to_dict(manifest: BackupManifest) -> Dict[str, Any]:
    return manifest.model_dump(mode='json')

def run_manifest_to_dict(manifest: MaintenanceRunManifest) -> Dict[str, Any]:
    return manifest.model_dump(mode='json')

def run_to_dict(run: MaintenanceRun) -> Dict[str, Any]:
    return run.model_dump(mode='json')

def report_to_dict(report: MaintenanceAutomationReport) -> Dict[str, Any]:
    return report.model_dump(mode='json')

def format_policy_text(policy: MaintenanceCadencePolicy) -> str:
    lines = [
        f"Policy ID: {policy.policy_id}",
        f"Name: {policy.name}",
        f"Cadence: {policy.cadence.value}",
        f"Enabled: {policy.enabled}",
        f"Actions: {len(policy.actions)}"
    ]
    for action in policy.actions:
        lines.append(f"  - {action.name} [{action.action_type.value}] (Destructive: {action.destructive})")
    lines.append(f"Disclaimer: {policy.disclaimer}")
    return "\n".join(lines)

def format_plan_text(plan: MaintenancePlan) -> str:
    lines = [
        f"Plan ID: {plan.plan_id}",
        f"Cadence: {plan.cadence.value}",
        f"Dry-Run: {plan.dry_run}",
        f"Confirm: {plan.confirm}",
        f"Status: {plan.status.value}",
        f"Estimated Destructive Actions: {plan.estimated_destructive_actions}",
        f"Disclaimer: {plan.disclaimer}"
    ]
    return "\n".join(lines)

def format_run_text(run: MaintenanceRun) -> str:
    lines = [
        f"Run ID: {run.run_id}",
        f"Started At: {run.started_at}",
        f"Status: {run.status.value}",
        f"Results: {len(run.results)}"
    ]
    for r in run.results:
        lines.append(f"  - {r.action_id}: {r.status.value} (Skipped: {r.skipped})")
    lines.append(f"Disclaimer: {run.disclaimer}")
    return "\n".join(lines)

def format_cleanup_candidates_text(candidates: List[CleanupCandidate]) -> str:
    lines = [f"Found {len(candidates)} cleanup candidates:"]
    for c in candidates:
        lines.append(f"  - [{c.artifact_kind.value}] {c.path} (Reason: {c.reason})")
    return "\n".join(lines)

def format_backup_manifest_text(manifest: BackupManifest) -> str:
    lines = [
        f"Backup ID: {manifest.backup_id}",
        f"Status: {manifest.status.value}",
        f"Dry-Run: {manifest.dry_run}",
        f"Source Paths: {len(manifest.source_paths)}",
        f"Checksums: {len(manifest.checksum_manifest)} files",
        f"Disclaimer: {manifest.disclaimer}"
    ]
    return "\n".join(lines)

def format_maintenance_automation_report_markdown(report: MaintenanceAutomationReport) -> str:
    lines = [
        f"# Maintenance Automation Report",
        f"Generated: {report.generated_at}",
        f"",
        f"## Summary",
        f"- Runs: {len(report.runs)}",
        f"- Cleanup Candidates: {len(report.cleanup_candidates)}",
        f"- Backup Manifests: {len(report.backup_manifests)}",
        f"",
        f"## Key Findings"
    ]
    if report.key_findings:
        for k in report.key_findings:
            lines.append(f"- {k}")
    else:
        lines.append("- No key findings.")

    lines.append("")
    lines.append(f"## Warnings")
    if report.warnings:
        for w in report.warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- No warnings.")

    lines.append("")
    lines.append(f"## Disclaimer")
    lines.append(f"> {report.disclaimer}")

    return "\n".join(lines)
