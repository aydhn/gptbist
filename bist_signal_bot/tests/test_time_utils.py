from datetime import date, datetime, time

import pytest

from bist_signal_bot.core.exceptions import ConfigurationError
from bist_signal_bot.core.time_utils import (
    combine_date_time_istanbul,
    ensure_istanbul_timezone,
    is_timezone_aware,
    parse_hhmm,
    parse_iso_date_list,
)


def test_parse_hhmm_valid():
    t = parse_hhmm("10:30")
    assert t == time(hour=10, minute=30)

def test_parse_hhmm_invalid():
    with pytest.raises(ConfigurationError):
        parse_hhmm("invalid")
    with pytest.raises(ConfigurationError):
        parse_hhmm("25:00")

def test_combine_date_time_istanbul():
    d = date(2023, 1, 1)
    dt = combine_date_time_istanbul(d, "10:00")
    assert dt.hour == 10
    assert dt.minute == 0
    assert is_timezone_aware(dt)

def test_ensure_istanbul_timezone_naive():
    dt = datetime(2023, 1, 1, 10, 0)
    aware_dt = ensure_istanbul_timezone(dt)
    assert is_timezone_aware(aware_dt)

def test_parse_iso_date_list_empty():
    assert parse_iso_date_list("") == set()
    assert parse_iso_date_list("  ") == set()

def test_parse_iso_date_list_valid():
    dates = parse_iso_date_list("2023-01-01, 2023-01-02")
    assert len(dates) == 2
    assert date(2023, 1, 1) in dates
    assert date(2023, 1, 2) in dates

def test_parse_iso_date_list_invalid():
    with pytest.raises(ConfigurationError):
        parse_iso_date_list("2023-13-01")
