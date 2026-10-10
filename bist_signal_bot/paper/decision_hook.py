"""Per-order hook of risk.decision.DecisionLayer into the paper trading path.

Only active when RUNTIME_USE_DECISION_LAYER is True. Every ENTRY is routed through
DecisionLayer.decide(); the resulting quantity never exceeds the legacy sizing. Exits are
reduce-only and bypass. Realized PnL of closed trades is fed to DailyLossGuard.

Paper/simulation only. No real order sent.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, Callable, Optional

from bist_signal_bot.intraday.sessions import IST, to_istanbul

logger = logging.getLogger(__name__)
NO_ORDER = "No real order sent."


def _cfg(settings: Any, key: str, default: Any) -> Any:
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


def decision_layer_enabled(settings: Any) -> bool:
    return bool(_cfg(settings, "RUNTIME_USE_DECISION_LAYER", False))


def overlay_enabled(settings: Any) -> bool:
    return bool(_cfg(settings, "RUNTIME_USE_DAILY_OVERLAY", False))


def _bars_per_day(timeframe: str) -> float:
    tf = str(timeframe or "1d").strip().lower()
    try:
        if tf.endswith("m") and tf[:-1].isdigit():
            return max(1.0, 510.0 / int(tf[:-1]))
        if tf.endswith("h") and tf[:-1].isdigit():
            return max(1.0, 510.0 / (60 * int(tf[:-1])))
    except Exception:
        pass
    return 1.0


def bar_timestamp(df: Any) -> Optional[datetime]:
    try:
        idx = df.index[-1]
        if hasattr(idx, "to_pydatetime"):
            return idx.to_pydatetime()
        if isinstance(idx, datetime):
            return idx
        for col in ("timestamp", "datetime", "date", "Date"):
            if col in df.columns:
                v = df.iloc[-1][col]
                return v.to_pydatetime() if hasattr(v, "to_pydatetime") else v
    except Exception:
        pass
    return None


def _trade_exit_ist(trade: Any) -> Optional[datetime]:
    t = getattr(trade, "exit_time", None)
    if t is None:
        return None
    if hasattr(t, "to_pydatetime"):
        t = t.to_pydatetime()
    if t.tzinfo is None:
        t = t.replace(tzinfo=UTC)
    return t.astimezone(IST)


class PaperDecisionHook:
    def __init__(self, settings: Any, guard: Any = None, clock: Optional[Callable[[], datetime]] = None,
                 log_path: Any = None):
        self.settings = settings
        self._guard = guard
        self.clock = clock
        self._log_path = log_path
        self._layer = None
        self._overlay = None
        self._fed: Optional[set] = None  # closed-trade ids already fed to the guard

    # ------------------------------------------------------------ wiring
    @property
    def guard(self):
        if self._guard is None:
            from bist_signal_bot.risk.daily_loss import DailyLossGuard
            self._guard = DailyLossGuard(self.settings)
        return self._guard

    @guard.setter
    def guard(self, g):
        if g is not self._guard:
            self._guard = g
            self._layer = None

    @property
    def layer(self):
        if self._layer is None:
            from bist_signal_bot.risk.decision import DecisionLayer
            from bist_signal_bot.risk.portfolio_limits import PortfolioLimits
            from bist_signal_bot.risk.sizing_intraday import IntradaySizer
            self._layer = DecisionLayer(self.settings, IntradaySizer(self.settings),
                                        PortfolioLimits(self.settings), self.guard)
        return self._layer

    def now(self, df: Any = None, metadata: Optional[dict] = None) -> datetime:
        md = metadata or {}
        if md.get("decision_clock") == "bar" and df is not None:
            ts = bar_timestamp(df)
            if ts is not None:
                return to_istanbul(ts)
        v = md.get("decision_now")
        if v is not None:
            if isinstance(v, str):
                v = datetime.fromisoformat(v)
            return to_istanbul(v)
        if self.clock is not None:
            return to_istanbul(self.clock())
        return datetime.now(IST)

    # ------------------------------------------------------------ context
    def build_context(self, symbol: str, df: Any, state: Any, timeframe: str, now: datetime,
                      signal: Any = None) -> dict:
        price = float(df.iloc[-1]["close"])
        bpd = _bars_per_day(timeframe)
        vol = None
        try:
            closes = df["close"].astype(float).tail(61)
            rets = (closes / closes.shift(1)).apply(math.log).dropna()
            if len(rets) >= 20:
                vol = float(rets.std()) * math.sqrt(252.0 * bpd)
        except Exception:
            vol = None
        if vol is None or not math.isfinite(vol) or vol <= 0:
            vol = float(_cfg(self.settings, "PAPER_DECISION_DEFAULT_VOL_ANNUAL", 0.60))
        vol = max(vol, 0.05)

        bar_value = adv = None
        try:
            if "volume" in df.columns:
                val = (df["close"].astype(float) * df["volume"].astype(float)).tail(20)
                if len(val) >= 5 and math.isfinite(float(val.mean())):
                    bar_value = float(val.iloc[-1])
                    adv = float(val.mean()) * bpd
        except Exception:
            bar_value = adv = None
        if adv is None:  # conservative default: unknown liquidity is treated as illiquid
            adv = float(_cfg(self.settings, "PAPER_DECISION_DEFAULT_ADV_TRY", 0.0))
        if bar_value is None:
            bar_value = float(_cfg(self.settings, "PAPER_DECISION_DEFAULT_BAR_VALUE_TRY", 0.0))

        try:
            from bist_signal_bot.edge_validation.costs import tick_size
            spread_bps = float(tick_size(price)) / price * 1e4
        except Exception:
            spread_bps = float(_cfg(self.settings, "PAPER_DECISION_DEFAULT_SPREAD_BPS", 20.0))

        open_positions = [
            {"symbol": p.symbol, "qty": p.quantity, "price": p.last_price, "notional": float(p.market_value)}
            for p in state.positions if p.is_open
        ]
        return {"price": price, "equity": float(state.account.equity), "cash": float(state.account.cash),
                "open_positions": open_positions, "asset_vol_annual": vol, "adv_value_try": adv,
                "bar_value_try": bar_value, "spread_bps": spread_bps, "edge_stats": None, "now": now}

    @staticmethod
    def _signal_view(symbol: str, sig: Any, price: float) -> Any:
        md = {}
        for attr in ("metadata", "params"):
            v = getattr(sig, attr, None)
            if isinstance(v, dict):
                md = {**v, **md}
        conf = getattr(sig, "confidence", None)
        try:
            conf = float(conf)
            conf = conf / 100.0 if conf > 1.0 else conf
        except Exception:
            conf = 1.0
        edge = md.get("expected_edge_bps")
        return SimpleNamespace(symbol=symbol, confidence=conf, price=price,
                               expected_edge_bps=None if edge is None else float(edge), reduce_only=False)

    # ------------------------------------------------------------ entry gate
    def gate_entry(self, symbol: str, sig: Any, df: Any, state: Any, legacy_qty: float,
                   timeframe: str, metadata: Optional[dict] = None) -> tuple[float, dict]:
        """Return (final_qty, record). final_qty == 0 means rejected."""
        now = self.now(df, metadata)
        rec: dict[str, Any] = {"ts": now.isoformat(), "symbol": symbol, "side": "BUY", "legacy_qty": legacy_qty,
                               "allowed": False, "qty": 0, "notional": 0.0, "reasons": [],
                               "binding_constraint": None, "note": NO_ORDER}
        try:
            ctx = self.build_context(symbol, df, state, timeframe, now, sig)
            dec = self.layer.decide(self._signal_view(symbol, sig, ctx["price"]), ctx)
            rec["reasons"] = list(dec.reasons)
            rec["binding_constraint"] = getattr(dec.sizing, "method", None)
            rec["guard_state"] = (dec.guard_state or {}).get("state")
            qty = 0.0
            if dec.allowed:
                qty = min(float(dec.qty), float(legacy_qty), math.floor(ctx["cash"] / ctx["price"]))
                if qty <= 0:
                    rec["reasons"].append("no_cash_or_legacy_qty_zero")
                    qty = 0.0
            if qty > 0 and overlay_enabled(self.settings):
                qty = self._apply_overlay(qty, state, now, rec)
            rec["allowed"] = qty > 0 and dec.allowed
            rec["qty"] = qty
            rec["notional"] = qty * ctx["price"]
            if not rec["allowed"]:
                qty = 0.0
        except Exception as e:  # fail closed
            logger.error("decision hook error for %s: %s", symbol, e)
            rec["reasons"] = [f"decision_error:{e}"]
            qty = 0.0
        self.log(rec)
        return qty, rec

    @property
    def overlay(self):
        if self._overlay is None:
            from pathlib import Path
            from bist_signal_bot.risk.overlay_gate import OverlayGate
            path = None
            try:
                if self._log_path is not None:
                    path = Path(self._log_path).parent / "overlay_nav.json"
                else:
                    from bist_signal_bot.storage.paths import get_data_dir
                    path = get_data_dir(self.settings) / "paper" / "overlay_nav.json"
            except Exception:
                path = None
            self._overlay = OverlayGate(self.settings, path=path)
        return self._overlay

    def _apply_overlay(self, qty: float, state: Any, now: datetime, rec: dict) -> float:
        """Entries only: scale qty by the daily overlay, rounded DOWN to whole shares, never up."""
        try:
            gate = self.overlay
            gate.record(now, float(state.account.equity))
            res = gate.current_scale(now)
        except Exception as e:  # fail closed to the conservative scale
            logger.error("overlay hook error for %s: %s", rec.get("symbol"), e)
            from bist_signal_bot.risk.overlay_gate import ERROR_SCALE, OverlayGateResult
            res = OverlayGateResult(ERROR_SCALE, [f"overlay_error:{e}"])
        scale = max(0.0, min(1.0, float(res.scale)))
        new_qty = float(min(qty, math.floor(qty * scale + 1e-9)))
        rec["overlay"] = {**res.to_dict(), "qty_before": qty, "qty_after": new_qty}
        if new_qty < qty:
            rec["reasons"].append(f"overlay_scale:{scale:.3f}")
            if new_qty <= 0:
                rec["reasons"].append("overlay_scale")
        return new_qty

    def log(self, rec: dict) -> None:
        try:
            path = self._log_path
            if path is None:
                from bist_signal_bot.storage.paths import get_data_dir
                path = get_data_dir(self.settings) / "paper" / "decisions.jsonl"
            from pathlib import Path
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            logger.debug("decision log failed: %s", e)

    @staticmethod
    def record_into(result: Any, rec: dict) -> None:
        md = result.metadata
        md.setdefault("decisions", []).append(rec)
        counter = md.setdefault("rejection_reasons", {})
        if not rec["allowed"]:
            for r in rec["reasons"]:
                key = str(r).split(":")[0]
                counter[key] = counter.get(key, 0) + 1

    # ------------------------------------------------------------ guard feed
    def realized_today(self, state: Any, now: datetime) -> float:
        day = to_istanbul(now).date()
        tot = 0.0
        for t in state.trades:
            ex = _trade_exit_ist(t)
            if t.status == "CLOSED" and ex is not None and ex.date() == day and t.net_pnl is not None:
                tot += float(t.net_pnl)
        return tot

    def sync_guard(self, state: Any, now: Optional[datetime] = None) -> None:
        """Feed equity and realized PnL (closed trades dated today, Istanbul) to the guard.

        First call seeds from existing closed trades; later calls feed each newly closed
        trade individually so the consecutive-loss counter works. Best-effort.
        """
        try:
            now = to_istanbul(now) if now is not None else self.now()
            g = self.guard
            equity = float(state.account.equity)
            closed = [t for t in state.trades if t.status == "CLOSED" and t.net_pnl is not None]
            if self._fed is None:
                self._fed = {t.trade_id for t in closed}
                g.update(equity, self.realized_today(state, now), now)
                return
            new = sorted((t for t in closed if t.trade_id not in self._fed),
                         key=lambda t: _trade_exit_ist(t) or now)
            for t in new:
                self._fed.add(t.trade_id)
                running = float(g.state.get("realized_pnl_today") or 0.0) + float(t.net_pnl)
                g.update(equity, running, now)
            if not new:
                g.update(equity, float(g.state.get("realized_pnl_today") or 0.0), now)
        except Exception as e:
            logger.warning("guard sync failed: %s", e)
