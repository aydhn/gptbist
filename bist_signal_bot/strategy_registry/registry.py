from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyFamily,
    StrategyRegistryStatus,
    StrategyLifecycleEvent
)
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore
from bist_signal_bot.strategy_registry.catalog import StrategyCatalogScanner
from bist_signal_bot.strategy_registry.lifecycle import StrategyLifecycleManager
from bist_signal_bot.core.exceptions import StrategyRegistryError

class StrategyRegistryManager:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.store = StrategyRegistryStore(self.settings, base_dir)
        self.catalog = StrategyCatalogScanner(self.settings)
        self.lifecycle = StrategyLifecycleManager(self.settings, base_dir)

    def register_strategy(self, definition: StrategyDefinition, confirm: bool = False) -> StrategyDefinition:
        if not confirm and getattr(self.settings, "STRATEGY_REGISTRY_REQUIRE_CONFIRM_FOR_REGISTER", True):
            raise StrategyRegistryError("Registering a strategy requires explicit confirmation.")

        errors = self.catalog.validate_strategy_definition(definition)
        if errors:
            raise StrategyRegistryError(f"Invalid strategy definition: {', '.join(errors)}")

        existing = self.store.get_definition(definition.strategy_name)
        if existing:
            raise StrategyRegistryError(f"Strategy {definition.strategy_name} is already registered.")

        self.store.append_definition(definition)

        self.lifecycle.transition(
            strategy_id=definition.strategy_id,
            new_status=definition.status,
            reason="Initial registration",
            confirm=True
        )

        return definition

    def get_strategy(self, strategy_id_or_name: str) -> StrategyDefinition | None:
        return self.store.get_definition(strategy_id_or_name)

    def list_strategies(self, status: StrategyRegistryStatus | None = None, family: StrategyFamily | None = None, limit: int = 1000) -> list[StrategyDefinition]:
        definitions = self.store.load_definitions(limit=limit)
        filtered = []
        for d in definitions:
            if status and d.status != status:
                continue
            if family and d.family != family:
                continue
            filtered.append(d)
        return filtered

    def update_strategy(self, definition: StrategyDefinition, confirm: bool = False) -> StrategyDefinition:
        if not confirm:
            raise StrategyRegistryError("Updating a strategy requires explicit confirmation.")

        existing = self.store.get_definition(definition.strategy_id)
        if not existing:
            raise StrategyRegistryError(f"Strategy {definition.strategy_id} not found.")

        # Update logic - essentially append new definition version
        self.store.append_definition(definition)

        self.lifecycle.transition(
            strategy_id=definition.strategy_id,
            new_status=definition.status,
            reason="Strategy definition updated",
            confirm=True
        )

        return definition

    def archive_strategy(self, strategy_id: str, reason: str, confirm: bool = False) -> StrategyLifecycleEvent:
        if not confirm:
            raise StrategyRegistryError("Archiving a strategy requires explicit confirmation.")

        return self.lifecycle.transition(
            strategy_id=strategy_id,
            new_status=StrategyRegistryStatus.ARCHIVED,
            reason=reason,
            confirm=True
        )

    def sync_from_catalog(self, confirm: bool = False) -> list[StrategyDefinition]:
        if not confirm:
            raise StrategyRegistryError("Syncing from catalog requires explicit confirmation.")

        existing = self.store.load_definitions()
        missing = self.catalog.detect_missing_registry_entries(existing)

        registered = []
        for d in missing:
            try:
                registered.append(self.register_strategy(d, confirm=True))
            except Exception as e:
                print(f"Warning: Failed to auto-register strategy {d.strategy_name}: {e}")

        return registered
