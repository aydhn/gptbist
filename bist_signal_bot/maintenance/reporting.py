from typing import Any
from bist_signal_bot.maintenance.models import (
    BackupManifest, BackupResult, RestoreResult, CleanupResult,
    MigrationPlan, MigrationResult, MaintenanceDoctorReport, BackupFileEntry, CleanupCandidate
)

def format_maintenance_report_markdown(report_or_result: Any) -> str:
    md = []

    if isinstance(report_or_result, BackupResult):
        md.append(f"# Backup Result: {report_or_result.status.value}")
        md.append(f"- ID: {report_or_result.backup_id}")
        md.append(f"- Verified: {report_or_result.verified}")
        md.append(f"- Time: {report_or_result.elapsed_seconds:.2f}s")
        md.append(f"- Files: {report_or_result.manifest.included_files}")
        if report_or_result.warnings:
             md.append("## Warnings")
             for w in report_or_result.warnings:
                  md.append(f"- {w}")

    elif isinstance(report_or_result, RestoreResult):
        md.append(f"# Restore Result: {report_or_result.status.value}")
        md.append(f"- ID: {report_or_result.restore_id}")
        md.append(f"- Dry Run: {report_or_result.request.dry_run}")
        md.append(f"- Restored: {report_or_result.restored_files}")
        md.append(f"- Blocked: {report_or_result.blocked_files}")

    elif isinstance(report_or_result, CleanupResult):
        md.append(f"# Cleanup Result: {report_or_result.status.value}")
        md.append(f"- ID: {report_or_result.cleanup_id}")
        md.append(f"- Dry Run: {report_or_result.dry_run}")
        md.append(f"- Candidates: {len(report_or_result.candidates)}")
        md.append(f"- Deleted: {report_or_result.deleted_files}")

    elif isinstance(report_or_result, MaintenanceDoctorReport):
        md.append(f"# Doctor Report: {report_or_result.status.value}")
        md.append(f"- Missing Dirs: {len(report_or_result.missing_dirs)}")
        md.append(f"- Corrupted JSONL: {len(report_or_result.corrupted_files)}")
        md.append(f"- Secret Risks: {len(report_or_result.secret_risk_files)}")
        if report_or_result.recommendations:
             md.append("## Recommendations")
             for r in report_or_result.recommendations:
                  md.append(f"- {r}")

    md.append("\n***\n")
    if hasattr(report_or_result, "disclaimer"):
         md.append(f"_{report_or_result.disclaimer}_")

    return "\n".join(md)
