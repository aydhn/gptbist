from pathlib import Path
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore
from bist_signal_bot.strategy_registry.catalog import StrategyCatalogScanner
from bist_signal_bot.strategy_registry.registry import StrategyRegistryManager
from bist_signal_bot.strategy_registry.evidence import StrategyEvidenceCollector
from bist_signal_bot.strategy_registry.scorecard import StrategyScorecardBuilder
from bist_signal_bot.strategy_registry.lifecycle import StrategyLifecycleManager
from bist_signal_bot.strategy_registry.promotion import StrategyPromotionManager
from bist_signal_bot.strategy_registry.gates import StrategyQualityGate
from bist_signal_bot.strategy_registry.snapshot import StrategyRegistrySnapshotBuilder

def create_strategy_registry_store(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyRegistryStore:
    return StrategyRegistryStore(settings, base_dir)

def create_strategy_catalog_scanner(settings: Settings | None = None) -> StrategyCatalogScanner:
    return StrategyCatalogScanner(settings)

def create_strategy_registry_manager(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyRegistryManager:
    return StrategyRegistryManager(settings, base_dir)

def create_strategy_evidence_collector(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyEvidenceCollector:
    return StrategyEvidenceCollector(settings, base_dir)

def create_strategy_scorecard_builder(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyScorecardBuilder:
    return StrategyScorecardBuilder(settings, base_dir)

def create_strategy_lifecycle_manager(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyLifecycleManager:
    return StrategyLifecycleManager(settings, base_dir)

def create_strategy_promotion_manager(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyPromotionManager:
    return StrategyPromotionManager(settings, base_dir)

def create_strategy_quality_gate(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyQualityGate:
    return StrategyQualityGate(settings, base_dir)

def create_strategy_registry_snapshot_builder(settings: Settings | None = None, base_dir: Path | None = None) -> StrategyRegistrySnapshotBuilder:
    return StrategyRegistrySnapshotBuilder(settings, base_dir)
