from pathlib import Path
from typing import Optional
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.signals.fingerprint import SignalFingerprintBuilder
from bist_signal_bot.signals.policy import SignalPolicyManager
from bist_signal_bot.signals.lifecycle import SignalLifecycleManager
from bist_signal_bot.signals.watchlist import SignalWatchlistManager
from bist_signal_bot.signals.exit_simulation import ResearchExitSimulator
from bist_signal_bot.signals.outcomes import SignalOutcomeTracker

def create_signal_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> SignalStore:
    return SignalStore(base_dir=base_dir)

def create_signal_lifecycle_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> SignalLifecycleManager:
    store = create_signal_store(settings, base_dir)
    fingerprint_builder = SignalFingerprintBuilder()
    policy_manager = SignalPolicyManager()
    policy = policy_manager.load_alert_policy()
    return SignalLifecycleManager(store=store, fingerprint_builder=fingerprint_builder, alert_policy=policy)

def create_signal_watchlist_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> SignalWatchlistManager:
    store = create_signal_store(settings, base_dir)
    return SignalWatchlistManager(store=store)

def create_research_exit_simulator(settings: Optional[Settings] = None) -> ResearchExitSimulator:
    return ResearchExitSimulator()

def create_signal_outcome_tracker(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> SignalOutcomeTracker:
    store = create_signal_store(settings, base_dir)
    return SignalOutcomeTracker(store=store)
