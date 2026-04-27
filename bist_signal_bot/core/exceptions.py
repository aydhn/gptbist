from typing import Any


class BistSignalBotError(Exception):
    """Base exception class for BIST Signal Bot."""
    def __init__(self, message: str, error_code: str | None = None, context: dict[str, Any] | None = None, recoverable: bool = True):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable

class ConfigurationError(BistSignalBotError):
    """Raised when there is a configuration issue."""
    pass

class DataProviderError(BistSignalBotError):
    """Raised when a data provider fails to fetch data."""
    pass

class StrategyError(BistSignalBotError):
    """Raised when a strategy execution fails."""
    pass

class InvalidSymbolError(BistSignalBotError):
    """Raised when a symbol is invalid or doesn't match internal format rules."""
    pass

class SymbolUniverseError(BistSignalBotError):
    """Raised for general SymbolUniverse related errors."""
    pass

class DuplicateSymbolError(SymbolUniverseError):
    """Raised when attempting to add a duplicate symbol to the universe."""
    pass

class DataProviderTimeoutError(DataProviderError):
    """Raised when a data provider request times out."""
    pass

class DataProviderValidationError(DataProviderError):
    """Raised when fetched data is invalid or missing required columns."""
    pass

class StorageError(BistSignalBotError):
    """Raised when there is a general storage error."""
    pass

class MarketDataStoreError(StorageError):
    """Raised when there is an error specific to the local market data store."""
    pass

class DataQualityError(BistSignalBotError):
    """Raised when data quality checks fail and fail_on_error is configured."""
    pass

class MarketCalendarError(BistSignalBotError):
    """Raised when there is an error in market calendar calculations."""
    pass

class MarketSessionError(BistSignalBotError):
    """Raised when there is an error in market session logic."""
    pass

class NotificationError(BistSignalBotError):
    """Raised when there is an error in the notification system."""
    pass

class TelegramConfigurationError(NotificationError):
    """Raised when there is an error with Telegram configuration."""
    pass

class TelegramSendError(NotificationError):
    """Raised when there is an error sending a Telegram message."""
    pass

class AuditLogError(BistSignalBotError):
    """Raised when there is an error writing an audit log."""
    pass

class OperationalSafetyError(BistSignalBotError):
    """Raised when an operational safety check fails."""
    pass
