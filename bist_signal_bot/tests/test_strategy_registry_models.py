import pytest
from datetime import datetime, UTC
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyFamily,
    StrategyRegistryStatus,
    StrategyScoreComponent,
    StrategyEvidenceType,
    StrategyGateDecision,
    StrategyScorecard
)

def test_strategy_definition_validation():
    # Empty name
    with pytest.raises(ValueError, match="strategy_name cannot be empty"):
        StrategyDefinition(
            strategy_id="test", strategy_name="", display_name="",
            version="1.0", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE
        )

    # Empty version
    with pytest.raises(ValueError, match="version cannot be empty"):
        StrategyDefinition(
            strategy_id="test", strategy_name="test", display_name="",
            version="", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE
        )

    # Forbidden metadata triggers BLOCKED status and warnings
    defn = StrategyDefinition(
        strategy_id="test", strategy_name="test", display_name="",
        version="1.0", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE,
        metadata={"live_trading_account": "abc"}
    )
    assert defn.status == StrategyRegistryStatus.BLOCKED
    assert any("Forbidden metadata key" in w for w in defn.warnings)

def test_strategy_score_component_validation():
    with pytest.raises(ValueError, match="weight cannot be negative"):
        StrategyScoreComponent(
            component_id="1", name="test", evidence_type=StrategyEvidenceType.BACKTEST,
            score=100, weight=-1.0, status=None, message=""
        )

    # Clamp testing
    comp = StrategyScoreComponent(
        component_id="1", name="test", evidence_type=StrategyEvidenceType.BACKTEST,
        score=150.0, weight=1.0, status=None, message=""
    )
    assert comp.score == 100.0

def test_scorecard_summary():
    scorecard = StrategyScorecard(
        scorecard_id="test_sc", strategy_id="test_st", strategy_name="test", version="1.0",
        aggregate_score=85.0, status=StrategyRegistryStatus.VALIDATED_RESEARCH,
        gate_decision=StrategyGateDecision.ALLOW
    )

    summary = scorecard.summary()
    assert summary["scorecard_id"] == "test_sc"
    assert summary["aggregate_score"] == 85.0
    assert summary["status"] == "VALIDATED_RESEARCH"
    assert summary["gate_decision"] == "ALLOW"
