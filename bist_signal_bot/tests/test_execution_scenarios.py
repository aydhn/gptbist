import pytest
from bist_signal_bot.execution_sim.scenarios import ExecutionScenarioManager

def test_default_scenarios_exist():
    mgr = ExecutionScenarioManager()
    scenarios = mgr.default_scenarios()
    assert len(scenarios) == 4
    names = [s.name for s in scenarios]
    assert "Base" in names
    assert "Stress" in names
