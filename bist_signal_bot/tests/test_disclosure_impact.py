import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureSeverity, DisclosureSentiment, DisclosureType, DisclosureRiskTag, DisclosureRiskTagType
from bist_signal_bot.disclosures.impact import DisclosureImpactAssessor

def test_impact_narrative_risk_score():
    assessor = DisclosureImpactAssessor()

    # Critical and Negative
    record = DisclosureRecord(
        disclosure_id="123", title="İflas", body="İflas",
        severity=DisclosureSeverity.CRITICAL, sentiment=DisclosureSentiment.NEGATIVE,
        disclosure_type=DisclosureType.MATERIAL_EVENT
    )

    assessment = assessor.assess(record, [])
    assert assessment.narrative_risk_score == 100.0  # 80 + 20
    assert assessment.recommended_decision == "REQUIRE_REVIEW"

def test_impact_confidence_adjustment():
    assessor = DisclosureImpactAssessor()

    record = DisclosureRecord(
        disclosure_id="123", title="Test", body="Test",
        severity=DisclosureSeverity.HIGH, sentiment=DisclosureSentiment.NEGATIVE
    )

    # Score should be 50 + 20 = 70
    assessment = assessor.assess(record, [])
    assert assessment.narrative_risk_score == 70.0
    assert assessment.confidence_adjustment == -10.0 # Score > 60
