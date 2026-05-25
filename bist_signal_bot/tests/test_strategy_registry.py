import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.registry import StrategyRegistryManager
from bist_signal_bot.strategy_registry.models import StrategyDefinition, StrategyRegistryStatus, StrategyFamily
from bist_signal_bot.core.exceptions import StrategyRegistryError

@pytest.fixture
def manager(tmp_path):
    settings = Settings(STRATEGY_REGISTRY_REQUIRE_CONFIRM_FOR_REGISTER=True)
    return StrategyRegistryManager(settings, tmp_path)

def test_registry_register_requires_confirm(manager):
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)

    with pytest.raises(StrategyRegistryError, match="requires explicit confirmation"):
        manager.register_strategy(defn, confirm=False)

def test_registry_register_and_get(manager):
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)

    manager.store.append_definition(defn)

    loaded = manager.get_strategy("test")
    assert loaded is not None
    assert loaded.strategy_id == "1"

def test_registry_archive_requires_confirm(manager):
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    manager.store.append_definition(defn)

    with pytest.raises(StrategyRegistryError, match="requires explicit confirmation"):
        manager.archive_strategy("1", reason="test", confirm=False)

def test_registry_list(manager):
    defn1 = StrategyDefinition(strategy_id="1", strategy_name="test1", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    defn2 = StrategyDefinition(strategy_id="2", strategy_name="test2", display_name="Test", version="1", family=StrategyFamily.MOMENTUM, status=StrategyRegistryStatus.VALIDATED_RESEARCH)

    manager.store.append_definition(defn1)
    manager.store.append_definition(defn2)

    assert len(manager.list_strategies()) == 2
    assert len(manager.list_strategies(status=StrategyRegistryStatus.VALIDATED_RESEARCH)) == 1
    assert len(manager.list_strategies(family=StrategyFamily.TREND)) == 1
