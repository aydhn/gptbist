import pytest
from bist_signal_bot.strategies.registry import StrategyRegistry
from bist_signal_bot.core.exceptions import StrategyRegistryError
from bist_signal_bot.strategies.base_strategy import BaseStrategy
from bist_signal_bot.strategies.models import StrategySpec
from bist_signal_bot.strategies.context import StrategyContext
from bist_signal_bot.signals.models import SignalCandidate
from typing import Any

class MockStrategy(BaseStrategy):
    @property
    def spec(self) -> StrategySpec:
        return StrategySpec(name="mock_strat", display_name="Mock")

    def generate_candidate(self, context: StrategyContext, params: dict[str, Any]) -> SignalCandidate | None:
        return None

def test_strategy_registry_register_and_get():
    registry = StrategyRegistry()
    strat = MockStrategy()
    registry.register(strat)

    assert registry.exists("mock_strat")
    retrieved = registry.get("mock_strat")
    assert retrieved is strat

def test_strategy_registry_duplicate():
    registry = StrategyRegistry()
    strat = MockStrategy()
    registry.register(strat)

    with pytest.raises(StrategyRegistryError):
        registry.register(strat)

def test_strategy_registry_not_found():
    registry = StrategyRegistry()
    with pytest.raises(StrategyRegistryError):
        registry.get("unknown")
