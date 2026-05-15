import pandas as pd
from typing import Any

from bist_signal_bot.security.models import (
    SecurityAuditReport, SecurityCheckResult, SecretFinding,
    ForbiddenActionFinding, KillSwitchState
)

def security_audit_report_to_dict(report: SecurityAuditReport) -> dict[str, Any]:
    return report.safe_public_dict()

def security_checks_to_dataframe(checks: list[SecurityCheckResult]) -> pd.DataFrame:
    data = []
    for c in checks:
        data.append({
            "Check": c.check_name,
            "Component": c.component.value,
            "Severity": c.severity.value,
            "Status": c.status.value,
            "Message": c.message
        })
    return pd.DataFrame(data)

def secret_findings_to_dataframe(findings: list[SecretFinding]) -> pd.DataFrame:
    data = []
    for f in findings:
        data.append({
            "Key": f.key,
            "Classification": f.classification.value,
            "Masked_Value": f.masked_value,
            "Source": f.source,
            "Severity": f.severity.value
        })
    return pd.DataFrame(data)

def forbidden_findings_to_dataframe(findings: list[ForbiddenActionFinding]) -> pd.DataFrame:
    data = []
    for f in findings:
        data.append({
            "Action_Type": f.action_type.value,
            "Location": f.location,
            "Message": f.message,
            "Severity": f.severity.value
        })
    return pd.DataFrame(data)

def format_security_audit_text(report: SecurityAuditReport) -> str:
    lines = [
        "=== BIST SIGNAL BOT SECURITY AUDIT ===",
        f"Overall Score: {report.overall_score:.1f}/100.0",
        f"Status: {report.status.value}",
        f"Checks Performed: {len(report.checks)}",
        f"Secret Leaks Found: {len(report.secret_findings)}",
        f"Forbidden Actions Detected: {len(report.forbidden_action_findings)}",
        f"Kill Switch Active: {'YES' if report.kill_switch_state.enabled else 'NO'}",
        "",
        "--- Disclaimer ---",
        report.disclaimer
    ]

    if report.warnings:
        lines.append("\n--- Warnings ---")
        for w in report.warnings:
            lines.append(f" - {w}")

    recs = report.metadata.get("recommendations", [])
    if recs:
         lines.append("\n--- Recommendations ---")
         for r in recs:
             lines.append(f" * {r}")

    return "\n".join(lines)

def format_security_audit_markdown(report: SecurityAuditReport) -> str:
    md = [
        "# Security Audit Report",
        f"**Score:** {report.overall_score:.1f}/100.0 | **Status:** {report.status.value}",
        "",
        "## Summary",
        f"- **Checks Performed:** {len(report.checks)}",
        f"- **Secret Leaks:** {len(report.secret_findings)}",
        f"- **Forbidden Actions:** {len(report.forbidden_action_findings)}",
        f"- **Kill Switch Active:** {'YES' if report.kill_switch_state.enabled else 'NO'}",
        "",
        "## Details",
    ]

    for c in report.checks:
        icon = "✅" if c.status.value == "PASS" else "❌" if c.status.value == "FAIL" else "⚠️"
        md.append(f"### {icon} {c.check_name} ({c.severity.value})")
        md.append(f"**Component:** {c.component.value}")
        md.append(f"**Message:** {c.message}")
        if c.recommendations:
            for r in c.recommendations:
                md.append(f"- *Rec:* {r}")
        md.append("")

    md.append("## Disclaimer")
    md.append(report.disclaimer)
    return "\n".join(md)

def format_kill_switch_status(state: KillSwitchState) -> str:
    status = "ACTIVE 🔴" if state.enabled else "INACTIVE 🟢"
    lines = [
        f"Kill Switch Status: {status}",
        f"Scopes: {', '.join([s.value for s in state.scopes]) if state.scopes else 'NONE'}"
    ]
    if state.enabled:
        lines.append(f"Reason: {state.reason}")
        lines.append(f"Activated At: {state.activated_at}")
        lines.append(f"Activated By: {state.activated_by}")
    return "\n".join(lines)
