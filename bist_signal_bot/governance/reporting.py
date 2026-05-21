from typing import Any

from bist_signal_bot.governance.models import (
    AuditReviewResult,
    ComplianceAttestation,
    EvidencePackManifest,
    GovernanceFinding,
    GovernanceGateResult,
    GovernancePolicy,
)

def governance_policy_to_dict(policy: GovernancePolicy) -> dict[str, Any]:
    return policy.model_dump(mode="json")

def governance_finding_to_dict(finding: GovernanceFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def audit_review_to_dict(result: AuditReviewResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def gate_result_to_dict(result: GovernanceGateResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def evidence_manifest_to_dict(manifest: EvidencePackManifest) -> dict[str, Any]:
    return manifest.model_dump(mode="json")

def attestation_to_dict(attestation: ComplianceAttestation) -> dict[str, Any]:
    return attestation.model_dump(mode="json")

def findings_to_dataframe(findings: list[GovernanceFinding]) -> Any:
    try:
        import pandas as pd
        return pd.DataFrame([f.model_dump(mode="json") for f in findings])
    except ImportError:
        return None

def format_audit_review_text(result: AuditReviewResult) -> str:
    lines = [
        "========================================",
        "BIST Signal Bot - Governance Audit Review",
        "========================================",
        f"Review ID  : {result.review_id}",
        f"Date       : {result.generated_at.isoformat()}",
        f"Status     : {result.status.value}",
        f"Findings   : {len(result.findings)}",
        f"Blocked    : {result.blocked_count}",
        f"Warnings   : {result.warning_count}",
        f"Passed     : {result.pass_count}",
        "----------------------------------------",
        "Findings Summary:"
    ]
    for f in result.findings:
        lines.append(f" - [{f.severity.value}] {f.title}: {f.decision.value}")
        if f.message:
            lines.append(f"   > {f.message}")

    lines.append("----------------------------------------")
    lines.append(result.disclaimer)
    lines.append("========================================")
    return "\n".join(lines)

def format_gate_result_text(result: GovernanceGateResult) -> str:
    lines = [
        "--- Governance Gate Result ---",
        f"Gate Name: {result.request.gate_name}",
        f"Status   : {result.status.value}",
        f"Decision : {result.decision.value}",
    ]
    if result.warnings:
        lines.append("Warnings :")
        for w in result.warnings:
            lines.append(f" - {w}")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_evidence_pack_text(manifest: EvidencePackManifest) -> str:
    lines = [
        "--- Evidence Pack Manifest ---",
        f"Pack Name: {manifest.pack_name}",
        f"Checksum : {manifest.checksum_sha256 or 'N/A'}",
        f"Files    : {len(manifest.files)}",
        f"Excluded : {len(manifest.excluded_files)}",
    ]
    if manifest.warnings:
        for w in manifest.warnings:
            lines.append(f"Warning  : {w}")
    lines.append(manifest.disclaimer)
    return "\n".join(lines)

def format_attestation_markdown(attestation: ComplianceAttestation) -> str:
    from bist_signal_bot.governance.attestation import ComplianceAttestationBuilder
    builder = ComplianceAttestationBuilder()
    return builder.render_markdown(attestation)

def format_governance_report_markdown(result: AuditReviewResult) -> str:
    return format_audit_review_text(result)
