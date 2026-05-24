from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

class CorporateActionType(str, Enum):
    CASH_DIVIDEND = "CASH_DIVIDEND"
    STOCK_DIVIDEND = "STOCK_DIVIDEND"
    BONUS_ISSUE = "BONUS_ISSUE"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    STOCK_SPLIT = "STOCK_SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    CAPITAL_REDUCTION = "CAPITAL_REDUCTION"
    MERGER = "MERGER"
    SPIN_OFF = "SPIN_OFF"
    SYMBOL_CHANGE = "SYMBOL_CHANGE"
    UNKNOWN = "UNKNOWN"

class CorporateActionStatus(str, Enum):
    ANNOUNCED = "ANNOUNCED"
    CONFIRMED = "CONFIRMED"
    APPLIED = "APPLIED"
    CANCELLED = "CANCELLED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"

class AdjustmentDirection(str, Enum):
    BACKWARD = "BACKWARD"
    FORWARD = "FORWARD"

class CorporateActionRecord(BaseModel):
    action_id: str
    symbol: str
    action_type: CorporateActionType
    status: CorporateActionStatus
    announced_at: datetime | None = None
    ex_date: datetime | None = None
    payment_date: datetime | None = None
    effective_date: datetime
    cash_amount: float | None = None
    ratio: float | None = None
    old_shares: float | None = None
    new_shares: float | None = None
    rights_price: float | None = None
    adjustment_factor: float | None = None
    source: str
    source_ref: str | None = None
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    def validate_symbol(cls, v):
        return v.upper().strip()

    @field_validator("cash_amount", "ratio")
    def validate_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Value cannot be negative")
        return v

    @field_validator("adjustment_factor")
    def validate_factor(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Adjustment factor must be positive")
        return v

class PriceAdjustmentFactor(BaseModel):
    factor_id: str
    symbol: str
    effective_date: datetime
    action_ids: list[str] = Field(default_factory=list)
    factor: float
    cumulative_factor: float
    direction: AdjustmentDirection
    source: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AdjustedPriceResult(BaseModel):
    result_id: str
    symbol: str
    direction: AdjustmentDirection
    raw_rows: int = 0
    adjusted_rows: int = 0
    actions_applied: int = 0
    start_date: datetime | None = None
    end_date: datetime | None = None
    output_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Adjusted price output is historical data processing only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CorporateActionImportResult(BaseModel):
    import_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    source_path: str
    rows_seen: int = 0
    actions_imported: int = 0
    actions_skipped: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Corporate action import is operational data processing only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
