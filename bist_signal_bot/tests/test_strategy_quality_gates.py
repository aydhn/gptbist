import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.gates import StrategyQualityGate
from bist_signal_bot.strategy_registry.registry import StrategyRegistryManager
from bist_signal_bot.strategy_registry.models import StrategyDefinition, StrategyRegistryStatus, StrategyFamily, StrategyGateDecision

@pytest.fixture
def env(tmp_path):
    settings = Settings(STRATEGY_ALLOW_CANDIDATE_IN_SCANNER=False)
    registry = StrategyRegistryManager(settings, tmp_path)
    return settings, tmp_path, registry

def test_gate_blocks_blocked_strategy(env):
    settings, tmp_path, registry = env
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.BLOCKED)
    registry.store.append_definition(defn)

    gate = StrategyQualityGate(settings, tmp_path)
    assert gate.scanner_gate("test") == StrategyGateDecision.BLOCK
    assert gate.evaluate_strategy("test") == StrategyGateDecision.BLOCK

def test_gate_scanner_blocks_candidate_by_default(env):
    settings, tmp_path, registry = env
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    registry.store.append_definition(defn)

    gate = StrategyQualityGate(settings, tmp_path)
    assert gate.scanner_gate("test") == StrategyGateDecision.BLOCK

def test_gate_scanner_allows_candidate_if_enabled(env):
    settings, tmp_path, registry = env
    object.__setattr__(settings, 'STRATEGY_ALLOW_CANDIDATE_IN_SCANNER', True)
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    registry.store.append_definition(defn)

    gate = StrategyQualityGate(settings, tmp_path)
    assert gate.scanner_gate("test") == StrategyGateDecision.ALLOW

def test_gate_allows_validated(env):
    settings, tmp_path, registry = env
    defn = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.VALIDATED_RESEARCH)
    registry.store.append_definition(defn)

    gate = StrategyQualityGate(settings, tmp_path)
    assert gate.scanner_gate("test") == StrategyGateDecision.ALLOW
    assert gate.evaluate_strategy("test") == StrategyGateDecision.ALLOW
