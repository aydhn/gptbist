import pytest
from unittest.mock import MagicMock

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import (
    BistSignalBotError,
    ConfigurationError,
    DataQualityError,
    DataProviderError
)
from bist_signal_bot.core.error_handler import ErrorHandler

def test_classify_error():
    handler = ErrorHandler(Settings())
    assert handler.classify_error(ConfigurationError("test")) == "CONFIGURATION"
    assert handler.classify_error(DataQualityError("test")) == "DATA_QUALITY"
    assert handler.classify_error(DataProviderError("test")) == "DATA_PROVIDER"
    assert handler.classify_error(ValueError("test")) == "UNKNOWN"

def test_is_recoverable():
    handler = ErrorHandler(Settings())
    assert handler.is_recoverable(BistSignalBotError("test", recoverable=True)) is True
    assert handler.is_recoverable(BistSignalBotError("test", recoverable=False)) is False
    assert handler.is_recoverable(ValueError("test")) is False

def test_build_error_summary():
    handler = ErrorHandler(Settings())
    err = ConfigurationError("Bad config")
    context = {"key": "val"}
    summary = handler.build_error_summary(err, context)

    assert summary["error_type"] == "CONFIGURATION"
    assert summary["error_class"] == "ConfigurationError"
    assert summary["message"] == "Bad config"
    assert summary["recoverable"] is True
    assert summary["context"] == {"key": "val"}
    assert "timestamp" in summary

def test_handle_exception_sanitizes_context():
    handler = ErrorHandler(Settings(ENABLE_ERROR_NOTIFICATIONS=False))
    err = ValueError("Test")
    context = {"token": "secret123456789", "normal": "val"}
    summary = handler.handle_exception(err, context=context, notify=False)

    assert summary["context"]["token"] == "secr...6789"
    assert summary["context"]["normal"] == "val"

def test_handle_exception_calls_notifier():
    mock_notifier = MagicMock()
    settings = Settings(ENABLE_ERROR_NOTIFICATIONS=True, ERROR_NOTIFICATION_MIN_LEVEL="ERROR")
    handler = ErrorHandler(settings, notifier=mock_notifier)

    err = ValueError("Test Error")
    handler.handle_exception(err, context={"info": "test"}, notify=True)

    mock_notifier.send_error.assert_called_once()

def test_handle_exception_notifier_failure_does_not_crash():
    mock_notifier = MagicMock()
    mock_notifier.send_error.side_effect = Exception("Notifier failed")

    settings = Settings(ENABLE_ERROR_NOTIFICATIONS=True)
    handler = ErrorHandler(settings, notifier=mock_notifier)

    # This should not raise an exception
    handler.handle_exception(ValueError("Main Error"))
