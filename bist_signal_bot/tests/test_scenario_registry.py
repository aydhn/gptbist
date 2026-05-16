import pytest
from bist_signal_bot.scenarios.registry import ScenarioRegistry
from bist_signal_bot.scenarios.models import ScenarioType

def test_registry_defaults():
    registry = ScenarioRegistry()
    scenarios = registry.list_scenarios()

    assert len(scenarios) > 0
    ids = [s.scenario_id for s in scenarios]
    assert "smoke" in ids
    assert "acceptance" in ids
    assert "e2e-research" in ids
    assert "e2e-ml" in ids
    assert "security-failsafe" in ids
    assert "monitoring-recovery" in ids
    assert "performance-smoke" in ids

def test_get_scenario():
    registry = ScenarioRegistry()
    smoke = registry.get_scenario("smoke")
    assert smoke is not None
    assert smoke.scenario_type == ScenarioType.SMOKE

    # Check steps content
    assert any(s.name == "Package Doctor" for s in smoke.steps)
    assert any(s.name == "Security Audit" for s in smoke.steps)

def test_validate_acceptance_scenario():
    registry = ScenarioRegistry()
    acc = registry.get_scenario("acceptance")
    assert acc is not None
    assert acc.use_sandbox is True
    assert acc.source == "mock"
    assert "ASELS" in acc.symbols
    assert len(acc.steps) == 7
