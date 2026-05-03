import pytest
import pandas as pd
from typing import Any
from bist_signal_bot.core.exceptions import StrategyValidationError
from bist_signal_bot.strategies.base_strategy import BaseStrategy
from bist_signal_bot.strategies.models import StrategySpec, StrategyParameter
from bist_signal_bot.strategies.context import StrategyContext
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

class TestStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(
            name="test_strat",
            display_name="Test",
            required_columns=["close"],
            min_rows=5,
            parameters=[
                StrategyParameter(name="p1", default=10, param_type="int", min_value=1, max_value=20),
                StrategyParameter(name="p2", default="A", param_type="str", choices=["A", "B"])
            ],
            default_params={"p1": 10, "p2": "A"}
        )

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        return self.build_signal_candidate(context, SignalDirection.LONG)

def test_base_strategy_validate_params():
    strat = TestStrategy()

    # Valid merge
    params = strat.validate_params({"p1": 15})
    assert params["p1"] == 15
    assert params["p2"] == "A"

    # Unknown param
    with pytest.raises(StrategyValidationError):
        strat.validate_params({"unknown": 1})

    # Min value
    with pytest.raises(StrategyValidationError):
        strat.validate_params({"p1": 0})

    # Max value
    with pytest.raises(StrategyValidationError):
        strat.validate_params({"p1": 25})

    # Choices
    with pytest.raises(StrategyValidationError):
        strat.validate_params({"p2": "C"})

def test_base_strategy_validate_context():
    strat = TestStrategy()

    df = pd.DataFrame({"close": [1, 2, 3, 4, 5, 6]})
    ctx = StrategyContext(symbol="TEST", data=df)

    # Valid
    strat.validate_context(ctx, {"allow_short": False})

    # Min rows
    ctx_short = StrategyContext(symbol="TEST", data=pd.DataFrame({"close": [1, 2, 3]}))
    with pytest.raises(StrategyValidationError, match="requires at least 5 rows"):
        strat.validate_context(ctx_short, {})

    # Required columns (context init checks for missing if require_columns called)
    ctx_missing = StrategyContext(symbol="TEST", data=pd.DataFrame({"open": [1, 2, 3, 4, 5]}))
    with pytest.raises(StrategyValidationError, match="Missing required columns"):
        strat.validate_context(ctx_missing, {})

    # Short support
    with pytest.raises(StrategyValidationError, match="does not support short"):
        strat.validate_context(ctx, {"allow_short": True})
