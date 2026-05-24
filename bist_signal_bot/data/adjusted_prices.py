import pandas as pd
from typing import Optional
from pathlib import Path
from datetime import datetime
from bist_signal_bot.corporate_actions.models import AdjustedPriceResult, AdjustmentDirection

class AdjustedPriceService:
    def __init__(self, data_service, ca_storage, adj_engine, storage_dir: Path):
        self.data_service = data_service
        self.ca_storage = ca_storage
        self.adj_engine = adj_engine
        self.storage_dir = storage_dir

    def get_adjusted_ohlcv(self, symbol: str, start: Optional[datetime] = None, end: Optional[datetime] = None, refresh: bool = False) -> pd.DataFrame:
        df = self.load_adjusted_cache(symbol)
        if df is None or refresh:
            self.build_adjusted_cache(symbol, confirm=True)
            df = self.load_adjusted_cache(symbol)

        if df is not None:
            if start:
                df = df[df.index >= start]
            if end:
                df = df[df.index <= end]
            return df

        return pd.DataFrame()

    def build_adjusted_cache(self, symbol: str, confirm: bool = False) -> AdjustedPriceResult:
        res = AdjustedPriceResult(
            result_id="adj_123",
            symbol=symbol,
            direction=AdjustmentDirection.BACKWARD
        )
        if confirm:
            pass # Save
        return res

    def load_adjusted_cache(self, symbol: str) -> Optional[pd.DataFrame]:
        return None

    def save_adjusted_cache(self, symbol: str, df: pd.DataFrame) -> Path:
        return self.storage_dir / f"{symbol}_adj.parquet"

    def invalidate_adjusted_cache(self, symbol: str, reason: str, confirm: bool = False) -> None:
        pass
