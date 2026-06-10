from datetime import datetime, UTC, timedelta

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
        import hashlib
        hash_val = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16)
        symbol_seed = self.seed + abs(hash_val) % 10000
        np.random.seed(symbol_seed)

        if not end:
            end = istanbul_now()

        if not start:
            start = end - timedelta(days=rows)

        # Calculate actual rows based on start/end if both provided, otherwise use self.rows

        if isinstance(start, str):
            try:
                pd.to_datetime(start)
            except ValueError:
                # likely a period like "2y"
                start = datetime.now(UTC) - pd.Timedelta(days=730)
                end = datetime.now(UTC)

        if isinstance(end, str):
            try:
                pd.to_datetime(end)
            except ValueError:
                end = datetime.now(UTC)

        start_str = start if isinstance(start, str) else start.strftime("%Y-%m-%d")
        end_str = end if isinstance(end, str) else end.strftime("%Y-%m-%d")
        dates = pd.bdate_range(start=start_str, end=end_str)


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
            adjusted=adjusted,
            metadata={'from_cache': False, 'requested_period': period}
        )

    def fetch_ohlcv(self, request: DataFetchRequest) -> dict[str, MarketDataFrame]:
        start = request.start
        end = request.end
        if not end:
            end = istanbul_now()
        if not start:
            start = end - timedelta(days=self.rows)

        if isinstance(start, str):
            try:
                pd.to_datetime(start)
            except ValueError:
                start = datetime.now(UTC) - pd.Timedelta(days=730)
                end = datetime.now(UTC)

        if isinstance(end, str):
            try:
                pd.to_datetime(end)
            except ValueError:
                end = datetime.now(UTC)

        start_str = start if isinstance(start, str) else start.strftime("%Y-%m-%d")
        end_str = end if isinstance(end, str) else end.strftime("%Y-%m-%d")
        dates = pd.bdate_range(start=start_str, end=end_str)

        if len(dates) == 0:
            return {
                sym: MarketDataFrame(
                    symbol=sym,
                    timeframe=request.timeframe,
                    source=self.vendor,
                    data=pd.DataFrame(),
                    fetched_at=utc_now(),
                    adjusted=request.adjusted,
                    metadata={'from_cache': False, 'requested_period': request.period}
                )
                for sym in request.symbols
            }

        num_dates = len(dates)
        results = {}
        now = utc_now()

        for symbol in request.symbols:
            # Deterministic hash function compatible with versions < 3.3 and bypassing session hash randomization
            import hashlib
            hash_val = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16)
            symbol_seed = self.seed + abs(hash_val) % 10000
            np.random.seed(symbol_seed)

            initial_price = np.random.uniform(10.0, 100.0)
            returns = np.random.normal(loc=0.0005, scale=0.02, size=num_dates)
            close_prices = initial_price * np.exp(np.cumsum(returns))
            close_prices = np.maximum(close_prices, 0.01)

            open_prices = close_prices * np.random.normal(1.0, 0.005, num_dates)
            high_prices = np.maximum(open_prices, close_prices) * np.random.uniform(1.0, 1.02, num_dates)
            low_prices = np.minimum(open_prices, close_prices) * np.random.uniform(0.98, 1.0, num_dates)
            high_prices = np.maximum(high_prices, low_prices + 0.01)

            base_volume = np.random.uniform(100000, 5000000)
            volume = base_volume * np.random.lognormal(mean=0, sigma=0.5, size=num_dates)
            volume = np.maximum(volume, 1)

            df = pd.DataFrame({
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": volume
            }, index=dates)

            results[symbol] = MarketDataFrame(
                symbol=symbol,
                timeframe=request.timeframe,
                source=self.vendor,
                data=df,
                fetched_at=now,
                adjusted=request.adjusted,
                metadata={'from_cache': False, 'requested_period': request.period}
            )

        return results
