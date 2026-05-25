import inspect
import uuid
import sys
from typing import Any
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyFamily,
    StrategyRegistryStatus
)
from bist_signal_bot.core.exceptions import StrategyCatalogError

class StrategyCatalogScanner:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def scan_available_strategies(self) -> list[StrategyDefinition]:
        strategies = []
        try:
            import bist_signal_bot.strategies as strategies_module
            import pkgutil

            for importer, modname, ispkg in pkgutil.iter_modules(strategies_module.__path__):
                if modname.startswith('test_') or modname == 'base':
                    continue
                try:
                    import importlib
                    module = importlib.import_module(f'bist_signal_bot.strategies.{modname}')
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (obj.__module__ == module.__name__ and
                            hasattr(obj, 'generate_candidate') and
                            not name.startswith('Base')):
                            strategies.append(self.definition_from_strategy_class(obj))
                except Exception as e:
                    print(f"Warning: Failed to import strategy module {modname}: {e}")
        except Exception as e:
            print(f"Warning: Failed to scan strategies module: {e}")

        return strategies

    def definition_from_strategy_class(self, strategy_cls: Any) -> StrategyDefinition:
        strategy_name = getattr(strategy_cls, "strategy_name", strategy_cls.__name__)
        version = getattr(strategy_cls, "version", "1.0.0")

        family_str = getattr(strategy_cls, "family", "UNKNOWN")
        try:
            family = StrategyFamily(family_str)
        except ValueError:
            family = StrategyFamily.UNKNOWN

        default_params = getattr(strategy_cls, "default_parameters", {})
        if not default_params and hasattr(strategy_cls, "params") and isinstance(getattr(strategy_cls, "params"), dict):
            default_params = getattr(strategy_cls, "params")

        return StrategyDefinition(
            strategy_id=f"strat_{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            display_name=getattr(strategy_cls, "display_name", strategy_name.replace("_", " ").title()),
            version=version,
            family=family,
            status=StrategyRegistryStatus.CANDIDATE,
            module_path=strategy_cls.__module__,
            class_name=strategy_cls.__name__,
            default_parameters=default_params,
            parameter_schema=getattr(strategy_cls, "parameter_schema", {}),
            supported_timeframes=getattr(strategy_cls, "supported_timeframes", ["1d"]),
            supported_order_sides=getattr(strategy_cls, "supported_order_sides", ["BUY", "SELL"]),
            supported_universes=getattr(strategy_cls, "supported_universes", ["ALL"]),
            requires_adjusted_prices=getattr(strategy_cls, "requires_adjusted_prices", False),
            supports_short=getattr(strategy_cls, "supports_short", False),
            supports_cost_model=getattr(strategy_cls, "supports_cost_model", False),
            metadata=getattr(strategy_cls, "metadata", {})
        )

    def validate_strategy_definition(self, definition: StrategyDefinition) -> list[str]:
        errors = []
        if not definition.strategy_name:
            errors.append("strategy_name cannot be empty")
        if not definition.version:
            errors.append("version cannot be empty")

        forbidden_keys = ["broker", "live_trading", "order_routing", "real_money"]
        if definition.metadata:
            for key in definition.metadata:
                if any(f in key.lower() for f in forbidden_keys):
                    errors.append(f"Forbidden metadata key detected: {key}")

        return errors

    def detect_missing_registry_entries(self, existing_definitions: list[StrategyDefinition]) -> list[StrategyDefinition]:
        available = self.scan_available_strategies()
        existing_names = {d.strategy_name for d in existing_definitions}

        missing = []
        for d in available:
            if d.strategy_name not in existing_names:
                missing.append(d)

        return missing
