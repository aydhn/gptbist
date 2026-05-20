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
