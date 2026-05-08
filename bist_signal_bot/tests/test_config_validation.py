import pytest
from pydantic import BaseModel

from bist_signal_bot.config.validation import (
    enforce_production_safety,
    validate_app_env,
    validate_default_market,
    validate_iso_date_list,
    validate_market_hours,
    validate_run_mode,
    validate_telegram_message_length,
    validate_time_format,
)
from bist_signal_bot.core.exceptions import ConfigurationError, OperationalSafetyError


class MockSettings(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    APP_ENV: str = "production"
    DEBUG_TRACEBACKS: bool = False
    DRY_RUN: bool = True
    ENABLE_TELEGRAM: bool = False
    TELEGRAM_DRY_RUN: bool = True

def test_validate_app_env():
    assert validate_app_env("development") == "development"
    with pytest.raises(ConfigurationError):
        validate_app_env("staging")

def test_validate_run_mode():
    assert validate_run_mode("research") == "research"
    with pytest.raises(ConfigurationError):
        validate_run_mode("invalid")

def test_validate_default_market():
    assert validate_default_market("bist") == "BIST"
    with pytest.raises(ConfigurationError):
        validate_default_market("NYSE")

def test_validate_telegram_message_length():
    assert validate_telegram_message_length(1000) == 1000
    with pytest.raises(ConfigurationError):
        validate_telegram_message_length(100)

def test_validate_time_format():
    assert validate_time_format("10:00", "BIST_REGULAR_OPEN") == "10:00"
    with pytest.raises(ConfigurationError):
        validate_time_format("1000", "BIST_REGULAR_OPEN")

def test_validate_market_hours():
    validate_market_hours("10:00", "18:00")
    with pytest.raises(ConfigurationError):
        validate_market_hours("18:00", "10:00")

def test_validate_iso_date_list():
    assert validate_iso_date_list("2026-01-01,2026-04-23") == "2026-01-01,2026-04-23"
    with pytest.raises(ConfigurationError):
        validate_iso_date_list("01/01/2026")

def test_enforce_production_safety():
    settings = MockSettings()
    # Should pass
    enforce_production_safety(settings)

    settings.DEBUG_TRACEBACKS = True
    with pytest.raises(ConfigurationError):
        enforce_production_safety(settings)

    settings.DEBUG_TRACEBACKS = False
    settings.DRY_RUN = False
    with pytest.raises(OperationalSafetyError):
        enforce_production_safety(settings)
