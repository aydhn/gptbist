"""Capacity diagnostics for the daily cross-sectional book (research only; no real order is ever sent).

The cost model uses the t0 ADV (known at decision time). Capacity is judged against the traded value of the ENTRY day
(outcome-side, report only) at several capital levels: participation, share of orders above the participation cap
and the expected cost uplift when the entry-day liquidity (capped by ADV) is used instead of ADV.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.costs_daily import DailyCostModel


def _entry_value(events: pd.DataFrame, ctx) -> np.ndarray:
    if "entry_value_try" in events.columns:
        return events["entry_value_try"].to_numpy(float)
    col = {s: k for k, s in enumerate(ctx.symbols)}
    pos = pd.Series(np.arange(len(ctx.index)), index=ctx.index)
    V = ctx.value.to_numpy(float)
    return np.array([V[int(pos[t]), col[s]] for t, s in zip(events["t_entry"], events["symbol"])], dtype=float)


def capacity_report(events: pd.DataFrame, ctx, capitals: Sequence[float] = (1e5, 1e6, 1e7),
                    cost_model=None, max_participation: float = 0.05) -> dict:
    """{capital: {...}} with participation vs entry-day traded value.

    Keys per capital: n_orders, median/p90/max participation, share_over_cap (participation > max_participation),
    share_entry_value_missing, mean_cost_bps_adv (round trip, t0 ADV), mean_cost_bps_entry (liquidity =
    min(ADV, entry-day value)), cost_uplift_bps (mean difference over orders allowed in both), share_blocked_entry
    (disallowed by the cost model only when entry-day liquidity is used). Order value scales linearly with capital
    (order_value at ``ctx.capital`` x capital/ctx.capital)."""
    out: dict = {}
    if events is None or len(events) == 0:
        return {float(c): {"n_orders": 0} for c in capitals}
    cm = cost_model
    if cm is None:
        try:
            cm = DailyCostModel.from_settings(None)
        except Exception:  # pragma: no cover
            cm = DailyCostModel()
    ev_val = _entry_value(events, ctx)
    adv = events["bar_value_try"].to_numpy(float)
    px = events["price"].to_numpy(float)
    base_ov = events["order_value"].to_numpy(float)
    liq = np.fmin(adv, ev_val)
    liq = np.where(np.isfinite(ev_val), liq, adv)
    for c in capitals:
        ov = base_ov * (float(c) / float(ctx.capital))
        with np.errstate(invalid="ignore", divide="ignore"):
            part = np.where(ev_val > 0, ov / ev_val, np.nan)
        z = np.zeros(len(ov))
        c_adv = -cm.apply_costs(z, px, ov, adv) * 1e4
        c_ent = -cm.apply_costs(z, px, ov, liq) * 1e4
        both = np.isfinite(c_adv) & np.isfinite(c_ent)
        fin = part[np.isfinite(part)]
        out[float(c)] = {
            "n_orders": int(len(ov)),
            "median_participation": float(np.median(fin)) if len(fin) else float("nan"),
            "p90_participation": float(np.quantile(fin, 0.9)) if len(fin) else float("nan"),
            "max_participation": float(fin.max()) if len(fin) else float("nan"),
            "share_over_cap": float(np.mean(np.where(np.isfinite(part), part > max_participation, False))),
            "share_entry_value_missing": float(np.mean(~np.isfinite(ev_val))),
            "mean_cost_bps_adv": float(np.nanmean(c_adv)) if np.isfinite(c_adv).any() else float("nan"),
            "mean_cost_bps_entry": float(np.nanmean(c_ent)) if np.isfinite(c_ent).any() else float("nan"),
            "cost_uplift_bps": float(np.mean(c_ent[both] - c_adv[both])) if both.any() else float("nan"),
            "share_blocked_entry": float(np.mean(np.isfinite(c_adv) & ~np.isfinite(c_ent))),
        }
    return out
