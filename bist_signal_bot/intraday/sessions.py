"""BIST equity market session model (Europe/Istanbul). Pure, research-only.

Halt / circuit-breaker handling is intentionally out of scope (see ``halt_stub``).
Midday single-price session (13:00-14:00) is NOT assumed (unverified); opt in via
``midday_single_price=True`` which removes that window from the continuous bar grid.
"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:  # tzdata may be missing on Windows; Turkey is fixed UTC+3 since 2016.
    from zoneinfo import ZoneInfo

    IST: tzinfo = ZoneInfo("Europe/Istanbul")
except Exception:  # pragma: no cover
    IST = timezone(timedelta(hours=3), "Europe/Istanbul")

OPENING_AUCTION_COLLECT = (time(9, 40), time(9, 55))
OPENING_PRICE_DETERMINATION = (time(9, 55), time(10, 0))
CONTINUOUS_OPEN = time(10, 0)
CONTINUOUS_CLOSE = time(18, 0)
CLOSING_AUCTION = (time(18, 0), time(18, 10))
CLOSING_COLLECT = (time(18, 1), time(18, 5))
CLOSING_PRICE_DETERMINATION = (time(18, 5), time(18, 7))
CLOSING_TRADES = (time(18, 8), time(18, 10))

HALF_DAY_CLOSE = time(12, 30)
HALF_DAY_CLOSING_AUCTION = (time(12, 30), time(12, 40))
MIDDAY_SINGLE_PRICE = (time(13, 0), time(14, 0))  # unverified; opt-in only

PRICE_LIMIT_PCT = Decimal("0.10")

# (upper bound exclusive, tick)
_TICK_TABLE = (
    (Decimal("20.00"), Decimal("0.01")),
    (Decimal("50.00"), Decimal("0.02")),
    (Decimal("100.00"), Decimal("0.05")),
)
_TICK_TOP = Decimal("0.10")

# (month, day)
FIXED_HOLIDAYS = ((1, 1), (4, 23), (5, 1), (5, 19), (7, 15), (8, 30), (10, 29))
FIXED_HALF_DAYS = ((10, 28),)

HOLIDAYS_FILE = Path(__file__).with_name("bist_holidays.json")


def to_istanbul(dt: datetime) -> datetime:
    """Naive datetimes are interpreted as Istanbul local time."""
    if hasattr(dt, "to_pydatetime"):
        dt = dt.to_pydatetime()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def _as_date(d) -> date:
    return d.date() if isinstance(d, datetime) else d


@lru_cache(maxsize=4)
def _load_calendar(path: str) -> tuple[frozenset, frozenset]:
    holidays: set[date] = set()
    half: set[date] = set()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return frozenset(), frozenset()
    for entry in (data.get("years") or {}).values():
        for s in entry.get("holidays", []):
            holidays.add(date.fromisoformat(s))
        for s in entry.get("half_days", []):
            half.add(date.fromisoformat(s))
    return frozenset(holidays), frozenset(half)


def holiday_sets(path: Optional[Path] = None) -> tuple[frozenset, frozenset]:
    """JSON-listed (full-day holidays, half days); fixed dates are handled separately."""
    return _load_calendar(str(path or HOLIDAYS_FILE))


def is_holiday(d, holidays_path: Optional[Path] = None) -> bool:
    d = _as_date(d)
    if (d.month, d.day) in FIXED_HOLIDAYS:
        return True
    return d in holiday_sets(holidays_path)[0]


def is_half_day(d, holidays_path: Optional[Path] = None) -> bool:
    d = _as_date(d)
    if is_holiday(d, holidays_path) or d.weekday() >= 5:
        return False
    return (d.month, d.day) in FIXED_HALF_DAYS or d in holiday_sets(holidays_path)[1]


def is_trading_day(d, holidays_path: Optional[Path] = None) -> bool:
    d = _as_date(d)
    return d.weekday() < 5 and not is_holiday(d, holidays_path)


def _at(d: date, t: time) -> datetime:
    return datetime.combine(d, t, tzinfo=IST)


def session_bounds(d, half_day_close: time = HALF_DAY_CLOSE,
                   holidays_path: Optional[Path] = None) -> Optional[tuple[datetime, datetime]]:
    """Continuous-session (open, close), tz-aware Istanbul; None when closed."""
    d = _as_date(d)
    if not is_trading_day(d, holidays_path):
        return None
    close = half_day_close if is_half_day(d, holidays_path) else CONTINUOUS_CLOSE
    return _at(d, CONTINUOUS_OPEN), _at(d, close)


def closing_auction_window(d, half_day_close: time = HALF_DAY_CLOSE,
                           holidays_path: Optional[Path] = None) -> Optional[tuple[datetime, datetime]]:
    d = _as_date(d)
    if not is_trading_day(d, holidays_path):
        return None
    if is_half_day(d, holidays_path):
        return _at(d, half_day_close), _at(d, HALF_DAY_CLOSING_AUCTION[1])
    return _at(d, CLOSING_AUCTION[0]), _at(d, CLOSING_AUCTION[1])


VENDORS = ("yahoo", "exchange")


def _vendor_first_start(open_dt: datetime, minutes: int, vendor: str) -> datetime:
    """First bar start for the vendor grid.

    exchange: bars aligned to the 10:00 continuous open.
    yahoo (observed live for THYAO.IS): 1h -> 09:30..17:30 (9 bars); 15m -> 09:45 (carries the
    opening-auction print), 10:00..17:45 (33); 5m -> 09:55, 10:00..17:55 (97).
    UNVERIFIED extrapolation: for minutes < 60 the first bar starts at 10:00 - minutes
    (so 30m -> 09:30, 10:00..17:30, 17 bars); for minutes >= 60 bars are anchored at 09:30.
    """
    if vendor == "exchange":
        return open_dt
    if vendor != "yahoo":
        raise ValueError(f"unknown vendor: {vendor}")
    if minutes < 60:
        return open_dt - timedelta(minutes=minutes)
    return open_dt - timedelta(minutes=30)


def expected_bar_starts(d, minutes: int, midday_single_price: bool = False,
                        half_day_close: time = HALF_DAY_CLOSE,
                        holidays_path: Optional[Path] = None,
                        vendor: str = "yahoo") -> list[datetime]:
    """Bar-start timestamps for the day (closing auction excluded; bars start before the close).

    Half days: same first-bar rules, bars with start < close.
    """
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    b = session_bounds(d, half_day_close, holidays_path)
    if b is None:
        return []
    open_dt, close_dt = b
    step = timedelta(minutes=minutes)
    ms = _at(open_dt.date(), MIDDAY_SINGLE_PRICE[0])
    me = _at(open_dt.date(), MIDDAY_SINGLE_PRICE[1])
    out: list[datetime] = []
    cur = _vendor_first_start(open_dt, minutes, vendor)
    if vendor == "yahoo" and minutes < 60:
        # first (auction-print) bar, then the regular 10:00-aligned grid
        out.append(cur)
        cur = open_dt
    while cur < close_dt:
        if not (midday_single_price and ms <= cur < me):
            out.append(cur)
        cur += step
    return out


def last_completed_bar_start(now: datetime, minutes: int, data_delay_minutes: int = 15,
                             midday_single_price: bool = False,
                             holidays_path: Optional[Path] = None,
                             vendor: str = "yahoo") -> Optional[datetime]:
    """Latest grid bar whose start + minutes + delay <= now."""
    now = to_istanbul(now)
    step = timedelta(minutes=minutes)
    delay = timedelta(minutes=data_delay_minutes)
    for back in range(0, 15):
        d = now.date() - timedelta(days=back)
        for s in reversed(expected_bar_starts(d, minutes, midday_single_price,
                                              holidays_path=holidays_path, vendor=vendor)):
            if s + step + delay <= now:
                return s
    return None


def previous_trading_day(d, holidays_path: Optional[Path] = None) -> date:
    d = _as_date(d) - timedelta(days=1)
    while not is_trading_day(d, holidays_path):
        d -= timedelta(days=1)
    return d


def _tick_for(p: Decimal) -> Decimal:
    for upper, tick in _TICK_TABLE:
        if p < upper:
            return tick
    return _TICK_TOP


def round_to_tick(price: float) -> float:
    """Round to the nearest valid tick (half up) per the price-band tick table."""
    p = Decimal(str(price))
    tick = _tick_for(p)
    return float((p / tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick)


def daily_price_limits(prev_close: float, tick_table: bool = True) -> tuple[float, float]:
    """(floor, ceiling) = prev_close -/+ 10%; ceiling rounded down, floor rounded up to a valid tick."""
    pc = Decimal(str(prev_close))
    raw_hi = pc * (1 + PRICE_LIMIT_PCT)
    raw_lo = pc * (1 - PRICE_LIMIT_PCT)
    if not tick_table:
        return float(raw_lo.quantize(Decimal("0.01"))), float(raw_hi.quantize(Decimal("0.01")))
    hi_t, lo_t = _tick_for(raw_hi), _tick_for(raw_lo)
    hi = (raw_hi / hi_t).to_integral_value(rounding=ROUND_FLOOR) * hi_t
    lo = (raw_lo / lo_t).to_integral_value(rounding=ROUND_CEILING) * lo_t
    return float(lo), float(hi)


def halt_stub(*_args, **_kwargs) -> None:
    """Stub: trading halts / circuit breakers (volatility stops) are not modelled."""
    return None
