import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import run_healthcheck


def test_healthcheck_includes_calendar():
    """Test that the healthcheck returns a dictionary with expected calendar keys."""
    health_status = run_healthcheck()
    assert isinstance(health_status, dict)
    assert "calendar" in health_status

    calendar_info = health_status["calendar"]
    assert "market_timezone" in calendar_info
    assert "regular_open" in calendar_info
    assert "regular_close" in calendar_info
    assert "manual_holiday_count" in calendar_info
    assert "today_day_type" in calendar_info
    assert "is_today_trading_day" in calendar_info
    assert "is_market_open_now" in calendar_info
    assert "next_trading_day" in calendar_info
    assert "previous_trading_day" in calendar_info
    assert "daily_signal_enabled" in calendar_info
    assert "intraday_signal_enabled" in calendar_info
    assert "signal_after_close_minutes" in calendar_info
