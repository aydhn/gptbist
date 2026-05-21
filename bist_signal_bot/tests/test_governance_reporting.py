from bist_signal_bot.governance.models import AuditReviewResult, AuditReviewRequest, GovernanceStatus
from bist_signal_bot.governance.reporting import format_audit_review_text
from datetime import datetime

def test_format_audit_review_text():
    review = AuditReviewResult(
        review_id="rev_1234",
        request=AuditReviewRequest(),
        status=GovernanceStatus.PASS,
        generated_at=datetime.utcnow()
    )

    text = format_audit_review_text(review)
    assert "BIST Signal Bot - Governance Audit Review" in text
    assert "Review ID  : rev_1234" in text
    assert "Status     : PASS" in text
    assert "Audit review is operational governance output only." in text
