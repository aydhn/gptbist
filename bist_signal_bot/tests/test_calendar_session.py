import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import Mock, patch

from bist_signal_bot.calendar.session import BistMarketSessionService
from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.calendar.models import MarketDayType, MarketSessionType, MarketSessionStatus

@pytest.fixture
def mock_calendar():
    calendar = Mock(spec=BistMarketCalendar)
    calendar.timezone_name = "Europe/Istanbul"
    # Default mock returns
    calendar.get_day_type.return_value = MarketDayType.TRADING_DAY
    calendar.is_trading_day.return_value = True
    calendar.next_trading_day.return_value = date(2023, 10, 3)
    calendar.previous_trading_day.return_value = date(2023, 9, 29)
    return calendar

@pytest.fixture
def session_service(mock_calendar):
    return BistMarketSessionService(
        calendar=mock_calendar,
        signal_after_close_minutes=15,
        intraday_signal_enabled=True,
        daily_signal_enabled=True
    )

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_get_status_weekend(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 9, 30, 12, 0, tzinfo=timezone.utc) # Saturday
    mock_ensure_tz.return_value = now

    mock_calendar.is_trading_day.return_value = False
    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None
    mock_calendar.get_day_type.return_value = MarketDayType.WEEKEND
    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None

    status = session_service.get_status(now)

    assert status.session_type == MarketSessionType.WEEKEND
    assert status.is_market_open is False
    assert status.is_trading_day is False
    assert status.message == "Market is closed for the weekend."

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_get_status_holiday(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 29, 12, 0, tzinfo=timezone.utc) # Republic Day
    mock_ensure_tz.return_value = now

    mock_calendar.is_trading_day.return_value = False
    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None
    mock_calendar.get_day_type.return_value = MarketDayType.HOLIDAY
    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None

    status = session_service.get_status(now)

    assert status.session_type == MarketSessionType.HOLIDAY
    assert status.is_market_open is False
    assert status.is_trading_day is False
    assert status.message == "Market is closed for a holiday."

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_get_status_pre_market(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 9, 30, tzinfo=timezone.utc) # Monday 09:30
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    status = session_service.get_status(now)

    assert status.session_type == MarketSessionType.PRE_MARKET
    assert status.is_market_open is False
    assert status.is_trading_day is True
    assert status.message == "Market is in pre-market session."

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_get_status_open(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc) # Monday 14:00
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    status = session_service.get_status(now)

    assert status.session_type == MarketSessionType.REGULAR
    assert status.is_market_open is True
    assert status.is_trading_day is True
    assert status.message == "Market is open."

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_get_status_post_market(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 18, 30, tzinfo=timezone.utc) # Monday 18:30
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    status = session_service.get_status(now)

    assert status.session_type == MarketSessionType.POST_MARKET
    assert status.is_market_open is False
    assert status.is_trading_day is True
    assert status.message == "Market is in post-market session."

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_get_status_no_hours(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 12, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None

    status = session_service.get_status(now)

    assert status.session_type == MarketSessionType.CLOSED
    assert status.is_market_open is False
    assert status.message == "Market hours not defined for today."

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_is_market_open(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    assert session_service.is_market_open(now) is True

    now_closed = datetime(2023, 10, 2, 9, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now_closed
    assert session_service.is_market_open(now_closed) is False


@patch("bist_signal_bot.calendar.session.istanbul_now")
def test_is_market_open_no_now(mock_istanbul_now, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_istanbul_now.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    assert session_service.is_market_open() is True


@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_generate_intraday_signal(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    # Enabled and open
    assert session_service.should_generate_intraday_signal(now) is True

    # Disabled
    session_service.intraday_signal_enabled = False
    assert session_service.should_generate_intraday_signal(now) is False

    # Enabled but closed
    session_service.intraday_signal_enabled = True
    now_closed = datetime(2023, 10, 2, 9, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now_closed
    assert session_service.should_generate_intraday_signal(now_closed) is False

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_generate_daily_signal(mock_ensure_tz, session_service, mock_calendar):
    now_pre = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    now_post = datetime(2023, 10, 2, 18, 20, tzinfo=timezone.utc)

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    # Before target time
    mock_ensure_tz.return_value = now_pre
    assert session_service.should_generate_daily_signal(now_pre) is False

    # After target time (18:00 + 15 mins = 18:15)
    mock_ensure_tz.return_value = now_post
    assert session_service.should_generate_daily_signal(now_post) is True

    # Disabled
    session_service.daily_signal_enabled = False
    assert session_service.should_generate_daily_signal(now_post) is False
    session_service.daily_signal_enabled = True

    # Non-trading day
    mock_calendar.is_trading_day.return_value = False
    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None
    assert session_service.should_generate_daily_signal(now_post) is False

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_send_daily_report(mock_ensure_tz, session_service, mock_calendar):
    now_post = datetime(2023, 10, 2, 18, 20, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now_post

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    assert session_service.should_send_daily_report(now_post) is True

    session_service.daily_signal_enabled = False
    assert session_service.should_send_daily_report(now_post) is False

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_send_daily_report_before_target(mock_ensure_tz, session_service, mock_calendar):
    now_pre = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now_pre

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    assert session_service.should_send_daily_report(now_pre) is False

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_send_daily_report_non_trading_day(mock_ensure_tz, session_service, mock_calendar):
    now_post = datetime(2023, 10, 2, 18, 20, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now_post

    mock_calendar.is_trading_day.return_value = False
    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None

    assert session_service.should_send_daily_report(now_post) is False

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_send_daily_report_no_market_close(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None

    assert session_service.should_send_daily_report(now) is False

@patch("bist_signal_bot.calendar.session.istanbul_now")
def test_should_send_daily_report_no_now(mock_istanbul_now, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 18, 20, tzinfo=timezone.utc)
    mock_istanbul_now.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    assert session_service.should_send_daily_report() is True # Passed no now

@patch("bist_signal_bot.calendar.session.BistMarketCalendar")
def test_from_settings(mock_calendar_class):
    from bist_signal_bot.config.settings import Settings

    mock_calendar_instance = Mock()
    mock_calendar_class.from_settings.return_value = mock_calendar_instance

    settings = Settings(
        BIST_SIGNAL_AFTER_CLOSE_MINUTES=30,
        BIST_INTRADAY_SIGNAL_ENABLED=True,
        BIST_DAILY_SIGNAL_ENABLED=False
    )

    service = BistMarketSessionService.from_settings(settings)

    mock_calendar_class.from_settings.assert_called_once_with(settings)
    assert service.calendar == mock_calendar_instance
    assert service.signal_after_close_minutes == 30
    assert service.intraday_signal_enabled is True
    assert service.daily_signal_enabled is False


@patch("bist_signal_bot.calendar.session.istanbul_now")
def test_get_status_no_now(mock_istanbul_now, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_istanbul_now.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    status = session_service.get_status() # Passed no now

    assert status.session_type == MarketSessionType.REGULAR
    assert status.is_market_open is True

@patch("bist_signal_bot.calendar.session.ensure_istanbul_timezone")
def test_should_generate_daily_signal_no_market_close(mock_ensure_tz, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_ensure_tz.return_value = now

    mock_calendar.market_open_datetime.return_value = None
    mock_calendar.market_close_datetime.return_value = None

    assert session_service.should_generate_daily_signal(now) is False

@patch("bist_signal_bot.calendar.session.istanbul_now")
def test_should_generate_intraday_signal_no_now(mock_istanbul_now, session_service, mock_calendar):
    now = datetime(2023, 10, 2, 14, 0, tzinfo=timezone.utc)
    mock_istanbul_now.return_value = now

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    # Enabled and open
    assert session_service.should_generate_intraday_signal() is True

    # Disabled
    session_service.intraday_signal_enabled = False
    assert session_service.should_generate_intraday_signal() is False


@patch("bist_signal_bot.calendar.session.istanbul_now")
def test_should_generate_daily_signal_no_now(mock_istanbul_now, session_service, mock_calendar):
    now_post = datetime(2023, 10, 2, 18, 20, tzinfo=timezone.utc)
    mock_istanbul_now.return_value = now_post

    mock_calendar.market_open_datetime.return_value = datetime(2023, 10, 2, 10, 0, tzinfo=timezone.utc)
    mock_calendar.market_close_datetime.return_value = datetime(2023, 10, 2, 18, 0, tzinfo=timezone.utc)

    # After target time (18:00 + 15 mins = 18:15)
    assert session_service.should_generate_daily_signal() is True

    # Disabled
    session_service.daily_signal_enabled = False
    assert session_service.should_generate_daily_signal() is False
