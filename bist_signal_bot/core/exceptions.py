class BistSignalBotError(Exception):
    """Base exception class for BIST Signal Bot."""
    pass

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
