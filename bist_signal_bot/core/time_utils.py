from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from bist_signal_bot.config.settings import settings

ISTANBUL_TZ = ZoneInfo(settings.DEFAULT_TIMEZONE)

def utc_now() -> datetime:
    """Returns the current UTC time as an aware datetime."""
    return datetime.now(UTC)

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

from datetime import date, time

from bist_signal_bot.core.exceptions import ConfigurationError


def parse_hhmm(value: str) -> time:
    """Parses a string in 'HH:MM' format to a datetime.time object."""
    try:
        hour, minute = map(int, value.split(':'))
        return time(hour=hour, minute=minute)
    except (ValueError, AttributeError) as e:
        raise ConfigurationError(f"Invalid time format: '{value}'. Expected 'HH:MM'.") from e

def combine_date_time_istanbul(day: date, hhmm: str) -> datetime:
    """Combines a date and a time string into an Istanbul timezone aware datetime."""
    t = parse_hhmm(hhmm)
    dt = datetime.combine(day, t)
    return ensure_timezone(dt, settings.MARKET_TIMEZONE)

def is_timezone_aware(dt: datetime) -> bool:
    """Checks if a datetime object is timezone aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

def ensure_istanbul_timezone(dt: datetime) -> datetime:
    """Ensures datetime is in Istanbul timezone, either by replacing or astimezone."""
    return ensure_timezone(dt, settings.MARKET_TIMEZONE)

def parse_iso_date_list(value: str) -> set[date]:
    """Parses a comma-separated list of ISO date strings into a set of date objects."""
    if not value or not value.strip():
        return set()
    dates = set()
    for ds in value.split(','):
        ds = ds.strip()
        if ds:
            try:
                dates.add(date.fromisoformat(ds))
            except ValueError as e:
                raise ConfigurationError(f"Invalid date format in list: '{ds}'. Expected 'YYYY-MM-DD'.") from e
    return dates
