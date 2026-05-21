from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import AuditReviewResult, AuditReviewRequest, GovernanceStatus
from bist_signal_bot.governance.attestation import ComplianceAttestationBuilder
import uuid
from datetime import datetime

def test_attestation_builder():
    builder = ComplianceAttestationBuilder(Settings())

    review = AuditReviewResult(
        review_id="rev_1",
        request=AuditReviewRequest(),
        status=GovernanceStatus.PASS,
        generated_at=datetime.utcnow()
    )

    attestation = builder.build_attestation(review, signed_by="Test Runner")
    assert attestation.status == GovernanceStatus.PASS
    assert attestation.signed_by == "Test Runner"
    assert len(attestation.statements) > 0
    assert "Bot is designed to run in research-only mode." in attestation.statements

    md = builder.render_markdown(attestation)
    assert "# Compliance Attestation" in md
    assert "**Signed By:** Test Runner" in md
