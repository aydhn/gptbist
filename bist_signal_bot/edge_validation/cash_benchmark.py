"""Cash (policy-rate proxy) benchmark utilities (research only; no real order is ever sent)."""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd


def daily_cash_returns(index, annual_rate: float, withholding: float = 0.0, day_count: int = 365) -> pd.Series:
    """Per-bar cash return, compounding over CALENDAR days elapsed since the previous bar (weekend = 3 days).

    First bar has 1 day by convention. Withholding is applied to the interest of each period."""
    idx = pd.DatetimeIndex(index)
    if len(idx) == 0:
        return pd.Series([], index=idx, dtype=float, name="cash_ret")
    gaps = np.diff(idx.normalize().values).astype("timedelta64[D]").astype(float)
    days = np.concatenate([[1.0], gaps])
    w = min(max(withholding, 0.0), 1.0)
    gross = (1.0 + annual_rate) ** (days / day_count) - 1.0
    return pd.Series(gross * (1.0 - w), index=idx, name="cash_ret")


def daily_cash_returns_series(index, rate_series: pd.Series, withholding: float = 0.0, day_count: int = 365,
                              fallback_rate: Optional[float] = None) -> pd.Series:
    """Like ``daily_cash_returns`` but with a TIME-VARYING annual rate (fraction), e.g. TLREF.

    Causal: the rate accrued over (previous bar, bar] is the last one known at the previous bar (as-of, no look-
    ahead). Bars before the series starts use ``fallback_rate``; without one they raise (never assumed)."""
    idx = pd.DatetimeIndex(index)
    if len(idx) == 0:
        return pd.Series([], index=idx, dtype=float, name="cash_ret")
    rs = pd.Series(rate_series).astype(float).dropna().sort_index()
    rs.index = pd.DatetimeIndex(rs.index).normalize()
    rs = rs[~rs.index.duplicated(keep="last")]
    norm = idx.normalize()
    days = np.concatenate([[1.0], np.diff(norm.values).astype("timedelta64[D]").astype(float)])
    known_at = np.concatenate([[norm[0]], norm[:-1]]) if len(norm) > 1 else np.array([norm[0]])
    pos = np.searchsorted(rs.index.values, pd.DatetimeIndex(known_at).values, side="right") - 1
    vals = rs.to_numpy(float)
    r = np.where(pos >= 0, vals[np.clip(pos, 0, None)], np.nan)
    if np.isnan(r).any():
        if fallback_rate is None:
            raise ValueError("cash rate series does not cover the start of the index and no fallback rate given")
        r = np.where(np.isnan(r), float(fallback_rate), r)
    w = min(max(withholding, 0.0), 1.0)
    gross = (1.0 + r) ** (days / day_count) - 1.0
    return pd.Series(gross * (1.0 - w), index=idx, name="cash_ret")


def cash_equity_curve(index, annual_rate: float, withholding: float = 0.0, day_count: int = 365,
                      initial: float = 1.0) -> pd.Series:
    r = daily_cash_returns(index, annual_rate, withholding, day_count)
    return initial * (1.0 + r).cumprod()


def alpha_over_cash(strategy_returns: pd.Series, cash_returns: pd.Series, periods_per_year: int = 252) -> dict:
    df = pd.concat([strategy_returns.rename("s"), cash_returns.rename("c")], axis=1, join="inner").dropna()
    n = len(df)
    if n < 2:
        return {"n": n, "excess_mean": float("nan"), "excess_sharpe_annual": float("nan"),
                "excess_total": float("nan"), "strategy_total": float("nan"), "cash_total": float("nan")}
    ex = df["s"] - df["c"]
    sd = float(ex.std(ddof=1))
    sharpe = float(ex.mean() / sd * math.sqrt(periods_per_year)) if sd > 0 else float("nan")
    st, ct = float((1 + df["s"]).prod() - 1), float((1 + df["c"]).prod() - 1)
    return {"n": n, "excess_mean": float(ex.mean()), "excess_std": sd, "excess_sharpe_annual": sharpe,
            "excess_total": st - ct, "strategy_total": st, "cash_total": ct,
            "hit_rate_vs_cash": float((ex > 0).mean())}


def real_return(nominal_returns: pd.Series, cpi: Optional[pd.Series] = None, cpi_kind: str = "monthly") -> pd.Series:
    """Deflate nominal returns by CPI inflation (fractions) indexed by period start ('monthly': month start,
    spread over the days of that month; 'annual': year start). No CPI data yet -> raises, never assumes."""
    if cpi is None or len(cpi) == 0:
        raise ValueError("real_return requires a CPI series; no CPI data available (refusing to assume)")
    if cpi_kind not in ("monthly", "annual"):
        raise ValueError("cpi_kind must be 'monthly' or 'annual'")
    idx = pd.DatetimeIndex(nominal_returns.index)
    s = cpi.copy()
    s.index = pd.DatetimeIndex(s.index)
    freq = "M" if cpi_kind == "monthly" else "Y"
    per = s.reindex(idx.to_period(freq).to_timestamp())
    if per.isna().any():
        raise ValueError("CPI series does not cover all periods of nominal_returns")
    per.index = idx
    span = pd.Series(idx.days_in_month if cpi_kind == "monthly" else 365, index=idx)
    daily = (1.0 + per) ** (1.0 / span) - 1.0
    return (1.0 + nominal_returns) / (1.0 + daily) - 1.0
