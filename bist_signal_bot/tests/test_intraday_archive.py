import pandas as pd
import pytest

from bist_signal_bot.intraday.archive import BarArchive


def make_df(n=4, start="2024-03-04 10:00", tz="Europe/Istanbul", base=10.0):
    idx = pd.date_range(start, periods=n, freq="1h", tz=tz)
    return pd.DataFrame({"open": base, "high": base + 1, "low": base - 1, "close": base + 0.5,
                         "volume": 100.0}, index=idx)


@pytest.fixture
def arch(tmp_path):
    a = BarArchive(tmp_path / "sub" / "bars.sqlite")
    yield a
    a.close()


def test_idempotent_upsert(arch):
    df = make_df()
    r1 = arch.upsert_bars(df, "THYAO.IS", "60m", "t")
    assert (r1.inserted, r1.updated, r1.unchanged) == (4, 0, 0)
    r2 = arch.upsert_bars(df, "THYAO.IS", "1h", "t")
    assert (r2.inserted, r2.updated, r2.unchanged) == (0, 0, 4)
    assert arch.count("THYAO.IS", "1h") == 4


def test_updated_bar_overwritten(arch):
    df = make_df()
    arch.upsert_bars(df, "A", "1h", "t")
    df2 = df.copy()
    df2.iloc[1, df2.columns.get_loc("close")] = 10.9
    r = arch.upsert_bars(df2, "A", "1h", "t")
    assert (r.inserted, r.updated, r.unchanged) == (0, 1, 3)
    assert arch.read_bars("A", "1h")["close"].iloc[1] == pytest.approx(10.9)


def test_tz_handling(arch):
    utc = make_df(tz="UTC", start="2024-03-04 07:00")
    arch.upsert_bars(utc, "A", "1h", "t")
    out = arch.read_bars("A", "1h")
    assert str(out.index.tz) == "Europe/Istanbul"
    assert out.index[0].hour == 10
    # naive treated as Istanbul -> same instants, so unchanged
    naive = make_df(tz=None)
    assert arch.upsert_bars(naive, "A", "1h", "t").unchanged == 4
    assert arch.first_ts("A", "1h") == out.index[0]
    assert arch.last_ts("A", "1h") == out.index[-1]
    assert arch.symbols("1h") == ["A"]


def test_invalid_and_nan_rows_dropped(arch):
    df = make_df()
    df.iloc[0, df.columns.get_loc("high")] = 5.0   # high < low
    df.iloc[1, df.columns.get_loc("close")] = float("nan")
    r = arch.upsert_bars(df, "A", "1h", "t")
    assert r.inserted == 2


def test_read_range(arch):
    arch.upsert_bars(make_df(), "A", "1h", "t")
    sub = arch.read_bars("A", "1h", start="2024-03-04 11:00", end="2024-03-04 12:00")
    assert len(sub) == 2
    assert arch.read_bars("ZZ", "1h").empty


def test_split_adjustment_does_not_mutate_raw(arch):
    df = make_df(n=4, start="2024-03-04 10:00")
    df2 = make_df(n=2, start="2024-03-06 10:00", base=5.0)
    arch.upsert_bars(pd.concat([df, df2]), "A", "1h", "t")
    arch.record_actions("A", [("2024-03-06", "split", 2.0)])
    assert arch.get_actions("A") == [("2024-03-06", "split", 2.0)]
    raw = arch.read_bars("A", "1h")
    adj = arch.adjust_for_splits(raw, "A")
    assert adj["close"].iloc[0] == pytest.approx(10.5 / 2)
    assert adj["volume"].iloc[0] == pytest.approx(200.0)
    assert adj["close"].iloc[-1] == pytest.approx(5.5)
    assert arch.read_bars("A", "1h")["close"].iloc[0] == pytest.approx(10.5)


def test_survivorship_transitions(tmp_path):
    class S:
        INTRADAY_UNIVERSE_DELIST_MISSES = 3

    a = BarArchive(tmp_path / "b.sqlite", settings=S())
    a.snapshot_universe("2024-03-01", ["A", "B"])
    a.snapshot_universe("2024-03-04", ["A"])
    assert a.survivorship_report()["missing"] == ["B"]
    a.snapshot_universe("2024-03-05", ["A"])
    assert a.survivorship_report()["missing"] == ["B"]
    a.snapshot_universe("2024-03-06", ["A"])
    rep = a.survivorship_report()
    assert rep["delisted"] == ["B"] and rep["active"] == ["A"]
    # reappearing resets
    a.snapshot_universe("2024-03-07", ["A", "B"])
    assert a.survivorship_report()["active"] == ["A", "B"]
    a.close()
