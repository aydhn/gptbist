"""Daily-bar event labels (leak-free) with explicit decision/entry/exit dates.

Convention: the decision is taken at the CLOSE of day ``t0`` (features known at
``t0``); the position is entered at the OPEN of the next trading day
(``t_entry``). Horizons are counted in TRADING days (rows of ``bars``). Events
whose exit lies beyond the available data are dropped, never padded, so a label
never depends on bars after its own ``t1`` (appending/changing later bars cannot
change earlier labels). Long-only, gross of costs except for ``fee_bps``
(charged per side, round trip = 2x). Research/paper only; no orders.

Note (BIST daily price limits, +-10%): not modelled. A limit-up/limit-down day
can make the open/barrier price unreachable in practice; barrier fills here are
assumed at the barrier level. Treat results near limit days with caution.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ISTANBUL_TZ = "Europe/Istanbul"
_FWD_COLS = ["t0", "t_entry", "t1", "ret", "entry_price"]
_TB_COLS = ["t0", "t_entry", "t1", "ret", "label", "barrier"]


def _check_bars(bars: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(bars.index, pd.DatetimeIndex):
        raise TypeError("bars must have a DatetimeIndex")
    if not bars.index.is_monotonic_increasing:
        bars = bars.sort_index()
    return bars


def _naive_dates(idx) -> pd.DatetimeIndex:
    """tz-safe calendar-date key (Istanbul local date, tz-naive, midnight)."""
    idx = pd.DatetimeIndex(idx)
    if idx.tz is not None:
        idx = idx.tz_convert(ISTANBUL_TZ).tz_localize(None)
    return idx.normalize()


def forward_return_labels_daily(
    bars: pd.DataFrame,
    horizon_days: int,
    fee_bps: float = 0.0,
    entry: str = "next_open",
) -> pd.DataFrame:
    """Fixed-horizon forward return labels on daily bars.

    ``entry='next_open'``: buy at open of t+1, sell at close of t+horizon_days.
    ``entry='close'`` (optimistic reference): buy at close of t, sell at close of
    t+horizon_days. Returns DataFrame[t0, t_entry, t1, ret, entry_price].
    """
    if horizon_days < 1:
        raise ValueError("horizon_days must be >= 1")
    if entry not in ("next_open", "close"):
        raise ValueError("entry must be 'next_open' or 'close'")
    bars = _check_bars(bars)
    n = len(bars)
    if n < 2:
        return pd.DataFrame(columns=_FWD_COLS)
    idx = bars.index
    op = bars["open"].to_numpy(float)
    cl = bars["close"].to_numpy(float)

    last_t0 = n - 1 - horizon_days  # exit position i+h must exist
    if last_t0 < 0:
        return pd.DataFrame(columns=_FWD_COLS)
    i = np.arange(last_t0 + 1)
    e = i + 1 if entry == "next_open" else i
    x = i + horizon_days
    px = op[e] if entry == "next_open" else cl[e]
    with np.errstate(divide="ignore", invalid="ignore"):
        ret = cl[x] / px - 1.0 - 2.0 * fee_bps / 1e4
    ok = np.isfinite(ret) & np.isfinite(px) & (px > 0)
    i, e, x, px, ret = i[ok], e[ok], x[ok], px[ok], ret[ok]
    return pd.DataFrame(
        {"t0": idx[i], "t_entry": idx[e], "t1": idx[x], "ret": ret, "entry_price": px}
    ).reset_index(drop=True)


def triple_barrier_labels_daily(
    bars: pd.DataFrame,
    pt_mult: float,
    sl_mult: float,
    vol_window: int,
    max_horizon_days: int,
    fee_bps: float = 0.0,
) -> pd.DataFrame:
    """AFML triple-barrier labels on daily bars (long-only).

    Volatility: EWM std (span=vol_window) of daily log close returns up to and
    including t0 (known at the decision). Barriers are set from the entry price
    (open of t0+1): pt = entry*(1+pt_mult*vol), sl = entry*(1-sl_mult*vol).
    Each day from the entry day to t0+max_horizon_days is checked with high/low;
    if both barriers are touched the same day the STOP is assumed first
    (conservative). Otherwise exit at the vertical barrier = close of
    t0+max_horizon_days. Events whose vertical barrier is beyond the data are
    dropped. ``ret`` is net of round-trip ``fee_bps``; ``label`` is +1 (pt),
    -1 (sl), 0 (vertical). Returns DataFrame[t0, t_entry, t1, ret, label, barrier].
    """
    if max_horizon_days < 1:
        raise ValueError("max_horizon_days must be >= 1")
    if vol_window < 2:
        raise ValueError("vol_window must be >= 2")
    if pt_mult <= 0 or sl_mult <= 0:
        raise ValueError("pt_mult and sl_mult must be > 0")
    bars = _check_bars(bars)
    n = len(bars)
    h = max_horizon_days
    if n < h + 1:
        return pd.DataFrame(columns=_TB_COLS)
    idx = bars.index
    op = bars["open"].to_numpy(float)
    hi = bars["high"].to_numpy(float)
    lo = bars["low"].to_numpy(float)
    cl = bars["close"].to_numpy(float)

    with np.errstate(divide="ignore", invalid="ignore"):
        logret = pd.Series(np.log(cl)).diff()
    vol = logret.ewm(span=vol_window, min_periods=vol_window, adjust=True).std().to_numpy()

    i = np.arange(n - h)  # vertical exit position i+h must exist
    entry_px = op[i + 1]
    v = vol[i]
    ok = np.isfinite(v) & (v > 0) & np.isfinite(entry_px) & (entry_px > 0)
    i, entry_px, v = i[ok], entry_px[ok], v[ok]
    if len(i) == 0:
        return pd.DataFrame(columns=_TB_COLS)

    pt = entry_px * (1.0 + pt_mult * v)
    sl = entry_px * (1.0 - sl_mult * v)
    pos = i[:, None] + 1 + np.arange(h)[None, :]  # (m, h) days entry..exit
    hit_pt = hi[pos] >= pt[:, None]
    hit_sl = lo[pos] <= sl[:, None]
    big = h  # sentinel: not hit
    k_pt = np.where(hit_pt.any(axis=1), hit_pt.argmax(axis=1), big)
    k_sl = np.where(hit_sl.any(axis=1), hit_sl.argmax(axis=1), big)

    is_sl = (k_sl < big) & (k_sl <= k_pt)  # stop-first on ties
    is_pt = (k_pt < big) & ~is_sl

    k = np.where(is_sl, k_sl, np.where(is_pt, k_pt, h - 1))
    exit_pos = i + 1 + k
    exit_px = np.where(is_sl, sl, np.where(is_pt, pt, cl[i + h]))
    ret = exit_px / entry_px - 1.0 - 2.0 * fee_bps / 1e4
    label = np.where(is_pt, 1, np.where(is_sl, -1, 0)).astype(int)
    barrier = np.where(is_pt, "pt", np.where(is_sl, "sl", "vertical"))
    good = np.isfinite(ret)
    return pd.DataFrame(
        {
            "t0": idx[i], "t_entry": idx[i + 1], "t1": idx[exit_pos],
            "ret": ret, "label": label, "barrier": barrier,
        }
    )[good].reset_index(drop=True)


def meta_labels(
    primary_signal_bool: pd.Series,
    tb_labels: pd.DataFrame,
    min_ret: float = 0.0,
) -> pd.DataFrame:
    """Meta-labelling target restricted to primary-signal days.

    ``primary_signal_bool`` is indexed by decision date (t0; tz-aware or naive,
    matched on Istanbul calendar date). For each t0 where the signal is True and
    a triple-barrier event exists, ``meta_label`` = 1 if the long trade's ``ret``
    (already net of the fee used when building ``tb_labels``) exceeds
    ``min_ret``, else 0. Returns DataFrame[t0, t1, ret, meta_label].
    """
    cols = ["t0", "t1", "ret", "meta_label"]
    if len(tb_labels) == 0 or len(primary_signal_bool) == 0:
        return pd.DataFrame(columns=cols)
    sig = pd.Series(
        primary_signal_bool.fillna(False).astype(bool).to_numpy(),
        index=_naive_dates(primary_signal_bool.index),
    )
    sig = sig[~sig.index.duplicated(keep="last")]
    keys = _naive_dates(pd.DatetimeIndex(tb_labels["t0"]))
    on = sig.reindex(keys).fillna(False).to_numpy(dtype=bool)
    sub = tb_labels.loc[on, ["t0", "t1", "ret"]].copy()
    sub["meta_label"] = (sub["ret"].to_numpy(float) > min_ret).astype(int)
    return sub.reset_index(drop=True)
