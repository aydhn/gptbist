from typing import Any, Dict, Optional
from datetime import datetime, timezone
from bist_signal_bot.signals.models import TrackedSignal, ResearchExitSimulation, SignalOutcomeState
from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.config.settings import get_settings

class SignalOutcomeTracker:
    def __init__(self, store: SignalStore):
        self.store = store
        self.settings = get_settings()

    def update_from_exit_simulation(self, simulation: ResearchExitSimulation, confirm: bool = False) -> TrackedSignal:
        s = self.store.get_signal(simulation.signal_id)
        if not s:
            raise ValueError(f"Signal not found: {simulation.signal_id}")

        s.outcome_state = simulation.outcome_state
        s.outcome_return_pct = simulation.simulated_return_pct
        s.updated_at = datetime.now(timezone.utc)
        self.store.update_signal(s)
        self.store.append_exit_simulation(simulation)
        return s

    def update_manual_outcome(self, signal_id: str, outcome: SignalOutcomeState, return_pct: Optional[float] = None, confirm: bool = False) -> TrackedSignal:
        if not confirm and getattr(self.settings, "SIGNAL_EXIT_REQUIRE_CONFIRM_FOR_MANUAL_OUTCOME", True):
            raise ValueError("Confirm flag required for manual outcome update")

        s = self.store.get_signal(signal_id)
        if not s:
            raise ValueError(f"Signal not found: {signal_id}")

        s.outcome_state = outcome
        s.outcome_return_pct = return_pct
        s.updated_at = datetime.now(timezone.utc)
        self.store.update_signal(s)
        return s

    def sync_to_research_journal(self, signal: TrackedSignal) -> Dict[str, Any]:
        return {
            "signal_id": signal.signal_id,
            "fingerprint_id": signal.fingerprint_id,
            "symbol": signal.symbol,
            "outcome_state": signal.outcome_state.value,
            "return_pct": signal.outcome_return_pct,
            "lifecycle_state": signal.state.value,
            "created_at": signal.created_at.isoformat(),
            "updated_at": signal.updated_at.isoformat()
        }

    def summarize_outcomes(self, symbol: Optional[str] = None, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        signals = self.store.load_signals(limit=10000)

        target_hits = 0
        stop_hits = 0
        time_expired = 0
        invalidated = 0

        total = 0
        ret_sum = 0.0

        for s in signals:
            if symbol and s.symbol != symbol: continue
            if strategy_name and s.strategy_name != strategy_name: continue

            if s.outcome_state == SignalOutcomeState.HIT_RESEARCH_TARGET:
                target_hits += 1
            elif s.outcome_state == SignalOutcomeState.HIT_RESEARCH_STOP:
                stop_hits += 1
            elif s.outcome_state == SignalOutcomeState.TIME_EXPIRED:
                time_expired += 1
            elif "INVALIDATED" in s.outcome_state.value:
                invalidated += 1

            if s.outcome_return_pct is not None:
                total += 1
                ret_sum += s.outcome_return_pct

        return {
            "target_hits": target_hits,
            "stop_hits": stop_hits,
            "time_expired": time_expired,
            "invalidated": invalidated,
            "average_simulated_return": (ret_sum / total) if total > 0 else 0.0,
            "tracked_count": total
        }
