from bist_signal_bot.explainability.governance import ExplanationGovernanceEngine
from bist_signal_bot.explainability.models import ExplanationObjectType, ExplanationMethod, FeatureAttribution, AttributionDirection

def test_governance_unsafe_language():
    engine = ExplanationGovernanceEngine()
    text = "This is a guaranteed return."
    findings = engine.unsafe_language_findings(text)
    assert len(findings) > 0
    assert "guarantee" in findings[0].lower()

def test_governance_coverage_score():
    engine = ExplanationGovernanceEngine()
    fnames = ["f1", "f2"]
    attrs = [FeatureAttribution(
        attribution_id="1", object_type=ExplanationObjectType.MODEL, object_id="1",
        feature_name="f1", method=ExplanationMethod.FEATURE_ATTRIBUTION, direction=AttributionDirection.POSITIVE
    )]
    score = engine.feature_coverage_score(fnames, attrs)
    assert score == 50.0

def test_governance_status():
    engine = ExplanationGovernanceEngine()
    status = engine.status_from_parts(True, 40.0, [])
    assert status.value == "WATCH"
    status2 = engine.status_from_parts(True, 80.0, ["unsafe"])
    assert status2.value == "BLOCKED"
