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

def test_monte_carlo_config_validation_simulations():
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

def test_stress_test_request_valid_symbols():
    mc_config = MonteCarloConfig(
        method=MonteCarloMethod.BOOTSTRAP,
        simulations=10,
        horizon_days=30,
        seed=42,
        initial_value=10000.0
    )
    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=mc_config,
        ruin_threshold_pct=50.0,
        symbols=[" aapl ", "msft", " ", ""]
    )
    assert req.symbols == ["AAPL", "MSFT"]

def test_stress_test_request_invalid_source():
    mc_config = MonteCarloConfig(
        method=MonteCarloMethod.BOOTSTRAP,
        simulations=10,
        horizon_days=30,
        seed=42,
        initial_value=10000.0
    )
    with pytest.raises(ValueError, match="Source must be one of"):
        StressTestRequest(
            input_type=StressInputType.CUSTOM_RETURNS,
            monte_carlo_config=mc_config,
            ruin_threshold_pct=50.0,
            source="invalid_source"
        )

def test_stress_test_request_invalid_ruin_threshold():
    mc_config = MonteCarloConfig(
        method=MonteCarloMethod.BOOTSTRAP,
        simulations=10,
        horizon_days=30,
        seed=42,
        initial_value=10000.0
    )
    with pytest.raises(ValueError, match="ruin_threshold_pct must be between 0 and 100"):
        StressTestRequest(
            input_type=StressInputType.CUSTOM_RETURNS,
            monte_carlo_config=mc_config,
            ruin_threshold_pct=-1.0
        )
    with pytest.raises(ValueError, match="ruin_threshold_pct must be between 0 and 100"):
        StressTestRequest(
            input_type=StressInputType.CUSTOM_RETURNS,
            monte_carlo_config=mc_config,
            ruin_threshold_pct=101.0
        )

def test_monte_carlo_config_validation_horizon_days():
    with pytest.raises(ValueError, match="horizon_days must be positive"):
        MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=0,
            seed=42,
            initial_value=100000.0
        )

def test_monte_carlo_config_validation_initial_value():
    with pytest.raises(ValueError, match="initial_value must be positive"):
        MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=30,
            seed=42,
            initial_value=-100.0
        )

def test_monte_carlo_config_validation_block_size():
    with pytest.raises(ValueError, match="block_size must be positive if provided"):
        MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=30,
            seed=42,
            initial_value=100000.0,
            block_size=0
        )
