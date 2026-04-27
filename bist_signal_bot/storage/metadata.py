import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

from bist_signal_bot.core.exceptions import StorageError
from bist_signal_bot.storage.paths import ensure_dir

class StoredMarketDataMetadata(BaseModel):
    symbol: str
    vendor: str
    timeframe: str
    file_path: str
    row_count: int
    start: datetime | None = None
    end: datetime | None = None
    adjusted: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"

class MarketDataIndex(BaseModel):
    items: dict[str, StoredMarketDataMetadata] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def make_key(symbol: str, vendor: str, timeframe: str) -> str:
        return f"{symbol}_{vendor}_{timeframe}".lower()

    def add_or_update(self, metadata: StoredMarketDataMetadata) -> None:
        key = self.make_key(metadata.symbol, metadata.vendor, metadata.timeframe)
        metadata.updated_at = datetime.utcnow()
        self.items[key] = metadata
        self.updated_at = datetime.utcnow()

    def get(self, symbol: str, vendor: str, timeframe: str) -> StoredMarketDataMetadata | None:
        key = self.make_key(symbol, vendor, timeframe)
        return self.items.get(key)

    def remove(self, symbol: str, vendor: str, timeframe: str) -> bool:
        key = self.make_key(symbol, vendor, timeframe)
        if key in self.items:
            del self.items[key]
            self.updated_at = datetime.utcnow()
            return True
        return False

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "MarketDataIndex":
        return cls.model_validate(data)

def load_market_data_index(path: Path) -> MarketDataIndex:
    if not path.exists():
        return MarketDataIndex()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return MarketDataIndex.from_dict(data)
    except json.JSONDecodeError as e:
        raise StorageError(f"Failed to parse metadata index at {path}: {e}")
    except Exception as e:
        raise StorageError(f"Failed to load metadata index from {path}: {e}")

def save_market_data_index(index: MarketDataIndex, path: Path) -> None:
    try:
        ensure_dir(path.parent)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(index.to_dict(), f, indent=4)
    except Exception as e:
        raise StorageError(f"Failed to save metadata index to {path}: {e}")
