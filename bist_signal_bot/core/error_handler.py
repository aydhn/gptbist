import logging
import traceback
from datetime import UTC, datetime
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import (
    BistSignalBotError,
    ConfigurationError,
    DataProviderError,
    DataQualityError,
    MarketCalendarError,
    NotificationError,
    StorageError,
)
from bist_signal_bot.core.logging_setup import safe_log_dict
from bist_signal_bot.core.safety import sanitize_mapping


class ErrorHandler:
    def __init__(self, settings: Settings, notifier=None, logger: logging.Logger | None = None):
        self.settings = settings
        self.notifier = notifier
        self.logger = logger or logging.getLogger("bist_signal_bot.error_handler")

    def handle_exception(self, error: Exception, context: dict[str, Any] | None = None, notify: bool = True) -> dict[str, Any]:
        """Handles an exception by sanitizing context, logging, optionally notifying, and returning a summary."""
        sanitized_context = sanitize_mapping(context) if context else {}
        error_summary = self.build_error_summary(error, sanitized_context)

        # Log error
        log_msg = f"Handled Exception: {error_summary['error_class']} - {error_summary['message']}"
        self.logger.error(log_msg)

        # Log sanitized context safely
        if sanitized_context:
            safe_log_dict(self.logger, logging.DEBUG, "Error Context", sanitized_context, self.settings.MASK_SECRETS_IN_LOGS)

        if self.settings.DEBUG_TRACEBACKS:
            self.logger.debug(f"Traceback:\n{''.join(traceback.format_exception(type(error), error, error.__traceback__))}")

        # Send Telegram notification
        min_level = self.settings.ERROR_NOTIFICATION_MIN_LEVEL.upper()
        if self.settings.ENABLE_ERROR_NOTIFICATIONS and notify and self.notifier and min_level in ["ERROR", "CRITICAL"]:
             try:
                 # notifier.send_error is expected to format the error safely
                 self.notifier.send_error(error, sanitized_context)
             except Exception as notify_err:
                 self.logger.error(f"Failed to send error notification: {notify_err}")

        return error_summary

    def classify_error(self, error: Exception) -> str:
        """Classifies the exception into a broader category string."""
        if isinstance(error, ConfigurationError):
            return "CONFIGURATION"
        if isinstance(error, DataProviderError):
            return "DATA_PROVIDER"
        if isinstance(error, StorageError):
            return "STORAGE"
        if isinstance(error, DataQualityError):
            return "DATA_QUALITY"
        if isinstance(error, MarketCalendarError):
            return "CALENDAR"
        if isinstance(error, NotificationError):
            return "NOTIFICATION"

        return "UNKNOWN"

    def is_recoverable(self, error: Exception) -> bool:
        """Determines if the application should attempt to recover from this error."""
        if isinstance(error, BistSignalBotError):
            return error.recoverable
        return False

    def build_error_summary(self, error: Exception, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Builds a structured dictionary summarizing the error."""
        return {
            "error_type": self.classify_error(error),
            "error_class": type(error).__name__,
            "message": str(error),
            "recoverable": self.is_recoverable(error),
            "context": context or {},
            "timestamp": datetime.now(UTC).isoformat()
        }
