"""Daily-loss / consecutive-loss / drawdown guard (paper/research only).

Tracks one Istanbul trading day at a time. On a trip the guard moves to HALTED_FOR_DAY:
new entries are blocked, exits/flattening stay allowed. The PAPER kill switch is engaged
(only when it is not already engaged by someone else) so the paper engine stops opening
positions. Daily-loss and consecutive-loss trips auto-reset at the next trading-day open;
a drawdown trip (or a corrupt state file) requires an explicit ``reset(confirm=True)``.
A manually engaged kill switch is never cleared by this module.

No real order sent.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from bist_signal_bot.intraday.sessions import IST, is_trading_day, session_bounds, to_istanbul

logger = logging.getLogger(__name__)

ACTIVE = "ACTIVE"
HALTED_FOR_DAY = "HALTED_FOR_DAY"

TRIP_DAILY_LOSS = "daily_loss"
TRIP_CONSECUTIVE = "consecutive_losses"
TRIP_DRAWDOWN = "drawdown"
TRIP_CORRUPT = "corrupt_state"
_AUTO_RESET_KINDS = (TRIP_DAILY_LOSS, TRIP_CONSECUTIVE)

GUARD_ACTOR = "risk_daily_loss_guard"
NO_ORDER = "No real order sent."
_EPS = 1e-9


def _cfg(settings: Any, key: str, default: Any) -> Any:
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


class DailyLossGuard:
    def __init__(self, settings: Any, state_path: Optional[Path] = None,
                 clock: Optional[Callable[[], datetime]] = None,
                 kill_switch: Any = None, audit: Any = None):
        self.settings = settings
        self._clock = clock or (lambda: datetime.now(IST))
        if state_path is None:
            from bist_signal_bot.storage.paths import get_risk_state_dir
            state_path = get_risk_state_dir(settings) / "daily_loss_state.json"
        self.state_path = Path(state_path)
        self._kill_switch = kill_switch
        self._audit = audit
        self.max_daily_loss_pct = float(_cfg(settings, "RISK_MAX_DAILY_LOSS_PCT", 2.0))
        self.max_consecutive = int(_cfg(settings, "RISK_MAX_CONSECUTIVE_LOSSES", 6))
        self.max_drawdown_pct = float(_cfg(settings, "RISK_MAX_DRAWDOWN_PCT", 8.0))
        self.state: dict[str, Any] = self._load()

    # ---------------------------------------------------------------- plumbing
    def _now(self, now: Optional[datetime]) -> datetime:
        return to_istanbul(now if now is not None else self._clock())

    @staticmethod
    def _fresh() -> dict[str, Any]:
        return {"state": ACTIVE, "day": None, "start_equity": None, "equity": None,
                "peak_equity": None, "day_peak_equity": None, "realized_pnl_today": 0.0,
                "consecutive_losses": 0, "max_intraday_drawdown_pct": 0.0,
                "trip_kind": None, "trip_reason": None, "tripped_at": None,
                "tripped_day": None, "ks_engaged_by_guard": False}

    def _load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._fresh()
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("state") not in (ACTIVE, HALTED_FOR_DAY):
                raise ValueError("bad state schema")
            st = self._fresh()
            st.update(data)
            return st
        except Exception as e:  # fail closed
            logger.error("Corrupt daily loss state %s (%s); failing closed (HALTED).", self.state_path, e)
            st = self._fresh()
            st.update({"state": HALTED_FOR_DAY, "trip_kind": TRIP_CORRUPT,
                       "trip_reason": f"corrupt state file: {e}"})
            return st

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.state_path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.state_path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    @property
    def kill_switch(self):
        if self._kill_switch is None:
            from bist_signal_bot.security.kill_switch import KillSwitchManager
            from bist_signal_bot.storage.paths import get_data_dir
            self._kill_switch = KillSwitchManager(self.settings, get_data_dir(self.settings))
        return self._kill_switch

    def _audit_event(self, etype_name: str, message: str, level: str, meta: dict) -> None:
        try:
            if self._audit is None:
                from bist_signal_bot.core.audit import AuditLogger
                self._audit = AuditLogger(self.settings)
            from bist_signal_bot.core.audit import AuditEvent, AuditEventType
            meta = dict(meta, no_real_order_sent=True)
            self._audit.log_event(AuditEvent(AuditEventType[etype_name], message, level=level, metadata=meta))
        except Exception as e:  # audit must never break risk control
            logger.warning("guard audit failed: %s", e)

    # ---------------------------------------------------------------- kill switch
    def _engage_kill_switch(self, reason: str) -> None:
        try:
            from bist_signal_bot.security.models import KillSwitchScope
            ks = self.kill_switch
            if ks.is_active(KillSwitchScope.PAPER):
                return  # someone else (or us earlier) already stopped paper; do not overwrite
            ks.activate([KillSwitchScope.PAPER], reason=f"risk guard: {reason}", activated_by=GUARD_ACTOR)
            self.state["ks_engaged_by_guard"] = True
        except Exception as e:
            logger.error("could not engage kill switch: %s", e)

    def _release_kill_switch_if_ours(self) -> None:
        if not self.state.get("ks_engaged_by_guard"):
            return
        try:
            st = self.kill_switch.load_state()
            if st.enabled and st.activated_by == GUARD_ACTOR:
                self.kill_switch.deactivate(confirm=True)
        except Exception as e:
            logger.error("could not release kill switch: %s", e)
        self.state["ks_engaged_by_guard"] = False

    def kill_switch_active(self) -> bool:
        try:
            from bist_signal_bot.security.models import KillSwitchScope
            return bool(self.kill_switch.is_active(KillSwitchScope.PAPER))
        except Exception:
            return True  # fail closed

    # ---------------------------------------------------------------- day handling
    def _maybe_roll(self, now: datetime) -> None:
        day = now.date().isoformat()
        st = self.state
        halted = st["state"] == HALTED_FOR_DAY
        if halted and st["trip_kind"] in _AUTO_RESET_KINDS and st.get("tripped_day") \
                and day > st["tripped_day"] and is_trading_day(now.date()):
            bounds = session_bounds(now.date())
            if bounds and now >= bounds[0]:
                self._release_kill_switch_if_ours()
                self._audit_event("RISK_GUARD_RESET", "Daily loss guard auto-reset at trading-day open",
                                  "INFO", {"previous_trip": st["trip_kind"], "day": day})
                keep_peak = st.get("peak_equity")
                self.state = self._fresh()
                self.state["peak_equity"] = keep_peak
                self.state["day"] = day
                self._save()
                return
        if st["day"] != day and (not halted):
            # new calendar day while active: start a new accounting day
            peak = st.get("peak_equity")
            self.state = self._fresh()
            self.state["peak_equity"] = peak
            self.state["day"] = day
            self._save()

    # ---------------------------------------------------------------- public API
    def update(self, equity: float, realized_pnl_today: float = 0.0, now: Optional[datetime] = None) -> dict[str, Any]:
        now = self._now(now)
        self._maybe_roll(now)
        st = self.state
        equity = float(equity)
        if st["day"] is None:
            st["day"] = now.date().isoformat()
        if st["day"] != now.date().isoformat():
            # halted across days and not eligible for reset yet: keep tripped state, track equity only
            st["equity"] = equity
            self._save()
            return self.snapshot()
        if st["start_equity"] is None:
            st["start_equity"] = equity
            st["day_peak_equity"] = equity
        prev_realized = float(st.get("realized_pnl_today") or 0.0)
        realized = float(realized_pnl_today)
        delta = realized - prev_realized
        if delta < -_EPS:
            st["consecutive_losses"] = int(st["consecutive_losses"]) + 1
        elif delta > _EPS:
            st["consecutive_losses"] = 0
        st["realized_pnl_today"] = realized
        st["equity"] = equity
        st["peak_equity"] = max(float(st["peak_equity"]), equity) if st["peak_equity"] is not None else equity
        st["day_peak_equity"] = max(float(st["day_peak_equity"] or equity), equity)
        if st["day_peak_equity"] > 0:
            dd_day = (st["day_peak_equity"] - equity) / st["day_peak_equity"] * 100.0
            st["max_intraday_drawdown_pct"] = max(float(st["max_intraday_drawdown_pct"]), dd_day)

        if st["state"] == ACTIVE:
            self._evaluate_trip(now)
        self._save()
        return self.snapshot()

    def record_trade(self, pnl: float, now: Optional[datetime] = None) -> None:
        """Convenience: feed one closed trade (updates realized PnL, equity unchanged unless known)."""
        eq = self.state.get("equity")
        self.update(eq if eq is not None else 0.0,
                    float(self.state.get("realized_pnl_today") or 0.0) + float(pnl), now)

    def _evaluate_trip(self, now: datetime) -> None:
        st = self.state
        start, eq, peak = st["start_equity"], st["equity"], st["peak_equity"]
        if start and start > 0:
            loss_pct = (start - eq) / start * 100.0
            if loss_pct >= self.max_daily_loss_pct - _EPS:
                return self._trip(TRIP_DAILY_LOSS, f"daily loss {loss_pct:.2f}% >= {self.max_daily_loss_pct:.2f}%", now)
        if int(st["consecutive_losses"]) >= self.max_consecutive:
            return self._trip(TRIP_CONSECUTIVE,
                              f"{st['consecutive_losses']} consecutive losses >= {self.max_consecutive}", now)
        if peak and peak > 0:
            dd = (peak - eq) / peak * 100.0
            if dd >= self.max_drawdown_pct - _EPS:
                return self._trip(TRIP_DRAWDOWN, f"drawdown {dd:.2f}% >= {self.max_drawdown_pct:.2f}%", now)

    def _trip(self, kind: str, reason: str, now: datetime) -> None:
        st = self.state
        st.update({"state": HALTED_FOR_DAY, "trip_kind": kind, "trip_reason": reason,
                   "tripped_at": now.isoformat(), "tripped_day": now.date().isoformat()})
        self._engage_kill_switch(reason)
        logger.warning("Risk guard TRIPPED (%s): %s. %s", kind, reason, NO_ORDER)
        self._save()
        self._audit_event("RISK_GUARD_TRIPPED", f"Risk guard tripped: {reason}", "WARNING",
                          {"kind": kind, "reason": reason, "equity": st["equity"],
                           "start_equity": st["start_equity"], "peak_equity": st["peak_equity"]})

    def can_open_new_position(self, now: Optional[datetime] = None) -> tuple[bool, str]:
        now = self._now(now)
        self._maybe_roll(now)
        st = self.state
        if st["state"] == HALTED_FOR_DAY:
            return False, f"guard_halted:{st['trip_kind']}:{st['trip_reason']}"
        if self.kill_switch_active():
            return False, "kill_switch_active"
        return True, "ok"

    def reset(self, confirm: bool = False, equity: Optional[float] = None, now: Optional[datetime] = None) -> dict[str, Any]:
        if not confirm:
            raise ValueError("reset requires confirm=True")
        now = self._now(now)
        prev = self.state.get("trip_kind")
        self._release_kill_switch_if_ours()
        eq = equity if equity is not None else self.state.get("equity")
        self.state = self._fresh()
        self.state["day"] = now.date().isoformat()
        if eq is not None:
            self.state["start_equity"] = self.state["equity"] = float(eq)
            self.state["peak_equity"] = self.state["day_peak_equity"] = float(eq)
        self._save()
        self._audit_event("RISK_GUARD_RESET", "Daily loss guard manually reset", "INFO", {"previous_trip": prev})
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        s = dict(self.state)
        s["no_real_order_sent"] = True
        return s
