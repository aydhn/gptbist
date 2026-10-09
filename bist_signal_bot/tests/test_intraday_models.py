import pytest

from bist_signal_bot.intraday.models import (MAX_LOOKBACK_DAYS, interval_minutes, max_lookback_days,
                                             normalize_interval)


def test_normalize_aliases():
    assert normalize_interval("60m") == "1h"
    assert normalize_interval("1H") == "1h"
    assert normalize_interval("5m") == "5m"
    with pytest.raises(ValueError):
        normalize_interval("2m")


def test_interval_minutes():
    assert interval_minutes("60m") == 60
    assert interval_minutes("15m") == 15


def test_lookback_defaults_and_override():
    assert MAX_LOOKBACK_DAYS["1m"] == 7
    assert max_lookback_days("5m") == 60

    class S:
        INTRADAY_MAX_LOOKBACK_1H = 100

    assert max_lookback_days("60m", S()) == 100
    assert max_lookback_days("1m", S()) == 7
