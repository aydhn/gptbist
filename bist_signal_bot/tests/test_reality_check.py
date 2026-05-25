from bist_signal_bot.monte_carlo.reality_check import RealityCheckEngine
from bist_signal_bot.monte_carlo.models import RealityCheckStatus

def test_reality_check_engine():
    engine = RealityCheckEngine()

    observed = 10.0
    simulated = [1.0, 2.0, 3.0, 4.0, 5.0]

    res = engine.run(observed, simulated)
    assert res.status == RealityCheckStatus.ROBUST
    assert res.simulated_p_value == 0.0
    assert res.multiple_testing_warning is False

def test_reality_check_overfit():
    engine = RealityCheckEngine()

    observed = 2.0
    simulated = [1.0, 2.0, 3.0, 4.0, 5.0]

    res = engine.run(observed, simulated)
    assert res.status == RealityCheckStatus.LIKELY_OVERFIT
    assert res.simulated_p_value == 0.8
