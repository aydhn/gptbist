"""Intraday event labels with explicit start (t0) and end (t1) times.

Convention (no look-ahead): the decision is taken at the CLOSE of bar ``t0``;
the position is entered at the OPEN of the NEXT bar. With ``session_bound=True``
an event never crosses the trading-day boundary (no overnight carry): if the
horizon would cross, the exit happens at that day's last bar close. Events with
no next bar inside the session are dropped. Research/paper only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

ISTANBUL_TZ = "Europe/Istanbul"
_COLS = ["t0", "t1", "ret", "label"]


def _day_ids(index: pd.DatetimeIndex) -> np.ndarray:
    """Integer trading-day id per bar (calendar date in Europe/Istanbul)."""
    idx = pd.DatetimeIndex(index)
    if len(idx) == 0:
        return np.array([], dtype=int)
    if idx.tz is None:
        idx = idx.tz_localize(ISTANBUL_TZ)
    else:
        idx = idx.tz_convert(ISTANBUL_TZ)
    return pd.factorize(idx.normalize().tz_localize(None))[0]


def _last_bar_of_day(day: np.ndarray) -> np.ndarray:
    """For each bar position, position of the last bar of its trading day."""
    n = len(day)
    last = np.empty(n, dtype=int)
    cur = n - 1
    for i in range(n - 1, -1, -1):
        if i < n - 1 and day[i] != day[i + 1]:
            cur = i
        last[i] = cur
    return last


def _check_bars(bars: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(bars.index, pd.DatetimeIndex):
        raise TypeError("bars must have a DatetimeIndex")
    if not bars.index.is_monotonic_increasing:
        bars = bars.sort_index()
    return bars


def forward_return_labels(
    bars: pd.DataFrame,
    horizon_bars: int,
    session_bound: bool = True,
    fee_bps: float = 0.0,
) -> pd.DataFrame:
    """Fixed-horizon forward return labels.

    Decision at close of bar i (t0), entry at open of bar i+1, exit at close of
    bar i+horizon_bars (t1). ``fee_bps`` is charged per side (round trip = 2x).
    Returns DataFrame[t0, t1, ret, label] with label = sign(ret) in {-1,0,1}.
    """
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    bars = _check_bars(bars)
    n = len(bars)
    if n < 2:
        return pd.DataFrame(columns=_COLS)
    idx = bars.index
    op = bars["open"].to_numpy(float)
    cl = bars["close"].to_numpy(float)
    day = _day_ids(idx)
    last = _last_bar_of_day(day)

    i = np.arange(n - 1)
    entry = i + 1
    exit_ = i + horizon_bars
    if session_bound:
        valid = day[entry] == day[i]  # a next bar inside the same session
        exit_ = np.minimum(exit_, last[i])
    else:
        valid = exit_ <= n - 1
        exit_ = np.minimum(exit_, n - 1)
    valid &= exit_ >= entry
    i, entry, exit_ = i[valid], entry[valid], exit_[valid]
    ret = cl[exit_] / op[entry] - 1.0 - 2.0 * fee_bps / 1e4
    ok = np.isfinite(ret)
    out = pd.DataFrame(
        {
            "t0": idx[i[ok]],
            "t1": idx[exit_[ok]],
            "ret": ret[ok],
            "label": np.sign(ret[ok]).astype(int),
        }
    )
    return out.reset_index(drop=True)


def triple_barrier_labels(
    bars: pd.DataFrame,
    pt_mult: float,
    sl_mult: float,
    vol_window: int,
    max_horizon_bars: int,
    session_bound: bool = True,
    fee_bps: float = 0.0,
) -> pd.DataFrame:
    """Triple-barrier labels (AFML ch.3) with next-bar-open entry.

    Barrier width = rolling std (``vol_window``) of close-to-close returns known
    at the decision bar. Upper = entry*(1+pt_mult*vol), lower = entry*(1-sl_mult*vol).
    Bars i+1.. are scanned using high/low; if both barriers are hit in the same
    bar the stop-loss is assumed first (conservative). Exit price is the barrier
    price; vertical barrier exits at the close of the last bar (session end if
    ``session_bound``). Returns DataFrame[t0, t1, ret, label, barrier, vol] with
    label in {-1, 0, 1} and barrier in {"pt", "sl", "vertical"}.
    """
    if max_horizon_bars < 1 or vol_window < 2:
        raise ValueError("max_horizon_bars must be >= 1 and vol_window >= 2")
    bars = _check_bars(bars)
    n = len(bars)
    cols = _COLS + ["barrier", "vol"]
    if n < 2:
        return pd.DataFrame(columns=cols)
    idx = bars.index
    op = bars["open"].to_numpy(float)
    hi = bars["high"].to_numpy(float)
    lo = bars["low"].to_numpy(float)
    cl = bars["close"].to_numpy(float)
    vol = bars["close"].pct_change().rolling(vol_window).std().to_numpy(float)
    day = _day_ids(idx)
    last = _last_bar_of_day(day)

    rows = []
    for i in range(n - 1):
        v = vol[i]
        if not np.isfinite(v) or v <= 0:
            continue
        e = i + 1
        if session_bound and day[e] != day[i]:
            continue
        end = min(i + max_horizon_bars, n - 1)
        if session_bound:
            end = min(end, last[i])
        elif i + max_horizon_bars > n - 1:
            continue
        p = op[e]
        up, dn = p * (1 + pt_mult * v), p * (1 - sl_mult * v)
        j, px, label, tag = end, cl[end], 0, "vertical"
        for k in range(e, end + 1):
            if lo[k] <= dn:  # stop first when both touched
                j, px, label, tag = k, dn, -1, "sl"
                break
            if hi[k] >= up:
                j, px, label, tag = k, up, 1, "pt"
                break
        ret = px / p - 1.0 - 2.0 * fee_bps / 1e4
        rows.append((idx[i], idx[j], ret, label, tag, v))
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows, columns=cols)
