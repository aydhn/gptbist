import re
from enum import Enum
from datetime import datetime
from typing import Any
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator


class BenchmarkCategory(str, Enum):
    BUY_AND_HOLD = "BUY_AND_HOLD"
    CASH = "CASH"
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    RANDOM_BASELINE = "RANDOM_BASELINE"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class BenchmarkPositionIntent(str, Enum):
    LONG = "LONG"
    FLAT = "FLAT"
    SHORT = "SHORT"
    HOLD = "HOLD"
    UNKNOWN = "UNKNOWN"

class BenchmarkStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class BenchmarkSpec(BaseModel):
    name: str
    display_name: str
    category: BenchmarkCategory
    description: str
    required_columns: list[str] = Field(default_factory=list)
    default_params: dict[str, Any] = Field(default_factory=dict)
    min_rows: int = Field(default=1)
    supports_portfolio: bool = Field(default=False)
    supports_short: bool = Field(default=False)
    deterministic: bool = Field(default=True)
    version: str = Field(default="1.0")

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("name must be lowercase snake_case")
        return v

    @field_validator("display_name")
    def validate_display_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("display_name cannot be empty")
        return v

    @field_validator("min_rows")
    def validate_min_rows(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("min_rows must be positive")
        return v


class BenchmarkRequest(BaseModel):
    benchmark_name: str
    symbol: str | None = None
    symbols: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    timeframe: str = Field(default="1d")
    run_mode: str = Field(default="research")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("benchmark_name")
    def validate_benchmark_name(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("symbol")
    def validate_symbol(cls, v: str | None) -> str | None:
        if v is not None:
            return v.upper().strip()
        return v

    @field_validator("symbols")
    def validate_symbols(cls, v: list[str]) -> list[str]:
        return [s.upper().strip() for s in v if s.strip()]


class BenchmarkSignal(BaseModel):
    symbol: str
    benchmark_name: str
    intent: BenchmarkPositionIntent
    score: float
    weight: float | None = None
    reference_price: float | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    signal_bar_timestamp: datetime | None = None
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = Field(default="Benchmark reference output only. Not investment advice. No order was sent.")

    @field_validator("score")
    def validate_score(cls, v: float) -> float:
        if not 0.0 <= v <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")
        return v

    @field_validator("weight")
    def validate_weight(cls, v: float | None) -> float | None:
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")
        return v


class BenchmarkExecutionResult(BaseModel):
    request: BenchmarkRequest
    status: BenchmarkStatus
    signals: list[BenchmarkSignal] = Field(default_factory=list)
    output_data: Any | None = None # Use Any to allow pandas dataframe, since pydantic struggles natively
    issues: list[str] = Field(default_factory=list)
    elapsed_seconds: float = Field(default=0.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    def summary(self) -> dict[str, Any]:
        return {
            "benchmark_name": self.request.benchmark_name,
            "status": self.status.value,
            "signal_count": len(self.signals),
            "long_count": self.long_count(),
            "flat_count": self.flat_count(),
            "short_count": self.short_count(),
            "elapsed_seconds": self.elapsed_seconds,
            "issues": self.issues
        }

    def long_count(self) -> int:
        return sum(1 for s in self.signals if s.intent == BenchmarkPositionIntent.LONG)

    def flat_count(self) -> int:
        return sum(1 for s in self.signals if s.intent == BenchmarkPositionIntent.FLAT)

    def short_count(self) -> int:
        return sum(1 for s in self.signals if s.intent == BenchmarkPositionIntent.SHORT)


class BenchmarkBatchResult(BaseModel):
    benchmark_name: str
    requested_symbols: list[str] = Field(default_factory=list)
    results: list[BenchmarkExecutionResult] = Field(default_factory=list)
    success_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    elapsed_seconds: float = Field(default=0.0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "benchmark_name": self.benchmark_name,
            "requested_symbols_count": len(self.requested_symbols),
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "elapsed_seconds": self.elapsed_seconds
        }
