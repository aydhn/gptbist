import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from bist_signal_bot.signals.models import WatchlistEntry, SignalPriority
from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.security.claims_guard import UnsafeClaimGuard

logger = logging.getLogger(__name__)

class SignalWatchlistManager:
    def __init__(self, store: SignalStore):
        self.store = store
        self.settings = get_settings()

    def add(self, signal_id: str, notes: Optional[List[str]] = None, tags: Optional[List[str]] = None, confirm: bool = False) -> WatchlistEntry:
        # Note: add does not require confirm natively unless configured
        s = self.store.get_signal(signal_id)
        if not s:
            raise ValueError(f"Signal not found: {signal_id}")

        safe_notes = []
        if notes:
            # check safe claims
            for n in notes:
                 try:
                     UnsafeClaimGuard.validate_text(n)
                     safe_notes.append(n)
                 except Exception as e:
                     logger.warning(f"Unsafe claim detected in note, skipping: {n} - {e}")

        entry = WatchlistEntry(
            watchlist_id=str(uuid.uuid4()),
            signal_id=signal_id,
            symbol=s.symbol,
            strategy_name=s.strategy_name,
            added_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=getattr(self.settings, "SIGNAL_WATCHLIST_DEFAULT_EXPIRY_DAYS", 14)),
            priority=s.priority,
            notes=safe_notes,
            tags=tags or []
        )
        self.store.append_watchlist(entry)

        # update signal state
        s.watchlist = True
        self.store.update_signal(s)

        return entry

    def remove(self, watchlist_id: str, confirm: bool = False) -> WatchlistEntry:
        if not confirm and getattr(self.settings, "SIGNAL_REQUIRE_CONFIRM_FOR_WATCHLIST_REMOVE", True):
            raise ValueError("Confirm flag required to remove from watchlist")

        entries = self.store.load_watchlist(active_only=True)
        target = next((e for e in entries if e.watchlist_id == watchlist_id), None)
        if not target:
            raise ValueError(f"Watchlist entry not found: {watchlist_id}")

        target.active = False
        self.store.append_watchlist(target)

        # update signal
        s = self.store.get_signal(target.signal_id)
        if s:
            s.watchlist = False
            self.store.update_signal(s)

        return target

    def list_active(self, symbol: Optional[str] = None, strategy_name: Optional[str] = None) -> List[WatchlistEntry]:
        entries = self.store.load_watchlist(active_only=True)
        if symbol:
            entries = [e for e in entries if e.symbol == symbol]
        if strategy_name:
            entries = [e for e in entries if e.strategy_name == strategy_name]
        return entries

    def expire_watchlist_entries(self, now: Optional[datetime] = None) -> List[WatchlistEntry]:
        if now is None:
            now = datetime.now(timezone.utc)

        entries = self.store.load_watchlist(active_only=True)
        expired = []
        for e in entries:
            if e.expires_at and e.expires_at < now:
                e.active = False
                self.store.append_watchlist(e)
                expired.append(e)

                # update signal
                s = self.store.get_signal(e.signal_id)
                if s:
                    s.watchlist = False
                    self.store.update_signal(s)

        return expired

    def sync_from_active_signals(self, min_priority: SignalPriority = SignalPriority.NORMAL) -> List[WatchlistEntry]:
        signals = self.store.load_signals(limit=5000)
        added = []
        order = {SignalPriority.LOW: 1, SignalPriority.NORMAL: 2, SignalPriority.HIGH: 3, SignalPriority.CRITICAL: 4}
        min_val = order.get(min_priority, 2)

        for s in signals:
            if not s.watchlist and order.get(s.priority, 0) >= min_val and s.state in ["ACTIVE", "NEW"]:
                 entry = self.add(s.signal_id, tags=["auto-sync"])
                 added.append(entry)
        return added
