import pytest
from datetime import datetime
from bist_signal_bot.explainability.models import (
    FeatureContribution,
    ContributionDirection,
    ContributionStrength,
    SignalExplanation,
    ExplanationStatus,
    EvidenceCard,
    DecisionTrace
)

def test_feature_contribution_clamp():
    fc = FeatureContribution(
        contribution_id="test",
        feature_name="test_feature",
        contribution_score=150.0,
        contribution_direction=ContributionDirection.SUPPORTS,
        strength=ContributionStrength.STRONG,
        message="test"
    )
    assert fc.contribution_score == 100.0

    fc2 = FeatureContribution(
        contribution_id="test",
        feature_name="test_feature",
        contribution_score=-200.0,
        contribution_direction=ContributionDirection.OPPOSES,
        strength=ContributionStrength.STRONG,
        message="test"
    )
    assert fc2.contribution_score == -100.0

def test_signal_explanation_summary():
    se = SignalExplanation(
        explanation_id="exp-1",
        signal_id="sig-1",
        symbol="ASELS",
        strategy_name="trend",
        generated_at=datetime(2025, 1, 1),
        summary="Test summary",
        final_status=ExplanationStatus.PASS
    )
    res = se.summary_dict()
    assert res["explanation_id"] == "exp-1"
    assert res["symbol"] == "ASELS"
    assert res["final_status"] == "PASS"

def test_evidence_card_creation():
    card = EvidenceCard(
        card_id="card-1",
        symbol="ASELS",
        created_at=datetime.utcnow(),
        title="Test Card",
        summary="Test",
        overall_status=ExplanationStatus.PASS
    )
    assert card.overall_status == ExplanationStatus.PASS

def test_decision_trace_creation():
    trace = DecisionTrace(
        trace_id="trace-1",
        symbol="ASELS",
        created_at=datetime.utcnow(),
        final_decision="PROCEED",
        stages=[{"name": "test", "status": "PASS"}]
    )
    assert trace.final_decision == "PROCEED"
    assert len(trace.stages) == 1
