from datetime import datetime
from pathlib import Path

import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config.settings import settings as default_settings
from bist_signal_bot.core.exceptions import MarketDataStoreError
from bist_signal_bot.data.models import DataVendor, MarketDataFrame, Timeframe
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.storage.metadata import (
    MarketDataIndex,
    StoredMarketDataMetadata,
    load_market_data_index,
    save_market_data_index,
)
from bist_signal_bot.storage.paths import (
    ensure_dir,
    get_market_data_dir,
    get_market_data_index_path,
    get_ohlcv_file_path,
)


class LocalMarketDataStore:
    """Local storage engine for OHLCV data."""

    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or default_settings
        # Not fully supporting injecting a completely separate base_dir in this simple version,
        # but using settings allows tmp_path overrides during testing
        self.index_path = get_market_data_index_path(self.settings)
        self.format = self.settings.STORAGE_FORMAT.lower()
        if self.format != "csv":
            raise MarketDataStoreError(f"Unsupported storage format: {self.format}")

        self.index = self._load_index()

    def _load_index(self) -> MarketDataIndex:
        return load_market_data_index(self.index_path)

    def _save_index(self) -> None:
        save_market_data_index(self.index, self.index_path)

    def exists(self, symbol: str, vendor: DataVendor | str, timeframe: Timeframe | str) -> bool:
        v_str = vendor.value if isinstance(vendor, DataVendor) else vendor
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe

        # Check index first, but verify file actually exists
        metadata = self.index.get(symbol, v_str, tf_str)
        if not metadata:
            return False

        file_path = Path(metadata.file_path)
        return file_path.exists()

    def write_ohlcv(self, market_data: MarketDataFrame) -> StoredMarketDataMetadata:
        try:
            market_data.validate_schema()
        except Exception as e:
            raise MarketDataStoreError(f"Cannot write invalid MarketDataFrame: {e}")

        v_str = market_data.source.value
        tf_str = market_data.timeframe.value

        file_path = get_ohlcv_file_path(
            market_data.symbol,
            v_str,
            tf_str,
            self.settings,
            extension=self.format
        )

        ensure_dir(file_path.parent)

        df = market_data.data.copy()

        # Ensure timestamp is the index for writing to CSV
        if not isinstance(df.index, pd.DatetimeIndex):
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)
            else:
                 raise MarketDataStoreError("DataFrame must have a DatetimeIndex or a 'timestamp' column.")

        df.index.name = "timestamp"

        try:
            df.to_csv(file_path)
        except Exception as e:
            raise MarketDataStoreError(f"Failed to write CSV to {file_path}: {e}")

        # Generate metadata
        start, end = market_data.date_range()
        metadata = StoredMarketDataMetadata(
            symbol=market_data.symbol,
            vendor=v_str,
            timeframe=tf_str,
            file_path=str(file_path),
            row_count=market_data.row_count(),
            start=start,
            end=end,
            adjusted=market_data.adjusted
        )

        self.index.add_or_update(metadata)
        self._save_index()

        return metadata

    def read_ohlcv(self, symbol: str, vendor: DataVendor | str, timeframe: Timeframe | str) -> MarketDataFrame:
        v_str = vendor.value if isinstance(vendor, DataVendor) else vendor
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe

        metadata = self.index.get(symbol, v_str, tf_str)

        # Determine fallback path if index missing
        file_path = get_ohlcv_file_path(symbol, v_str, tf_str, self.settings, extension=self.format)

        if metadata and Path(metadata.file_path).exists():
            file_path = Path(metadata.file_path)
        elif not file_path.exists():
            raise MarketDataStoreError(f"No local data found for {symbol} ({v_str}, {tf_str})")

        try:
            df = pd.read_csv(file_path, parse_dates=["timestamp"], index_col="timestamp")

            # Normalize columns
            df.columns = [str(c).lower() for c in df.columns]

            mdf = MarketDataFrame(
                symbol=ensure_valid_internal_symbol(symbol),
                timeframe=Timeframe(tf_str),
                source=DataVendor(v_str.upper()) if hasattr(DataVendor, v_str.upper()) else DataVendor.UNKNOWN, # Robust handling
                data=df,
                fetched_at=datetime.utcnow(),
                adjusted=metadata.adjusted if metadata else True
            )
            mdf.validate_schema()
            return mdf
        except Exception as e:
            raise MarketDataStoreError(f"Failed to read or parse local data for {symbol}: {e}")

    def delete_ohlcv(self, symbol: str, vendor: DataVendor | str, timeframe: Timeframe | str) -> bool:
        v_str = vendor.value if isinstance(vendor, DataVendor) else vendor
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe

        metadata = self.index.get(symbol, v_str, tf_str)
        deleted = False

        file_path = get_ohlcv_file_path(symbol, v_str, tf_str, self.settings, extension=self.format)

        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
            except Exception as e:
                raise MarketDataStoreError(f"Failed to delete file {file_path}: {e}")

        if self.index.remove(symbol, v_str, tf_str):
            self._save_index()
            deleted = True

        return deleted

    def get_metadata(self, symbol: str, vendor: DataVendor | str, timeframe: Timeframe | str) -> StoredMarketDataMetadata | None:
        v_str = vendor.value if isinstance(vendor, DataVendor) else vendor
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
        return self.index.get(symbol, v_str, tf_str)

    def list_available_symbols(self, vendor: DataVendor | str | None = None, timeframe: Timeframe | str | None = None) -> list[str]:
        v_str = vendor.value if isinstance(vendor, DataVendor) else vendor if vendor else None
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe if timeframe else None

        symbols = set()
        for key, meta in self.index.items.items():
            if v_str and meta.vendor != v_str:
                continue
            if tf_str and meta.timeframe != tf_str:
                continue
            symbols.add(meta.symbol)

        return sorted(list(symbols))

    def refresh_index_from_files(self) -> MarketDataIndex:
        """Scan directories and rebuild index."""
        # Note: This is a basic implementation for this phase.
        # It assumes vendor and timeframe can be inferred or are passed explicitly for a full scan.
        # Since scanning everything is complex without strict folder rules, we'll scan based on existing index
        # and simple globbing of the base ohlcv dir.

        new_index = MarketDataIndex()

        ohlcv_base_dir = get_market_data_dir(self.settings) / self.settings.OHLCV_DIR_NAME

        if not ohlcv_base_dir.exists():
            self.index = new_index
            self._save_index()
            return new_index

        for file_path in ohlcv_base_dir.rglob("*.csv"):
            # Expected format: data/market_data/ohlcv/yfinance/1d/ASELS.csv
            parts = file_path.parts

            # Find index of OHLCV_DIR_NAME
            try:
                base_idx = parts.index(self.settings.OHLCV_DIR_NAME)
                if len(parts) >= base_idx + 4: # ohlcv / vendor / timeframe / symbol.csv
                    vendor = parts[base_idx + 1]
                    timeframe = parts[base_idx + 2]
                    symbol = file_path.stem

                    try:
                        df = pd.read_csv(file_path, parse_dates=["timestamp"], index_col="timestamp")
                        start = df.index.min().to_pydatetime() if not df.empty else None
                        end = df.index.max().to_pydatetime() if not df.empty else None

                        # Just grab existing adjusted if available, else True
                        adjusted = True
                        old_meta = self.index.get(symbol, vendor, timeframe)
                        if old_meta:
                            adjusted = old_meta.adjusted

                        meta = StoredMarketDataMetadata(
                            symbol=symbol,
                            vendor=vendor,
                            timeframe=timeframe,
                            file_path=str(file_path),
                            row_count=len(df),
                            start=start,
                            end=end,
                            adjusted=adjusted
                        )
                        new_index.add_or_update(meta)
                    except Exception:
                        # Skip unreadable files
                        pass
            except ValueError:
                pass

        self.index = new_index
        self._save_index()
        return self.index
