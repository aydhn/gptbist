from bist_signal_bot.monitoring.collectors import MonitoringDataCollector

def test_collector_returns_empty_safely():
    col = MonitoringDataCollector()
    res = col.collect_strategy_outcomes("test")
    assert res == []
