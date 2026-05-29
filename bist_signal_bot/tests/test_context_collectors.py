import pytest
from bist_signal_bot.context_fusion.collectors import ContextCollector
from bist_signal_bot.config.settings import Settings

def test_context_collector_empty_fallback():
    collector = ContextCollector(Settings())
    payload = {
        "symbol": "ASELS",
        "strategy_name": "test",
        "signal_id": "1",
        "direction": "LONG",
        "score": 80.0
    }
    signals = collector.collect_for_signal(payload)
    # At least technical signal should be collected
    assert len(signals) >= 1
    assert signals[0].symbol == "ASELS"
