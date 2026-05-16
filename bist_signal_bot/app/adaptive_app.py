from pathlib import Path
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.adaptive.engine import AdaptiveEngine
from bist_signal_bot.adaptive.policy import AdaptivePolicyManager
from bist_signal_bot.adaptive.storage import AdaptiveStore

def create_adaptive_engine(settings: Settings | None = None, base_dir: Path | None = None) -> AdaptiveEngine:
    s = settings or get_settings()
    store = AdaptiveStore(s, base_dir)
    return AdaptiveEngine(storage=store, settings=s)

def create_adaptive_policy_manager(settings: Settings | None = None) -> AdaptivePolicyManager:
    s = settings or get_settings()
    return AdaptivePolicyManager(settings=s)

def create_adaptive_store(settings: Settings | None = None, base_dir: Path | None = None) -> AdaptiveStore:
    s = settings or get_settings()
    return AdaptiveStore(settings=s, base_dir=base_dir)
