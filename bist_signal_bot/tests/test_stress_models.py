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

def test_return_series_valid_returns():
    rs = ReturnSeries(
        series_id="test-valid",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[0.01, -0.05, 0.0, 0.1],
        frequency="1D"
    )
    assert len(rs.returns) == 4
    assert len(rs.warnings) == 0

def test_return_series_negative_inf():
    rs = ReturnSeries(
        series_id="test-neg-inf",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[0.01, float('-inf'), 0.02],
        frequency="1D"
    )
    assert len(rs.returns) == 2
    assert 0.01 in rs.returns
    assert 0.02 in rs.returns
    assert 'Cleaned 1 invalid returns (NaN/inf).' in rs.warnings

def test_return_series_cleaned_to_empty():
    rs = ReturnSeries(
        series_id="test-cleaned-empty",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[float('nan'), float('inf')],
        frequency="1D"
    )
    assert len(rs.returns) == 0
    # Initial validation does not flag empty since initial list was not empty
    assert 'Cleaned 2 invalid returns (NaN/inf).' in rs.warnings
    assert 'Return series is empty.' not in rs.warnings

from bist_signal_bot.stress.models import (
    StressTestResult, StressStatus, StressSeverity,
    MonteCarloResult, RiskOfRuinResult, DrawdownSimulationResult
)

def test_stress_test_result_summary_and_safe_dict():
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
        symbols=["AAPL"]
    )

    mc_res = MonteCarloResult(
        result_id="mc-1",
        config=mc_config,
        status=StressStatus.PASS,
        final_return_pct_p05=-10.5
    )

    ror_res = RiskOfRuinResult(
        result_id="ror-1",
        status=StressStatus.PASS,
        ruin_threshold_pct=50.0,
        estimated_ruin_probability_pct=2.5
    )

    dd_res = DrawdownSimulationResult(
        result_id="dd-1",
        status=StressStatus.PASS,
        max_drawdown_pct=-15.0
    )

    res = StressTestResult(
        stress_id="stress-1",
        request=req,
        status=StressStatus.PASS,
        stress_score=85.5,
        stress_rating=StressSeverity.LOW,
        monte_carlo_result=mc_res,
        risk_of_ruin_result=ror_res,
        drawdown_result=dd_res,
        warnings=["Test warning"]
    )

    summary = res.summary()
    assert summary["stress_id"] == "stress-1"
    assert summary["status"] == "PASS"
    assert summary["stress_score"] == 85.5
    assert summary["stress_rating"] == "LOW"
    assert summary["warnings_count"] == 1
    assert summary["mc_p05_return_pct"] == -10.5
    assert summary["ruin_prob_pct"] == 2.5
    assert summary["max_drawdown_pct"] == -15.0
    assert summary["shock_count"] == 0

    safe_dict = res.safe_public_dict()
    assert safe_dict["stress_id"] == "stress-1"
    assert safe_dict["status"] == "PASS"
    assert safe_dict["stress_rating"] == "LOW"
    assert "disclaimer" in safe_dict
    assert safe_dict["summary"] == summary
