import time
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from bist_signal_bot.data.providers_v2.base import BaseMarketDataProviderV2
from bist_signal_bot.data.providers_v2.models import (
    ProviderType,
    ProviderRequest,
    ProviderResponse,
    ProviderHealthSnapshot,
    DataFetchStatus,
    DataLineageSource
)
from bist_signal_bot.config.settings import Settings

class FallbackProviderRouter:
    def __init__(self, providers: List[BaseMarketDataProviderV2], settings: Settings):
        self.providers = {p.provider_type(): p for p in providers}
        self.settings = settings

    def fetch(self, request: ProviderRequest) -> ProviderResponse:
        start_time = time.time()

        provider_order = request.provider_order
        if not provider_order:
            order_str = getattr(self.settings, "DATA_PROVIDER_DEFAULT_ORDER", "local_file,yfinance")
            provider_order = []
            for p_str in order_str.split(","):
                try:
                    provider_order.append(ProviderType(p_str.strip().upper()))
                except ValueError:
                    continue

        all_responses = []
        pending_symbols = set(request.symbols)

        for p_type in provider_order:
            if not pending_symbols:
                break

            provider = self.providers.get(p_type)
            if not provider:
                continue

            sub_request = ProviderRequest(
                symbols=list(pending_symbols),
                timeframe=request.timeframe,
                start_date=request.start_date,
                end_date=request.end_date,
                rows=request.rows,
                prefer_cache=request.prefer_cache,
                allow_network=request.allow_network
            )

            response = provider.fetch(sub_request)
            all_responses.append(response)

            fetched = set(response.data_by_symbol.keys())
            pending_symbols -= fetched

        return self.merge_provider_responses(all_responses, request, start_time)

    def select_best_data_for_symbol(self, symbol: str, responses: List[ProviderResponse]) -> Tuple[Optional[pd.DataFrame], Optional[DataLineageSource]]:
        for response in responses:
            if symbol in response.data_by_symbol:
                data = response.data_by_symbol[symbol]
                lineage = next((l for l in response.lineage if l.symbol == symbol), None)
                return data, lineage
        return None, None

    def merge_provider_responses(self, responses: List[ProviderResponse], original_request: ProviderRequest, start_time: float) -> ProviderResponse:
        merged_data = {}
        merged_lineage = []
        merged_provider_results = {}
        merged_warnings = []
        merged_errors = []

        for symbol in original_request.symbols:
            data, lineage = self.select_best_data_for_symbol(symbol, responses)
            if data is not None:
                merged_data[symbol] = data
                if lineage:
                    merged_lineage.append(lineage)

        for response in responses:
            merged_warnings.extend(response.warnings)
            merged_errors.extend(response.errors)
            p_type_name = response.lineage[0].provider_type.value if response.lineage else "UNKNOWN"
            merged_provider_results[p_type_name] = response.summary()

        status = DataFetchStatus.SUCCESS
        if not merged_data:
            status = DataFetchStatus.EMPTY
        elif len(merged_data) < len(original_request.symbols):
            status = DataFetchStatus.PARTIAL_SUCCESS

        return ProviderResponse(
            request=original_request,
            status=status,
            data_by_symbol=merged_data,
            lineage=merged_lineage,
            provider_results=merged_provider_results,
            warnings=merged_warnings,
            errors=merged_errors,
            elapsed_seconds=time.time() - start_time
        )

    def healthcheck_all(self) -> List[ProviderHealthSnapshot]:
        return [provider.healthcheck() for provider in self.providers.values()]
