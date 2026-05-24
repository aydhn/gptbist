from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class DataIssueType(str, Enum):
    MISSING_BAR = "MISSING_BAR"
    DUPLICATE_BAR = "DUPLICATE_BAR"
    ZERO_PRICE = "ZERO_PRICE"
    NEGATIVE_PRICE = "NEGATIVE_PRICE"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    ABNORMAL_GAP = "ABNORMAL_GAP"
    PROVIDER_MISMATCH = "PROVIDER_MISMATCH"
    CORPORATE_ACTION_GAP = "CORPORATE_ACTION_GAP"
    STALE_DATA = "STALE_DATA"
    UNKNOWN = "UNKNOWN"

class DataIssueSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DataQualityIssue(BaseModel):
    issue_id: str
    symbol: str
    issue_type: DataIssueType
    severity: DataIssueSeverity
    timestamp: datetime | None = None
    message: str
    source: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataReconciliationResult(BaseModel):
    reconciliation_id: str
    symbol: str
    provider_a: str
    provider_b: str
    rows_compared: int = 0
    mismatches: int = 0
    max_close_diff_pct: float | None = None
    max_volume_diff_pct: float | None = None
    issues: list[DataQualityIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Data reconciliation is operational data quality output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
