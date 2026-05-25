from bist_signal_bot.monte_carlo.bootstrap import BootstrapEngine
from bist_signal_bot.monte_carlo.models import ResamplingMethod

def test_bootstrap_trades():
    engine = BootstrapEngine()
    trades = [{"val": 1}, {"val": 2}, {"val": 3}]
    res = engine.bootstrap_trades(trades, simulations=2, seed=42)
    assert len(res) == 2
    assert len(res[0]) == 3

def test_validate_sample_size():
    engine = BootstrapEngine()
    warn = engine.validate_sample_size(10, 100)
    assert len(warn) == 1
    assert "very small" in warn[0]

    warn2 = engine.validate_sample_size(100, 20000)
    assert len(warn2) == 1
    assert "High number of simulations" in warn2[0]
