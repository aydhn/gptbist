from bist_signal_bot.disclosures.impact import DisclosureImpactAssessor
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity
def test_impact_assessment():
    assessor = DisclosureImpactAssessor()
    rec = DisclosureRecord(disclosure_id="1", title="A", body="B", severity=DisclosureSeverity.HIGH, source="c")
    tags = [DisclosureRiskTag(tag_id="t1", disclosure_id="1", tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE, severity=DisclosureSeverity.HIGH, sentiment="NEGATIVE", score=75.0, message="a")]
    assessment = assessor.assess(rec, tags)
    assert assessment.narrative_risk_score == 100.0
