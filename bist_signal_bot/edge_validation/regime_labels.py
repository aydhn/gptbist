"""Causal market-regime labels and exposure scaling. Research/paper only.

Every value at date t uses data <= t only (close-of-day information). To trade
on it, apply the regime from the NEXT session. Rows in the warm-up period
(insufficient history) are omitted, never guessed.
Rule: volatile and/or bear regime => smaller positions, more cash.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

REGIMES = ("calm_bull", "volatile_bull", "calm_bear", "volatile_bear")


def regime_exposure_scale(
    regime_df: pd.DataFrame,
    bear_scale: float = 0.4,
    volatile_scale: float = 0.6,
    breadth: Optional[pd.Series] = None,
    breadth_floor: float = 0.5,
    min_scale: float = 0.05,
) -> pd.Series:
    """Exposure multiplier in (0, 1]: product of bear and volatile scales.

    Needs columns ``trend`` ('bear' scales down) and ``vol`` ('high' scales down).
    Optional ``breadth`` (fraction of stocks above their 200d average, indexed
    by date, causal) further scales exposure: >= 50% -> 1, 0% -> breadth_floor,
    linear in between (aligned by forward-fill; missing -> 1).
    """
    for nm, v in (("bear_scale", bear_scale), ("volatile_scale", volatile_scale),
                  ("breadth_floor", breadth_floor)):
        if not 0 < v <= 1:
            raise ValueError(f"{nm} must be in (0, 1]")
    scale = np.ones(len(regime_df))
    scale = np.where(regime_df["trend"].to_numpy() == "bear", scale * bear_scale, scale)
    scale = np.where(regime_df["vol"].to_numpy() == "high", scale * volatile_scale, scale)
    out = pd.Series(scale, index=regime_df.index, name="exposure_scale")
    if breadth is not None and len(breadth):
        b = breadth.reindex(regime_df.index.union(breadth.index)).ffill().reindex(regime_df.index)
        mult = breadth_floor + (1 - breadth_floor) * np.clip(b / 0.5, 0.0, 1.0)
        out = out * mult.fillna(1.0)
    return out.clip(lower=min_scale, upper=1.0)


def label_regimes(
    index_close: pd.Series,
    vol_window: int = 20,
    trend_window: int = 200,
    vol_lookback: int = 252,
    vol_quantile: float = 0.5,
    neutral_band: float = 0.02,
    bear_scale: float = 0.4,
    volatile_scale: float = 0.6,
) -> pd.DataFrame:
    """Label each day as bull/bear/neutral trend and low/high volatility.

    trend: close vs SMA(trend_window): above by ``neutral_band`` -> bull, below
    -> bear, else neutral. vol: realised std of log returns (vol_window) vs its
    rolling ``vol_quantile`` over ``vol_lookback`` days (causal). ``regime``
    folds neutral into the side of the SMA the close is on.
    Returns DataFrame[date, trend, vol, regime, exposure_scale].
    """
    cols = ["date", "trend", "vol", "regime", "exposure_scale"]
    close = pd.Series(index_close).astype(float)
    close = close[~close.index.duplicated(keep="last")].sort_index()
    close = close.where(close > 0)
    if len(close) == 0:
        return pd.DataFrame(columns=cols)
    sma = close.rolling(trend_window, min_periods=trend_window).mean()
    lr = np.log(close).diff()
    rv = lr.rolling(vol_window, min_periods=vol_window).std()
    thr = rv.rolling(vol_lookback, min_periods=max(vol_window * 2, 2)).quantile(vol_quantile)
    valid = sma.notna() & rv.notna() & thr.notna() & close.notna()
    c, s, r, t = close[valid], sma[valid], rv[valid], thr[valid]
    trend = np.where(c > s * (1 + neutral_band), "bull",
                     np.where(c < s * (1 - neutral_band), "bear", "neutral"))
    vol = np.where(r > t, "high", "low")
    eff_bull = np.where(trend == "neutral", (c >= s).to_numpy(), trend == "bull")
    regime = np.array([
        ("volatile_" if v == "high" else "calm_") + ("bull" if b else "bear")
        for v, b in zip(vol, eff_bull)
    ], dtype=object)
    df = pd.DataFrame({"date": c.index, "trend": trend, "vol": vol, "regime": regime},
                      index=c.index)
    df["exposure_scale"] = regime_exposure_scale(
        pd.DataFrame({"trend": np.where(eff_bull, "bull", "bear"), "vol": vol}, index=c.index),
        bear_scale, volatile_scale,
    ).to_numpy()
    return df.reset_index(drop=True)


def breadth_regime(
    close_matrix: pd.DataFrame,
    short_window: int = 50,
    long_window: int = 200,
    strong: float = 0.6,
    weak: float = 0.4,
) -> pd.DataFrame:
    """Market breadth: fraction of stocks above their 50d / 200d SMA (causal).

    Only stocks with a valid SMA and close count on each date. Returns
    DataFrame[date, pct_above_short, pct_above_long, breadth]; breadth in
    {'strong','mixed','weak'} from the long-window share. Warm-up rows dropped.
    """
    cols = ["date", "pct_above_short", "pct_above_long", "breadth"]
    if close_matrix.empty:
        return pd.DataFrame(columns=cols)
    cm = close_matrix.sort_index().astype(float)

    def share(w: int) -> pd.Series:
        sma = cm.rolling(w, min_periods=w).mean()
        valid = sma.notna() & cm.notna()
        above = (cm > sma) & valid
        cnt = valid.sum(axis=1)
        return above.sum(axis=1) / cnt.where(cnt > 0)

    ps, pl = share(short_window), share(long_window)
    df = pd.DataFrame({"date": cm.index, "pct_above_short": ps.to_numpy(),
                       "pct_above_long": pl.to_numpy()})
    df = df.dropna().reset_index(drop=True)
    pl_v = df["pct_above_long"]
    df["breadth"] = np.where(pl_v >= strong, "strong", np.where(pl_v <= weak, "weak", "mixed"))
    return df
