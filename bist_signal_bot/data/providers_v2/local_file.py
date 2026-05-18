import time
import pandas as pd
from typing import Optional
from pathlib import Path
from bist_signal_bot.data.providers_v2.base import BaseMarketDataProviderV2
from bist_signal_bot.data.providers_v2.models import (
    ProviderType,
    ProviderRequest,
    ProviderResponse,
    ProviderHealthSnapshot,
    ProviderStatus,
    DataFetchStatus
)
from bist_signal_bot.storage.paths import get_market_data_dir
from bist_signal_bot.security.path_guard import PathGuard
import os

class LocalFileProvider(BaseMarketDataProviderV2):
    def provider_type(self) -> ProviderType:
        return ProviderType.LOCAL_FILE

    def provider_name(self) -> str:
        return "Local File Provider"

    def supports_network(self) -> bool:
        return False

    def load_symbol_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        file_path = self.find_local_file(symbol, timeframe)
        if not file_path:
            return None

        try:
            if file_path.suffix == '.parquet':
                return pd.read_parquet(file_path)
            elif file_path.suffix == '.csv':
                return pd.read_csv(file_path, parse_dates=['date'])
        except Exception as e:
            return None
        return None

    def find_local_file(self, symbol: str, timeframe: str) -> Optional[Path]:
        symbol = self.normalize_symbol(symbol)
        try:
            base_dir = get_market_data_dir()
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if symbol in file and timeframe in file:
                         p = Path(root) / file
                         PathGuard.check_path(p, base_dir)
                         return p
        except Exception:
            pass
        return None

    def fetch(self, request: ProviderRequest) -> ProviderResponse:
        start_time = time.time()
        status = DataFetchStatus.SUCCESS
        data_by_symbol = {}
        lineage = []
        warnings = []
        errors = []

        for symbol in request.symbols:
            try:
                df = self.load_symbol_data(symbol, request.timeframe)
                if df is not None and not df.empty:
                    if request.start_date:
                        df = df[df['date'] >= pd.to_datetime(request.start_date)]
                    if request.end_date:
                        df = df[df['date'] <= pd.to_datetime(request.end_date)]
                    if request.rows and len(df) > request.rows:
                        df = df.tail(request.rows)

                    if not df.empty:
                        data_by_symbol[symbol] = df
                        lineage.append(self.build_lineage(symbol, df, request))
                    else:
                        warnings.append(f"Data for {symbol} empty after filtering.")
                else:
                    warnings.append(f"No local data found for {symbol}.")
            except Exception as e:
                errors.append(f"Failed to load {symbol}: {e}")

        if not data_by_symbol:
            status = DataFetchStatus.EMPTY
        elif len(data_by_symbol) < len(request.symbols):
            status = DataFetchStatus.PARTIAL_SUCCESS

        return ProviderResponse(
            request=request,
            status=status,
            data_by_symbol=data_by_symbol,
            lineage=lineage,
            warnings=warnings,
            errors=errors,
            elapsed_seconds=time.time() - start_time
        )

    def healthcheck(self) -> ProviderHealthSnapshot:
        return ProviderHealthSnapshot(
            provider_type=self.provider_type(),
            provider_name=self.provider_name(),
            status=ProviderStatus.HEALTHY
        )
