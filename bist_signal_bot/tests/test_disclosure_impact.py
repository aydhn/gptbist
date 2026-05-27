import pytest
from bist_signal_bot.disclosures.impact import DisclosureImpactAssessor
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity, DisclosureSentiment, DisclosureType
from datetime import datetime

def test_disclosure_impact_assessor_narrative_risk_score():
    assessor = DisclosureImpactAssessor()
    record = DisclosureRecord(disclosure_id="1", title="Test", body="Test", disclosure_type=DisclosureType.MATERIAL_EVENT, received_at=datetime.now(), source="test", language="tr")
    tag = DisclosureRiskTag(tag_id="1", disclosure_id="1", tag_type=DisclosureRiskTagType.LEGAL_REGULATORY, severity=DisclosureSeverity.HIGH, sentiment=DisclosureSentiment.NEGATIVE, message="Test", score=80.0)
    assessment = assessor.assess(record, risk_tags=[tag])
    assert assessment.narrative_risk_score is not None
    assert assessment.narrative_risk_score > 0
