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

def test_engine_run_risk_of_ruin_fail(tmp_path):
    from bist_signal_bot.stress.risk_of_ruin import RiskOfRuinResult
    from bist_signal_bot.stress.models import ReturnSeries

    estimator = MagicMock()
    # Mock estimate to return a FAIL status
    estimator.estimate.return_value = RiskOfRuinResult(
        result_id="test-id",
        status=StressStatus.FAIL,
        ruin_threshold_pct=30.0,
        estimated_ruin_probability_pct=50.0,
        warnings=["High risk of ruin!"]
    )

    engine = StressTestEngine(
        return_builder=ReturnSeriesBuilder(),
        monte_carlo_simulator=MonteCarloSimulator(),
        shock_engine=ShockScenarioEngine(),
        drawdown_simulator=DrawdownSimulator(),
        risk_of_ruin_estimator=estimator
    )

    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        include_risk_of_ruin=True,
        ruin_threshold_pct=30.0,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP,
            simulations=10,
            horizon_days=5,
            seed=42,
            initial_value=100.0
        ),
    )

    series = ReturnSeries(
        series_id="test-series",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[0.01, -0.05],
        frequency="daily"
    )

    mc_result = MagicMock()

    ror_result, status = engine._run_risk_of_ruin(req, series, mc_result)

    assert status == StressStatus.FAIL
    assert ror_result.status == StressStatus.FAIL
    estimator.estimate.assert_called_once_with(series, mc_result, 30.0)


def test_engine_save_output_success(tmp_path):
    from unittest.mock import patch, MagicMock
    from pathlib import Path

    engine = StressTestEngine(
        return_builder=ReturnSeriesBuilder(),
        monte_carlo_simulator=MonteCarloSimulator(),
        shock_engine=ShockScenarioEngine(),
        drawdown_simulator=DrawdownSimulator(),
        risk_of_ruin_estimator=RiskOfRuinEstimator()
    )

    # Mock save_result to return dummy paths
    dummy_json_path = tmp_path / "result.json"
    engine.store.save_result = MagicMock(return_value={"result_json": dummy_json_path})

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

    result_pre = StressTestResult(
        stress_id="test-id-success",
        request=req,
        status=StressStatus.PASS,
        stress_rating=StressSeverity.MEDIUM,
        warnings=[]
    )

    with patch("bist_signal_bot.stress.engine.format_stress_report_markdown", return_value="# Mock Report"):
        with patch("builtins.open", new_callable=MagicMock()) as mock_open:
            engine._save_output(req, result_pre)

            # Verify open was called to write the markdown report
            mock_open.assert_called_once_with(tmp_path / "stress_report.md", "w", encoding="utf-8")

            # Verify output_files are set
            assert result_pre.output_files["result_json"] == str(dummy_json_path)
            assert result_pre.output_files["report_md"] == str(tmp_path / "stress_report.md")
            assert len(result_pre.warnings) == 0
