"""Causal global macro regime features from FRED series (default OFF)."""
from __future__ import annotations

import numpy as np
import pandas as pd

FLAG = "REGIME_USE_GLOBAL_MACRO"

# Publication lag per series in CALENDAR days, applied to the series' own dates BEFORE ffill/reindex.
# Daily market series (VIX, DGS10, HY OAS) are published same/next day -> covered by the final shift(1) BIST day.
# DTWEXBGS (Broad USD index) is released weekly with ~1 week delay -> 7 calendar days extra.
PUBLICATION_LAG_DAYS: dict[str, int] = {"VIXCLS": 0, "DGS10": 0, "BAMLH0A0HYM2": 0, "DTWEXBGS": 7}


def global_macro_enabled(settings) -> bool:
    """Settings never raises AttributeError, so only an explicitly present key counts (default False)."""
    try:
        return bool(settings.get(FLAG, False))
    except Exception:
        return False


def build_global_macro_features(bist_index: pd.DatetimeIndex, series: dict[str, pd.Series],
                                z_window: int = 252, chg_window: int = 5) -> pd.DataFrame:
    """Features indexed by BIST days. Value on day t uses only FRED data dated <= t-1
    (US-calendar features -> ffill onto BIST days -> shift(1))."""
    bi = pd.DatetimeIndex(bist_index)
    idx = (bi.tz_localize(None) if bi.tz is not None else bi).normalize()
    raw = {}
    for k, v in series.items():
        v = v.astype(float).copy()
        ix = pd.DatetimeIndex(v.index)
        ix = (ix.tz_localize(None) if ix.tz is not None else ix).normalize()
        if ix.has_duplicates:
            raise ValueError(f"global macro series {k} has repeated dates (intraday / non-daily index); "
                             "pass one observation per day")
        v.index = ix
        raw[k] = v.sort_index()
    lag = lambda k: pd.Timedelta(days=PUBLICATION_LAG_DAYS.get(k, 0))  # noqa: E731
    parts = {}  # each feature is computed on its own series' calendar, then its dates are moved to publication day
    if "VIXCLS" in raw:
        v = raw["VIXCLS"].ffill()
        m = v.rolling(z_window, min_periods=20).mean()
        sd = v.rolling(z_window, min_periods=20).std()
        parts["macro_vix_level"] = (v, "VIXCLS")
        parts["macro_vix_z"] = ((v - m) / sd.replace(0, np.nan), "VIXCLS")
    if "DGS10" in raw:
        parts["macro_us10y_chg"] = (raw["DGS10"].ffill().diff(chg_window), "DGS10")
    if "DTWEXBGS" in raw:
        parts["macro_usd_mom"] = (raw["DTWEXBGS"].ffill().pct_change(20, fill_method=None), "DTWEXBGS")
    if "BAMLH0A0HYM2" in raw:
        parts["macro_hy_spread"] = (raw["BAMLH0A0HYM2"].ffill(), "BAMLH0A0HYM2")
    shifted = {}
    for name, (f, k) in parts.items():
        f = f.copy()
        f.index = f.index + lag(k)
        shifted[name] = f[~f.index.duplicated(keep="last")]
    feats = pd.DataFrame(shifted).sort_index()
    union = feats.index.union(idx)
    out = feats.reindex(union).ffill().reindex(idx).shift(1)
    out.index = bist_index
    return out
