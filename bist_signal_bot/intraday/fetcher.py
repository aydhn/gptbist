"""Rate-limited intraday fetcher and incremental archive updater (research only, no orders)."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.intraday.archive import BarArchive, TZ
from bist_signal_bot.intraday.models import interval_minutes, max_lookback_days, normalize_interval

logger = get_logger(__name__)

FetchFn = Callable[[list, str, object, object], dict]

_RATE_MARKERS = ("429", "too many requests", "rate")


def is_rate_limit_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _RATE_MARKERS)


def default_yfinance_fetch(symbols: list, interval: str, start, end) -> dict:
    """Default fetch_fn: yfinance.download (lazy import).

    Internal symbols (THYAO) are mapped to Yahoo tickers (THYAO.IS) and results are
    returned keyed by the internal symbol.
    """
    import yfinance as yf  # lazy

    ymap = {s: (s if str(s).upper().endswith(".IS") else f"{s}.IS") for s in symbols}
    raw = yf.download(tickers=list(ymap.values()), interval=interval, start=start, end=end,
                      auto_adjust=False, threads=False, progress=False, group_by="ticker")
    out: dict = {}
    if raw is None or raw.empty:
        return out
    for s, ys in ymap.items():
        try:
            sub = raw[ys] if isinstance(raw.columns, pd.MultiIndex) else raw
        except KeyError:
            continue
        sub = sub.dropna(how="all")
        if not sub.empty:
            sub = sub.copy()
            sub.columns = [str(c).lower().replace(" ", "_") for c in sub.columns]
            out[s] = sub
    return out


@dataclass
class FetchResult:
    data: dict = field(default_factory=dict)
    failures: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    clamped: bool = False
    effective_start: object = None


def _cfg(settings, key, default, cast):
    v = getattr(settings, key, None) if settings is not None else None
    try:
        return cast(v) if v is not None else default
    except (TypeError, ValueError):
        return default


class RateLimitedFetcher:
    def __init__(self, fetch_fn: FetchFn | None = None, settings=None, archive: BarArchive | None = None,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
                 jitter_fn: Callable[[], float] = random.random,
                 circuit_threshold: int = 3, circuit_cooldown_seconds: float = 300.0):
        self.fetch_fn = fetch_fn or default_yfinance_fetch
        self.settings = settings
        self.archive = archive
        self.clock = clock
        self.sleep = sleep
        self.jitter_fn = jitter_fn
        self.batch_size = max(1, _cfg(settings, "INTRADAY_FETCH_BATCH_SIZE", 20, int))
        self.min_interval = _cfg(settings, "INTRADAY_MIN_REQUEST_INTERVAL_SECONDS", 1.0, float)
        self.backoff_base = _cfg(settings, "INTRADAY_BACKOFF_BASE_SECONDS", 2.0, float)
        self.max_retries = _cfg(settings, "INTRADAY_MAX_RETRIES", 4, int)
        self.circuit_threshold = circuit_threshold
        self.circuit_cooldown = circuit_cooldown_seconds
        self._last_request: float | None = None
        self._rate_errors = 0
        self._open_until: float | None = None

    @property
    def circuit_open(self) -> bool:
        return self._open_until is not None and self.clock() < self._open_until

    def backoff_delay(self, attempt: int) -> float:
        return self.backoff_base * (2 ** attempt) + self.jitter_fn() * self.backoff_base

    def _space(self) -> None:
        if self._last_request is not None:
            wait = self.min_interval - (self.clock() - self._last_request)
            if wait > 0:
                self.sleep(wait)
        self._last_request = self.clock()

    def _call_with_retries(self, chunk: list, interval: str, start, end) -> dict:
        last_exc: BaseException | None = None
        for attempt in range(self.max_retries + 1):
            if self.circuit_open:
                raise RuntimeError("circuit_open")
            self._space()
            try:
                res = self.fetch_fn(list(chunk), interval, start, end)
                self._rate_errors = 0
                return res or {}
            except Exception as exc:  # noqa: BLE001 - isolation by design
                last_exc = exc
                if is_rate_limit_error(exc):
                    self._rate_errors += 1
                    if self._rate_errors >= self.circuit_threshold:
                        self._open_until = self.clock() + self.circuit_cooldown
                        logger.warning("intraday fetch circuit opened for %.0fs", self.circuit_cooldown)
                        raise
                else:
                    self._rate_errors = 0
                if attempt < self.max_retries:
                    self.sleep(self.backoff_delay(attempt))
        assert last_exc is not None
        raise last_exc

    def clamp_start(self, interval: str, start, end):
        end_ts = pd.Timestamp(end)
        if end_ts.tzinfo is None:
            end_ts = end_ts.tz_localize(TZ)
        # 1 day safety margin so the request is never at the exact provider limit
        floor = end_ts - timedelta(days=max_lookback_days(interval, self.settings)) + timedelta(days=1)
        s = pd.Timestamp(start)
        if s.tzinfo is None:
            s = s.tz_localize(TZ)
        if s < floor:
            return floor, (f"start clamped to {floor.isoformat()} "
                           f"(max lookback {max_lookback_days(interval, self.settings)}d for {interval})")
        return s, None

    def fetch(self, symbols: list, interval: str, start, end) -> FetchResult:
        interval = normalize_interval(interval)
        result = FetchResult()
        eff_start, note = self.clamp_start(interval, start, end)
        result.effective_start = eff_start
        if note:
            result.clamped = True
            result.notes.append(note)
        symbols = list(dict.fromkeys(symbols))
        for i in range(0, len(symbols), self.batch_size):
            chunk = symbols[i:i + self.batch_size]
            started = time.time()
            try:
                got = self._call_with_retries(chunk, interval, eff_start, end)
                self._absorb(chunk, got, interval, started, result)
            except Exception as exc:  # noqa: BLE001
                if len(chunk) > 1 and not self.circuit_open and not is_rate_limit_error(exc):
                    # isolate: retry each symbol individually (single attempt each)
                    for s in chunk:
                        try:
                            self._space()
                            got = self.fetch_fn([s], interval, eff_start, end) or {}
                            self._absorb([s], got, interval, started, result)
                        except Exception as exc2:  # noqa: BLE001
                            self._fail(s, interval, started, exc2, result)
                else:
                    for s in chunk:
                        self._fail(s, interval, started, exc, result)
        return result

    def _absorb(self, chunk, got, interval, started, result: FetchResult) -> None:
        for s in chunk:
            df = got.get(s)
            if df is None or len(df) == 0:
                result.failures[s] = "no_data"
                self._log(s, interval, started, 0, False, "no_data")
            else:
                result.data[s] = df
                self._log(s, interval, started, len(df), True, None)

    def _fail(self, s, interval, started, exc, result: FetchResult) -> None:
        msg = f"{type(exc).__name__}: {exc}"
        result.failures[s] = msg
        self._log(s, interval, started, 0, False, msg)

    def _log(self, s, interval, started, rows, ok, err) -> None:
        if self.archive is not None:
            try:
                self.archive.log_fetch(s, interval, started, rows, ok, err)
            except Exception:  # noqa: BLE001
                logger.exception("fetch_log write failed")


@dataclass
class UpdateReport:
    interval: str
    rows: dict = field(default_factory=dict)       # symbol -> rows fetched
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    failures: dict = field(default_factory=dict)
    clamped: bool = False
    notes: list = field(default_factory=list)


class ArchiveUpdater:
    def __init__(self, archive: BarArchive, fetcher: RateLimitedFetcher,
                 universe_provider: Callable[[], list] | None = None, settings=None,
                 source: str = "yfinance"):
        self.archive = archive
        self.fetcher = fetcher
        self.universe_provider = universe_provider
        self.source = source
        self.overlap_bars = _cfg(settings or fetcher.settings, "INTRADAY_ARCHIVE_OVERLAP_BARS", 2, int)

    def update(self, symbols: list | None, interval: str, now) -> UpdateReport:
        interval = normalize_interval(interval)
        if symbols is None:
            symbols = list(self.universe_provider()) if self.universe_provider else []
        now_ts = pd.Timestamp(now)
        if now_ts.tzinfo is None:
            now_ts = now_ts.tz_localize(TZ)
        report = UpdateReport(interval=interval)
        if not symbols:
            return report
        overlap = timedelta(minutes=interval_minutes(interval) * self.overlap_bars)
        lookback_start = now_ts - timedelta(days=max_lookback_days(interval, self.fetcher.settings))
        starts = []
        for s in symbols:
            last = self.archive.last_ts(s, interval)
            starts.append(last - overlap if last is not None else lookback_start)
        res = self.fetcher.fetch(list(symbols), interval, min(starts), now_ts)
        report.clamped = res.clamped
        report.notes = list(res.notes)
        report.failures = dict(res.failures)
        for s, df in res.data.items():
            try:
                up = self.archive.upsert_bars(df, s, interval, self.source)
            except Exception as exc:  # noqa: BLE001
                report.failures[s] = f"upsert: {exc}"
                continue
            report.rows[s] = len(df)
            report.inserted += up.inserted
            report.updated += up.updated
            report.unchanged += up.unchanged
        return report
