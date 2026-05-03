from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional
import pandas as pd
from pydantic import BaseModel, Field
from bist_signal_bot.data.models import Timeframe

class TimeframeRole(str, Enum):
    BASE = "BASE"
    HIGHER = "HIGHER"
    LOWER = "LOWER"
    DERIVED = "DERIVED"

class AlignmentMode(str, Enum):
    CLOSED_BAR_ONLY = "CLOSED_BAR_ONLY"
    ALLOW_CURRENT_PARTIAL = "ALLOW_CURRENT_PARTIAL"
    EXACT_TIMESTAMP = "EXACT_TIMESTAMP"
    ASOF_BACKWARD = "ASOF_BACKWARD"

class ResampleRule(str, Enum):
    DAILY = "1D"
    WEEKLY = "W-FRI"
    MONTHLY = "ME"

class TimeframeResampleConfig(BaseModel):
    source_timeframe: Timeframe
    target_timeframe: Timeframe
    rule: str
    label: str = "right"
    closed: str = "right"
    drop_incomplete: bool = True

class TimeframeAlignmentConfig(BaseModel):
    base_timeframe: Timeframe
    higher_timeframes: List[Timeframe]
    alignment_mode: AlignmentMode = AlignmentMode.CLOSED_BAR_ONLY
    forward_fill: bool = True
    shift_higher_tf_by_one_bar: bool = True
    prefix_columns: bool = True
    drop_unaligned_rows: bool = False

class TimeframeIssue(BaseModel):
    message: str
    severity: str
    timeframe: Optional[str] = None
    affected_rows: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class TimeframeResampleReport(BaseModel):
    source_timeframe: str
    target_timeframe: str
    input_rows: int
    output_rows: int
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    issues: List[TimeframeIssue] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def summary(self) -> dict[str, Any]:
        return {
            "source_timeframe": self.source_timeframe,
            "target_timeframe": self.target_timeframe,
            "input_rows": self.input_rows,
            "output_rows": self.output_rows,
            "issue_count": len(self.issues),
            "elapsed_seconds": self.elapsed_seconds,
            "generated_at": self.generated_at.isoformat()
        }

class TimeframeAlignmentReport(BaseModel):
    base_timeframe: str
    higher_timeframes: List[str]
    input_base_rows: int
    output_rows: int
    added_columns: List[str] = Field(default_factory=list)
    alignment_mode: AlignmentMode
    forward_fill: bool
    shift_higher_tf_by_one_bar: bool
    issues: List[TimeframeIssue] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def summary(self) -> dict[str, Any]:
        return {
            "base_timeframe": self.base_timeframe,
            "higher_timeframes": self.higher_timeframes,
            "input_base_rows": self.input_base_rows,
            "output_rows": self.output_rows,
            "added_columns_count": len(self.added_columns),
            "alignment_mode": self.alignment_mode.value,
            "forward_fill": self.forward_fill,
            "shift_higher_tf_by_one_bar": self.shift_higher_tf_by_one_bar,
            "issue_count": len(self.issues),
            "elapsed_seconds": self.elapsed_seconds,
            "generated_at": self.generated_at.isoformat()
        }

class MultiTimeframeResult(BaseModel):
    output_data: Any # pd.DataFrame
    resample_reports: List[TimeframeResampleReport] = Field(default_factory=list)
    alignment_report: TimeframeAlignmentReport
    symbol: str
    base_timeframe: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "arbitrary_types_allowed": True
    }

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "base_timeframe": self.base_timeframe,
            "output_rows": len(self.output_data) if isinstance(self.output_data, pd.DataFrame) else 0,
            "resample_reports_count": len(self.resample_reports),
            "alignment_report": self.alignment_report.summary() if self.alignment_report else None,
            "generated_at": self.generated_at.isoformat()
        }
