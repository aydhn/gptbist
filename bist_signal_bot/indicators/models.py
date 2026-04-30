from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
import pandas as pd

class IndicatorCategory(str, Enum):
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    VOLUME = "VOLUME"
    PRICE = "PRICE"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class IndicatorOutputType(str, Enum):
    SERIES = "SERIES"
    DATAFRAME = "DATAFRAME"
    MULTI_SERIES = "MULTI_SERIES"

class IndicatorBackend(str, Enum):
    NATIVE = "NATIVE"
    TA = "TA"
    TALIB = "TALIB"
    CUSTOM = "CUSTOM"

class IndicatorSpec(BaseModel):
    name: str
    display_name: str
    category: IndicatorCategory
    backend: IndicatorBackend
    required_columns: List[str]
    default_params: Dict[str, Any]
    output_columns: List[str]
    min_rows: int
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v:
            raise ValueError("Indicator name cannot be empty")
        if v != v.lower() or ' ' in v:
            raise ValueError("Indicator name must be lowercase and contain no spaces (snake_case)")
        return v

    @field_validator('required_columns')
    @classmethod
    def validate_required_columns(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Indicator must require at least one column")
        return v

    @field_validator('min_rows')
    @classmethod
    def validate_min_rows(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("min_rows must be positive")
        return v

    @field_validator('output_columns')
    @classmethod
    def validate_output_columns(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Indicator must have at least one output column")
        return v

class IndicatorRequest(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    output_prefix: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v:
            raise ValueError("Indicator name cannot be empty")
        return v.lower().strip()

class IndicatorIssue(BaseModel):
    indicator: str
    message: str
    severity: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IndicatorResult(BaseModel):
    indicator: str
    status: str
    output_columns: List[str]
    row_count: int
    nan_count: int
    issues: List[IndicatorIssue] = Field(default_factory=list)
    elapsed_seconds: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "status": self.status,
            "output_columns": self.output_columns,
            "row_count": self.row_count,
            "nan_count": self.nan_count,
            "issues_count": len(self.issues),
            "elapsed_seconds": round(self.elapsed_seconds, 4)
        }

class IndicatorBatchResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    results: List[IndicatorResult]
    output_data: pd.DataFrame
    requested_count: int
    success_count: int
    failed_count: int
    elapsed_seconds: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def summary(self) -> Dict[str, Any]:
        return {
            "requested_count": self.requested_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "generated_at": self.generated_at.isoformat(),
            "results": [r.summary() for r in self.results]
        }
