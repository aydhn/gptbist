"""Daily bar layer tests (fake downloaders, no network)."""
import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.cli.daily_cli import build_parser
from bist_signal_bot.daily.fetch import (BENCHMARKS, DailyFetcher, DailyUpdater, clean_daily)
from bist_signal_bot.daily.panel import (adv, close_matrix, load_benchmark, load_daily_panel,
                                         resample_hourly_to_daily, value_matrix)
from bist_signal_bot.intraday.archive import BarArchive


def _bars(n=30, start="2024-01-01", base=10.0, tz=None):
    idx = pd.bdate_range(start, periods=n, tz=tz)
    c = base + np.arange(n) * 0.1
    return pd.DataFrame({"Open": c, "High": c + 0.5, "Low": c - 0.5, "Close": c, "Volume": 1000.0 + np.arange(n)},
                        index=idx)


class Fake:
    def __init__(self, data=None, fail=None):
        self.data, self.fail, self.calls = data or {}, fail or {}, []

    def __call__(self, symbols, period, start):
        self.calls.append((list(symbols), period, start))
        for s in symbols:
            if s in self.fail:
                raise RuntimeError(self.fail[s])
        return {s: self.data[s] for s in symbols if s in self.data}


def _fetcher(fn, arch=None):
    return DailyFetcher(fetch_fn=fn, archive=arch, sleep=lambda s: None)


@pytest.fixture
def arch():
    a = BarArchive(":memory:")
    yield a
    a.close()


def test_upsert_idempotent(arch):
    fn = Fake({"AAA": _bars(), "XU100": _bars(base=100), "USDTRY": _bars(base=30)})
    up = DailyUpdater(arch, _fetcher(fn, arch))
    r1 = up.update(["AAA"], full=True)
    r2 = up.update(["AAA"], full=True)
    assert r1.inserted == 90 and r1.failures == {}
    assert r2.inserted == 0 and r2.unchanged == 90
    assert arch.count("AAA", "1d") == 30


def test_incremental_uses_start_for_existing(arch):
    fn = Fake({"AAA": _bars(), "XU100": _bars(), "USDTRY": _bars()})
    up = DailyUpdater(arch, _fetcher(fn, arch))
    up.update(["AAA"], period="5y")
    assert fn.calls[0][1] == "5y" and fn.calls[0][2] is None
    up.update(["AAA"])
    assert fn.calls[-1][2] is not None  # start passed for existing symbols


def test_adjusted_vs_split_prices_stored_as_given(arch):
    # adjusted series has no split discontinuity; stored unchanged and flagged adjusted
    c = np.r_[np.full(10, 5.0), np.full(10, 5.0)]
    df = _bars(20)
    df[["Open", "High", "Low", "Close"]] = np.c_[c, c + 0.1, c - 0.1, c]
    fn = Fake({"AAA": df})
    DailyUpdater(arch, _fetcher(fn, arch)).update(["AAA"], include_benchmarks=False)
    got = arch.read_bars("AAA", "1d")
    assert np.allclose(got["close"], 5.0)
    flag = arch._conn.execute("SELECT DISTINCT adjusted FROM bars WHERE symbol='AAA'").fetchall()
    assert flag == [(1,)]


def test_bad_data_rejected():
    df = _bars(10)
    df.iloc[2, df.columns.get_loc("Close")] = -1.0
    df.iloc[3, df.columns.get_loc("Open")] = 0.0
    df.iloc[4, df.columns.get_loc("High")] = np.nan
    df.iloc[5, df.columns.get_loc("High")] = 0.1  # high < low
    dup = pd.concat([df, df.iloc[[7]]])
    out = clean_daily(dup)
    assert len(out) == 6 and out.index.is_unique
    assert (out[["open", "high", "low", "close"]] > 0).all().all()
    assert clean_daily(pd.DataFrame({"x": [1, 2]})).empty
    assert clean_daily(None).empty and clean_daily(pd.DataFrame()).empty


