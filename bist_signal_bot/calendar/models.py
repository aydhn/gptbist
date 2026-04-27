from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel


class MarketSessionType(str, Enum):
    REGULAR = "REGULAR"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"
    CLOSED = "CLOSED"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"
    UNKNOWN = "UNKNOWN"

class MarketDayType(str, Enum):
    TRADING_DAY = "TRADING_DAY"
    WEEKEND = "WEEKEND"
    HOLIDAY = "HOLIDAY"
    HALF_DAY = "HALF_DAY"
    UNKNOWN = "UNKNOWN"

class MarketSessionStatus(BaseModel):
    now: datetime
    timezone: str
    is_trading_day: bool
    is_market_open: bool
    day_type: MarketDayType
    session_type: MarketSessionType
    market_open: datetime | None = None
    market_close: datetime | None = None
    next_trading_day: date | None = None
    previous_trading_day: date | None = None
    message: str = ""
