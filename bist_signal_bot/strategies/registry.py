from typing import Dict, List, Optional
from bist_signal_bot.core.exceptions import StrategyRegistryError
from bist_signal_bot.strategies.models import StrategySpec, StrategyCategory
from bist_signal_bot.strategies.base_strategy import BaseStrategy

class StrategyRegistry:
    """Registry for managing available strategies."""

    def __init__(self):
        self._strategies: dict[str, BaseStrategy] = {}

    def register(self, strategy: BaseStrategy) -> None:
        """Register a new strategy."""
        name = strategy.spec.name
        if name in self._strategies:
            raise StrategyRegistryError(f"Strategy '{name}' is already registered")
        self._strategies[name] = strategy

    def get(self, name: str) -> BaseStrategy:
        """Get a strategy by name."""
        name = name.lower().replace(" ", "_")
        if name not in self._strategies:
            raise StrategyRegistryError(f"Strategy '{name}' not found in registry")
        return self._strategies[name]

    def exists(self, name: str) -> bool:
        """Check if a strategy exists."""
        return name.lower().replace(" ", "_") in self._strategies

    def list_specs(self, category: StrategyCategory | None = None) -> list[StrategySpec]:
        """List all strategy specs, optionally filtered by category."""
        specs = [s.spec for s in self._strategies.values()]
        if category:
            specs = [s for s in specs if s.category == category]
        return specs

    def list_names(self, category: StrategyCategory | None = None) -> list[str]:
        """List all strategy names, optionally filtered by category."""
        return [s.name for s in self.list_specs(category)]

# Singleton instance
_registry_instance = None

def get_registry() -> StrategyRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = create_default_strategy_registry()
    return _registry_instance

def create_default_strategy_registry() -> StrategyRegistry:
    """Create a registry and populate it with builtin strategies."""
    registry = StrategyRegistry()

    try:
        from bist_signal_bot.strategies.builtin import (
            MovingAverageTrendStrategy,
            RSIMeanReversionStrategy,
            BreakoutVolumeStrategy,
            CompositeFeatureStrategy
        )
        registry.register(MovingAverageTrendStrategy())
        registry.register(RSIMeanReversionStrategy())
        registry.register(BreakoutVolumeStrategy())
        registry.register(CompositeFeatureStrategy())
    except ImportError:
        pass

    return registry
