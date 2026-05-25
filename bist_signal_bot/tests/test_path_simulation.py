from bist_signal_bot.monte_carlo.path_simulation import PathSimulator

def test_equity_curve_from_returns():
    sim = PathSimulator()
    returns = [10.0, -5.0, 5.0]
    curve = sim.equity_curve_from_returns(returns, 100.0)
    assert len(curve) == 4
    assert curve[0] == 100.0
    assert abs(curve[-1] - 109.725) < 1e-5

def test_max_drawdown():
    sim = PathSimulator()
    curve = [100.0, 110.0, 99.0, 105.0]
    mdd = sim.max_drawdown_pct(curve)
    assert abs(mdd - 10.0) < 1e-5

def test_ruin_hit():
    sim = PathSimulator()
    curve = [100.0, 110.0, 69.0, 80.0]
    assert sim.ruin_hit(curve, 100.0, 30.0) is True
    assert sim.ruin_hit(curve, 100.0, 35.0) is False
