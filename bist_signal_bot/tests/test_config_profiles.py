import pytest

from bist_signal_bot.config.profiles import AppEnvironment, get_profile
from bist_signal_bot.core.exceptions import ConfigurationError


def test_get_profile_development():
    profile = get_profile("development")
    assert profile.env == AppEnvironment.DEVELOPMENT
    assert profile.safe_defaults["DRY_RUN"] is True

def test_get_profile_test():
    profile = get_profile("test")
    assert profile.env == AppEnvironment.TEST
    assert profile.safe_defaults["ENABLE_TELEGRAM"] is False
    assert profile.safe_defaults["LOG_TO_FILE"] is False

def test_get_profile_production():
    profile = get_profile("production")
    assert profile.env == AppEnvironment.PRODUCTION
    assert profile.safe_defaults["MASK_SECRETS_IN_LOGS"] is True
    assert profile.safe_defaults["DEBUG_TRACEBACKS"] is False

def test_get_profile_invalid():
    with pytest.raises(ConfigurationError):
        get_profile("unknown")
