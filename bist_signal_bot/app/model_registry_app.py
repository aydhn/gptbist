from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.model_registry.storage import ModelRegistryStore
from bist_signal_bot.model_registry.registry import LocalModelRegistry
from bist_signal_bot.model_registry.experiments import ExperimentTracker
from bist_signal_bot.model_registry.artifacts import ModelArtifactManager
from bist_signal_bot.model_registry.model_cards import ModelCardBuilder
from bist_signal_bot.model_registry.validation import ModelValidationGovernance
from bist_signal_bot.model_registry.calibration import ModelCalibrationGovernance
from bist_signal_bot.model_registry.promotion import ModelPromotionManager
from bist_signal_bot.model_registry.drift import ModelDriftDetector
from bist_signal_bot.model_registry.lineage import ModelLineageTracker
from bist_signal_bot.model_registry.governance import ModelGovernanceEngine


def create_model_registry_store(settings: Settings | None = None, base_dir: Path | None = None) -> ModelRegistryStore:
    return ModelRegistryStore(settings, base_dir)

def create_local_model_registry(settings: Settings | None = None, base_dir: Path | None = None) -> LocalModelRegistry:
    store = create_model_registry_store(settings, base_dir)
    return LocalModelRegistry(settings, store)

def create_experiment_tracker(settings: Settings | None = None, base_dir: Path | None = None) -> ExperimentTracker:
    store = create_model_registry_store(settings, base_dir)
    return ExperimentTracker(settings, store)

def create_model_artifact_manager(settings: Settings | None = None, base_dir: Path | None = None) -> ModelArtifactManager:
    store = create_model_registry_store(settings, base_dir)
    return ModelArtifactManager(settings, store)

def create_model_card_builder(settings: Settings | None = None, base_dir: Path | None = None) -> ModelCardBuilder:
    store = create_model_registry_store(settings, base_dir)
    return ModelCardBuilder(settings, store)

def create_model_validation_governance(settings: Settings | None = None, base_dir: Path | None = None) -> ModelValidationGovernance:
    return ModelValidationGovernance(settings)

def create_model_calibration_governance(settings: Settings | None = None, base_dir: Path | None = None) -> ModelCalibrationGovernance:
    return ModelCalibrationGovernance(settings)

def create_model_drift_detector(settings: Settings | None = None, base_dir: Path | None = None) -> ModelDriftDetector:
    return ModelDriftDetector(settings)

def create_model_lineage_tracker(settings: Settings | None = None, base_dir: Path | None = None) -> ModelLineageTracker:
    store = create_model_registry_store(settings, base_dir)
    return ModelLineageTracker(settings, store)

def create_model_governance_engine(settings: Settings | None = None, base_dir: Path | None = None) -> ModelGovernanceEngine:
    registry = create_local_model_registry(settings, base_dir)
    store = create_model_registry_store(settings, base_dir)
    return ModelGovernanceEngine(settings, registry, store)

def create_model_promotion_manager(settings: Settings | None = None, base_dir: Path | None = None) -> ModelPromotionManager:
    registry = create_local_model_registry(settings, base_dir)
    store = create_model_registry_store(settings, base_dir)
    gov_engine = create_model_governance_engine(settings, base_dir)
    return ModelPromotionManager(settings, registry, gov_engine, store)
