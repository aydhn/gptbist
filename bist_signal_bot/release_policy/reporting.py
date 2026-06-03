from typing import Any, Dict
from bist_signal_bot.release_policy.models import (
    BranchPolicy, VersionSnapshot, ChangeRequest, CompatibilityCheckResult,
    ChangelogEntry, MigrationNote, DeprecationNotice, ReleaseBranchFreezeManifest,
    FinalClosureManifest, ReleasePolicyGovernanceAssessment, ReleasePolicyReport
)

def branch_policy_to_dict(policy: BranchPolicy) -> Dict[str, Any]:
    return policy.model_dump()

def version_snapshot_to_dict(snapshot: VersionSnapshot) -> Dict[str, Any]:
    return snapshot.model_dump()

def change_request_to_dict(change: ChangeRequest) -> Dict[str, Any]:
    return change.model_dump()

def compatibility_result_to_dict(result: CompatibilityCheckResult) -> Dict[str, Any]:
    return result.model_dump()

def changelog_entry_to_dict(entry: ChangelogEntry) -> Dict[str, Any]:
    return entry.model_dump()

def migration_note_to_dict(note: MigrationNote) -> Dict[str, Any]:
    return note.model_dump()

def deprecation_notice_to_dict(notice: DeprecationNotice) -> Dict[str, Any]:
    return notice.model_dump()

def freeze_manifest_to_dict(manifest: ReleaseBranchFreezeManifest) -> Dict[str, Any]:
    return manifest.model_dump()

def closure_manifest_to_dict(manifest: FinalClosureManifest) -> Dict[str, Any]:
    return manifest.model_dump()

def governance_to_dict(assessment: ReleasePolicyGovernanceAssessment) -> Dict[str, Any]:
    return assessment.model_dump()

def report_to_dict(report: ReleasePolicyReport) -> Dict[str, Any]:
    return report.model_dump()

def format_branch_policy_text(policy: BranchPolicy) -> str:
    return f"Branch Policy ({policy.branch_kind.value}): {policy.policy_id}"

def format_version_snapshot_text(snapshot: VersionSnapshot) -> str:
    return f"Version Snapshot: {snapshot.project_version}"

def format_compatibility_text(result: CompatibilityCheckResult) -> str:
    return f"Compatibility Check: {result.status.value}"

def format_freeze_text(manifest: ReleaseBranchFreezeManifest) -> str:
    return f"Freeze Manifest for {manifest.branch_name}: Frozen={manifest.frozen}"

def format_closure_text(manifest: FinalClosureManifest) -> str:
    return f"Final Closure Manifest: Phase {manifest.phase_range} - Status={manifest.final_status.value}"

def format_release_policy_report_markdown(report: ReleasePolicyReport) -> str:
    lines = ["# Release Policy Report"]
    if report.closures:
        lines.append(f"Closure Status: {report.closures[-1].final_status.value}")
    if report.governance_assessments:
        lines.append(f"Governance Status: {report.governance_assessments[-1].status.value}")
    lines.append(f"\n> *{report.disclaimer}*\n")
    return "\n".join(lines)
