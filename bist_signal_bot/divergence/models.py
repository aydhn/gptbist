from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import pandas as pd


class PivotType(str, Enum):
    HIGH = "HIGH"
    LOW = "LOW"

class PivotMode(str, Enum):
    LOOKBACK_ONLY = "LOOKBACK_ONLY"
    CONFIRMED_LAGGED = "CONFIRMED_LAGGED"

class DivergenceType(str, Enum):
    REGULAR_BULLISH = "REGULAR_BULLISH"
    REGULAR_BEARISH = "REGULAR_BEARISH"
    HIDDEN_BULLISH = "HIDDEN_BULLISH"
    HIDDEN_BEARISH = "HIDDEN_BEARISH"
    NONE = "NONE"

class DivergenceStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class DivergenceStrength(str, Enum):
    WEAK = "WEAK"
    MEDIUM = "MEDIUM"
    STRONG = "STRONG"
    UNKNOWN = "UNKNOWN"

class PivotPoint(BaseModel):
    timestamp: datetime
    index_position: int
    pivot_type: PivotType
    value: float
    confirmed: bool
    confirmation_lag: int
    metadata: dict[str, Any] = Field(default_factory=dict)

class DivergenceEvent(BaseModel):
    symbol: str
    indicator: str
    divergence_type: DivergenceType
    pivot_mode: PivotMode
    price_pivot_1_timestamp: datetime
    price_pivot_2_timestamp: datetime
    indicator_pivot_1_value: float
    indicator_pivot_2_value: float
    price_pivot_1_value: float
    price_pivot_2_value: float
    bars_between: int
    strength_score: float
    strength: DivergenceStrength
    confirmed: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

from pydantic import model_validator

class DivergenceRequest(BaseModel):
    indicators: list[str]
    pivot_mode: PivotMode = PivotMode.LOOKBACK_ONLY
    lookback: int = 5
    confirmation_bars: int = 3
    max_pivot_distance: int = 60
    min_pivot_distance: int = 3
    min_strength_score: float = 0.0
    include_hidden: bool = True
    include_regular: bool = True

    @field_validator("indicators")
    @classmethod
    def check_indicators(cls, v):
        if not v:
            raise ValueError("indicators list cannot be empty")
        return v

    @field_validator("lookback")
    @classmethod
    def check_lookback(cls, v):
        if v <= 0:
            raise ValueError("lookback must be positive")
        return v

    @field_validator("confirmation_bars")
    @classmethod
    def check_confirmation_bars(cls, v):
        if v < 0:
            raise ValueError("confirmation_bars cannot be negative")
        return v

    @field_validator("min_strength_score")
    @classmethod
    def check_min_strength_score(cls, v):
        if not (0.0 <= v <= 100.0):
            raise ValueError("min_strength_score must be between 0.0 and 100.0")
        return v

class DivergenceIssue(BaseModel):
    indicator: str | None = None
    message: str
    severity: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class DivergenceResult(BaseModel):
    symbol: str
    timeframe: str
    status: DivergenceStatus
    pivot_mode: PivotMode
    requested_indicators: list[str]
    events: list[DivergenceEvent] = Field(default_factory=list)
    output_columns: list[str] = Field(default_factory=list)
    row_count: int = 0
    detected_count: int = 0
    issues: list[DivergenceIssue] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "status": self.status.value,
            "pivot_mode": self.pivot_mode.value,
            "requested_indicators": self.requested_indicators,
            "row_count": self.row_count,
            "detected_count": self.detected_count,
            "bullish_count": self.bullish_count(),
            "bearish_count": self.bearish_count(),
            "strong_count": self.strong_count(),
            "issue_count": len(self.issues),
            "output_columns": self.output_columns,
            "elapsed_seconds": self.elapsed_seconds,
            "generated_at": self.generated_at.isoformat()
        }

    def bullish_count(self) -> int:
        return sum(1 for e in self.events if e.divergence_type in (DivergenceType.REGULAR_BULLISH, DivergenceType.HIDDEN_BULLISH))

    def bearish_count(self) -> int:
        return sum(1 for e in self.events if e.divergence_type in (DivergenceType.REGULAR_BEARISH, DivergenceType.HIDDEN_BEARISH))

    def strong_count(self) -> int:
        return sum(1 for e in self.events if e.strength == DivergenceStrength.STRONG)

class DivergenceFeatureResult(BaseModel):
    result: DivergenceResult
    output_data: Any = Field(description="Output DataFrame. Annotated as Any to avoid pydantic issues with pandas.")

    class Config:
        arbitrary_types_allowed = True
def check_max_min_distance(cls, values):
    min_dist = values.data.get('min_pivot_distance')
    max_dist = values.data.get('max_pivot_distance')
    if min_dist is not None and max_dist is not None:
        if max_dist <= min_dist:
            raise ValueError("max_pivot_distance must be strictly greater than min_pivot_distance")
    return values

# We have to patch DivergenceRequest with model_validator
