"""Survivorship honesty (pure, cheap, no refits).

yfinance carries no delisted BIST symbols, so every daily-panel result is survivorship-optimistic. The functions here
only re-weight / re-filter EXISTING events by listing age as a SENSITIVITY check; they never claim a numerical
correction of survivorship bias (that bound is not measurable from the data we have).

Listing age = days between the symbol's first valid close in the panel and the event date. For symbols already present
at the panel start this is a LOWER bound (true listing is earlier), so young-symbol exclusion is conservative-ish.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

AGE_FULL_WEIGHT_DAYS_DEFAULT = 750
RECENT_LISTING_DAYS = 730  # 2 years
ANN = 252.0

HONESTY_STATEMENT = ("Delisted symbols absent from free yfinance data: results are survivorship-optimistic; "
                     "true value is lower than reported, bound not measurable")


def first_bar_dates(ctx) -> pd.Series:
    """First valid close date per symbol (NaT if none)."""
    return ctx.close.apply(lambda c: c.first_valid_index())


def count_young_symbols(ctx, min_days: int = RECENT_LISTING_DAYS) -> int:
    """Panel symbols with < ``min_days`` of history up to the last panel date."""
    if ctx is None or not len(getattr(ctx, "index", [])):
        return 0
    first = first_bar_dates(ctx)
    last = pd.Timestamp(ctx.index[-1])
    return int(sum(1 for s in first.index if pd.notna(first[s]) and (last - first[s]).days < min_days))


def _prep(ctx, events, net_col: str) -> Optional[pd.DataFrame]:
    if events is None or len(events) == 0 or "symbol" not in events or "t0" not in events:
        return None
    col = net_col if net_col in events else ("gross_ret" if "gross_ret" in events else None)
    if col is None:
        return None
    first = first_bar_dates(ctx)
    ev = pd.DataFrame({"symbol": events["symbol"].to_numpy(), "t0": pd.to_datetime(events["t0"]).to_numpy(),
                       "r": pd.to_numeric(events[col], errors="coerce").to_numpy(float)})
    ev["first"] = pd.to_datetime(ev["symbol"].map(first))
    ev = ev.dropna(subset=["r"])
    ev["age"] = (pd.to_datetime(ev["t0"]) - ev["first"]).dt.days.astype(float)
    ev["age"] = ev["age"].fillna(0.0).clip(lower=0.0)
    return ev


def _stat(r: np.ndarray, w: np.ndarray, horizon: Optional[int]) -> Dict[str, Any]:
    sw = float(w.sum()) if len(w) else 0.0
    if sw <= 0:
        return {"n_events": 0, "eff_n": 0.0, "mean_net_excess_bps": None, "approx_annual_excess": None}
    m = float((r * w).sum() / sw)
    out = {"n_events": int(len(r)), "eff_n": sw, "mean_net_excess_bps": m * 1e4, "approx_annual_excess": None}
    if horizon and horizon > 0 and m > -1:
        out["approx_annual_excess"] = float((1.0 + m) ** (ANN / horizon) - 1.0)  # compounding of the mean event; approximate
    return out


def _ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or not math.isfinite(a) or not math.isfinite(b) or b <= 1e-9:
        return None
    return float(a / b)


def age_weight_sensitivity(ctx, events, *, full_weight_days: int = AGE_FULL_WEIGHT_DAYS_DEFAULT,
                           net_col: str = "net_ret", horizon: Optional[int] = None) -> Dict[str, Any]:
    """Event mean with weight = min(1, listing_age_days / full_weight_days); young symbols count less."""
    n = max(1, int(full_weight_days))
    ev = _prep(ctx, events, net_col)
    if ev is None or ev.empty:
        return {"full_weight_days": n, "n_events": 0, "unweighted": None, "weighted": None, "retained_fraction": None}
    r = ev["r"].to_numpy(float)
    w = np.minimum(1.0, ev["age"].to_numpy(float) / n)
    base, wt = _stat(r, np.ones(len(r)), horizon), _stat(r, w, horizon)
    return {"full_weight_days": n, "n_events": int(len(r)), "unweighted": base, "weighted": wt,
            "retained_fraction": _ratio(wt["mean_net_excess_bps"], base["mean_net_excess_bps"])}


def exclude_recent_listings_sensitivity(ctx, events, *, min_age_days: int = RECENT_LISTING_DAYS,
                                        net_col: str = "net_ret", horizon: Optional[int] = None) -> Dict[str, Any]:
    """Same statistic excluding events whose symbol first traded < ``min_age_days`` before the event date."""
    ev = _prep(ctx, events, net_col)
    if ev is None or ev.empty:
        return {"min_age_days": int(min_age_days), "n_events": 0, "n_kept": 0, "n_excluded": 0, "unweighted": None,
                "kept": None, "retained_fraction": None, "excluded_symbols": []}
    keep = ev["age"].to_numpy(float) >= min_age_days
    r = ev["r"].to_numpy(float)
    base, kept = _stat(r, np.ones(len(r)), horizon), _stat(r[keep], np.ones(int(keep.sum())), horizon)
    return {"min_age_days": int(min_age_days), "n_events": int(len(r)), "n_kept": int(keep.sum()),
            "n_excluded": int((~keep).sum()), "unweighted": base, "kept": kept,
            "retained_fraction": _ratio(kept["mean_net_excess_bps"], base["mean_net_excess_bps"]),
            "excluded_symbols": sorted(set(ev.loc[~keep, "symbol"].astype(str)))}


def optimism_bound(ctx, events=None, *, full_weight_days: int = AGE_FULL_WEIGHT_DAYS_DEFAULT,
                   recent_days: int = RECENT_LISTING_DAYS, net_col: str = "net_ret",
                   horizon: Optional[int] = None) -> Dict[str, Any]:
    """Summary dict. ``retained_*`` are sensitivity fractions (NOT a survivorship correction)."""
    try:
        aw = age_weight_sensitivity(ctx, events, full_weight_days=full_weight_days, net_col=net_col, horizon=horizon)
        ex = exclude_recent_listings_sensitivity(ctx, events, min_age_days=recent_days, net_col=net_col,
                                                 horizon=horizon)
        young = count_young_symbols(ctx, recent_days)
        err = None
    except Exception as exc:  # never break a report
        aw = ex = None
        young = None
        err = f"{type(exc).__name__}: {exc}"
    n_sym = len(getattr(ctx, "symbols", []) or [])
    return {"statement": HONESTY_STATEMENT, "measurable": False,
            "retained_fraction_age_weighted": None if aw is None else aw.get("retained_fraction"),
            "retained_fraction_excl_recent": None if ex is None else ex.get("retained_fraction"),
            "n_panel_symbols": n_sym, "n_symbols_lt_2y_history": young,
            "age_weighted": aw, "excl_recent_listings": ex, "error": err}


def header_line(sv: Optional[Dict[str, Any]]) -> str:
    """One-line 'İYİMSERLİK SINIRI' header for markdown/text reports."""
    sv = sv or {}

    def _p(x):
        return "n/a" if x is None else f"{x:.0%}"

    return (f"İYİMSERLİK SINIRI: {HONESTY_STATEMENT}. <2y-history symbols: {sv.get('n_symbols_lt_2y_history', 'n/a')}; "
            f"sensitivity retained (age-weighted / ex-recent): {_p(sv.get('retained_fraction_age_weighted'))} / "
            f"{_p(sv.get('retained_fraction_excl_recent'))} (sensitivity only, not a correction)")
