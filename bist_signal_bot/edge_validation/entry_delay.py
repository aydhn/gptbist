"""Entry-delay sensitivity (informational; never part of the gate verdict). No real order is sent.

The model enters at the OPEN of t0+1 (t0 = decision close). ``delayed_entry_report`` recomputes the net event excess
when the entry is instead filled at the CLOSE of t0+``delay_sessions`` (default 1 => the close of the model's own
entry session, i.e. "I could only act after the first session"). The exit is unchanged (``fills_daily.get_fills``
``exit_next``: same locked-limit-down deferral / NaN carry as the model). The EW-universe benchmark leg is recomputed on
the same delayed window over the same point-in-time universe (``universe_mask[t0]``), so the statistic stays an excess.
Costs: the supplied cost model applied to the delayed price / bar value (strategy leg only), like the gate.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.fills_daily import get_fills

NO_ORDER = "No real order sent."


def _net(cost_model, gross, price, order_value, bar_value, flags=None) -> np.ndarray:
    if cost_model is None:
        return np.asarray(gross, dtype=float)
    kw = {}
    if flags is not None and getattr(cost_model, "supports_price_limit_flags", False):
        kw["price_limit_flags"] = np.asarray(flags, dtype=bool)
    return np.asarray(cost_model.apply_costs(np.asarray(gross, float), np.asarray(price, float),
                                             np.asarray(order_value, float), np.asarray(bar_value, float), **kw),
                      dtype=float)


def _bps(x: np.ndarray) -> Optional[float]:
    x = x[np.isfinite(x)]
    return float(x.mean() * 1e4) if len(x) else None


def delayed_entry_report(ctx, selected_trial_events: pd.DataFrame, delay_sessions: int = 1,
                         cost_model=None) -> dict:
    """Pure function: see module docstring. ``selected_trial_events`` = the (benchmark-adjusted) events of the selected
    trial (``gross_ret`` = excess over EW). Returns a JSON-friendly dict."""
    d_s = int(delay_sessions)
    if d_s < 0:
        raise ValueError("delay_sessions must be >= 0")
    ev = selected_trial_events
    out = {"delay_sessions": d_s, "entry": "close of t0+delay", "n_events": 0 if ev is None else int(len(ev)),
           "n_valid": 0, "base_net_excess_mean_bps": None, "net_excess_mean_bps": None, "delta_bps": None,
           "edge_retained_fraction": None, "no_order": NO_ORDER}
    if ev is None or len(ev) == 0:
        return out
    f = get_fills(ctx)
    pos = pd.Series(np.arange(len(ctx.index)), index=ctx.index)
    col = pd.Series(np.arange(len(ctx.symbols)), index=ctx.symbols)
    CL, VOL = ctx.close.to_numpy(float), ctx.volume.to_numpy(float)
    M = ctx.universe_mask.to_numpy(bool)
    n_rows = len(ctx.index)
    i_ = pos[ev["t0"]].to_numpy()
    x_ = pos[ev["t1"]].to_numpy()
    j_ = col[ev["symbol"]].to_numpy()
    scale = (ev["exposure_scale"].to_numpy(float) if "exposure_scale" in ev else np.ones(len(ev)))
    cache: dict = {}
    gross = np.full(len(ev), np.nan)
    dprice = np.full(len(ev), np.nan)
    dval = np.full(len(ev), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        for k in range(len(ev)):
            i, x, j = int(i_[k]), int(x_[k]), int(j_[k])
            d = i + d_s
            if d >= n_rows:
                continue
            key = (i, x)
            if key not in cache:
                xp = f.exit_next[x]
                m = len(xp)
                exit_px = np.where(xp >= 0, CL[np.where(xp >= 0, xp, 0), np.arange(m)], np.nan)
                ok = (M[i] & np.isfinite(CL[d]) & (CL[d] > 0) & (VOL[d] > 0) & (xp > d) & np.isfinite(exit_px))
                raw = np.where(ok, exit_px / np.where(CL[d] > 0, CL[d], np.nan) - 1.0, np.nan)
                ew = float(np.nanmean(raw)) if np.isfinite(raw).any() else 0.0
                cache[key] = (raw, ew)
            raw, ew = cache[key]
            if not np.isfinite(raw[j]):
                continue  # entry close not fillable / exit before the delayed entry
            gross[k] = scale[k] * (raw[j] - ew)
            dprice[k], dval[k] = CL[d, j], CL[d, j] * VOL[d, j]
    ov = ev["order_value"].to_numpy(float)
    flags = ev["price_limit_flag"].to_numpy(bool) if "price_limit_flag" in ev else None
    base = _net(cost_model, ev["gross_ret"].to_numpy(float), ev["price"].to_numpy(float), ov,
                ev["bar_value_try"].to_numpy(float), flags)
    valid = np.isfinite(gross)
    delayed = np.full(len(ev), np.nan)
    if valid.any():
        delayed[valid] = _net(cost_model, gross[valid], dprice[valid], ov[valid], dval[valid])
    # like-for-like: baseline restricted to the events that remain fillable under the delay
    b_all, b_cmp, d_cmp = _bps(base), _bps(np.where(valid, base, np.nan)), _bps(delayed)
    out.update({"n_valid": int(np.isfinite(delayed).sum()), "base_net_excess_mean_bps": b_all,
                "base_net_excess_mean_bps_same_events": b_cmp, "net_excess_mean_bps": d_cmp,
                "delta_bps": None if d_cmp is None or b_cmp is None else d_cmp - b_cmp,
                "edge_retained_fraction": (float(d_cmp / b_cmp) if d_cmp is not None and b_cmp and b_cmp > 0
                                           else None)})
    return out
