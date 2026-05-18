import pandas as pd
from abc import ABC, abstractmethod
from typing import Optional
from bist_signal_bot.data.providers_v2.models import (
    ProviderType,
    ProviderRequest,
    ProviderResponse,
    ProviderHealthSnapshot,
    DataLineageSource
)

class BaseMarketDataProviderV2(ABC):
    @abstractmethod
    def provider_type(self) -> ProviderType:
        pass

    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def supports_network(self) -> bool:
        pass

    @abstractmethod
    def fetch(self, request: ProviderRequest) -> ProviderResponse:
        pass

    @abstractmethod
    def healthcheck(self) -> ProviderHealthSnapshot:
        pass

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().strip()

    def build_lineage(
        self,
        symbol: str,
        data: pd.DataFrame,
        request: ProviderRequest,
        source_path: Optional[str] = None
    ) -> DataLineageSource:
        import uuid
        from datetime import datetime
        return DataLineageSource(
            source_id=str(uuid.uuid4()),
            provider_type=self.provider_type(),
            provider_name=self.provider_name(),
            symbol=self.normalize_symbol(symbol),
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            fetched_at=datetime.utcnow(),
            row_count=len(data),
            source_path=source_path,
            checksum=None
        )
