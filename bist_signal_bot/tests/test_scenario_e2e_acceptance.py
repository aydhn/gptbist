import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scenarios.registry import ScenarioRegistry
from bist_signal_bot.scenarios.runner import ScenarioRunner, ScenarioRunnerDependencies
from bist_signal_bot.scenarios.storage import ScenarioStore

def test_acceptance_scenario_instantiation():
    settings = Settings()
    registry = ScenarioRegistry()
    runner = ScenarioRunner(deps=ScenarioRunnerDependencies(settings=settings, registry=registry))

    # Check that acceptance scenario has required configuration without running it all to avoid network calls
    acc = registry.get_scenario("acceptance")
    assert acc is not None
    assert len(acc.steps) > 0
    assert any("moving_average_trend" in str(s.command) for s in acc.steps if s.command)
    assert acc.use_sandbox is True
