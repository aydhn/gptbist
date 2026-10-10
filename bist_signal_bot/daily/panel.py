"""Daily panel loaders (research only)."""
from __future__ import annotations

import pandas as pd

from bist_signal_bot.daily.fetch import BENCHMARKS, INTERVAL
from bist_signal_bot.intraday.archive import COLS, TZ, BarArchive


def _to_date_index(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    idx = pd.DatetimeIndex(d.index)
    if idx.tz is not None:
        idx = idx.tz_convert(TZ).tz_localize(None)
    d.index = pd.DatetimeIndex(idx.normalize(), name="date")
    return d


def load_daily_panel(archive: BarArchive, symbols: list | None = None, start=None, end=None,
                     min_history: int = 0) -> dict[str, pd.DataFrame]:
    """symbol -> OHLCV frame with tz-naive session-date DatetimeIndex. Benchmarks excluded unless named."""
    if symbols is None:
        symbols = [s for s in archive.symbols(INTERVAL) if s not in BENCHMARKS]
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        df = archive.read_bars(s, INTERVAL, start, end)
        if df.empty or len(df) < min_history:
            continue
        out[s] = _to_date_index(df)[COLS]
    return out


def close_matrix(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if not panel:
        return pd.DataFrame()
    return pd.DataFrame({s: d["close"] for s, d in panel.items()}).sort_index()


def value_matrix(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Traded value in TRY (close * volume)."""
    if not panel:
        return pd.DataFrame()
    return pd.DataFrame({s: d["close"] * d["volume"] for s, d in panel.items()}).sort_index()


def adv(panel: dict[str, pd.DataFrame], window: int = 20) -> pd.DataFrame:
    """Average daily traded value (TRY) over `window` sessions (min_periods=window, no look-ahead)."""
    return value_matrix(panel).rolling(window, min_periods=window).mean()


def load_benchmark(archive: BarArchive, name: str = "XU100", start=None, end=None) -> pd.DataFrame:
    df = archive.read_bars(name, INTERVAL, start, end)
    return _to_date_index(df)[COLS] if not df.empty else pd.DataFrame(columns=COLS)


def resample_hourly_to_daily(bars_1h: pd.DataFrame) -> pd.DataFrame:
    """Aggregate 1h bars to BIST session-day bars (grouped by Istanbul calendar date).

    open=first, high=max, low=min, close=last, volume=sum. Returns a tz-naive date index.
    Prices are unadjusted (raw archive), unlike fetched daily bars.
    """
    if bars_1h is None or len(bars_1h) == 0:
        return pd.DataFrame(columns=COLS)
    d = bars_1h.copy()
    d.columns = [str(c).lower() for c in d.columns]
    d = d.sort_index()
    idx = pd.DatetimeIndex(d.index)
    idx = idx.tz_localize(TZ) if idx.tz is None else idx.tz_convert(TZ)
    day = pd.DatetimeIndex(idx.tz_localize(None).normalize(), name="date")
    g = d.groupby(day)
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                        "close": g["close"].last(), "volume": g["volume"].sum()})
    return out[COLS]


def field_matrix(panel: dict[str, pd.DataFrame], col: str) -> pd.DataFrame:
    """date x symbol matrix of one OHLCV column (e.g. 'high'/'low' for the bar-health and lock checks)."""
    if not panel:
        return pd.DataFrame()
    return pd.DataFrame({s: d[col] for s, d in panel.items()}).sort_index()
