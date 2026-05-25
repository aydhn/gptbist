from bist_signal_bot.monte_carlo.resampling import ResamplingEngine

def test_return_bootstrap_deterministic():
    engine = ResamplingEngine()
    returns = [1.0, -0.5, 2.0, -1.0, 0.5]
    resampled = engine.return_bootstrap(returns, seed=42)
    assert len(resampled) == 5
    for r in resampled:
        assert r in returns

def test_block_bootstrap():
    engine = ResamplingEngine()
    returns = [1.0, -0.5, 2.0, -1.0, 0.5, 3.0, -2.0, 1.5, 0.0, -0.1]
    resampled = engine.block_bootstrap(returns, block_size=3, seed=42)
    assert len(resampled) == len(returns)

def test_trade_shuffle():
    engine = ResamplingEngine()
    trades = [{"id": i} for i in range(5)]
    shuffled = engine.trade_shuffle(trades, seed=42)
    assert len(shuffled) == 5
    assert shuffled != trades
    assert sorted([t["id"] for t in shuffled]) == [0, 1, 2, 3, 4]
