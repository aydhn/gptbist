import pytest
from bist_signal_bot.strategies.models import (
    StrategySpec,
    StrategyParameter,
    StrategyCategory,
    StrategyPositionSide,
    StrategyRequest,
    StrategyRunMode
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength

def test_signal_candidate_normalization():
    candidate = SignalCandidate(
        symbol="asels.IS  ",
        strategy_name="Test Strategy",
        direction=SignalDirection.LONG
    )
    assert candidate.symbol == "ASELS"
    assert candidate.strategy_name == "test_strategy"

def test_signal_candidate_score_validation():
    with pytest.raises(ValueError):
        SignalCandidate(
            symbol="ASELS",
            strategy_name="test",
            direction=SignalDirection.LONG,
            score=150.0
        )

    with pytest.raises(ValueError):
        SignalCandidate(
            symbol="ASELS",
            strategy_name="test",
            direction=SignalDirection.LONG,
            score=-10.0
        )

def test_signal_candidate_disclaimer():
    candidate = SignalCandidate(
        symbol="ASELS",
        strategy_name="test",
        direction=SignalDirection.LONG
    )
    assert "Not investment advice" in candidate.disclaimer

def test_strategy_spec_validation():
    with pytest.raises(ValueError):
        StrategySpec(
            name="test",
            display_name="Test",
            min_rows=0
        )

    with pytest.raises(ValueError):
        StrategySpec(
            name="test",
            display_name="Test",
            default_params={"unknown": 123}
        )

    spec = StrategySpec(
        name="Test Spec",
        display_name="Test",
        parameters=[StrategyParameter(name="p1", default=1, param_type="int")],
        default_params={"p1": 2}
    )
    assert spec.name == "test_spec"

def test_strategy_request_normalization():
    req = StrategyRequest(
        strategy_name="My Strat",
        symbol="thyAo.is "
    )
    assert req.symbol == "THYAO"
    assert req.strategy_name == "my_strat"
