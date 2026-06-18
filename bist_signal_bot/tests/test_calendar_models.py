import pytest
from datetime import date, datetime, timezone
from pydantic import ValidationError

from bist_signal_bot.calendar.models import MarketSessionType, MarketDayType, MarketSessionStatus

def test_market_session_type_enum():
    """Test MarketSessionType enum values."""
    assert MarketSessionType.REGULAR == "REGULAR"
    assert MarketSessionType.PRE_MARKET == "PRE_MARKET"
    assert MarketSessionType.POST_MARKET == "POST_MARKET"
    assert MarketSessionType.CLOSED == "CLOSED"
    assert MarketSessionType.HOLIDAY == "HOLIDAY"
    assert MarketSessionType.WEEKEND == "WEEKEND"
    assert MarketSessionType.UNKNOWN == "UNKNOWN"

def test_market_day_type_enum():
    """Test MarketDayType enum values."""
    assert MarketDayType.TRADING_DAY == "TRADING_DAY"
    assert MarketDayType.WEEKEND == "WEEKEND"
    assert MarketDayType.HOLIDAY == "HOLIDAY"
    assert MarketDayType.HALF_DAY == "HALF_DAY"
    assert MarketDayType.UNKNOWN == "UNKNOWN"

def test_market_session_status_valid_creation():
    """Test creating a MarketSessionStatus with valid required fields."""
    now = datetime.now(timezone.utc)
    status = MarketSessionStatus(
        now=now,
        timezone="Europe/Istanbul",
        is_trading_day=True,
        is_market_open=False,
        day_type=MarketDayType.TRADING_DAY,
        session_type=MarketSessionType.PRE_MARKET
    )

    assert status.now == now
    assert status.timezone == "Europe/Istanbul"
    assert status.is_trading_day is True
    assert status.is_market_open is False
    assert status.day_type == MarketDayType.TRADING_DAY
    assert status.session_type == MarketSessionType.PRE_MARKET

    # Check defaults
    assert status.market_open is None
    assert status.market_close is None
    assert status.next_trading_day is None
    assert status.previous_trading_day is None
    assert status.message == ""

def test_market_session_status_with_optional_fields():
    """Test creating a MarketSessionStatus with optional fields populated."""
    now = datetime.now(timezone.utc)
    market_open = datetime(2023, 10, 2, 9, 55, tzinfo=timezone.utc)
    market_close = datetime(2023, 10, 2, 18, 10, tzinfo=timezone.utc)
    next_day = date(2023, 10, 3)
    prev_day = date(2023, 9, 29)

    status = MarketSessionStatus(
        now=now,
        timezone="Europe/Istanbul",
        is_trading_day=True,
        is_market_open=True,
        day_type=MarketDayType.TRADING_DAY,
        session_type=MarketSessionType.REGULAR,
        market_open=market_open,
        market_close=market_close,
        next_trading_day=next_day,
        previous_trading_day=prev_day,
        message="Market is currently open"
    )

    assert status.market_open == market_open
    assert status.market_close == market_close
    assert status.next_trading_day == next_day
    assert status.previous_trading_day == prev_day
    assert status.message == "Market is currently open"

def test_market_session_status_missing_required_fields():
    """Test that validation fails when required fields are missing."""
    with pytest.raises(ValidationError):
        MarketSessionStatus(
            timezone="Europe/Istanbul",
            is_trading_day=True,
            is_market_open=True,
            day_type=MarketDayType.TRADING_DAY,
            session_type=MarketSessionType.REGULAR
        ) # Missing now

    with pytest.raises(ValidationError):
        MarketSessionStatus(
            now=datetime.now(timezone.utc),
            timezone="Europe/Istanbul",
            is_trading_day=True,
            is_market_open=True,
            day_type=MarketDayType.TRADING_DAY
            # Missing session_type
        )

def test_market_session_status_invalid_types():
    """Test that validation fails with invalid types."""
    with pytest.raises(ValidationError):
        MarketSessionStatus(
            now="not-a-datetime",
            timezone="Europe/Istanbul",
            is_trading_day=True,
            is_market_open=True,
            day_type=MarketDayType.TRADING_DAY,
            session_type=MarketSessionType.REGULAR
        )
