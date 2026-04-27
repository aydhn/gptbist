from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from bist_signal_bot.config.settings import settings

ISTANBUL_TZ = ZoneInfo(settings.DEFAULT_TIMEZONE)

def utc_now() -> datetime:
    """Returns the current UTC time as an aware datetime."""
    return datetime.now(timezone.utc)

def istanbul_now() -> datetime:
    """Returns the current time in Istanbul timezone as an aware datetime."""
    return datetime.now(ISTANBUL_TZ)

def ensure_timezone(dt: datetime, timezone_name: str = settings.DEFAULT_TIMEZONE) -> datetime:
    """Ensures the given datetime is timezone aware. If naive, sets to timezone_name."""
    tz = ZoneInfo(timezone_name)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)

def to_naive_istanbul(dt: datetime) -> datetime:
    """Converts a given datetime to Istanbul timezone and makes it naive."""
    istanbul_dt = ensure_timezone(dt, settings.DEFAULT_TIMEZONE)
    return istanbul_dt.replace(tzinfo=None)
