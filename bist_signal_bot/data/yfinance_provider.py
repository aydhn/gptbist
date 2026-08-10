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
            adjusted=adjusted,
            metadata={'from_cache': False, 'requested_period': period}
        )


    def _fetch_batch_from_yfinance(self, symbols_yf: list[str], timeframe: Timeframe, start: datetime | None, end: datetime | None, period: str | None, adjusted: bool) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError:
            raise DataProviderError("yfinance library is not installed.")

        kwargs = {}
        if start and end:
            kwargs["start"] = start.strftime("%Y-%m-%d")
            kwargs["end"] = end.strftime("%Y-%m-%d")
        elif period:
            kwargs["period"] = period
        else:
            kwargs["period"] = "2y" # default fallback

        try:
            # group_by="ticker" makes column multi-index (Ticker, Price)
            df = yf.download(
                " ".join(symbols_yf),
                interval=timeframe.value,
                group_by="ticker",
                auto_adjust=adjusted,
                **kwargs
            )
            return df
        except Exception as e:
            raise DataProviderError(f"Failed to fetch batch data from YFinance: {e}")

    def fetch_ohlcv(self, request: DataFetchRequest) -> dict[str, MarketDataFrame]:
        results = {}
        if not request.symbols:
            return results

        symbols_yf = [self.normalize_provider_symbol(s) for s in request.symbols]

        try:
            batch_df = self._fetch_batch_from_yfinance(
                symbols_yf=symbols_yf,
                timeframe=request.timeframe,
                start=request.start,
                end=request.end,
                period=request.period,
                adjusted=request.adjusted
            )
        except Exception as e:
            # Fallback to sequential if batch fails entirely
            print(f"Warning: Batch fetch failed: {e}. Falling back to sequential.")
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
                except Exception as inner_e:
                    print(f"Warning: Failed to fetch {symbol} sequentially: {inner_e}")
            return results

        # Process batch results
        for symbol, symbol_yf in zip(request.symbols, symbols_yf):
            try:
                # If only one symbol was requested, yfinance might not use multi-index depending on version
                if len(symbols_yf) == 1:
                    if isinstance(batch_df.columns, pd.MultiIndex):
                        if symbol_yf in batch_df:
                            df = batch_df[symbol_yf].copy()
                        else:
                            df = batch_df.copy()
                            # Strip ticker level if it exists
                            if len(df.columns.levels) > 1 and df.columns.names[1] == 'Ticker':
                                df.columns = df.columns.droplevel(1)
                    else:
                        df = batch_df.copy()
                else:
                    if symbol_yf in batch_df:
                        df = batch_df[symbol_yf].copy()
                    else:
                        df = pd.DataFrame()

                # Check if data is completely empty
                if df.empty or df.isna().all().all():
                    results[symbol] = MarketDataFrame(
                        symbol=symbol,
                        timeframe=request.timeframe,
                        source=self.vendor,
                        data=pd.DataFrame(),
                        fetched_at=utc_now(),
                        adjusted=request.adjusted
                    )
                    continue

                # Normalize columns
                df.columns = [str(c).lower() for c in df.columns]

                # Keep only required columns if they exist
                required_cols = {"open", "high", "low", "close", "volume"}

                if not required_cols.issubset(set(df.columns)):
                    print(f"Warning: Missing required columns from YFinance batch for {symbol}. Got: {list(df.columns)}")
                    continue

                # Drop rows where all required columns are NaN
                df = df.dropna(subset=list(required_cols), how='all')

                if df.empty:
                    results[symbol] = MarketDataFrame(
                        symbol=symbol,
                        timeframe=request.timeframe,
                        source=self.vendor,
                        data=pd.DataFrame(),
                        fetched_at=utc_now(),
                        adjusted=request.adjusted
                    )
                    continue

                df = df[list(required_cols)].copy()

                results[symbol] = MarketDataFrame(
                    symbol=symbol,
                    timeframe=request.timeframe,
                    source=self.vendor,
                    data=df,
                    fetched_at=utc_now(),
                    adjusted=request.adjusted,
                    metadata={'from_cache': False, 'requested_period': request.period}
                )

            except Exception as e:
                print(f"Warning: Failed to process batch data for {symbol}: {e}")

        return results
