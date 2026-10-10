"""Causal exposure overlay + integer-lot position construction for the multi-day long-only book.

Research/paper only. No real order sent.

Exposure rule (long-only, no leverage, exposure in [0, 1], remainder in cash earning the cash return):

    exposure_t = min(regime_scale, drawdown_scale, vol_target_scale [, re-entry ramp])

CAUSALITY (the one definition used everywhere): exposure applied to the return of session ``t`` is decided
at the close of session ``t-1`` and uses ONLY data with index <= t-1:
  * regime_scale[t-1] (the regime label at date d is computed from data <= d, see regime_labels.py),
  * the overlaid NAV through t-1 (drawdown vs its running peak),
  * the realised vol of the raw strategy returns over the ``vol_window`` sessions ending t-1.
The same function therefore applies to a backtest NAV and, step by step, to a live paper NAV.

GAP RISK: the ladder reacts to the drawdown measured at the previous close. A single-session loss on the
exposure held that day can still push the overlaid drawdown past ``max_dd`` by at most
``exposure_t * |worst one-day strategy return|`` (documented, tested with a tolerance of one gap day).
After a halt and re-entry the reference peak is reset to the current NAV (full reset), so the drawdown of the
overlaid NAV measured from its ALL-TIME peak can exceed ``max_dd`` across cycles; the report shows that
true maximum drawdown separately (never hidden).

MAPPING TO DailyLossGuard: ``DailyLossGuard`` (risk/daily_loss.py) trips a trailing-drawdown halt at
``RISK_MAX_DRAWDOWN_PCT`` (PERCENT, default 8.0, intraday paper guard, needs reset(confirm=True)). The overlay
key is ``DAILY_OVERLAY_MAX_DD`` (FRACTION, default 0.20 = the user's psychological limit). Both measure a
trailing drawdown from equity peak; the overlay ladder is the soft version that de-risks BEFORE the hard
guard level. If the guard percent is below the overlay max DD the guard would trip first and halt the
paper engine; ``guard_consistency`` returns a warning text in that case (set the guard to >= 100*max_dd for the
multi-day book).

Fail closed: non-finite / <=-100% returns, NaN cash returns beyond the index, or invalid config raise
``ValueError`` instead of guessing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

NO_ORDER = "No real order sent."
HALT_EXPOSURE = 0.10  # ladder exposure at/below which the book is declared halted (all cash) until re-entry


def _cfg(settings: Any, key: str, default: Any) -> Any:
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


@dataclass(frozen=True)
class OverlayConfig:
    max_dd: float = 0.20
    derisk_start_frac: float = 0.5
    floor_frac: float = 0.75
    floor_exposure: float = 0.25
    hysteresis: float = 0.02
    recover_rebound_frac: float = 0.5
    min_halt_days: int = 10
    max_halt_days: int = 60
    ramp_days: int = 10
    target_vol: float = 0.25
    vol_window: int = 20
    missing_regime_scale: float = 1.0
    periods_per_year: int = 252

    def __post_init__(self):
        if not 0 < self.max_dd < 1:
            raise ValueError("max_dd must be in (0,1)")
        if not 0 < self.derisk_start_frac < self.floor_frac < 1:
            raise ValueError("need 0 < derisk_start_frac < floor_frac < 1")
        if not 0 <= self.floor_exposure <= 1:
            raise ValueError("floor_exposure must be in [0,1]")
        if self.hysteresis < 0 or self.recover_rebound_frac <= 0:
            raise ValueError("hysteresis >= 0 and recover_rebound_frac > 0 required")
        if self.min_halt_days < 0 or self.max_halt_days < self.min_halt_days or self.ramp_days < 0:
            raise ValueError("invalid halt/ramp day settings")
        if self.target_vol <= 0 or self.vol_window < 2:
            raise ValueError("target_vol > 0 and vol_window >= 2 required")
        if not 0 <= self.missing_regime_scale <= 1:
            raise ValueError("missing_regime_scale must be in [0,1]")

    @classmethod
    def from_settings(cls, settings: Any = None) -> "OverlayConfig":
        if settings is None:
            from bist_signal_bot.config.settings import get_settings
            settings = get_settings()
        g = lambda k, d: _cfg(settings, k, d)  # noqa: E731
        return cls(max_dd=float(g("DAILY_OVERLAY_MAX_DD", 0.20)),
                   derisk_start_frac=float(g("DAILY_OVERLAY_DERISK_START_FRAC", 0.5)),
                   floor_frac=float(g("DAILY_OVERLAY_FLOOR_FRAC", 0.75)),
                   floor_exposure=float(g("DAILY_OVERLAY_FLOOR_EXPOSURE", 0.25)),
                   hysteresis=float(g("DAILY_OVERLAY_HYSTERESIS", 0.02)),
                   recover_rebound_frac=float(g("DAILY_OVERLAY_RECOVER_REBOUND_FRAC", 0.5)),
                   min_halt_days=int(g("DAILY_OVERLAY_MIN_HALT_DAYS", 10)),
                   max_halt_days=int(g("DAILY_OVERLAY_MAX_HALT_DAYS", 60)),
                   ramp_days=int(g("DAILY_OVERLAY_RAMP_DAYS", 10)),
                   target_vol=float(g("DAILY_OVERLAY_TARGET_VOL", 0.25)),
                   vol_window=int(g("DAILY_OVERLAY_VOL_WINDOW", 20)),
                   missing_regime_scale=float(g("DAILY_OVERLAY_MISSING_REGIME_SCALE", 1.0)))


def guard_consistency(cfg: OverlayConfig, settings: Any = None) -> Optional[str]:
    """Warning text when DailyLossGuard (RISK_MAX_DRAWDOWN_PCT, percent) would trip before the overlay halts."""
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    guard = float(_cfg(settings, "RISK_MAX_DRAWDOWN_PCT", 8.0)) / 100.0
    if guard < cfg.max_dd:
        return (f"RISK_MAX_DRAWDOWN_PCT={guard * 100:.1f}% < overlay max_dd={cfg.max_dd * 100:.1f}%: "
                "DailyLossGuard would halt (manual reset) before the overlay ladder completes.")
    return None


@dataclass
class OverlayResult:
    returns: pd.Series
    exposure: pd.Series
    events: List[Dict[str, Any]] = field(default_factory=list)
    components: Optional[pd.DataFrame] = None  # regime/dd/vol scales actually used
    warnings: List[str] = field(default_factory=list)

    @property
    def nav(self) -> pd.Series:
        return (1.0 + self.returns).cumprod()


def dd_scale(dd: float, cfg: OverlayConfig) -> float:
    """Drawdown ladder: 1 below start; linear to floor_exposure at floor_frac*max_dd; linear to 0 at max_dd."""
    a, b, c = cfg.derisk_start_frac * cfg.max_dd, cfg.floor_frac * cfg.max_dd, cfg.max_dd
    if dd <= a:
        return 1.0
    if dd >= c:
        return 0.0
    if dd <= b:
        return 1.0 - (1.0 - cfg.floor_exposure) * (dd - a) / (b - a)
    return cfg.floor_exposure * (c - dd) / (c - b)


def vol_scale_series(returns: pd.Series, cfg: OverlayConfig) -> pd.Series:
    """min(1, target/realised) known at close of each date (window ending at that date, inclusive)."""
    rv = returns.rolling(cfg.vol_window, min_periods=cfg.vol_window).std(ddof=1) * math.sqrt(cfg.periods_per_year)
    s = (cfg.target_vol / rv.where(rv > 0)).clip(upper=1.0)
    return s.where(rv.notna(), 1.0).where(rv != 0, 1.0)  # warm-up / zero vol -> 1.0 (no data to de-risk on)


def apply_overlay(returns: pd.Series, regime_scale: Optional[pd.Series], cash_returns: pd.Series,
                  cfg: Optional[OverlayConfig] = None, *, use_vol_target: bool = True) -> OverlayResult:
    """Overlay full-exposure strategy ``returns`` (daily, fractions). See module docstring for causality."""
    cfg = cfg or OverlayConfig()
    r = pd.Series(returns).astype(float)
    if len(r) == 0:
        raise ValueError("empty returns")
    if not np.isfinite(r.to_numpy()).all() or (r <= -1.0).any():
        raise ValueError("returns must be finite and > -100% (fail closed)")
    idx = r.index
    if not idx.is_monotonic_increasing or idx.has_duplicates:
        raise ValueError("returns index must be strictly increasing")
    c = pd.Series(cash_returns).astype(float).reindex(idx)
    warns: List[str] = []
    if c.isna().any():
        warns.append(f"{int(c.isna().sum())} cash-return values missing; treated as 0 (conservative)")
        c = c.fillna(0.0)
    if (c <= -1.0).any() or not np.isfinite(c.to_numpy()).all():
        raise ValueError("cash returns must be finite and > -100%")
    # regime scale known at close of d: ffill after the first valid value, warm-up -> missing_regime_scale
    if regime_scale is None:
        reg = pd.Series(1.0, index=idx)
    else:
        rs = pd.Series(regime_scale).astype(float).sort_index()
        rs = rs[~rs.index.duplicated(keep="last")]
        reg = rs.reindex(rs.index.union(idx)).ffill().reindex(idx)
        n_warm = int(reg.isna().sum())
        if n_warm:
            warns.append(f"regime scale missing for first {n_warm} sessions; using {cfg.missing_regime_scale}")
        reg = reg.fillna(cfg.missing_regime_scale).clip(0.0, 1.0)
    vs = vol_scale_series(r, cfg) if use_vol_target else pd.Series(1.0, index=idx)

    n = len(r)
    R, C, REG, VS = r.to_numpy(), c.to_numpy(), reg.to_numpy(), vs.to_numpy()
    out, expo = np.empty(n), np.empty(n)
    comp = np.empty((n, 5))  # regime, dd, vol, ramp, dd_eff
    nav = peak = shadow = 1.0
    halted, halt_days, trough, ramp_left, dd_eff = False, 0, 1.0, 0, 0.0
    events: List[Dict[str, Any]] = []
    prev_expo = 1.0
    for t in range(n):
        d = idx[t]
        if t == 0:  # nothing known before the first session: only warm-up defaults
            reg_t, vs_t = cfg.missing_regime_scale if regime_scale is not None else 1.0, 1.0
        else:
            reg_t, vs_t = float(REG[t - 1]), float(VS[t - 1])
        dd = 1.0 - nav / peak
        if halted:
            halt_days += 1
            rebound = shadow / trough - 1.0
            if (halt_days >= cfg.min_halt_days and rebound >= cfg.recover_rebound_frac * cfg.max_dd) \
                    or halt_days >= cfg.max_halt_days:
                halted, peak, dd, dd_eff, ramp_left = False, nav, 0.0, 0.0, cfg.ramp_days
                events.append({"date": d, "kind": "reenter", "dd": 0.0, "shadow_rebound": float(rebound),
                               "forced": bool(halt_days >= cfg.max_halt_days and
                                              rebound < cfg.recover_rebound_frac * cfg.max_dd)})
        elif dd_scale(dd, cfg) <= HALT_EXPOSURE:  # ladder is (almost) at zero => explicit halt state
            halted, halt_days, trough = True, 0, shadow
            events.append({"date": d, "kind": "halt", "dd": float(dd)})
        # hysteresis: improvements of dd smaller than cfg.hysteresis are not recognised
        if dd <= 0.0 or dd >= dd_eff or (dd_eff - dd) >= cfg.hysteresis:
            dd_eff = dd
        ds = 0.0 if halted else dd_scale(dd_eff, cfg)
        if ramp_left > 0 and not halted:
            k = (cfg.ramp_days - ramp_left + 1) / (cfg.ramp_days + 1)
            ramp = cfg.floor_exposure + (1.0 - cfg.floor_exposure) * k
            ramp_left -= 1
        else:
            ramp = 1.0
        e = max(0.0, min(1.0, reg_t, ds, vs_t, ramp))
        if not halted and prev_expo >= 0.999 and e < 0.999 and ds < 0.999 and dd_eff > 0:
            events.append({"date": d, "kind": "derisk", "dd": float(dd), "exposure": float(e)})
        prev_expo = e
        out[t] = e * R[t] + (1.0 - e) * C[t]
        expo[t] = e
        comp[t] = (reg_t, dd, vs_t, ramp, dd_eff)
        nav *= 1.0 + out[t]
        peak = max(peak, nav)
        shadow *= 1.0 + R[t]
        if halted:
            trough = min(trough, shadow)
    res_r = pd.Series(out, index=idx, name="overlay_ret")
    comp_df = pd.DataFrame(comp, index=idx, columns=["regime_scale", "dd_ref", "vol_scale", "ramp", "dd_eff"])
    return OverlayResult(res_r, pd.Series(expo, index=idx, name="exposure"), events, comp_df, warns)


# --------------------------------------------------------------------------- position construction
@dataclass
class LotPlan:
    shares: Dict[str, int]
    values: Dict[str, float]
    residual_cash: float
    capital: float
    dropped: Dict[str, str] = field(default_factory=dict)  # symbol -> reason
    notes: List[str] = field(default_factory=list)

    @property
    def invested(self) -> float:
        return float(sum(self.values.values()))

    @property
    def n_names(self) -> int:
        return len(self.shares)

    @property
    def message(self) -> str:
        return NO_ORDER


def at_limit_up(prev_close: float, price: float) -> bool:
    """True when ``price`` sits at/above the daily ceiling (cannot be bought reliably). Reuses sessions.daily_price_limits."""
    from bist_signal_bot.intraday.sessions import daily_price_limits
    _, hi = daily_price_limits(float(prev_close))
    return float(price) >= hi - 1e-9


def to_lots(weights: Dict[str, float], prices: Dict[str, float], capital: float, *, max_names: int = 8,
            per_name_cap: float = 0.25, min_order_value: float = 500.0, lot_size: int = 1,
            price_buffer: float = 0.0, blocked: Optional[Callable[[str, float], bool]] = None) -> LotPlan:
    """Integer-share plan for a long-only book. weights are fractions of ``capital`` (sum <= 1, rest cash).

    Steps: validate (fail closed) -> keep the ``max_names`` largest -> cap each at ``per_name_cap`` (excess stays
    cash, not redistributed) -> ``blocked(symbol, price)`` hook (e.g. limit-up/halted; dropped to cash) ->
    floor to lots at price*(1+price_buffer) -> drop orders below ``min_order_value`` -> greedily add one lot to the
    most under-allocated name while it reduces the rounding error and total spend stays <= capital*sum(weights).
    Never spends more than capital: residual_cash = capital - invested >= 0 always.
    """
    if capital <= 0 or not math.isfinite(capital):
        raise ValueError("capital must be positive and finite")
    if max_names < 1 or lot_size < 1 or not 0 < per_name_cap <= 1 or price_buffer < 0 or min_order_value < 0:
        raise ValueError("invalid sizing parameters")
    for s, w in weights.items():
        if not math.isfinite(w) or w < 0:
            raise ValueError(f"weight for {s} must be finite and >= 0 (long-only)")
    if sum(weights.values()) > 1.0 + 1e-9:
        raise ValueError("sum of weights > 1 (no leverage)")
    dropped: Dict[str, str] = {}
    notes: List[str] = []
    ranked = sorted(((s, w) for s, w in weights.items() if w > 0), key=lambda x: (-x[1], x[0]))
    for s, _ in ranked[max_names:]:
        dropped[s] = "beyond_max_names"
    kept = ranked[:max_names]
    target: Dict[str, float] = {}
    for s, w in kept:
        p = prices.get(s)
        if p is None or not math.isfinite(p) or p <= 0:
            dropped[s] = "bad_price"
            continue
        if blocked is not None and blocked(s, float(p)):
            dropped[s] = "blocked_price_limit"
            continue
        if w > per_name_cap:
            notes.append(f"{s}: weight {w:.3f} capped to {per_name_cap:.3f}")
            w = per_name_cap
        target[s] = w * capital
    budget = capital * sum(target.values()) / capital if target else 0.0
    eff = {s: float(prices[s]) * (1.0 + price_buffer) * lot_size for s in target}  # cost per lot
    lots = {s: int(math.floor(target[s] / eff[s] + 1e-12)) for s in target}
    for s in list(lots):
        if lots[s] * eff[s] < min_order_value or lots[s] == 0:
            dropped[s] = "below_min_order_or_zero_lots"
            del lots[s], target[s]
    spent = sum(lots[s] * eff[s] for s in lots)
    while True:  # round-to-nearest under the budget
        best, gain = None, 0.0
        for s in lots:
            err0 = abs(target[s] - lots[s] * eff[s])
            err1 = abs(target[s] - (lots[s] + 1) * eff[s])
            if err1 < err0 and spent + eff[s] <= budget + 1e-9 and (err0 - err1) > gain:
                best, gain = s, err0 - err1
        if best is None:
            break
        lots[best] += 1
        spent += eff[best]
    shares = {s: lots[s] * lot_size for s in lots}
    values = {s: shares[s] * float(prices[s]) for s in shares}
    residual = capital - sum(values.values())
    if residual < -1e-9:  # cannot happen (buffer >= 0); fail closed
        raise AssertionError("lot plan exceeds capital")
    return LotPlan(shares, values, max(residual, 0.0), float(capital), dropped, notes)
