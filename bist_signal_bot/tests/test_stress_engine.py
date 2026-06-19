import pytest
from bist_signal_bot.stress.engine import StressTestEngine
from bist_signal_bot.stress.models import StressTestRequest, StressInputType, MonteCarloConfig, MonteCarloMethod
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


from unittest.mock import patch, MagicMock

def test_engine_prepare_input_error():
    from bist_signal_bot.stress.models import StressStatus
    engine = StressTestEngine(
        return_builder=MagicMock(),
        monte_carlo_simulator=MagicMock(),
        shock_engine=MagicMock(),
        drawdown_simulator=MagicMock(),
        risk_of_ruin_estimator=MagicMock()
    )
    with patch.object(engine, '_prepare_inputs', side_effect=Exception("Test mock error")):
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
        assert res.status == StressStatus.ERROR
        assert "Failed to prepare input: Test mock error" in res.warnings

def test_engine_save_output_error():
    engine = StressTestEngine(
        return_builder=MagicMock(),
        monte_carlo_simulator=MagicMock(),
        shock_engine=MagicMock(),
        drawdown_simulator=MagicMock(),
        risk_of_ruin_estimator=MagicMock()
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
        save_output=True,
        metadata={"custom_returns": [0.01, -0.02, 0.01, 0.03]}
    )

    with patch.object(engine, '_prepare_inputs', return_value=(MagicMock(returns=[0.01]), MagicMock())):
        from bist_signal_bot.stress.models import StressStatus
        with patch.object(engine, '_run_monte_carlo', return_value=(None, StressStatus.PASS)):
            with patch.object(engine, '_run_drawdown', return_value=None):
                with patch.object(engine, '_run_risk_of_ruin', return_value=(None, StressStatus.PASS)):
                    with patch.object(engine, '_run_shocks', return_value=([], StressStatus.PASS)):
                        with patch.object(engine.store, 'save_result', side_effect=Exception("Test save error")):
                            res = engine.run(req)
                            assert "Failed to save output: Test save error" in res.warnings
