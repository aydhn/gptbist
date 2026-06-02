from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.final_audit.models import (
    FinalAuditCheckResult,
    FinalAcceptanceSuite,
    FinalIntegrationMatrixItem,
    FinalIntegrationMatrix,
    FinalSecurityAuditResult,
    ReleaseCandidateManifest,
    HardeningFreezeManifest,
    GoNoGoDecision,
    FinalRiskRegisterItem,
    FinalAuditReport
)

def check_result_to_dict(result: FinalAuditCheckResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def acceptance_suite_to_dict(suite: FinalAcceptanceSuite) -> dict[str, Any]:
    return suite.model_dump(mode="json")

def integration_item_to_dict(item: FinalIntegrationMatrixItem) -> dict[str, Any]:
    return item.model_dump(mode="json")

def integration_matrix_to_dict(matrix: FinalIntegrationMatrix) -> dict[str, Any]:
    return matrix.model_dump(mode="json")

def security_audit_to_dict(result: FinalSecurityAuditResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def release_candidate_to_dict(candidate: ReleaseCandidateManifest) -> dict[str, Any]:
    return candidate.model_dump(mode="json")

def freeze_manifest_to_dict(freeze: HardeningFreezeManifest) -> dict[str, Any]:
    return freeze.model_dump(mode="json")

def go_no_go_to_dict(decision: GoNoGoDecision) -> dict[str, Any]:
    return decision.model_dump(mode="json")

def risk_item_to_dict(item: FinalRiskRegisterItem) -> dict[str, Any]:
    return item.model_dump(mode="json")

def final_audit_report_to_dict(report: FinalAuditReport) -> dict[str, Any]:
    return report.model_dump(mode="json")

def format_acceptance_suite_text(suite: FinalAcceptanceSuite) -> str:
    lines = [
        f"Final Acceptance Suite: {suite.suite_id}",
        f"Status: {suite.status}",
        f"Total: {suite.total_count} | Pass: {suite.pass_count} | Fail: {suite.fail_count} | Blocked: {suite.blocked_count} | Watch: {suite.watch_count}",
        "",
        "Disclaimer:",
        suite.disclaimer
    ]
    return "\n".join(lines)

def format_integration_matrix_text(matrix: FinalIntegrationMatrix) -> str:
    lines = [
        f"Final Integration Matrix: {matrix.matrix_id}",
        f"Status: {matrix.status}",
        f"Total Pairs: {matrix.total_count} | Failing Required: {matrix.failing_required_count} | Blocked: {matrix.blocked_count}",
        "",
        "Disclaimer:",
        matrix.disclaimer
    ]
    return "\n".join(lines)

def format_security_audit_text(result: FinalSecurityAuditResult) -> str:
    lines = [
        f"Final Security Audit: {result.audit_id}",
        f"Safe Language: {result.safe_language_status}",
        f"No Real Order: {result.no_real_order_status}",
        f"No Broker Usage: {result.no_broker_status}",
        f"No External Calls: {result.no_external_calls_status}",
        f"Path Safety: {result.path_safety_status}",
        f"Secret Redaction: {result.secret_redaction_status}",
        "",
        "Disclaimer:",
        result.disclaimer
    ]
    if result.blocked_findings:
        lines.append(f"\nBlocked Findings:\n- " + "\n- ".join(result.blocked_findings))
    return "\n".join(lines)

def format_release_candidate_text(candidate: ReleaseCandidateManifest) -> str:
    lines = [
        f"Release Candidate: {candidate.candidate_id}",
        f"Stage: {candidate.stage}",
        f"Modules Included: {len(candidate.included_modules)}",
        "",
        "Known Limitations:",
        "- " + "\n- ".join(candidate.known_limitations),
        "",
        "Disclaimer:",
        candidate.disclaimer
    ]
    return "\n".join(lines)

def format_freeze_manifest_text(freeze: HardeningFreezeManifest) -> str:
    lines = [
        f"Hardening Freeze: {freeze.freeze_id}",
        f"Candidate ID: {freeze.candidate_id}",
        f"Frozen: {freeze.frozen}",
        "",
        "Disclaimer:",
        freeze.disclaimer
    ]
    return "\n".join(lines)

def format_go_no_go_text(decision: GoNoGoDecision) -> str:
    lines = [
        f"Go/No-Go Decision: {decision.decision_id}",
        f"Decision: {decision.decision} (Status: {decision.status})",
        f"Security Passed: {decision.security_passed}",
        f"Acceptance Passed: {decision.acceptance_passed}",
        f"Required Checks Passed: {decision.required_checks_passed}",
        "",
    ]
    if decision.blocking_reasons:
        lines.append("Blocking Reasons:\n- " + "\n- ".join(decision.blocking_reasons) + "\n")
    if decision.warning_reasons:
        lines.append("Warnings:\n- " + "\n- ".join(decision.warning_reasons) + "\n")

    lines.append("Disclaimer:")
    lines.append(decision.disclaimer)
    return "\n".join(lines)

def format_risk_register_text(items: list[FinalRiskRegisterItem]) -> str:
    lines = ["Final Risk Register:"]
    for i in items:
        lines.append(f"[{i.severity}] {i.title}: {i.description} (Accepted: {i.accepted})")
    return "\n".join(lines)

def format_final_audit_report_markdown(report: FinalAuditReport) -> str:
    lines = [
        "# Final Pre-Release Audit Report",
        f"**Generated At:** {report.generated_at.isoformat()}",
        "",
        "## Go/No-Go Decision"
    ]

    if report.go_no_go:
        lines.append(f"**Decision:** {report.go_no_go.decision}")
        if report.go_no_go.blocking_reasons:
            lines.append("### Blocking Reasons")
            for r in report.go_no_go.blocking_reasons:
                lines.append(f"- {r}")
        if report.go_no_go.warning_reasons:
            lines.append("### Warnings")
            for w in report.go_no_go.warning_reasons:
                lines.append(f"- {w}")
    else:
        lines.append("*Decision not available.*")

    lines.append("\n## Security Audit")
    if report.security_audit:
        lines.append(format_security_audit_text(report.security_audit))
    else:
        lines.append("*Security audit not available.*")

    lines.append("\n## Release Candidate")
    if report.release_candidate:
        lines.append(format_release_candidate_text(report.release_candidate))
    else:
        lines.append("*Candidate manifest not available.*")

    lines.append("\n## Risk Register")
    if report.risk_register:
        lines.append(format_risk_register_text(report.risk_register))
    else:
        lines.append("*Risk register not available.*")

    lines.extend([
        "",
        "## Disclaimer",
        report.disclaimer
    ])

    return "\n".join(lines)

def render_final_audit_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_audit",
        "section_key": "final_audit",
        "title": "Final Audit Report",
        "content_markdown": "*Final Audit summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
