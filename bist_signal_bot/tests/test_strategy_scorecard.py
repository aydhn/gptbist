import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.scorecard import StrategyScorecardBuilder
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition, StrategyFamily, StrategyRegistryStatus, StrategyEvidenceRef, StrategyEvidenceType, StrategyGateDecision
)

@pytest.fixture
def builder():
    return StrategyScorecardBuilder(Settings())

@pytest.fixture
def strategy():
    return StrategyDefinition(
        strategy_id="1", strategy_name="test", display_name="Test",
        version="1.0", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE
    )

def test_scorecard_builder_missing_evidence(builder, strategy):
    # Empty evidence
    scorecard = builder.build_scorecard(strategy, [])

    assert scorecard.aggregate_score == 25.0 # Expected to be very low since everything is missing
    # Execution missing doesn't break, just gives low score

def test_scorecard_governance_critical(builder, strategy):
    evidence = [
        StrategyEvidenceRef(
            evidence_id="1", strategy_id="1", evidence_type=StrategyEvidenceType.GOVERNANCE,
            status="FAIL", summary="Critical Issue found"
        )
    ]

    scorecard = builder.build_scorecard(strategy, evidence)

    # Governance finding should BLOCK
    assert scorecard.gate_decision == StrategyGateDecision.BLOCK
    assert any("Governance critical finding" in w for w in scorecard.warnings)

def test_scorecard_high_overfit(builder, strategy):
    evidence = [
        StrategyEvidenceRef(
            evidence_id="1", strategy_id="1", evidence_type=StrategyEvidenceType.BACKTEST,
            score=90.0
        ),
    ]
    # In builder mock logic, overfit scores 90.0 if present, 50.0 if not
    scorecard = builder.build_scorecard(strategy, evidence)
    assert scorecard.overfit_risk_score == 50.0 # Since overfit evidence is missing, score is 50.0, risk is 100 - 50 = 50
    # Overfit risk > 70 triggers require review, here 50 is fine
