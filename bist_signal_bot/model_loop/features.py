"""Causal intraday features + labelled panel. Feature at bar t uses data <= t only.

Decision convention matches edge_validation.labels: decision at the CLOSE of bar t0,
entry at the next bar open. Research/paper only; no orders are ever sent.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.labels import forward_return_labels
from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

TZ = "Europe/Istanbul"
RET_LAGS = (1, 3, 6, 12)
FEATURE_COLUMNS = [
    "ret_1", "ret_3", "ret_6", "ret_12", "vol_12", "vol_24", "vol_z", "range_atr", "rsi_14",
    "dist_sma20", "dist_sma50", "bar_idx", "tod_sin", "tod_cos", "dow", "gap_open_flag",
    "gap_ret", "ret_rank",
]


def _local_index(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(idx)
    return idx.tz_localize(TZ) if idx.tz is None else idx.tz_convert(TZ)


def _rank_last(w: np.ndarray) -> float:
    """Percentile rank of the last value within the window (causal)."""
    last = w[-1]
    if not np.isfinite(last):
        return np.nan
    v = w[np.isfinite(w)]
    return float((v < last).sum() + 0.5 * ((v == last).sum() - 1)) / max(len(v) - 1, 1)


def build_features(bars: pd.DataFrame, interval: str = "1h") -> pd.DataFrame:
    """Causal feature frame indexed like ``bars`` (warm-up rows contain NaN)."""
    if len(bars) == 0:
        return pd.DataFrame(columns=FEATURE_COLUMNS)
    bars = bars.sort_index()
    c, o, h, l, v = (bars[k].astype(float) for k in ("close", "open", "high", "low", "volume"))
    idx = _local_index(bars.index)
    lc = np.log(c)
    r1 = lc.diff()
    f = pd.DataFrame(index=bars.index)
    for k in RET_LAGS:
        f[f"ret_{k}"] = lc.diff(k)
    f["vol_12"] = r1.rolling(12).std()
    f["vol_24"] = r1.rolling(24).std()
    lv = np.log1p(v)
    f["vol_z"] = (lv - lv.rolling(48).mean()) / lv.rolling(48).std().replace(0, np.nan)
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    f["range_atr"] = (h - l) / atr.replace(0, np.nan)
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    f["rsi_14"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    f.loc[(dn == 0) & up.notna(), "rsi_14"] = 100.0
    vol24 = f["vol_24"].replace(0, np.nan)
    f["dist_sma20"] = (c / c.rolling(20).mean() - 1) / vol24
    f["dist_sma50"] = (c / c.rolling(50).mean() - 1) / vol24
    day = pd.Series(idx.normalize().tz_localize(None), index=bars.index)
    f["bar_idx"] = day.groupby(day.values).cumcount().astype(float)
    mins = pd.Series(idx.hour * 60 + idx.minute, index=bars.index).astype(float)
    f["tod_sin"] = np.sin(2 * np.pi * mins / 1440.0)
    f["tod_cos"] = np.cos(2 * np.pi * mins / 1440.0)
    f["dow"] = pd.Series(idx.dayofweek, index=bars.index).astype(float)
    first = (day != day.shift(1))
    first.iloc[0] = False  # no previous close for the very first bar
    f["gap_open_flag"] = first.astype(float)
    f["gap_ret"] = np.where(first, (o / prev_c - 1).to_numpy(), 0.0)
    f["ret_rank"] = f["ret_6"].rolling(120, min_periods=60).apply(_rank_last, raw=True)
    f = f.replace([np.inf, -np.inf], np.nan)
    return f[FEATURE_COLUMNS]


def to_end_ts(x) -> Optional[pd.Timestamp]:
    """Date-only strings are treated as inclusive end of that Istanbul day."""
    if x is None:
        return None
    t = pd.Timestamp(x)
    if t.tzinfo is None:
        if t == t.normalize() and not isinstance(x, pd.Timestamp):
            t = t + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        t = t.tz_localize(TZ)
    return t


def panel_for_symbol(bars: pd.DataFrame, symbol: str, interval: str, horizon_bars: int) -> pd.DataFrame:
    """Features + forward-return labels for one symbol (rows with any NaN dropped)."""
    cols = FEATURE_COLUMNS + ["t0", "t1", "symbol", "ret", "y", "price", "bar_value_try"]
    if len(bars) < 3:
        return pd.DataFrame(columns=cols)
    bars = bars.sort_index()
    lab = forward_return_labels(bars, horizon_bars, session_bound=True)
    if len(lab) == 0:
        return pd.DataFrame(columns=cols)
    feats = build_features(bars, interval)
    pos = bars.index.get_indexer(lab["t0"])
    out = feats.iloc[pos].reset_index(drop=True)
    out["t0"] = lab["t0"].reset_index(drop=True)
    out["t1"] = lab["t1"].reset_index(drop=True)
    out["symbol"] = symbol
    out["ret"] = lab["ret"].to_numpy(float)
    out["y"] = (out["ret"] > 0).astype(int)
    out["price"] = bars["open"].to_numpy(float)[pos + 1]
    out["bar_value_try"] = (bars["close"] * bars["volume"]).to_numpy(float)[pos]
    out = out.dropna(subset=FEATURE_COLUMNS + ["price", "ret"]).reset_index(drop=True)
    return out[cols]


def build_panel(archive, symbols: Iterable[str], interval: str, start=None, end=None,
                horizon_bars: int = 4, bars_by_symbol: Optional[Dict[str, pd.DataFrame]] = None
                ) -> pd.DataFrame:
    """Stacked feature+label panel sorted by t0 (then symbol). ``end`` is inclusive."""
    frames = []
    s_ts, e_ts = to_end_ts(start) if start is not None else None, to_end_ts(end)
    for sym in symbols:
        if bars_by_symbol is not None and sym in bars_by_symbol:
            b = bars_by_symbol[sym]
            if e_ts is not None:
                b = b[b.index <= e_ts]
        else:
            b = archive.read_bars(sym, interval, start=s_ts, end=e_ts)
        p = panel_for_symbol(b, sym, interval, horizon_bars)
        if len(p):
            frames.append(p)
    if not frames:
        return pd.DataFrame(columns=FEATURE_COLUMNS + ["t0", "t1", "symbol", "ret", "y", "price",
                                                      "bar_value_try"])
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["t0", "symbol"], kind="stable").reset_index(drop=True)
