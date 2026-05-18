import pandas as pd
from pathlib import Path
from typing import List, Optional
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_market_data_dir
from bist_signal_bot.data.providers_v2.models import DataLineageSource

class MarketStore:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.market_dir = get_market_data_dir(self.settings)

    def market_data_path(self, symbol: str, timeframe: str) -> Path:
        symbol_dir = self.market_dir / timeframe
        symbol_dir.mkdir(parents=True, exist_ok=True)
        return symbol_dir / f"{symbol}.parquet"

    def save_ohlcv(self, symbol: str, timeframe: str, data: pd.DataFrame, lineage: Optional[DataLineageSource] = None) -> Path:
        path = self.market_data_path(symbol, timeframe)
        data.to_parquet(path)
        # Note: Lineage saving is expected to be handled by DataService -> DataLineageStore
        return path

    def load_ohlcv(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        path = self.market_data_path(symbol, timeframe)
        if not path.exists():
            # Try CSV fallback
            csv_path = path.with_suffix('.csv')
            if csv_path.exists():
                 try:
                     return pd.read_csv(csv_path, parse_dates=['date'])
                 except:
                     pass
            return None

        try:
            return pd.read_parquet(path)
        except Exception:
            return None

    def exists(self, symbol: str, timeframe: str) -> bool:
        path = self.market_data_path(symbol, timeframe)
        return path.exists() or path.with_suffix('.csv').exists()

    def list_symbols(self, timeframe: Optional[str] = None) -> List[str]:
        symbols = set()

        # If timeframe specified, only look there. Else look in all timeframe subdirs
        if timeframe:
            dirs = [self.market_dir / timeframe]
        else:
            if not self.market_dir.exists():
                return []
            dirs = [d for d in self.market_dir.iterdir() if d.is_dir()]

        for d in dirs:
            if not d.exists():
                continue
            for f in d.iterdir():
                if f.suffix in ['.parquet', '.csv']:
                    symbols.add(f.stem)

        return sorted(list(symbols))
