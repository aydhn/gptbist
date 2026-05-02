import pytest
from bist_signal_bot.divergence.models import DivergenceRequest

def test_divergence_request_validation():
    # Valid
    req = DivergenceRequest(indicators=["rsi"])
    assert req.indicators == ["rsi"]
    assert req.lookback == 5

    # Empty indicators
    with pytest.raises(ValueError, match="indicators list cannot be empty"):
        DivergenceRequest(indicators=[])

    # max <= min distance
    with pytest.raises(ValueError, match="strictly greater"):
        DivergenceRequest(indicators=["rsi"], min_pivot_distance=10, max_pivot_distance=5)

    # min strength bounds
    with pytest.raises(ValueError):
        DivergenceRequest(indicators=["rsi"], min_strength_score=150)

    # Negative confirmation bars
    with pytest.raises(ValueError):
        DivergenceRequest(indicators=["rsi"], confirmation_bars=-1)

def test_divergence_request_include_flags():
    req = DivergenceRequest(indicators=["rsi"], include_hidden=False, include_regular=False)
    assert not req.include_hidden
    assert not req.include_regular