def test_fetcher_fail_closed_and_logged(arch):
    fn = Fake({"AAA": _bars(), "EMPTY": pd.DataFrame()}, fail={"BOOM": "kaboom"})
    f = DailyFetcher(fetch_fn=fn, archive=arch, sleep=lambda s: None)
    f.batch_size = 1
    f.max_retries = 1
    res = f.fetch(["AAA", "EMPTY", "BOOM"])
    assert set(res.data) == {"AAA"}
    assert res.failures["EMPTY"] == "no_data" and "kaboom" in res.failures["BOOM"]
    log = {r[0]: r for r in arch.fetch_log()}
    assert log["AAA"][4] == 1 and log["BOOM"][4] == 0


def test_tz_aware_index_normalized_to_session_date():
    df = _bars(5, tz="UTC")  # Yahoo-style UTC midnight stamps
    out = clean_daily(df)
    assert str(out.index.tz) == "Europe/Istanbul"
    assert all(t.hour == 0 for t in out.index)
    assert out.index[0].date() == pd.Timestamp("2024-01-01").date() or out.index[0].hour == 0


def test_panel_shapes_and_benchmark(arch):
    fn = Fake({"AAA": _bars(30), "BBB": _bars(25, base=20), "XU100": _bars(30, base=100), "USDTRY": _bars(30, base=30)})
    DailyUpdater(arch, _fetcher(fn, arch)).update(["AAA", "BBB"])
    panel = load_daily_panel(arch)
    assert set(panel) == {"AAA", "BBB"}  # benchmarks excluded by default
    assert list(panel["AAA"].columns) == ["open", "high", "low", "close", "volume"]
    assert panel["AAA"].index.tz is None and len(panel["AAA"]) == 30
    cm = close_matrix(panel)
    assert cm.shape == (30, 2) and cm["BBB"].isna().sum() == 5
    vm = value_matrix(panel)
    assert vm.loc[panel["AAA"].index[0], "AAA"] == pytest.approx(10.0 * 1000.0)
    a = adv(panel, 20)
    assert a["AAA"].iloc[:19].isna().all() and not np.isnan(a["AAA"].iloc[19])
    assert set(load_daily_panel(arch, min_history=28)) == {"AAA"}
    assert len(load_daily_panel(arch, ["AAA"], start="2024-01-15")["AAA"]) < 30
    bm = load_benchmark(arch, "XU100")
    assert len(bm) == 30 and bm["close"].iloc[0] == pytest.approx(100.0)
    assert set(BENCHMARKS) == {"XU100", "USDTRY"}


def test_resample_hourly_to_daily():
    idx = pd.DatetimeIndex(
        [f"2024-03-04 {h:02d}:00" for h in (10, 11, 12)] + [f"2024-03-05 {h:02d}:00" for h in (10, 11)],
        tz="Europe/Istanbul")
    h = pd.DataFrame({"open": [1, 2, 3, 10, 11], "high": [2, 5, 4, 12, 13], "low": [0.5, 1.5, 2.5, 9, 10],
                      "close": [1.5, 2.5, 3.5, 11, 12], "volume": [10, 20, 30, 5, 5]}, index=idx)
    d = resample_hourly_to_daily(h.iloc[::-1])  # unsorted input
    assert len(d) == 2
    r = d.iloc[0]
    assert (r.open, r.high, r.low, r.close, r.volume) == (1, 5, 0.5, 3.5, 60)
    assert d.iloc[1].open == 10 and d.iloc[1].close == 12
    assert resample_hourly_to_daily(pd.DataFrame()).empty


def test_cli_parser():
    p = build_parser()
    a = p.parse_args(["archive-update", "--symbols", "THYAO", "ASELS", "--period", "5y", "--dry-run"])
    assert a.symbols == ["THYAO", "ASELS"] and a.period == "5y" and a.dry_run
    assert p.parse_args(["archive-update", "--all-active"]).all_active
    assert p.parse_args(["status"]).daily_command == "status"
    with pytest.raises(SystemExit):
        p.parse_args(["archive-update", "--symbols", "A", "--all-active"])


def test_intraday_interval_still_strict():
    from bist_signal_bot.intraday.models import normalize_interval
    assert normalize_interval("1D") == "1d" and normalize_interval("60m") == "1h"
    with pytest.raises(ValueError):
        normalize_interval("2h")
