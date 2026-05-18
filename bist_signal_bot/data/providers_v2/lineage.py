import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from bist_signal_bot.data.providers_v2.models import DataLineageSource
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.config.settings import get_settings

class DataLineageStore:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.lineage_dir = get_data_dir(self.settings) / getattr(self.settings, "DATA_LINEAGE_DIR_NAME", "lineage")
        self.lineage_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.lineage_dir / "data_lineage.jsonl"

    def append(self, lineage: DataLineageSource) -> Path:
        with open(self.file_path, "a") as f:
            f.write(lineage.model_dump_json() + "\n")
        return self.file_path

    def load_recent(self, symbol: Optional[str] = None, limit: int = 100) -> List[DataLineageSource]:
        if not self.file_path.exists():
            return []

        sources = []
        with open(self.file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    source = DataLineageSource(**data)
                    if symbol is None or source.symbol == symbol:
                        sources.append(source)
                except Exception:
                    pass

        return sorted(sources, key=lambda x: x.fetched_at, reverse=True)[:limit]

    def latest_for_symbol(self, symbol: str, timeframe: str) -> Optional[DataLineageSource]:
        recent = self.load_recent(symbol=symbol, limit=100)
        for r in recent:
            if r.timeframe == timeframe:
                return r
        return None

    def lineage_summary(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        recent = self.load_recent(symbol=symbol)
        if not recent:
            return {"count": 0}

        summary = {
            "count": len(recent),
            "providers": list(set(r.provider_name for r in recent)),
            "latest_fetch": recent[0].fetched_at.isoformat()
        }
        return summary

    def calculate_checksum(self, data: pd.DataFrame) -> str:
        try:
            dump = data.to_json(orient="records", date_format="iso").encode('utf-8')
            return hashlib.sha256(dump).hexdigest()
        except Exception:
            return "UNKNOWN"
