from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scenarios.runner import ScenarioRunner, ScenarioRunnerDependencies
from bist_signal_bot.scenarios.registry import ScenarioRegistry
from bist_signal_bot.scenarios.storage import ScenarioStore
from bist_signal_bot.scenarios.golden import GoldenSnapshotManager
from bist_signal_bot.scenarios.validator import ScenarioValidator

def create_scenario_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ScenarioStore:
    return ScenarioStore(settings=settings, base_dir=base_dir)

def create_golden_snapshot_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> GoldenSnapshotManager:
    store = create_scenario_store(settings, base_dir)
    return GoldenSnapshotManager(golden_dir=store.get_golden_dir())

def create_scenario_registry(settings: Optional[Settings] = None) -> ScenarioRegistry:
    return ScenarioRegistry()

def create_scenario_runner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ScenarioRunner:
    store = create_scenario_store(settings, base_dir)
    registry = create_scenario_registry(settings)
    golden = create_golden_snapshot_manager(settings, base_dir)
    validator = ScenarioValidator(settings=settings)

    deps = ScenarioRunnerDependencies(
        registry=registry,
        storage=store,
        golden_manager=golden,
        validator=validator,
        settings=settings
    )
    return ScenarioRunner(deps=deps)
