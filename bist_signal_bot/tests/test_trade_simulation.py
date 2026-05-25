from bist_signal_bot.monte_carlo.trade_simulation import TradeSimulationAdapter

class MockBacktestResult:
    def __init__(self, trades):
        self.trades = trades

def test_trades_from_backtest_result():
    adapter = TradeSimulationAdapter()
    trades = [
        {"gross_return_pct": 2.0, "net_return_pct": 1.5, "symbol": "ASELS"},
        {"gross_return_pct": -1.0, "symbol": "THYAO"}
    ]
    res = adapter.trades_from_backtest_result(MockBacktestResult(trades))
    assert len(res) == 2
    assert res[0]["net_return_pct"] == 1.5
    assert res[1]["net_return_pct"] == -1.0

def test_returns_from_backtest_result():
    adapter = TradeSimulationAdapter()
    trades = [
        {"gross_return_pct": 2.0, "net_return_pct": 1.5},
        {"gross_return_pct": -1.0, "net_return_pct": -1.2}
    ]
    rets = adapter.returns_from_backtest_result(MockBacktestResult(trades), use_net=True)
    assert rets == [1.5, -1.2]
