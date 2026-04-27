import re
from typing import Any

from bist_signal_bot.core.exceptions import ConfigurationError, OperationalSafetyError


def validate_app_env(env: str) -> str:
    from bist_signal_bot.config.profiles import AppEnvironment
    valid_envs = [e.value for e in AppEnvironment]
    if env.lower() not in valid_envs:
        raise ConfigurationError(f"Invalid APP_ENV: '{env}'. Valid values are: {valid_envs}")
    return env.lower()

def validate_run_mode(mode: str) -> str:
    from bist_signal_bot.config.profiles import RunMode
    valid_modes = [e.value for e in RunMode]
    if mode.lower() not in valid_modes:
        raise ConfigurationError(f"Invalid RUN_MODE: '{mode}'. Valid values are: {valid_modes}")
    return mode.lower()

def validate_default_market(market: str) -> str:
    if market.upper() != "BIST":
        raise ConfigurationError(f"DEFAULT_MARKET must be 'BIST', got: '{market}'")
    return market.upper()

def validate_positive_int(value: int, field_name: str) -> int:
    if value <= 0:
        raise ConfigurationError(f"{field_name} must be greater than 0, got {value}")
    return value

def validate_non_negative_int(value: int, field_name: str) -> int:
    if value < 0:
        raise ConfigurationError(f"{field_name} must be non-negative, got {value}")
    return value

def validate_non_negative_float(value: float, field_name: str) -> float:
    if value < 0.0:
        raise ConfigurationError(f"{field_name} must be non-negative, got {value}")
    return value

def validate_percentage(value: float, field_name: str) -> float:
    if not (0.0 <= value <= 1.0):
        raise ConfigurationError(f"{field_name} must be between 0.0 and 1.0, got {value}")
    return value

def validate_telegram_message_length(value: int) -> int:
    if not (500 <= value <= 4096):
        raise ConfigurationError(f"TELEGRAM_MESSAGE_MAX_LENGTH must be between 500 and 4096, got {value}")
    return value

def validate_time_format(time_str: str, field_name: str) -> str:
    if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", time_str):
        raise ConfigurationError(f"Invalid time format for {field_name}: '{time_str}'. Expected HH:MM")
    return time_str

def validate_market_hours(open_time: str, close_time: str) -> None:
    if open_time >= close_time:
        raise ConfigurationError(f"BIST_REGULAR_OPEN ('{open_time}') must be strictly before BIST_REGULAR_CLOSE ('{close_time}')")

def validate_iso_date_list(dates_str: str) -> str:
    if not dates_str:
        return ""
    dates = [d.strip() for d in dates_str.split(",") if d.strip()]
    for date_str in dates:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise ConfigurationError(f"Invalid ISO date in manual holidays list: '{date_str}'. Expected YYYY-MM-DD")
    return dates_str

def validate_storage_format(format_str: str) -> str:
    if format_str.lower() != "csv":
        raise ConfigurationError(f"STORAGE_FORMAT currently only supports 'csv', got '{format_str}'")
    return format_str.lower()

def enforce_production_safety(settings: Any) -> None:
    """Enforces safety rules that only apply in production environment."""
    env = getattr(settings, "APP_ENV", "").lower()

    if env == "production":
        if getattr(settings, "DEBUG_TRACEBACKS", False):
            raise ConfigurationError("DEBUG_TRACEBACKS must be False in production environment")

        # Real trading is strictly not allowed in this system
        if not getattr(settings, "DRY_RUN", True):
            raise OperationalSafetyError("DRY_RUN cannot be False in production. Real trading is not implemented or allowed in this system.")

        # Check telegram
        from bist_signal_bot.config.secrets import validate_telegram_secrets
        validate_telegram_secrets(settings)
