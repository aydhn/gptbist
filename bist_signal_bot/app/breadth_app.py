from datetime import datetime
from typing import Any
from pathlib import Path

from bist_signal_bot.breadth.models import BreadthAnalysisRequest, BreadthAnalysisResult
from bist_signal_bot.breadth.engine import BreadthEngine
from bist_signal_bot.core.exceptions import BreadthValidationError

class BreadthApp:
    def __init__(self, engine: BreadthEngine | None = None, settings=None):
        self.settings = settings
        if engine:
            self.engine = engine
        else:
            self.engine = BreadthEngine.from_settings(settings)

    def generate_snapshot(
        self,
        symbols: list[str],
        universe_name: str = "CUSTOM",
        benchmark_symbol: str | None = None,
        source: str = "local_file",
        timeframe: str = "1d",
        as_of_date: datetime | None = None,
        save_snapshot: bool = True
    ) -> BreadthAnalysisResult:
        if not symbols:
            raise BreadthValidationError("At least one symbol must be provided.")

        req = BreadthAnalysisRequest(
            symbols=symbols,
            universe_name=universe_name,
            benchmark_symbol=benchmark_symbol,
            source=source,
            timeframe=timeframe,
            as_of_date=as_of_date,
            save_snapshot=save_snapshot,
            include_relative_strength=True,
            include_sector_rotation=True,
            include_fundamentals=False
        )

        return self.engine.analyze(req)

    def get_leaders(self, top_n: int = 20) -> list[dict[str, Any]]:
        leaders = self.engine.leaders(top_n=top_n)
        return [l.model_dump(mode='json') for l in leaders]

    def get_laggards(self, bottom_n: int = 20) -> list[dict[str, Any]]:
        laggards = self.engine.laggards(bottom_n=bottom_n)
        return [l.model_dump(mode='json') for l in laggards]

    def get_recent_snapshots(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.engine.store.list_recent_snapshots(limit=limit)
