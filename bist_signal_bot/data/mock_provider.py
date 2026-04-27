from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from bist_signal_bot.core.time_utils import istanbul_now, utc_now
from bist_signal_bot.data.base_provider import BaseMarketDataProvider
from bist_signal_bot.data.models import DataFetchRequest, DataVendor, MarketDataFrame, Timeframe


class MockMarketDataProvider(BaseMarketDataProvider):
    """
    Mock data provider that generates deterministic random OHLCV data.
    Useful for offline development and testing.
    """

    def __init__(self, seed: int = 42, rows: int = 252):
        self.seed = seed
        self.rows = rows

    @property
    def name(self) -> str:
        return "Mock Provider"

    @property
    def vendor(self) -> DataVendor:
        return DataVendor.INTERNAL

    @property
    def supports_intraday(self) -> bool:
        return True

    @property
    def supports_adjusted(self) -> bool:
        return True

    def is_available(self) -> bool:
        return True

    def normalize_provider_symbol(self, symbol: str) -> str:
        return symbol

    def _generate_deterministic_data(self, symbol: str, start: datetime | None, end: datetime | None, rows: int) -> pd.DataFrame:
        # Use symbol hash to make the seed deterministic but different per symbol
        symbol_seed = self.seed + abs(hash(symbol)) % 10000
        np.random.seed(symbol_seed)

        if not end:
            end = istanbul_now()

        if not start:
            start = end - timedelta(days=rows)

        # Calculate actual rows based on start/end if both provided, otherwise use self.rows
        dates = pd.bdate_range(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

        if len(dates) == 0:
            return pd.DataFrame()

        # Generate realistic looking price path
        initial_price = np.random.uniform(10.0, 100.0)
        returns = np.random.normal(loc=0.0005, scale=0.02, size=len(dates))
        close_prices = initial_price * np.exp(np.cumsum(returns))

        # Ensure positive
        close_prices = np.maximum(close_prices, 0.01)

        # Generate open, high, low around close
        open_prices = close_prices * np.random.normal(1.0, 0.005, len(dates))
        high_prices = np.maximum(open_prices, close_prices) * np.random.uniform(1.0, 1.02, len(dates))
        low_prices = np.minimum(open_prices, close_prices) * np.random.uniform(0.98, 1.0, len(dates))

        # Ensure high >= low
        high_prices = np.maximum(high_prices, low_prices + 0.01)

        # Volume
        base_volume = np.random.uniform(100000, 5000000)
        volume = base_volume * np.random.lognormal(mean=0, sigma=0.5, size=len(dates))
        volume = np.maximum(volume, 1)

        df = pd.DataFrame({
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volume
        }, index=dates)

        return df

    def fetch_one(self, symbol: str, timeframe: Timeframe, start: datetime | None = None, end: datetime | None = None, period: str | None = "2y", adjusted: bool = True) -> MarketDataFrame:
        df = self._generate_deterministic_data(symbol, start, end, self.rows)

        return MarketDataFrame(
            symbol=symbol,
            timeframe=timeframe,
            source=self.vendor,
            data=df,
            fetched_at=utc_now(),
            adjusted=adjusted
        )

    def fetch_ohlcv(self, request: DataFetchRequest) -> dict[str, MarketDataFrame]:
        results = {}
        for symbol in request.symbols:
            results[symbol] = self.fetch_one(
                symbol=symbol,
                timeframe=request.timeframe,
                start=request.start,
                end=request.end,
                period=request.period,
                adjusted=request.adjusted
            )
        return results
