"""Intraday interval helpers and Yahoo lookback limits."""
from __future__ import annotations

_ALIASES = {"60m": "1h", "1h": "1h", "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1d": "1d", "1day": "1d"}
_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "1d": 1440}

# Yahoo limits (1h value unverified).
MAX_LOOKBACK_DAYS = {"1m": 7, "5m": 60, "15m": 60, "30m": 60, "1h": 730, "1d": 36500}


def normalize_interval(s: str) -> str:
    key = str(s).strip().lower()
    if key not in _ALIASES:
        raise ValueError(f"Unsupported intraday interval: {s!r}")
    return _ALIASES[key]


def interval_minutes(s: str) -> int:
    return _MINUTES[normalize_interval(s)]


def max_lookback_days(interval: str, settings=None) -> int:
    """Lookback limit; overridable via INTRADAY_MAX_LOOKBACK_<INTERVAL> (e.g. _1H, _5M)."""
    iv = normalize_interval(interval)
    if settings is not None:
        v = getattr(settings, f"INTRADAY_MAX_LOOKBACK_{iv.upper()}", None)
        try:
            if v is not None and int(v) > 0:
                return int(v)
        except (TypeError, ValueError):
            pass
    return MAX_LOOKBACK_DAYS[iv]
