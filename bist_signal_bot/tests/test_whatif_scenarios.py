
from bist_signal_bot.whatif.scenarios import WhatIfScenarioFactory

def test_scenario_factory():
    f = WhatIfScenarioFactory()
    scenarios = f.default_scenarios()
    assert len(scenarios) > 0
    assert any(s.name == "Baseline" for s in scenarios)

    cs = f.cost_stress(1.5)
    assert cs.name == "Cost +50%"
