from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config_registry.diff import ConfigDiffEngine
from bist_signal_bot.config_registry.drift import ConfigDriftDetector
from bist_signal_bot.config_registry.flags import FeatureFlagManager
from bist_signal_bot.config_registry.gate import ConfigGate
from bist_signal_bot.config_registry.profiles import RuntimeProfileManager
from bist_signal_bot.config_registry.registry import ConfigRegistry
from bist_signal_bot.config_registry.schema import ConfigSchemaBuilder
from bist_signal_bot.config_registry.snapshot import ConfigSnapshotManager
from bist_signal_bot.config_registry.storage import ConfigRegistryStore
from bist_signal_bot.config_registry.validator import ConfigValidator


def create_config_schema_builder(settings: Settings | None = None) -> ConfigSchemaBuilder:
    return ConfigSchemaBuilder()

def create_config_registry_store(settings: Settings | None = None, base_dir: Path | None = None) -> ConfigRegistryStore:
    return ConfigRegistryStore(settings=settings, base_dir=base_dir)

def create_config_registry(settings: Settings | None = None, base_dir: Path | None = None) -> ConfigRegistry:
    settings = settings or Settings()
    builder = create_config_schema_builder(settings)
    return ConfigRegistry(schema_builder=builder, settings=settings)

def create_feature_flag_manager(settings: Settings | None = None, base_dir: Path | None = None) -> FeatureFlagManager:
    store = create_config_registry_store(settings, base_dir)
    return FeatureFlagManager(store=store)

def create_runtime_profile_manager(settings: Settings | None = None, base_dir: Path | None = None) -> RuntimeProfileManager:
    store = create_config_registry_store(settings, base_dir)
    return RuntimeProfileManager(store=store)

def create_config_validator(settings: Settings | None = None) -> ConfigValidator:
    return ConfigValidator(settings=settings)

def create_config_snapshot_manager(settings: Settings | None = None, base_dir: Path | None = None) -> ConfigSnapshotManager:
    registry = create_config_registry(settings, base_dir)
    flags = create_feature_flag_manager(settings, base_dir)
    store = create_config_registry_store(settings, base_dir)
    return ConfigSnapshotManager(registry=registry, flag_manager=flags, store=store)

def create_config_diff_engine(settings: Settings | None = None, base_dir: Path | None = None) -> ConfigDiffEngine:
    builder = create_config_schema_builder(settings)
    store = create_config_registry_store(settings, base_dir)
    return ConfigDiffEngine(schema_builder=builder, store=store)

def create_config_drift_detector(settings: Settings | None = None, base_dir: Path | None = None) -> ConfigDriftDetector:
    engine = create_config_diff_engine(settings, base_dir)
    store = create_config_registry_store(settings, base_dir)
    return ConfigDriftDetector(diff_engine=engine, store=store)

def create_config_gate(settings: Settings | None = None, base_dir: Path | None = None) -> ConfigGate:
    registry = create_config_registry(settings, base_dir)
    validator = create_config_validator(settings)
    store = create_config_registry_store(settings, base_dir)
    return ConfigGate(registry=registry, validator=validator, store=store)
