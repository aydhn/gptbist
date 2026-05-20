import pytest
from bist_signal_bot.stress.risk_of_ruin import RiskOfRuinEstimator
from bist_signal_bot.stress.models import ReturnSeries, StressInputType

def test_loss_streaks():
    returns = [0.01, -0.01, -0.02, 0.01, -0.01, -0.01, -0.01, 0.02]
    est = RiskOfRuinEstimator()
    streaks = est.loss_streaks(returns)
    assert streaks == [2, 3]
    assert est.worst_loss_streak(returns) == 3

def test_ruin_probability():
    paths = [
        [100.0, 90.0, 80.0, 70.0],
        [100.0, 95.0, 98.0, 105.0]
    ]
    est = RiskOfRuinEstimator()
    prob = est.ruin_probability_from_paths(paths, 100.0, 25.0)
    assert prob == 50.0
