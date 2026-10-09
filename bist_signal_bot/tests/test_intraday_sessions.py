from datetime import date, datetime, time

import pytest

from functools import partial

from bist_signal_bot.intraday import sessions as S

# Legacy tests below target the exchange (10:00-aligned) grid; yahoo tests pass vendor="yahoo".
_ex_bars = partial(S.expected_bar_starts, vendor="exchange")
_ex_last = partial(S.last_completed_bar_start, vendor="exchange")


@pytest.mark.parametrize("d,expected", [
    (date(2026, 6, 1), True),     # Monday
    (date(2026, 6, 6), False),    # Saturday
    (date(2026, 6, 7), False),    # Sunday
    (date(2026, 1, 1), False),
    (date(2026, 4, 23), False),
    (date(2026, 5, 1), False),
    (date(2026, 5, 19), False),
    (date(2026, 7, 15), False),
    (date(2026, 8, 30) , False),  # Sunday anyway
    (date(2026, 10, 29), False),
    (date(2026, 10, 28), True),   # half day, still trading
    (date(2026, 12, 31), True),   # NOT a holiday
    (date(2026, 3, 19), True),    # arife half day
    (date(2026, 3, 20), False),
    (date(2026, 5, 26), True),
    (date(2026, 5, 27), False),
    (date(2026, 5, 29), False),
])
def test_is_trading_day(d, expected):
    assert S.is_trading_day(d) is expected


def test_half_days():
    for d in (date(2026, 3, 19), date(2026, 5, 26), date(2026, 10, 28)):
        assert S.is_half_day(d)
        _, close = S.session_bounds(d)
        assert close.time() == time(12, 30)
    assert not S.is_half_day(date(2026, 6, 1))
    assert S.session_bounds(date(2026, 6, 6)) is None


def test_session_bounds_tz_aware():
    o, c = S.session_bounds(date(2026, 6, 1))
    assert o.time() == time(10, 0) and c.time() == time(18, 0)
    assert o.utcoffset().total_seconds() == 3 * 3600


def test_json_calendar_unverified_flag():
    import json
    data = json.loads(S.HOLIDAYS_FILE.read_text(encoding="utf-8"))
    assert data["verified"] is False and "source_note" in data
    assert "2027" not in data["years"]


@pytest.mark.parametrize("minutes,count", [(5, 96), (15, 32), (30, 16), (60, 8)])
def test_bar_grid_counts(minutes, count):
    bars = _ex_bars(date(2026, 6, 1), minutes)
    assert len(bars) == count
    assert bars[0].time() == time(10, 0)
    assert bars[-1].time() < time(18, 0)


def test_60m_starts_and_half_day_and_closed():
    bars = _ex_bars(date(2026, 6, 1), 60)
    assert [b.hour for b in bars] == list(range(10, 18))
    assert len(_ex_bars(date(2026, 10, 28), 5)) == 30
    assert _ex_bars(date(2026, 6, 6), 5) == []


def test_midday_single_price_optional():
    assert len(_ex_bars(date(2026, 6, 1), 60, midday_single_price=True)) == 7


def test_closing_auction_window():
    a, b = S.closing_auction_window(date(2026, 6, 1))
    assert (a.time(), b.time()) == (time(18, 0), time(18, 10))
    a, b = S.closing_auction_window(date(2026, 10, 28))
    assert (a.time(), b.time()) == (time(12, 30), time(12, 40))
    assert S.closing_auction_window(date(2026, 6, 6)) is None


@pytest.mark.parametrize("p,expected", [
    (10.004, 10.0), (10.005, 10.01), (20.01, 20.02), (20.03, 20.04),
    (49.99, 50.0), (50.02, 50.0), (50.03, 50.05), (99.97, 99.95), (100.04, 100.0),
    (100.06, 100.1),
])
def test_round_to_tick(p, expected):
    assert S.round_to_tick(p) == pytest.approx(expected)


@pytest.mark.parametrize("prev,lo,hi", [
    (10.00, 9.00, 11.00),
    (15.37, 13.84, 16.90),
    (30.00, 27.00, 33.00),
    (100.00, 90.00, 110.00),
    (123.45, 111.2, 135.7),
])
def test_daily_price_limits(prev, lo, hi):
    got_lo, got_hi = S.daily_price_limits(prev)
    assert got_lo == pytest.approx(lo)
    assert got_hi == pytest.approx(hi)


def test_price_limits_no_tick():
    assert S.daily_price_limits(15.37, tick_table=False) == (13.83, 16.91)


def test_last_completed_bar_start():
    now = datetime(2026, 6, 1, 11, 0)
    assert _ex_last(now, 15, 15).time() == time(10, 30)
    # before first bar completes -> previous trading day's last bar (Fri)
    r = _ex_last(datetime(2026, 6, 1, 10, 20), 15, 15)
    # 2026-05-29 is a Kurban holiday; 05-26 is a half day (closes 12:30)
    assert r.date() == date(2026, 5, 26)
    assert r.time() == time(12, 15)


@pytest.mark.parametrize("minutes,count,first,last", [
    (60, 9, time(9, 30), time(17, 30)),
    (15, 33, time(9, 45), time(17, 45)),
    (5, 97, time(9, 55), time(17, 55)),
    (30, 17, time(9, 30), time(17, 30)),  # unverified extrapolation
])
def test_yahoo_grid(minutes, count, first, last):
    bars = S.expected_bar_starts(date(2026, 6, 1), minutes, vendor="yahoo")
    assert len(bars) == count and bars[0].time() == first and bars[-1].time() == last
    assert bars == S.expected_bar_starts(date(2026, 6, 1), minutes)  # default vendor


def test_yahoo_15m_grid_shape_and_half_day():
    bars = S.expected_bar_starts(date(2026, 6, 1), 15)
    assert [b.time() for b in bars[:3]] == [time(9, 45), time(10, 0), time(10, 15)]
    half = S.expected_bar_starts(date(2026, 10, 28), 15)
    assert half[0].time() == time(9, 45) and half[-1].time() == time(12, 15) and len(half) == 11


def test_unknown_vendor():
    with pytest.raises(ValueError):
        S.expected_bar_starts(date(2026, 6, 1), 15, vendor="x")


def test_yahoo_last_completed():
    # 10:00 bar (15m) done at 10:30 incl. 15m delay; 09:45 first bar done at 10:15
    assert S.last_completed_bar_start(datetime(2026, 6, 1, 10, 16), 15, 15).time() == time(9, 45)
    assert S.last_completed_bar_start(datetime(2026, 6, 1, 10, 30), 15, 15).time() == time(10, 0)
    assert S.last_completed_bar_start(datetime(2026, 6, 1, 11, 0), 60, 15).time() == time(9, 30)
