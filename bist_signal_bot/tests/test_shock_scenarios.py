import pytest
from bist_signal_bot.stress.shocks import ShockScenarioEngine

def test_default_scenarios():
    engine = ShockScenarioEngine()
    scenarios = engine.default_scenarios()
    assert len(scenarios) > 0
    assert any(s.scenario_id == "market_drop_severe" for s in scenarios)

def test_market_shock():
    class DummyItem:
        def __init__(self, sym, beta):
            self.symbol = sym
            self.beta = beta

    items = [DummyItem("A", 1.0), DummyItem("B", 1.5)]
    engine = ShockScenarioEngine()
    impacts = engine.apply_market_shock(items, -10.0)
    assert impacts["A"] == -10.0
    assert impacts["B"] == -15.0

def test_sector_shock():
    class DummyItem:
        def __init__(self, sym, sector):
            self.symbol = sym
            self.sector = sector

    items = [DummyItem("A", "BANKA"), DummyItem("B", "SANAYI")]
    engine = ShockScenarioEngine()
    impacts = engine.apply_sector_shocks(items, {"BANKA": -20.0})
    assert impacts["A"] == -20.0
    assert impacts["B"] == 0.0
