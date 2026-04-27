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
