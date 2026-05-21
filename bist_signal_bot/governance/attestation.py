import uuid
from datetime import datetime
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.governance.models import (
    AuditReviewResult,
    ComplianceAttestation,
    EvidencePackManifest,
    GovernancePolicy,
    GovernanceStatus,
)
from bist_signal_bot.governance.policy import GovernancePolicyManager

class ComplianceAttestationBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def default_statements(self, policy: GovernancePolicy, review: AuditReviewResult) -> list[str]:
        return [
            "Bot is designed to run in research-only mode.",
            "Real order submission is explicitly disabled.",
            "Broker APIs are not used.",
            "HTML scraping is not used.",
            "Paid services are not strictly required.",
            "Outputs are subject to secret redaction and unsafe claim guards.",
            "This document is an operational summary, not a legal or regulatory certification."
        ]

    def build_attestation(
        self, review: AuditReviewResult, evidence_pack: EvidencePackManifest | None = None, signed_by: str | None = None
    ) -> ComplianceAttestation:
        policy_manager = GovernancePolicyManager(self.settings)
        policy = policy_manager.load_policy()

        statements = self.default_statements(policy, review)

        status = review.status

        findings_summary = {
            "total_findings": len(review.findings),
            "blocked_count": review.blocked_count,
            "warning_count": review.warning_count,
            "pass_count": review.pass_count
        }

        return ComplianceAttestation(
            attestation_id=f"att_{uuid.uuid4().hex[:8]}",
            created_at=datetime.utcnow(),
            policy_version=policy.version,
            status=status,
            statements=statements,
            findings_summary=findings_summary,
            evidence_pack_id=evidence_pack.pack_id if evidence_pack else None,
            signed_by=signed_by
        )

    def render_markdown(self, attestation: ComplianceAttestation) -> str:
        md = f"# Compliance Attestation ({attestation.attestation_id})\n\n"
        md += f"**Date:** {attestation.created_at.isoformat()}\n"
        md += f"**Policy Version:** {attestation.policy_version}\n"
        md += f"**Status:** {attestation.status.value}\n"

        if attestation.signed_by:
            md += f"**Signed By:** {attestation.signed_by}\n"

        if attestation.evidence_pack_id:
            md += f"**Evidence Pack ID:** {attestation.evidence_pack_id}\n"

        md += "\n## Statements\n\n"
        for stmt in attestation.statements:
            md += f"- {stmt}\n"

        md += "\n## Findings Summary\n\n"
        for k, v in attestation.findings_summary.items():
            md += f"- **{k}:** {v}\n"

        md += f"\n\n*Disclaimer: {attestation.disclaimer}*\n"
        return md
