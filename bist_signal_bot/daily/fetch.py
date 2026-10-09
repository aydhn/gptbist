"""Rate-limited yfinance daily fetcher + archive updater (research only, no orders).

Prices are fetched with ``auto_adjust=True`` (split AND dividend adjusted), so returns computed from
them are total-return approximations; volume stays raw (unadjusted share count).
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.intraday.archive import COLS, TZ, BarArchive
from bist_signal_bot.intraday.fetcher import is_rate_limit_error

logger = get_logger(__name__)

INTERVAL = "1d"
SOURCE = "yfinance_1d_adj"
# pseudo symbol -> Yahoo ticker (benchmark / macro series)
BENCHMARKS = {"XU100": "XU100.IS", "USDTRY": "USDTRY=X"}

# fetch_fn(symbols, period, start) -> {internal_symbol: DataFrame(open/high/low/close/volume)}
DailyFetchFn = Callable[[list, "str | None", object], dict]


def yahoo_ticker(sym: str) -> str:
    if sym in BENCHMARKS:
        return BENCHMARKS[sym]
    s = str(sym)
    return s if (s.upper().endswith(".IS") or "=" in s) else f"{s}.IS"


def default_yfinance_daily(symbols: list, period: str | None, start) -> dict:
    """yfinance.download 1d, auto_adjust=True. Handles MultiIndex columns in either level order."""
    import yfinance as yf  # lazy

    ymap = {s: yahoo_ticker(s) for s in symbols}
    kw = dict(tickers=list(ymap.values()), interval="1d", auto_adjust=True, threads=False,
              progress=False, group_by="ticker")
    if start is not None:
        kw["start"] = start
    else:
        kw["period"] = period or "10y"
    raw = yf.download(**kw)
    out: dict = {}
    if raw is None or raw.empty:
        return out
    for s, ys in ymap.items():
        sub = None
        if isinstance(raw.columns, pd.MultiIndex):
            for lvl in (0, 1):
                if ys in raw.columns.get_level_values(lvl):
                    sub = raw.xs(ys, axis=1, level=lvl)
                    break
        elif len(ymap) == 1:
            sub = raw
        if sub is None:
            continue
        sub = sub.dropna(how="all")
        if not sub.empty:
            sub = sub.copy()
            sub.columns = [str(c).lower().replace(" ", "_") for c in sub.columns]
            out[s] = sub
    return out


def clean_daily(df: pd.DataFrame | None) -> pd.DataFrame:
    """Normalize to OHLCV with a tz-aware (Europe/Istanbul) midnight session-date index.

    Drops NaN, non-positive prices, inconsistent OHLC rows and duplicate dates. Returns empty on garbage.
    """
    empty = pd.DataFrame(columns=COLS)
    if df is None or len(df) == 0:
        return empty
    d = df.copy()
    d.columns = [str(c).lower().replace(" ", "_") for c in d.columns]
    if any(c not in d.columns for c in ("open", "high", "low", "close")):
        return empty
    if "volume" not in d.columns:
        d["volume"] = 0.0
    d = d[COLS].apply(pd.to_numeric, errors="coerce")
    try:
        idx = pd.DatetimeIndex(pd.to_datetime(df.index))
    except (TypeError, ValueError):
        return empty
    if idx.tz is not None:  # session date as seen in the exchange tz
        idx = idx.tz_convert(TZ).tz_localize(None)
    d.index = idx.normalize()
    d = d[d.index.notna()]
    d = d.replace([float("inf"), float("-inf")], float("nan")).dropna()
    d = d[(d[["open", "high", "low", "close"]] > 0).all(axis=1) & (d["volume"] >= 0)]
    omax = d[["open", "close"]].max(axis=1)
    omin = d[["open", "close"]].min(axis=1)
    d = d[(d["high"] >= d["low"]) & (d["high"] >= omax) & (d["low"] <= omin)]
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d.index = d.index.tz_localize(TZ, nonexistent="shift_forward", ambiguous="NaT")
    d = d[d.index.notna()]
    d.index.name = "timestamp"
    return d


def _cfg(settings, key, default, cast):
    v = getattr(settings, key, None) if settings is not None else None
    try:
        return cast(v) if v is not None else default
    except (TypeError, ValueError):
        return default


@dataclass
class DailyFetchResult:
    data: dict = field(default_factory=dict)
    failures: dict = field(default_factory=dict)


class DailyFetcher:
    def __init__(self, fetch_fn: DailyFetchFn | None = None, settings=None, archive: BarArchive | None = None,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
                 jitter_fn: Callable[[], float] = random.random):
        self.fetch_fn = fetch_fn or default_yfinance_daily
        self.settings = settings
        self.archive = archive
        self.clock, self.sleep, self.jitter_fn = clock, sleep, jitter_fn
        self.batch_size = max(1, _cfg(settings, "DAILY_FETCH_BATCH_SIZE", 20, int))
        self.min_interval = _cfg(settings, "DAILY_MIN_REQUEST_INTERVAL_SECONDS", 1.0, float)
        self.backoff_base = _cfg(settings, "INTRADAY_BACKOFF_BASE_SECONDS", 2.0, float)
        self.max_retries = _cfg(settings, "INTRADAY_MAX_RETRIES", 4, int)
        self.period = _cfg(settings, "DAILY_HISTORY_PERIOD", "10y", str)
        self._last: float | None = None

    def _space(self) -> None:
        if self._last is not None:
            wait = self.min_interval - (self.clock() - self._last)
            if wait > 0:
                self.sleep(wait)
        self._last = self.clock()

    def _call(self, chunk: list, period, start) -> dict:
        last_exc: BaseException | None = None
        for attempt in range(self.max_retries + 1):
            self._space()
            try:
                return self.fetch_fn(list(chunk), period, start) or {}
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < self.max_retries:
                    mult = 2 if is_rate_limit_error(exc) else 1
                    self.sleep(self.backoff_base * mult * (2 ** attempt) + self.jitter_fn() * self.backoff_base)
        assert last_exc is not None
        raise last_exc

    def fetch(self, symbols: list, period: str | None = None, start=None) -> DailyFetchResult:
        res = DailyFetchResult()
        period = period or self.period
        symbols = list(dict.fromkeys(symbols))
        for i in range(0, len(symbols), self.batch_size):
            chunk = symbols[i:i + self.batch_size]
            started = time.time()
            try:
                got = self._call(chunk, period, start)
            except Exception as exc:  # noqa: BLE001
                msg = f"{type(exc).__name__}: {exc}"
                for s in chunk:
                    res.failures[s] = msg
                    self._log(s, started, 0, False, msg)
                continue
            for s in chunk:
                clean = clean_daily(got.get(s))
                if clean.empty:
                    res.failures[s] = "no_data"
                    self._log(s, started, 0, False, "no_data")
                else:
                    res.data[s] = clean
                    self._log(s, started, len(clean), True, None)
        return res

    def _log(self, s, started, rows, ok, err) -> None:
        if self.archive is not None:
            try:
                self.archive.log_fetch(s, INTERVAL, started, rows, ok, err)
            except Exception:  # noqa: BLE001
                logger.exception("daily fetch_log write failed")


@dataclass
class DailyUpdateReport:
    rows: dict = field(default_factory=dict)
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    failures: dict = field(default_factory=dict)


class DailyUpdater:
    """Full history (period) for symbols with no data; short overlap window refresh for existing ones.

    auto_adjust data is restated after dividends/splits; the overlap refresh only rewrites recent rows.
    Use ``full=True`` to re-pull the whole history (older rows are then restated through upsert).
    """

    def __init__(self, archive: BarArchive, fetcher: DailyFetcher, overlap_days: int = 7):
        self.archive, self.fetcher, self.overlap_days = archive, fetcher, overlap_days

    def update(self, symbols: list, period: str | None = None, include_benchmarks: bool = True,
               full: bool = False) -> DailyUpdateReport:
        rep = DailyUpdateReport()
        syms = list(dict.fromkeys(list(symbols) + (list(BENCHMARKS) if include_benchmarks else [])))
        new, old = [], []
        for s in syms:
            (old if (not full and self.archive.last_ts(s, INTERVAL) is not None) else new).append(s)
        results = []
        if new:
            results.append(self.fetcher.fetch(new, period=period))
        if old:
            starts = [self.archive.last_ts(s, INTERVAL) for s in old]
            start = (min(starts) - pd.Timedelta(days=self.overlap_days)).tz_localize(None).date().isoformat()
            results.append(self.fetcher.fetch(old, period=period, start=start))
        for r in results:
            rep.failures.update(r.failures)
            for s, df in r.data.items():
                try:
                    up = self.archive.upsert_bars(df, s, INTERVAL, SOURCE, adjusted=True)
                except Exception as exc:  # noqa: BLE001
                    rep.failures[s] = f"upsert: {exc}"
                    continue
                rep.rows[s] = len(df)
                rep.inserted += up.inserted
                rep.updated += up.updated
                rep.unchanged += up.unchanged
        return rep
