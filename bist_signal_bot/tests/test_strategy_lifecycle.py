import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.lifecycle import StrategyLifecycleManager
from bist_signal_bot.strategy_registry.registry import StrategyRegistryManager
from bist_signal_bot.strategy_registry.models import StrategyDefinition, StrategyRegistryStatus, StrategyFamily

@pytest.fixture
def lifecycle(tmp_path):
    settings = Settings(STRATEGY_REGISTRY_REQUIRE_CONFIRM_FOR_STATUS_CHANGE=True)
    manager = StrategyRegistryManager(settings, tmp_path)
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    manager.store.append_definition(defn)
    return manager.lifecycle

def test_lifecycle_transition_requires_confirm(lifecycle):
    with pytest.raises(ValueError, match="requires confirmation"):
        lifecycle.transition("1", StrategyRegistryStatus.VALIDATED_RESEARCH, "Testing", confirm=False)

def test_lifecycle_transition_produces_event(lifecycle):
    event = lifecycle.transition("1", StrategyRegistryStatus.VALIDATED_RESEARCH, "Testing", confirm=True)

    assert event.event_type.value == "PROMOTED"
    assert event.previous_status == StrategyRegistryStatus.CANDIDATE
    assert event.new_status == StrategyRegistryStatus.VALIDATED_RESEARCH

    # Check events list
    events = lifecycle.events_for_strategy("1")
    assert len(events) == 1 # Just the transition
