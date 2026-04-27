from abc import ABC, abstractmethod
from datetime import datetime

from bist_signal_bot.data.models import DataFetchRequest, DataVendor, MarketDataFrame, Timeframe


class BaseMarketDataProvider(ABC):
    """
    Abstract base class for all data providers.
    Every data provider (e.g., Yahoo Finance, local CSV) should inherit from this.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data provider."""
        pass

    @property
    @abstractmethod
    def vendor(self) -> DataVendor:
        """The data vendor type."""
        pass

    @property
    @abstractmethod
    def supports_intraday(self) -> bool:
        """Whether the provider supports intraday timeframes."""
        pass

    @property
    @abstractmethod
    def supports_adjusted(self) -> bool:
        """Whether the provider supports adjusted prices."""
        pass

    @abstractmethod
    def fetch_ohlcv(self, request: DataFetchRequest) -> dict[str, MarketDataFrame]:
        """Fetch historical OHLCV data for multiple symbols."""
        pass

    @abstractmethod
    def fetch_one(self, symbol: str, timeframe: Timeframe, start: datetime | None = None, end: datetime | None = None, period: str | None = "2y", adjusted: bool = True) -> MarketDataFrame:
        """Fetch historical OHLCV data for a single symbol."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready to use."""
        pass

    @abstractmethod
    def normalize_provider_symbol(self, symbol: str) -> str:
        """Normalize internal symbol format to provider's format (e.g., ASELS -> ASELS.IS)."""
        pass
