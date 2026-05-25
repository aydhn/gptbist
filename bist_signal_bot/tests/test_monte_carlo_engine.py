from bist_signal_bot.app.monte_carlo_app import create_monte_carlo_engine
from bist_signal_bot.monte_carlo.models import MonteCarloRequest, MonteCarloTarget, ResamplingMethod, MonteCarloStatus
from bist_signal_bot.config.settings import Settings

def test_engine_run_from_trades():
    settings = Settings()
    engine = create_monte_carlo_engine(settings)

    req = MonteCarloRequest("req1", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_SHUFFLE, 10, 42, 100000.0, 30.0)
    trades = [
        {"gross_return_pct": 5.0, "net_return_pct": 4.0},
        {"gross_return_pct": -2.0, "net_return_pct": -2.5},
        {"gross_return_pct": 1.0, "net_return_pct": 0.5}
    ]

    res = engine.run_from_trades(trades, req)

    assert res.status in (MonteCarloStatus.PASS, MonteCarloStatus.WATCH, MonteCarloStatus.FAIL)
    assert len(res.paths) == 10
    assert res.risk_summary is not None
    assert any("Sample size (3) is very small" in w for w in res.warnings)

def test_engine_insufficient_data():
    settings = Settings()
    engine = create_monte_carlo_engine(settings)

    req = MonteCarloRequest("req2", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_SHUFFLE, 10, 42, 100000.0, 30.0)

    res = engine.run_from_trades([], req)
    assert res.status == MonteCarloStatus.INSUFFICIENT_DATA
