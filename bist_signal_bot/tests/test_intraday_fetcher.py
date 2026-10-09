import pandas as pd
import pytest

from bist_signal_bot.intraday.archive import BarArchive
from bist_signal_bot.intraday.fetcher import ArchiveUpdater, RateLimitedFetcher


class Clock:
    def __init__(self):
        self.t = 0.0
        self.sleeps = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


class S:
    INTRADAY_FETCH_BATCH_SIZE = 2
    INTRADAY_MIN_REQUEST_INTERVAL_SECONDS = 1.0
    INTRADAY_BACKOFF_BASE_SECONDS = 2.0
    INTRADAY_MAX_RETRIES = 3
    INTRADAY_ARCHIVE_OVERLAP_BARS = 2


def frame(start="2024-03-04 10:00", n=3):
    idx = pd.date_range(start, periods=n, freq="1h", tz="Europe/Istanbul")
    return pd.DataFrame({"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 1.0}, index=idx)


def make(fn, **kw):
    c = Clock()
    f = RateLimitedFetcher(fn, settings=S(), clock=c.now, sleep=c.sleep, jitter_fn=lambda: 0.0, **kw)
    return f, c


NOW = pd.Timestamp("2024-03-05 18:00", tz="Europe/Istanbul")


def test_batching_and_spacing():
    calls = []

    def fn(syms, iv, s, e):
        calls.append(list(syms))
        return {x: frame() for x in syms}

    f, c = make(fn)
    r = f.fetch(["A", "B", "C", "D", "E"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert calls == [["A", "B"], ["C", "D"], ["E"]]
    assert len(r.data) == 5 and not r.failures
    assert c.sleeps == [1.0, 1.0]


def test_backoff_schedule_and_exhaustion():
    n = {"c": 0}

    def fn(syms, iv, s, e):
        n["c"] += 1
        raise ValueError("boom")

    f, c = make(fn)
    r = f.fetch(["A"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert n["c"] == 4  # 1 + 3 retries
    assert "A" in r.failures and "boom" in r.failures["A"]
    backoffs = [s for s in c.sleeps if s >= 2.0]
    assert backoffs == [2.0, 4.0, 8.0]


def test_retry_then_success():
    n = {"c": 0}

    def fn(syms, iv, s, e):
        n["c"] += 1
        if n["c"] < 3:
            raise ValueError("flaky")
        return {x: frame() for x in syms}

    f, _ = make(fn)
    r = f.fetch(["A"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert "A" in r.data and n["c"] == 3


def test_429_circuit_opens_and_cools_down():
    n = {"c": 0}

    def fn(syms, iv, s, e):
        n["c"] += 1
        raise RuntimeError("HTTP 429 Too Many Requests")

    f, c = make(fn)
    r = f.fetch(["A", "B", "C", "D"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert f.circuit_open
    assert n["c"] == 3  # threshold reached, later chunk short-circuited
    assert set(r.failures) == {"A", "B", "C", "D"}
    before = n["c"]
    f.fetch(["E"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert n["c"] == before  # still open, no calls
    c.t += 301
    assert not f.circuit_open


def test_lookback_clamp():
    seen = {}

    def fn(syms, iv, s, e):
        seen["s"] = s
        return {x: frame() for x in syms}

    f, _ = make(fn)
    r = f.fetch(["A"], "1m", NOW - pd.Timedelta(days=30), NOW)
    assert r.clamped and r.notes
    assert seen["s"] >= NOW - pd.Timedelta(days=7)
    r2 = f.fetch(["A"], "1m", NOW - pd.Timedelta(days=2), NOW)
    assert not r2.clamped


def test_per_symbol_isolation_and_fetch_log(tmp_path):
    def fn(syms, iv, s, e):
        if "BAD" in syms and len(syms) > 1:
            raise ValueError("batch broke")
        if syms == ["BAD"]:
            raise ValueError("bad symbol")
        return {x: frame() for x in syms}

    arch = BarArchive(tmp_path / "b.sqlite")
    f, _ = make(fn, archive=arch)
    r = f.fetch(["GOOD", "BAD"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert "GOOD" in r.data and "BAD" in r.failures
    log = {row[0]: row[4] for row in arch.fetch_log()}
    assert log == {"GOOD": 1, "BAD": 0}
    arch.close()


def test_missing_symbol_reported_no_data():
    f, _ = make(lambda syms, iv, s, e: {"A": frame()})
    r = f.fetch(["A", "B"], "1h", NOW - pd.Timedelta(days=1), NOW)
    assert r.failures == {"B": "no_data"}


def test_updater_incremental(tmp_path):
    arch = BarArchive(tmp_path / "b.sqlite")
    arch.upsert_bars(frame("2024-03-04 10:00", 3), "A", "1h", "t")  # last = 12:00
    seen = {}

    def fn(syms, iv, s, e):
        seen["s"], seen["syms"] = s, list(syms)
        return {x: frame("2024-03-04 10:00", 6) for x in syms}  # overlaps 3, new 3

    f, _ = make(fn)
    up = ArchiveUpdater(arch, f, universe_provider=lambda: ["A"])
    rep = up.update(None, "1h", NOW)
    assert seen["s"] == pd.Timestamp("2024-03-04 12:00", tz="Europe/Istanbul") - pd.Timedelta(hours=2)
    assert rep.inserted == 3 and rep.unchanged == 3 and rep.rows == {"A": 6}
    assert arch.count("A", "1h") == 6
    rep2 = up.update(["A"], "1h", NOW)
    assert rep2.inserted == 0 and rep2.unchanged == 6
    arch.close()


def test_updater_new_symbol_uses_lookback(tmp_path):
    arch = BarArchive(tmp_path / "b.sqlite")
    seen = {}

    def fn(syms, iv, s, e):
        seen["s"] = s
        return {x: frame() for x in syms}

    f, _ = make(fn)
    rep = ArchiveUpdater(arch, f).update(["N"], "5m", NOW)
    assert seen["s"] >= NOW - pd.Timedelta(days=60)
    assert rep.inserted == 3
    arch.close()
