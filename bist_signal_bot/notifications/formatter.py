from bist_signal_bot.maintenance_automation.models import (
    MaintenanceCadencePolicy,
    MaintenancePlan,
    MaintenanceRun,
    CleanupCandidate,
    BackupManifest,
    MaintenanceAutomationReport
)

def format_maintenance_policy(policy: MaintenanceCadencePolicy) -> str:
    return f"Policy {policy.name} formatted"

def format_maintenance_plan(plan: MaintenancePlan) -> str:
    return f"Plan {plan.plan_id} formatted"

def format_maintenance_run(run: MaintenanceRun) -> str:
    return f"Run {run.run_id} formatted"

def format_cleanup_candidates(candidates: list[CleanupCandidate]) -> str:
    return f"Found {len(candidates)} cleanup candidates"

def format_backup_manifest(manifest: BackupManifest) -> str:
    return f"Backup manifest {manifest.backup_id} formatted"

def format_maintenance_automation_report(report: MaintenanceAutomationReport) -> str:
    return f"""BIST Bot Maintenance Automation Özeti

Cadence: UNKNOWN
Status: {report.warnings}
Actions: {len(report.runs)}
Skipped: 0
Cleanup Candidates: {len(report.cleanup_candidates)}
Dry-run: true

Bu çıktı yerel yazılım bakım özetidir.
Yatırım tavsiyesi değildir.
İşlem uygunluğu anlamına gelmez.
Gerçek emir gönderilmedi."""
