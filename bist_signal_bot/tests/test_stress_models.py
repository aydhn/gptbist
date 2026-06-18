import pytest
from bist_signal_bot.stress.models import (
    ReturnSeries, StressInputType, StressTestRequest, MonteCarloConfig, MonteCarloMethod
)

def test_return_series_validation():
    rs = ReturnSeries(
        series_id="test-1",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[0.01, float('nan'), float('inf'), 0.02],
        frequency="1D"
    )
    assert len(rs.returns) == 2
    assert 0.01 in rs.returns
    assert 0.02 in rs.returns
    assert 'Cleaned 2 invalid returns (NaN/inf).' in rs.warnings

def test_monte_carlo_config_validation():
    with pytest.raises(ValueError, match="must be positive"):
        MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=0,
            horizon_days=60,
            seed=42,
            initial_value=100000.0
        )

def test_return_series_empty_returns_warning():
    rs = ReturnSeries(
        series_id="test-empty",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[],
        frequency="1D"
    )
    assert len(rs.returns) == 0
    assert "Return series is empty." in rs.warnings

def test_return_series_missing_frequency():
    with pytest.raises(ValueError, match="frequency is required"):
        ReturnSeries(
            series_id="test-empty-freq",
            source_type=StressInputType.CUSTOM_RETURNS,
            returns=[0.01, 0.02],
            frequency=""
        )
