from bist_signal_bot.monitoring.metrics import MonitoringMetricCalculator

def test_monitoring_win_rate():
    calc = MonitoringMetricCalculator()
    class Dummy:
        def __init__(self, pnl):
            self.pnl = pnl
    outcomes = [Dummy(10), Dummy(-5), Dummy(20)]
    assert calc.win_rate(outcomes) == 2.0 / 3.0

def test_monitoring_expectancy():
    calc = MonitoringMetricCalculator()
    class Dummy:
        def __init__(self, pnl):
            self.pnl = pnl
    outcomes = [Dummy(10), Dummy(-5), Dummy(20)]
    assert calc.expectancy(outcomes) == 25.0 / 3.0

def test_monitoring_profit_factor():
    calc = MonitoringMetricCalculator()
    class Dummy:
        def __init__(self, pnl):
            self.pnl = pnl
    outcomes = [Dummy(10), Dummy(-5), Dummy(20)]
    assert calc.profit_factor(outcomes) == 30.0 / 5.0

def test_monitoring_drawdown():
    calc = MonitoringMetricCalculator()
    returns = [0.05, -0.02, -0.01, 0.04]
    dd = calc.max_drawdown_from_returns(returns)
    assert round(dd, 4) == 0.03

def test_status_insufficient_data():
    calc = MonitoringMetricCalculator()
    status = calc.status_from_metric("test", 1.0, 1.0, 10)
    assert status == "INSUFFICIENT_DATA"
