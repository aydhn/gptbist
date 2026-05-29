import pandas as pd
from typing import Any

from bist_signal_bot.ops.models import (
    OpsCheckResult, OpsHealthSnapshot, StoreIntegrityResult, StalenessFinding,
    OpsIncident, OpsRunbook, BackupManifest, RestorePlan, RetentionFinding,
    MigrationCheckResult, OperationalReadinessResult, OpsReport
)

def ops_check_to_dict(check: OpsCheckResult) -> dict[str, Any]:
    return check.model_dump(mode="json")

def health_snapshot_to_dict(snapshot: OpsHealthSnapshot) -> dict[str, Any]:
    return snapshot.model_dump(mode="json")

def store_integrity_to_dict(result: StoreIntegrityResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def staleness_finding_to_dict(finding: StalenessFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def incident_to_dict(incident: OpsIncident) -> dict[str, Any]:
    return incident.model_dump(mode="json")

def runbook_to_dict(runbook: OpsRunbook) -> dict[str, Any]:
    return runbook.model_dump(mode="json")

def backup_manifest_to_dict(manifest: BackupManifest) -> dict[str, Any]:
    return manifest.model_dump(mode="json")

def restore_plan_to_dict(plan: RestorePlan) -> dict[str, Any]:
    return plan.model_dump(mode="json")

def retention_finding_to_dict(finding: RetentionFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def migration_check_to_dict(result: MigrationCheckResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def readiness_to_dict(result: OperationalReadinessResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def ops_report_to_dict(report: OpsReport) -> dict[str, Any]:
    return report.model_dump(mode="json")

def ops_checks_to_dataframe(checks: list[OpsCheckResult]) -> pd.DataFrame:
    return pd.DataFrame([ops_check_to_dict(c) for c in checks])

def incidents_to_dataframe(incidents: list[OpsIncident]) -> pd.DataFrame:
    return pd.DataFrame([incident_to_dict(i) for i in incidents])

def format_health_snapshot_text(snapshot: OpsHealthSnapshot) -> str:
    lines = [
        f"Health Snapshot: {snapshot.snapshot_id}",
        f"Status: {snapshot.status.value}",
        f"Pass: {snapshot.pass_count}, Watch: {snapshot.watch_count}, Fail: {snapshot.fail_count}, Blocked: {snapshot.blocked_count}",
    ]
    if snapshot.key_findings:
        lines.append("Key Findings:")
        for f in snapshot.key_findings:
            lines.append(f"  - {f}")
    lines.append(f"\nDisclaimer: {snapshot.disclaimer}")
    return "\n".join(lines)

def format_store_integrity_text(result: StoreIntegrityResult) -> str:
    return (f"Store Integrity: {result.status.value}\n"
            f"Files checked: {result.files_checked}\n"
            f"Invalid files: {len(result.invalid_files)}\n"
            f"Missing files: {len(result.missing_expected_files)}")

def format_incident_text(incident: OpsIncident) -> str:
    return (f"Incident: {incident.incident_id}\n"
            f"Type: {incident.incident_type.value}\n"
            f"Status: {incident.status.value}\n"
            f"Severity: {incident.severity.value}\n"
            f"Title: {incident.title}\n"
            f"Description: {incident.description}\n"
            f"\nDisclaimer: {incident.disclaimer}")

def format_runbook_text(runbook: OpsRunbook) -> str:
    lines = [
        f"Runbook: {runbook.title} ({runbook.runbook_type.value})",
        f"Description: {runbook.description}",
        "Steps:"
    ]
    for step in runbook.steps:
        lines.append(f"  - {step.title}: {step.description}")
        if step.command_hint:
            lines.append(f"    Command: {step.command_hint}")
        if step.destructive:
            lines.append("    [DESTRUCTIVE ACTION]")
    lines.append(f"\nDisclaimer: {runbook.disclaimer}")
    return "\n".join(lines)

def format_backup_manifest_text(manifest: BackupManifest) -> str:
    return (f"Backup: {manifest.backup_id}\n"
            f"Status: {manifest.status.value}\n"
            f"Scope: {[s.value for s in manifest.scope]}\n"
            f"Files included: {manifest.files_included}\n"
            f"Total bytes: {manifest.total_bytes}\n"
            f"\nDisclaimer: {manifest.disclaimer}")

def format_readiness_text(result: OperationalReadinessResult) -> str:
    lines = [
        f"Operational Readiness: {result.status.value}",
        f"Health: {result.health_snapshot.status.value if result.health_snapshot else 'UNKNOWN'}",
        f"Integrity: {result.store_integrity.status.value if result.store_integrity else 'UNKNOWN'}",
        f"QA Gate: {result.latest_qa_gate_status}",
        f"Open Incidents: {len(result.open_incidents)}"
    ]
    if result.blocking_reasons:
        lines.append("Blocking Reasons:")
        for br in result.blocking_reasons:
            lines.append(f"  - {br}")
    lines.append(f"\nDisclaimer: {result.disclaimer}")
    return "\n".join(lines)

def format_ops_report_markdown(report: OpsReport) -> str:
    lines = [
        "# Ops & Reliability Report",
        f"**Generated At**: {report.generated_at.isoformat()}",
        "",
        "## Readiness",
        format_readiness_text(report.readiness) if report.readiness else "Not evaluated",
        "",
        "## Health Snapshot",
        format_health_snapshot_text(report.health_snapshot) if report.health_snapshot else "Not evaluated",
        "",
        "## Store Integrity",
        format_store_integrity_text(report.store_integrity) if report.store_integrity else "Not evaluated",
        "",
        "## Incidents",
        f"Found {len(report.incidents)} recent incidents.",
        "",
        "## Backups",
        f"Found {len(report.backups)} backups.",
        "",
        "---",
        f"*{report.disclaimer}*"
    ]
    return "\n".join(lines)
