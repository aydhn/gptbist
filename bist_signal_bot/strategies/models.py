from datetime import datetime
from enum import Enum
from typing import Any, List, Dict, Optional
import pandas as pd
from pydantic import BaseModel, Field, field_validator

from bist_signal_bot.signals.models import SignalCandidate

class StrategyCategory(str, Enum):
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    BREAKOUT = "BREAKOUT"
    VOLATILITY = "VOLATILITY"
    VOLUME = "VOLUME"
    MULTI_FACTOR = "MULTI_FACTOR"
    BENCHMARK = "BENCHMARK"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class StrategyRunMode(str, Enum):
    RESEARCH = "RESEARCH"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE_SIGNAL = "LIVE_SIGNAL"

class StrategyPositionSide(str, Enum):
    LONG_ONLY = "LONG_ONLY"
    SHORT_ONLY = "SHORT_ONLY"
    LONG_SHORT = "LONG_SHORT"
    FLAT_ONLY = "FLAT_ONLY"

class StrategyParameter(BaseModel):
    name: str
    default: Any
    param_type: str
    min_value: float | None = None
    max_value: float | None = None
    choices: list[Any] | None = None
    description: str | None = None

class StrategySpec(BaseModel):
    name: str
    display_name: str
    category: StrategyCategory = StrategyCategory.UNKNOWN
    description: str = ""
    position_side: StrategyPositionSide = StrategyPositionSide.LONG_SHORT
    required_columns: list[str] = Field(default_factory=list)
    required_features: list[str] = Field(default_factory=list)
    parameters: list[StrategyParameter] = Field(default_factory=list)
    default_params: dict[str, Any] = Field(default_factory=dict)
    min_rows: int = 1
    supports_short: bool = False
    supports_multi_timeframe: bool = False
    produces_signal_candidates: bool = True
    version: str = "1.0"

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        return v.lower().replace(" ", "_")

    @field_validator("min_rows")
    def validate_min_rows(cls, v: int) -> int:
        if v < 1:
            raise ValueError("min_rows must be positive")
        return v

    @field_validator("default_params")
    def validate_default_params(cls, v: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        if "parameters" in values:
            param_names = {p.name for p in values["parameters"]}
            for k in v.keys():
                if k not in param_names:
                    raise ValueError(f"default_params contains unknown parameter: {k}")
        return v

class StrategyRequest(BaseModel):
    strategy_name: str
    symbol: str
    params: dict[str, Any] = Field(default_factory=dict)
    run_mode: StrategyRunMode = StrategyRunMode.RESEARCH
    timeframe: str = "1d"
    allow_short: bool = False
    use_latest_bar_only: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol", pre=True)
    def normalize_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.upper().strip()
            if v.endswith(".IS"):
                v = v[:-3]
        return v

    @field_validator("strategy_name")
    def normalize_strategy_name(cls, v: str) -> str:
        return str(v).lower().replace(" ", "_")

class StrategyExecutionIssue(BaseModel):
    strategy_name: str
    symbol: str | None = None
    message: str
    severity: str = "error"
    metadata: dict[str, Any] = Field(default_factory=dict)

class StrategyExecutionResult(BaseModel):
    request: StrategyRequest
    candidate: SignalCandidate | None = None
    output_data: pd.DataFrame | None = None
    status: str = "success"
    issues: list[StrategyExecutionIssue] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

    def summary(self) -> dict[str, Any]:
        return {
            "strategy": self.request.strategy_name,
            "symbol": self.request.symbol,
            "status": self.status,
            "has_candidate": self.candidate is not None,
            "candidate_direction": self.candidate.direction.value if self.candidate else None,
            "candidate_score": self.candidate.score if self.candidate else None,
            "issues_count": len(self.issues),
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "generated_at": self.generated_at.isoformat()
        }
