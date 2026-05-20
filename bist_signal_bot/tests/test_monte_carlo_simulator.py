import pytest
from bist_signal_bot.stress.monte_carlo import MonteCarloSimulator
from bist_signal_bot.stress.models import ReturnSeries, StressInputType, MonteCarloConfig, MonteCarloMethod

@pytest.fixture
def sample_series():
    return ReturnSeries(
        series_id="test",
        source_type=StressInputType.CUSTOM_RETURNS,
        returns=[0.01, -0.02, 0.03, -0.01, 0.01, 0.02, -0.01, 0.00] * 5,
        frequency="1D"
    )

def test_monte_carlo_bootstrap(sample_series):
    config = MonteCarloConfig(
        method=MonteCarloMethod.BOOTSTRAP,
        simulations=10,
        horizon_days=20,
        seed=42,
        initial_value=100000.0
    )
    sim = MonteCarloSimulator()
    res = sim.run(sample_series, config)
    assert len(res.final_values) == 10
    assert res.final_return_pct_p50 is not None

def test_monte_carlo_deterministic(sample_series):
    config = MonteCarloConfig(
        method=MonteCarloMethod.BOOTSTRAP,
        simulations=5,
        horizon_days=10,
        seed=123,
        initial_value=100.0
    )
    sim = MonteCarloSimulator()
    res1 = sim.run(sample_series, config)
    res2 = sim.run(sample_series, config)
    assert res1.final_values == res2.final_values

def test_block_bootstrap(sample_series):
    config = MonteCarloConfig(
        method=MonteCarloMethod.BLOCK_BOOTSTRAP,
        simulations=5,
        horizon_days=10,
        seed=123,
        block_size=3,
        initial_value=100.0
    )
    sim = MonteCarloSimulator()
    res = sim.run(sample_series, config)
    assert len(res.final_values) == 5

def test_normal_parametric(sample_series):
    config = MonteCarloConfig(
        method=MonteCarloMethod.NORMAL_PARAMETRIC,
        simulations=5,
        horizon_days=10,
        seed=123,
        initial_value=100.0
    )
    sim = MonteCarloSimulator()
    res = sim.run(sample_series, config)
    assert len(res.final_values) == 5
