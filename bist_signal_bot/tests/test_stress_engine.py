import pytest
from unittest.mock import MagicMock
from bist_signal_bot.stress.engine import StressTestEngine
from bist_signal_bot.stress.models import (
    StressTestRequest, StressInputType, MonteCarloConfig, MonteCarloMethod,
    StressTestResult, StressStatus, StressSeverity
)
from bist_signal_bot.stress.returns import ReturnSeriesBuilder
from bist_signal_bot.stress.monte_carlo import MonteCarloSimulator
from bist_signal_bot.stress.shocks import ShockScenarioEngine
from bist_signal_bot.stress.drawdown import DrawdownSimulator
from bist_signal_bot.stress.risk_of_ruin import RiskOfRuinEstimator

def test_engine_custom_returns(tmp_path):
    engine = StressTestEngine(
        return_builder=ReturnSeriesBuilder(),
        monte_carlo_simulator=MonteCarloSimulator(),
        shock_engine=ShockScenarioEngine(),
        drawdown_simulator=DrawdownSimulator(),
        risk_of_ruin_estimator=RiskOfRuinEstimator()
    )
    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=5,
            seed=42,
            initial_value=100.0
        ),
        ruin_threshold_pct=30.0,
        save_output=False,
        metadata={"custom_returns": [0.01, -0.02, 0.01, 0.03]}
    )
    res = engine.run(req)
    assert res.status.value in ["PASS", "WARN", "FAIL"]
    assert res.monte_carlo_result is not None
    assert res.drawdown_result is not None

def test_engine_save_output_error(tmp_path):
    engine = StressTestEngine(
        return_builder=ReturnSeriesBuilder(),
        monte_carlo_simulator=MonteCarloSimulator(),
        shock_engine=ShockScenarioEngine(),
        drawdown_simulator=DrawdownSimulator(),
        risk_of_ruin_estimator=RiskOfRuinEstimator()
    )

    # Mock the store's save_result method to raise an exception
    engine.store.save_result = MagicMock(side_effect=Exception("Mocked storage error"))

    # Create request that requires saving
    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=5,
            seed=42,
            initial_value=100.0
        ),
        ruin_threshold_pct=30.0,
        save_output=True,
        metadata={"custom_returns": [0.01]}
    )

    # Create result object to be modified by _save_output
    result_pre = StressTestResult(
        stress_id="test-id",
        request=req,
        status=StressStatus.PASS,
        stress_rating=StressSeverity.MEDIUM,
        warnings=[]
    )

    # Call the method
    engine._save_output(req, result_pre)

    # Assert exception was caught and warning appended
    assert len(result_pre.warnings) == 1
    assert "Mocked storage error" in result_pre.warnings[0]

def test_engine_prepare_inputs_exception():
    engine = StressTestEngine(
        return_builder=ReturnSeriesBuilder(),
        monte_carlo_simulator=MonteCarloSimulator(),
        shock_engine=ShockScenarioEngine(),
        drawdown_simulator=DrawdownSimulator(),
        risk_of_ruin_estimator=RiskOfRuinEstimator()
    )

    # Mock _prepare_inputs to raise Exception
    engine._prepare_inputs = MagicMock(side_effect=Exception("Mocked input preparation error"))

    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=5,
            seed=42,
            initial_value=100.0
        ),
        ruin_threshold_pct=30.0,
        save_output=False,
        metadata={"custom_returns": []}
    )

    res = engine.run(req)

    assert res.status == StressStatus.ERROR
    assert res.stress_rating == StressSeverity.EXTREME
    assert len(res.warnings) == 1
    assert "Failed to prepare input: Mocked input preparation error" in res.warnings[0]

def test_engine_empty_returns():
    engine = StressTestEngine(
        return_builder=ReturnSeriesBuilder(),
        monte_carlo_simulator=MonteCarloSimulator(),
        shock_engine=ShockScenarioEngine(),
        drawdown_simulator=DrawdownSimulator(),
        risk_of_ruin_estimator=RiskOfRuinEstimator()
    )

    # Mock _prepare_inputs to return series with no returns
    mock_series = MagicMock()
    mock_series.returns = []
    engine._prepare_inputs = MagicMock(return_value=(mock_series, None))

    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=5,
            seed=42,
            initial_value=100.0
        ),
        ruin_threshold_pct=30.0,
        save_output=False,
        metadata={"custom_returns": []}
    )

    res = engine.run(req)

    assert res.status == StressStatus.ERROR
    assert res.stress_rating == StressSeverity.EXTREME
    assert len(res.warnings) == 1
    assert "No returns available for stress test." in res.warnings[0]
