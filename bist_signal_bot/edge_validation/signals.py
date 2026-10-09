"""Native long-only research baseline signals (no LLM, no network, no orders).

Each function takes an OHLCV DataFrame and returns a boolean numpy array: True at bar i means
"enter long at the next bar's open", using ONLY data up to and including bar i.
"""
from __future__ import annotations

from typing import Callable, Dict

import numpy as np
import pandas as pd


def sma_trend(bars: pd.DataFrame, fast: int = 10, slow: int = 30) -> np.ndarray:
    """Fires when the fast SMA crosses above the slow SMA."""
    if fast >= slow:
        raise ValueError("fast must be < slow")
    c = bars["close"].astype(float)
    f, s = c.rolling(fast).mean(), c.rolling(slow).mean()
    up = (f > s)
    prev = up.shift(1, fill_value=False)
    valid = f.notna() & s.notna()
    return (up & ~prev.astype(bool) & valid).to_numpy(bool)


def rsi_meanrev(bars: pd.DataFrame, window: int = 14, lo: float = 30.0, hi: float = 70.0) -> np.ndarray:
    """Fires when RSI crosses back above ``lo`` from below (oversold bounce). ``hi`` is kept for the
    param grid / reporting and bounds the trigger (no entry while RSI >= hi)."""
    c = bars["close"].astype(float)
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1.0 / window, adjust=False, min_periods=window).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1.0 / window, adjust=False, min_periods=window).mean()
    rs = up / dn.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.where(dn > 0, 100.0).where(up.notna())
    prev = rsi.shift(1)
    sig = (prev < lo) & (rsi >= lo) & (rsi < hi)
    return sig.fillna(False).to_numpy(bool)


def breakout(bars: pd.DataFrame, window: int = 20) -> np.ndarray:
    """Fires when close exceeds the highest high of the previous ``window`` bars."""
    prior_hi = bars["high"].astype(float).rolling(window).max().shift(1)
    return (bars["close"].astype(float) > prior_hi).fillna(False).to_numpy(bool)


SIGNAL_FUNCS: Dict[str, Callable[..., np.ndarray]] = {
    "sma_trend": sma_trend,
    "rsi_meanrev": rsi_meanrev,
    "breakout": breakout,
}

DEFAULT_GRIDS: Dict[str, Dict[str, list]] = {
    "sma_trend": {"fast": [5, 10, 20], "slow": [30, 50]},
    "rsi_meanrev": {"window": [7, 14], "lo": [25.0, 30.0], "hi": [70.0]},
    "breakout": {"window": [10, 20, 40]},
}
