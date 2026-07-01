from pathlib import Path
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.drift.engine import DriftEngine, DriftEngineDependencies
from bist_signal_bot.drift.storage import DriftStore
from bist_signal_bot.drift.reference import DriftReferenceManager
from bist_signal_bot.drift.feature_drift import FeatureDriftDetector

def create_drift_engine(settings: Settings | None = None, base_dir: Path | None = None) -> DriftEngine:
    s = settings or get_settings()
    deps = DriftEngineDependencies(
        settings=s,
        store=create_drift_store(s, base_dir),
        reference_manager=create_reference_manager(s, base_dir)
    )
    return DriftEngine(deps=deps)

def create_drift_store(settings: Settings | None = None, base_dir: Path | None = None) -> DriftStore:
    return DriftStore(settings=settings, base_dir=base_dir)

def create_reference_manager(settings: Settings | None = None, base_dir: Path | None = None) -> DriftReferenceManager:
    return DriftReferenceManager(settings=settings, base_dir=base_dir)

def create_feature_drift_detector(settings: Settings | None = None) -> FeatureDriftDetector:
    return FeatureDriftDetector(settings=settings)
