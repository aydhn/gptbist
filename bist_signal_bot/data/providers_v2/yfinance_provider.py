import time
import pandas as pd
from typing import Optional, Dict, Any
from bist_signal_bot.data.providers_v2.base import BaseMarketDataProviderV2
from bist_signal_bot.data.providers_v2.models import (
    ProviderType,
    ProviderRequest,
    ProviderResponse,
    ProviderHealthSnapshot,
    ProviderStatus,
    DataFetchStatus
)
from bist_signal_bot.config.settings import get_settings

class YFinanceProviderV2(BaseMarketDataProviderV2):
    def provider_type(self) -> ProviderType:
        return ProviderType.YFINANCE

    def provider_name(self) -> str:
        return "YFinance Provider"

    def supports_network(self) -> bool:
        return True

    def _format_bist_symbol(self, symbol: str) -> str:
        s = self.normalize_symbol(symbol)
        if not s.endswith(".IS"):
            return f"{s}.IS"
        return s

    def fetch(self, request: ProviderRequest) -> ProviderResponse:
        start_time = time.time()

        if not request.allow_network:
            return ProviderResponse(
                request=request,
                status=DataFetchStatus.SKIPPED,
                data_by_symbol={},
                lineage=[],
                warnings=["Network access not allowed for request."],
                elapsed_seconds=time.time() - start_time
            )

        try:
            import yfinance as yf
        except ImportError:
            return ProviderResponse(
                request=request,
                status=DataFetchStatus.SKIPPED,
                data_by_symbol={},
                lineage=[],
                warnings=["yfinance library not installed."],
                elapsed_seconds=time.time() - start_time
            )

        status = DataFetchStatus.SUCCESS
        data_by_symbol = {}
        lineage = []
        warnings = []
        errors = []

        settings = get_settings()
        suffix = getattr(settings, "DATA_YFINANCE_SUFFIX", ".IS")

        for symbol in request.symbols:
            try:
                yf_symbol = f"{self.normalize_symbol(symbol)}{suffix}" if not symbol.endswith(suffix) else symbol

                kwargs = {
                    "tickers": yf_symbol,
                    "interval": request.timeframe,
                    "progress": False
                }

                if request.start_date:
                    kwargs["start"] = request.start_date.strftime("%Y-%m-%d")
                if request.end_date:
                    kwargs["end"] = request.end_date.strftime("%Y-%m-%d")
                if not request.start_date and not request.end_date:
                    kwargs["period"] = "2y"

                df = yf.download(**kwargs)

                if df is not None and not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [col[0] for col in df.columns]

                    df = df.reset_index()
                    df.columns = [c.lower() for c in df.columns]
                    if 'date' not in df.columns and 'datetime' in df.columns:
                        df.rename(columns={'datetime': 'date'}, inplace=True)

                    if request.rows and len(df) > request.rows:
                        df = df.tail(request.rows)

                    data_by_symbol[symbol] = df
                    lineage.append(self.build_lineage(symbol, df, request))
                else:
                    warnings.append(f"yfinance returned empty data for {symbol}.")
            except Exception as e:
                errors.append(f"Failed to fetch {symbol} from yfinance: {e}")

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
        try:
            import yfinance
            status = ProviderStatus.HEALTHY
        except ImportError:
            status = ProviderStatus.DISABLED

        return ProviderHealthSnapshot(
            provider_type=self.provider_type(),
            provider_name=self.provider_name(),
            status=status
        )
