from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import pandas as pd
from datetime import datetime

class PatternCategory(str, Enum):
    CANDLE = "CANDLE"
    BREAKOUT = "BREAKOUT"
    SUPPORT_RESISTANCE = "SUPPORT_RESISTANCE"
    PRICE_STRUCTURE = "PRICE_STRUCTURE"
    RANGE = "RANGE"
    GAP = "GAP"
    COMPOSITE = "COMPOSITE"
    UNKNOWN = "UNKNOWN"

class PatternDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"

class PatternStrength(str, Enum):
    WEAK = "WEAK"
    MEDIUM = "MEDIUM"
    STRONG = "STRONG"
    UNKNOWN = "UNKNOWN"

class PatternStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

@dataclass
class PatternSpec:
    name: str
    display_name: str
    category: PatternCategory
    required_columns: list[str]
    default_params: dict[str, Any]
    output_columns: list[str]
    min_rows: int
    description: str | None = None

@dataclass
class PatternRequest:
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    output_prefix: str | None = None

@dataclass
class PatternIssue:
    pattern: str
    message: str
    severity: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PatternResult:
    pattern: str
    status: PatternStatus
    output_columns: list[str]
    row_count: int
    detected_count: int
    issues: list[PatternIssue]
    elapsed_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "pattern": self.pattern,
            "status": self.status.value,
            "output_columns": self.output_columns,
            "row_count": self.row_count,
            "detected_count": self.detected_count,
            "issue_count": len(self.issues),
            "elapsed_seconds": round(self.elapsed_seconds, 4)
        }

@dataclass
class PatternBatchResult:
    results: list[PatternResult]
    output_data: pd.DataFrame
    requested_count: int
    success_count: int
    failed_count: int
    elapsed_seconds: float
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def summary(self) -> dict[str, Any]:
        return {
            "requested_count": self.requested_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "results": [r.summary() for r in self.results],
            "generated_at": self.generated_at.isoformat()
        }
