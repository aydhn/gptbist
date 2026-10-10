"""Daily framework: execution semantics (entry fillability, locked-limit exit deferral, NaN-exit carry) and the
causal bar-health mask. Research/paper only. No real order is ever sent.

ONE implementation of the entry/exit rules is used by ``xsection.build_portfolio_events``,
``xsection.benchmark_event_returns`` and ``model_loop.daily_training.build_labels`` (via ``resolve_window``), so labels,
events and the benchmark can never disagree about which names are bought and where they are sold.

Rules (all switchable through ``DailySemantics`` / config keys, see ``config/defaults.py``; ``DAILY_LEGACY_SEMANTICS``
reproduces the pre-audit behaviour):
* Entry at the open of ``t_entry`` is NOT fillable when volume==0, when the open sits at/above the limit-up price
  (prev close * (1+limit), floored to a tick), or when high==low (locked at a limit / no trading range). Policy
  ``cash`` (default: the slot stays in cash), ``next_ranked`` (take the next ranked fillable name), ``flag``
  (keep the event with ``price_limit_flag`` so the cost model disallows it) or ``off``.
* Exit at the close of ``t1`` is NOT possible when the close is locked limit-down (close <= limit-down price and
  close == low): the exit is deferred to the first unlocked session (conservative: the loss of further locked days is
  booked). A NaN exit close (halt) is carried to the next available close instead of dropping the name (dropping
  names with bad outcomes would be look-ahead selection).
* The limit pct is date dependent (``sessions.PRICE_LIMIT_SCHEDULE``; history UNVERIFIED, confirm with Borsa Istanbul).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.intraday import sessions as _ses

ENTRY_POLICIES = ("cash", "next_ranked", "flag", "off")
_FLAT10 = ((date(1900, 1, 1), Decimal("0.10")),)


def _g(settings, key, default):
    if settings is None:
        return default
    try:
        v = getattr(settings, key)
        return default if v is None else v
    except AttributeError:
        return default


@dataclass(frozen=True)
class DailySemantics:
    legacy: bool = False
    entry_policy: str = "cash"
    exit_lock_defer: bool = True
    nan_exit_carry: bool = True
    bar_health: bool = True
    health_tol: float = 0.005
    spike_pct: float = 0.08
    schedule: Optional[tuple] = None  # None -> sessions.PRICE_LIMIT_SCHEDULE

    def __post_init__(self):
        if self.entry_policy not in ENTRY_POLICIES:
            raise ValueError(f"entry_policy must be in {ENTRY_POLICIES}, got {self.entry_policy!r}")

    @classmethod
    def legacy_semantics(cls) -> "DailySemantics":
        """Pre-audit behaviour: flat 10% limit, no fill / lock / carry / health rules."""
        return cls(True, "off", False, False, False, 0.005, 0.08, _FLAT10)

    @classmethod
    def from_settings(cls, settings=None) -> "DailySemantics":
        if bool(_g(settings, "DAILY_LEGACY_SEMANTICS", False)):
            return cls.legacy_semantics()
        sched = _g(settings, "PRICE_LIMIT_SCHEDULE", "")
        return cls(False, str(_g(settings, "DAILY_ENTRY_FILL_POLICY", "cash")),
                   bool(_g(settings, "DAILY_EXIT_LOCK_DEFER", True)), bool(_g(settings, "DAILY_NAN_EXIT_CARRY", True)),
                   bool(_g(settings, "DAILY_BAR_HEALTH", True)), float(_g(settings, "DAILY_BAR_HEALTH_TOL", 0.005)),
                   float(_g(settings, "DAILY_BAR_SPIKE_PCT", 0.08)),
                   _ses.parse_price_limit_schedule(sched) if sched else None)


# ----------------------------------------------------------------------------- limit matrices
def limit_pct_series(index: pd.DatetimeIndex, semantics: DailySemantics) -> pd.Series:
    sched = semantics.schedule or _ses.PRICE_LIMIT_SCHEDULE
    return pd.Series([float(_ses.price_limit_pct(d, sched)) for d in index], index=index)


def limit_matrices(close: pd.DataFrame, pct: pd.Series):
    """(limit_down, limit_up) DataFrames for each session from the previous (forward-filled) close."""
    prev = close.ffill().shift(1)
    lo, hi = _ses.daily_price_limits_array(prev.to_numpy(float), pct.to_numpy(float)[:, None])
    return (pd.DataFrame(lo, index=close.index, columns=close.columns),
            pd.DataFrame(hi, index=close.index, columns=close.columns))


# ----------------------------------------------------------------------------- bar health
BAR_RULES = ("c2c_limit", "gap_limit", "zero_volume", "copy_bar", "spike_revert", "ohlc_inconsistent")


def bar_health_flags(ctx) -> Dict[str, pd.DataFrame]:
    """Per-rule boolean flags (date x symbol, True = BAD bar). Causal: the flag of row t uses rows <= t only
    (spike-and-revert is flagged on the REVERT bar, not retroactively on the spike bar)."""
    sem: DailySemantics = ctx.semantics
    idx, cols = ctx.index, ctx.symbols
    OP, CL, VOL = ctx.open.to_numpy(float), ctx.close.to_numpy(float), ctx.volume.to_numpy(float)
    pct = limit_pct_series(idx, sem).to_numpy(float)[:, None]
    prev = ctx.close.ffill().shift(1).to_numpy(float)
    tol = sem.health_tol
    with np.errstate(invalid="ignore", divide="ignore"):
        c2c = CL / prev - 1.0
        gap = OP / prev - 1.0
        f = {"c2c_limit": np.abs(c2c) > pct + tol, "gap_limit": np.abs(gap) > pct + tol,
             "zero_volume": np.isfinite(CL) & ~(VOL > 0)}
        # copy bar: identical O/H/L/C/V to the previous row (stale vendor copy)
        same = np.zeros_like(CL, dtype=bool)
        arrs = [OP, CL, VOL] + ([ctx.high.to_numpy(float), ctx.low.to_numpy(float)] if ctx.has_hl else [])
        if len(CL) > 1:
            eq = np.ones((len(CL) - 1, CL.shape[1]), dtype=bool)
            for a in arrs:
                eq &= (a[1:] == a[:-1])
            same[1:] = eq & np.isfinite(CL[1:]) & (VOL[1:] > 0)
        f["copy_bar"] = same
        sp = np.zeros_like(CL, dtype=bool)
        if len(CL) > 2:
            a, b = c2c[:-1], c2c[1:]
            two = CL[1:] / np.where(np.isfinite(prev[:-1]), prev[:-1], np.nan) - 1.0
            sp[1:] = (np.abs(a) > sem.spike_pct) & (np.abs(b) > sem.spike_pct) & (a * b < 0) & \
                     (np.abs(two) < sem.spike_pct / 2)
        f["spike_revert"] = sp
        if ctx.has_hl:
            H, L = ctx.high.to_numpy(float), ctx.low.to_numpy(float)
            top, bot = np.fmax(OP, CL), np.fmin(OP, CL)
            f["ohlc_inconsistent"] = (H < top * (1 - 1e-3)) | (L > bot * (1 + 1e-3)) | (L > H)
        else:
            f["ohlc_inconsistent"] = np.zeros_like(CL, dtype=bool)
    return {k: pd.DataFrame(np.nan_to_num(v, nan=0).astype(bool), index=idx, columns=cols) for k, v in f.items()}


def bar_health(ctx) -> pd.DataFrame:
    """Causal health mask (True = healthy / usable). All True when ``semantics.bar_health`` is off."""
    if not ctx.semantics.bar_health:
        return pd.DataFrame(True, index=ctx.index, columns=ctx.symbols)
    bad = np.zeros((len(ctx.index), len(ctx.symbols)), dtype=bool)
    for v in bar_health_flags(ctx).values():
        bad |= v.to_numpy(bool)
    return pd.DataFrame(~bad, index=ctx.index, columns=ctx.symbols)


def bar_health_report(ctx, max_examples: int = 10) -> dict:
    """Counts per rule + first flagged (date, symbol) examples, for reports. Always computed (even if the mask is off)."""
    flags = bar_health_flags(ctx)
    total = int(np.isfinite(ctx.close.to_numpy(float)).sum())
    out = {"enabled": bool(ctx.semantics.bar_health), "n_bars": total, "rules": {}, "examples": []}
    anybad = np.zeros_like(ctx.close.to_numpy(float), dtype=bool)
    for k, v in flags.items():
        out["rules"][k] = int(v.to_numpy().sum())
        anybad |= v.to_numpy(bool)
    out["n_flagged_bars"] = int(anybad.sum())
    out["share_flagged"] = float(anybad.sum() / total) if total else 0.0
    ii, jj = np.nonzero(anybad)
    for a, b in list(zip(ii, jj))[:max_examples]:
        out["examples"].append({"date": str(ctx.index[a].date()), "symbol": ctx.symbols[b],
                                "rules": [k for k, v in flags.items() if bool(v.iat[a, b])]})
    return out


# ----------------------------------------------------------------------------- fills
@dataclass
class Fills:
    base_ok: np.ndarray       # open finite>0 and volume>0 (legacy tradability)
    entry_ok: np.ndarray      # base_ok and not limit-up open / locked bar (per semantics)
    exit_next: np.ndarray     # exit row for a nominal exit at row x (>= x), -1 if never
    locked_down: np.ndarray


def get_fills(ctx) -> Fills:
    c = getattr(ctx, "_fills_cache", None)
    if c is not None:
        return c
    sem: DailySemantics = ctx.semantics
    OP, CL, VOL = ctx.open.to_numpy(float), ctx.close.to_numpy(float), ctx.volume.to_numpy(float)
    n, m = CL.shape
    with np.errstate(invalid="ignore"):
        base = np.isfinite(OP) & (OP > 0) & (VOL > 0)
        LD, LU = ctx.limit_down.to_numpy(float), ctx.limit_up.to_numpy(float)
        if ctx.has_hl:
            H, L = ctx.high.to_numpy(float), ctx.low.to_numpy(float)
            flat = np.isfinite(H) & np.isfinite(L) & (H == L)
            at_low = CL <= L * (1 + 1e-9)
        else:
            flat = np.zeros_like(base)
            at_low = np.ones_like(base)
        up_open = np.isfinite(LU) & (OP >= LU * (1 - 1e-6))
        locked_dn = np.isfinite(LD) & (CL <= LD * (1 + 1e-6)) & at_low & np.isfinite(CL)
    entry_ok = base if (sem.legacy or sem.entry_policy == "off") else (base & ~up_open & ~flat)
    good = np.isfinite(CL)
    pick = good & ~locked_dn if sem.exit_lock_defer else good
    nxt = np.full(m, -1, dtype=np.int64)
    last_fin = np.full(m, -1, dtype=np.int64)
    ex = np.full((n, m), -1, dtype=np.int64)
    for y in range(n - 1, -1, -1):
        nxt = np.where(pick[y], y, nxt)
        last_fin = np.where(good[y] & (last_fin < 0), y, last_fin)
        e_ = np.where(nxt >= 0, nxt, last_fin)
        if not sem.nan_exit_carry:
            e_ = np.where(good[y], e_, -1)
        ex[y] = e_
    f = Fills(base, entry_ok, ex, locked_dn)
    try:
        ctx._fills_cache = f
    except AttributeError:  # pragma: no cover
        pass
    return f


@dataclass
class WindowFills:
    price_ok: np.ndarray      # entry price valid (open finite>0, volume>0)
    entry_ok: np.ndarray      # entry fillable under the semantics
    exit_pos: np.ndarray      # row of the actual exit (-1 = none)
    exit_px: np.ndarray       # close at exit_pos (NaN if none)
    raw: np.ndarray           # exit_px / open[e] - 1 (NaN if no valid entry price / exit)
    ok: np.ndarray            # entry_ok & exit exists & finite raw


def resolve_window(ctx, i: int, e: int, x: int) -> WindowFills:
    """Entry at open of row ``e`` / nominal exit at close of row ``x`` for every symbol (decision row ``i``)."""
    f = get_fills(ctx)
    OP, CL = ctx.open.to_numpy(float), ctx.close.to_numpy(float)
    xp = f.exit_next[x]
    m = len(xp)
    exit_px = np.where(xp >= 0, CL[np.where(xp >= 0, xp, 0), np.arange(m)], np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = exit_px / np.where(f.base_ok[e], OP[e], np.nan) - 1.0
    ok = f.entry_ok[e] & (xp >= 0) & np.isfinite(raw)
    return WindowFills(f.base_ok[e], f.entry_ok[e], xp, exit_px, raw, ok)
