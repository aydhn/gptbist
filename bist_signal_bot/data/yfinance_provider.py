from datetime import datetime

import pandas as pd

from bist_signal_bot.core.exceptions import DataProviderError
from bist_signal_bot.core.time_utils import utc_now
from bist_signal_bot.data.base_provider import BaseMarketDataProvider
from bist_signal_bot.data.models import DataFetchRequest, DataVendor, MarketDataFrame, Timeframe


class YFinanceMarketDataProvider(BaseMarketDataProvider):
    """
    Yahoo Finance data provider implementation.
    """

    @property
    def name(self) -> str:
        return "YFinance Provider"

    @property
    def vendor(self) -> DataVendor:
        return DataVendor.YFINANCE

    @property
    def supports_intraday(self) -> bool:
        return True

    @property
    def supports_adjusted(self) -> bool:
        return True

    def is_available(self) -> bool:
        try:
            import yfinance
            return True
        except ImportError:
            return False

    def normalize_provider_symbol(self, symbol: str) -> str:
        if not symbol.endswith(".IS"):
            return f"{symbol}.IS"
        return symbol

    def _fetch_from_yfinance(self, symbol_yf: str, timeframe: Timeframe, start: datetime | None, end: datetime | None, period: str | None) -> pd.DataFrame:
        """Isolated yfinance call for easier testing/mocking."""
        try:
            import yfinance as yf
        except ImportError:
            raise DataProviderError("yfinance library is not installed.")

        ticker = yf.Ticker(symbol_yf)

        # yfinance expects start/end as strings or aware datetimes, but usually string "YYYY-MM-DD" is safer
        kwargs = {}

        if start and end:
            kwargs["start"] = start.strftime("%Y-%m-%d")
            kwargs["end"] = end.strftime("%Y-%m-%d")
        elif period:
            kwargs["period"] = period
        else:
            kwargs["period"] = "2y" # default fallback

        try:
            df = ticker.history(interval=timeframe.value, **kwargs)
            return df
        except Exception as e:
            raise DataProviderError(f"Failed to fetch data from YFinance for {symbol_yf}: {e}")

    def fetch_one(self, symbol: str, timeframe: Timeframe, start: datetime | None = None, end: datetime | None = None, period: str | None = "2y", adjusted: bool = True) -> MarketDataFrame:
        symbol_yf = self.normalize_provider_symbol(symbol)

        df = self._fetch_from_yfinance(symbol_yf, timeframe, start, end, period)

        if df.empty:
            # Return empty df gracefully
            return MarketDataFrame(
                symbol=symbol,
                timeframe=timeframe,
                source=self.vendor,
                data=pd.DataFrame(),
                fetched_at=utc_now(),
                adjusted=adjusted
            )

        # Normalize columns
        df.columns = [str(c).lower() for c in df.columns]

        # Keep only required columns if they exist
        required_cols = {"open", "high", "low", "close", "volume"}

        if not required_cols.issubset(set(df.columns)):
             raise DataProviderError(f"Missing required columns from YFinance for {symbol}. Got: {list(df.columns)}")

        df = df[list(required_cols)].copy()

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
            try:
                results[symbol] = self.fetch_one(
                    symbol=symbol,
                    timeframe=request.timeframe,
                    start=request.start,
                    end=request.end,
                    period=request.period,
                    adjusted=request.adjusted
                )
            except Exception as e:
                # Log error, but continue fetching others
                print(f"Warning: Failed to fetch {symbol}: {e}")
                # We could choose to insert an empty MarketDataFrame or leave it out. Let's leave it out.
        return results
