from datetime import datetime
from typing import Any
import pandas as pd
from pydantic import BaseModel, Field

from bist_signal_bot.data.models import MarketDataFrame
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import StrategyValidationError
from bist_signal_bot.strategies.models import StrategyRunMode

class StrategyContext(BaseModel):
    symbol: str
    timeframe: str = "1d"
    market_data: MarketDataFrame | None = None
    data: pd.DataFrame
    latest_row: pd.Series | dict[str, Any] | None = None
    settings: Settings | None = None
    run_mode: StrategyRunMode = StrategyRunMode.RESEARCH
    generated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.data is None or self.data.empty:
            raise StrategyValidationError(f"Cannot initialize StrategyContext with empty DataFrame for {self.symbol}")

        if self.latest_row is None and not self.data.empty:
            self.latest_row = self.data.iloc[-1]

    def require_columns(self, columns: list[str]) -> None:
        if not columns:
            return

        missing = [col for col in columns if col not in self.data.columns]
        if missing:
            raise StrategyValidationError(
                f"Missing required columns for {self.symbol}: {missing}. "
                f"Available columns: {list(self.data.columns)}"
            )

    def get_latest_value(self, column: str, default: Any = None) -> Any:
        if self.latest_row is None:
            return default

        if isinstance(self.latest_row, pd.Series):
            if column in self.latest_row.index:
                return self.latest_row[column]
        elif isinstance(self.latest_row, dict):
            if column in self.latest_row:
                return self.latest_row[column]

        return default

    def snapshot(self, columns: list[str], max_items: int = 50) -> dict[str, Any]:
        result = {}
        if self.latest_row is None:
            return result

        for col in columns:
            if len(result) >= max_items:
                break

            val = self.get_latest_value(col)
            if pd.isna(val):
                result[col] = None
            elif hasattr(val, "item"):
                result[col] = val.item()
            else:
                result[col] = val

        return result
