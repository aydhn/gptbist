from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.ensemble.engine import EnsembleEngine
from bist_signal_bot.ensemble.storage import EnsembleStore
from bist_signal_bot.ensemble.weights import EnsembleWeightManager

def create_ensemble_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> EnsembleEngine:
    s = settings or get_settings()
    engine = EnsembleEngine.from_settings(s)
    if base_dir:
        engine.store.base_dir = base_dir / getattr(s, "ENSEMBLE_DIR_NAME", "ensemble")
    return engine

def create_ensemble_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> EnsembleStore:
    s = settings or get_settings()
    store = EnsembleStore(s)
    if base_dir:
        store.base_dir = base_dir / getattr(s, "ENSEMBLE_DIR_NAME", "ensemble")
    return store

def create_weight_manager(settings: Optional[Settings] = None) -> EnsembleWeightManager:
    s = settings or get_settings()
    return EnsembleWeightManager(s)
