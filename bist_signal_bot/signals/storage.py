import json
from pathlib import Path
from typing import List, Optional
from bist_signal_bot.signals.models import (
    TrackedSignal, SignalLifecycleEvent, WatchlistEntry,
    ResearchExitSimulation, SignalAlertPolicy, SignalLifecycleState
)
from bist_signal_bot.storage.paths import get_signals_dir
import logging

logger = logging.getLogger(__name__)

class SignalStore:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or get_signals_dir()
        self.tracked_signals_path = self.base_dir / "tracked_signals.jsonl"
        self.events_path = self.base_dir / "lifecycle_events.jsonl"
        self.watchlist_path = self.base_dir / "watchlist.jsonl"
        self.simulations_path = self.base_dir / "exit_simulations.jsonl"
        self.policy_path = self.base_dir / "policy" / "alert_policy.json"

    def _append_jsonl(self, path: Path, data: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
        return path

    def _load_jsonl(self, path: Path, limit: int = 1000) -> List[dict]:
        if not path.exists():
            return []
        results = []
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    results.append(json.loads(line))
                    if len(results) >= limit:
                        break
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping corrupted JSONL line: {e}")
        return results

    def append_signal(self, signal: TrackedSignal) -> Path:
        return self._append_jsonl(self.tracked_signals_path, signal.model_dump(mode='json'))

    def update_signal(self, signal: TrackedSignal) -> Path:
        return self.append_signal(signal)  # Append-only update

    def load_signals(self, limit: int = 1000, state: Optional[SignalLifecycleState] = None, symbol: Optional[str] = None) -> List[TrackedSignal]:
        raw_data = self._load_jsonl(self.tracked_signals_path, limit=limit*10)

        # Keep latest by signal_id
        latest_signals = {}
        for row in reversed(raw_data): # Older to newer so newer overwrites
             latest_signals[row["signal_id"]] = row

        results = []
        for row in latest_signals.values():
            s = TrackedSignal(**row)
            if state and s.state != state:
                continue
            if symbol and s.symbol != symbol:
                continue
            results.append(s)

        # Sort newest first
        results.sort(key=lambda x: x.updated_at, reverse=True)
        return results[:limit]

    def get_signal(self, signal_id: str) -> Optional[TrackedSignal]:
        # Optimize by loading from end until found
        if not self.tracked_signals_path.exists():
            return None
        with open(self.tracked_signals_path, "r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    if data.get("signal_id") == signal_id:
                        return TrackedSignal(**data)
                except json.JSONDecodeError:
                    pass
        return None

    def find_by_fingerprint(self, fingerprint_id: str, active_only: bool = True) -> Optional[TrackedSignal]:
        raw_data = self._load_jsonl(self.tracked_signals_path, limit=5000)
        latest_for_fp = None
        for row in raw_data:
            if row.get("fingerprint_id") == fingerprint_id:
                if latest_for_fp is None or row.get("updated_at") > latest_for_fp.get("updated_at"):
                    latest_for_fp = row

        if latest_for_fp:
            s = TrackedSignal(**latest_for_fp)
            if active_only and s.state not in [SignalLifecycleState.NEW, SignalLifecycleState.ACTIVE, SignalLifecycleState.WATCHING]:
                return None
            return s
        return None

    def append_event(self, event: SignalLifecycleEvent) -> Path:
        return self._append_jsonl(self.events_path, event.model_dump(mode='json'))

    def load_events(self, signal_id: Optional[str] = None, limit: int = 1000) -> List[SignalLifecycleEvent]:
        raw_data = self._load_jsonl(self.events_path, limit=limit*5)
        events = [SignalLifecycleEvent(**row) for row in raw_data]
        if signal_id:
            events = [e for e in events if e.signal_id == signal_id]
        return events[:limit]

    def append_watchlist(self, entry: WatchlistEntry) -> Path:
        return self._append_jsonl(self.watchlist_path, entry.model_dump(mode='json'))

    def load_watchlist(self, active_only: bool = True) -> List[WatchlistEntry]:
        raw_data = self._load_jsonl(self.watchlist_path, limit=5000)
        # Latest by watchlist_id
        latest = {}
        for row in reversed(raw_data):
            latest[row["watchlist_id"]] = row

        results = []
        for row in latest.values():
            e = WatchlistEntry(**row)
            if active_only and not e.active:
                continue
            results.append(e)
        return results

    def append_exit_simulation(self, simulation: ResearchExitSimulation) -> Path:
        return self._append_jsonl(self.simulations_path, simulation.model_dump(mode='json'))

    def load_exit_simulations(self, signal_id: Optional[str] = None, limit: int = 1000) -> List[ResearchExitSimulation]:
        raw_data = self._load_jsonl(self.simulations_path, limit=limit*5)
        sims = [ResearchExitSimulation(**row) for row in raw_data]
        if signal_id:
            sims = [s for s in sims if s.signal_id == signal_id]
        return sims[:limit]

    def save_policy(self, policy: SignalAlertPolicy) -> Path:
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        self.policy_path.write_text(policy.model_dump_json(indent=2), encoding="utf-8")
        return self.policy_path

    def load_policy(self) -> Optional[SignalAlertPolicy]:
        if self.policy_path.exists():
            try:
                return SignalAlertPolicy(**json.loads(self.policy_path.read_text(encoding="utf-8")))
            except Exception as e:
                logger.error(f"Failed to load policy: {e}")
        return None
