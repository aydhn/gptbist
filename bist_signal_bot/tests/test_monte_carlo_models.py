import pytest
from bist_signal_bot.monte_carlo.models import (
    MonteCarloRequest, MonteCarloTarget, ResamplingMethod, CostRandomizationConfig
)
from bist_signal_bot.core.exceptions import MonteCarloValidationError

def test_monte_carlo_request_validation():
    with pytest.raises(MonteCarloValidationError, match="Simulations must be positive"):
        MonteCarloRequest("id1", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_BOOTSTRAP, 0, 42, 1000.0, 30.0)

    with pytest.raises(MonteCarloValidationError, match="Initial equity must be positive"):
        MonteCarloRequest("id1", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_BOOTSTRAP, 10, 42, 0.0, 30.0)

    with pytest.raises(MonteCarloValidationError, match="Ruin threshold must be between 0 and 100"):
        MonteCarloRequest("id1", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_BOOTSTRAP, 10, 42, 1000.0, 150.0)

    req = MonteCarloRequest("id1", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_BOOTSTRAP, 10, 42, 1000.0, 30.0, symbol="asels")
    assert req.symbol == "ASELS"

def test_cost_randomization_config_validation():
    with pytest.raises(MonteCarloValidationError, match="Multipliers cannot be negative"):
        CostRandomizationConfig("c1", -0.5, 1.0, 0.5, 1.0, 0.5, 1.0, 0.5, 1.0, 42)

    with pytest.raises(MonteCarloValidationError, match="Commission min > max"):
        CostRandomizationConfig("c1", 1.5, 1.0, 0.5, 1.0, 0.5, 1.0, 0.5, 1.0, 42)
