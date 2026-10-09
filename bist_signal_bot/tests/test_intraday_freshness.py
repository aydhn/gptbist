from datetime import datetime

import pytest

from bist_signal_bot.intraday.freshness import check_freshness


def dt(*a):
    return datetime(*a)


@pytest.mark.parametrize("last,now,ok,lag", [
    (dt(2026, 6, 1, 10, 30), dt(2026, 6, 1, 11, 0), True, 0),
    (dt(2026, 6, 1, 10, 0), dt(2026, 6, 1, 11, 0), True, 2),
    (dt(2026, 6, 1, 9 + 1, 0), dt(2026, 6, 1, 12, 0), False, 6),
    # closed: Saturday, last bar is Friday's last 15m bar
    (dt(2026, 6, 5, 17, 45), dt(2026, 6, 6, 12, 0), True, 0),
    # closed but stale by a bar
    (dt(2026, 6, 5, 17, 30), dt(2026, 6, 6, 12, 0), True, 1),
    (dt(2026, 6, 5, 16, 0), dt(2026, 6, 6, 12, 0), False, 7),
    # evening after close
    (dt(2026, 6, 1, 17, 45), dt(2026, 6, 1, 20, 0), True, 0),
    # next morning before first bar completes (10:00 bar done at 10:30)
    (dt(2026, 6, 1, 17, 45), dt(2026, 6, 2, 10, 20), True, 0),
])
def test_freshness_table(last, now, ok, lag):
    r = check_freshness(last, now, 15, vendor="exchange")
    assert (r.ok, r.lag_bars) == (ok, lag)


def test_none_last_bar():
    r = check_freshness(None, dt(2026, 6, 1, 11, 0), 15)
    assert not r.ok and r.reason == "no_bars"


def test_holiday_weekend_gap_not_counted_as_lag():
    # Friday 17:00 60m bar, now Monday 10:50 (10:00 bar not complete w/ delay) -> fresh
    r = check_freshness(dt(2026, 6, 5, 17, 0), dt(2026, 6, 8, 10, 50), 60, vendor="exchange")
    assert r.ok and r.lag_bars == 0


def test_custom_tolerance():
    r = check_freshness(dt(2026, 6, 1, 10, 0), dt(2026, 6, 1, 11, 0), 15, max_lag_bars=1, vendor="exchange")
    assert not r.ok and r.lag_bars == 2


def test_yahoo_freshness():
    # Monday 10:20: first completed 15m bar is 09:45 (ends 10:00, +15 delay = 10:15)
    assert check_freshness(dt(2026, 6, 1, 9, 45), dt(2026, 6, 1, 10, 20), 15).lag_bars == 0
    # 1h bars: 09:30 done at 10:30+15=10:45; at 11:00 last completed is 09:30
    r = check_freshness(dt(2026, 6, 1, 9, 30), dt(2026, 6, 1, 11, 0), 60)
    assert r.ok and r.lag_bars == 0
    # prior-session last yahoo 15m bar (17:45) counts as fresh while closed
    assert check_freshness(dt(2026, 6, 5, 17, 45), dt(2026, 6, 6, 12, 0), 15).ok
    # stale: 09:45 bar while 11:30 target
    r = check_freshness(dt(2026, 6, 1, 9, 45), dt(2026, 6, 1, 12, 0), 15)
    assert not r.ok and r.lag_bars == 7
