from enum import Enum
from typing import Any, Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field
import pandas as pd

class ProviderType(str, Enum):
    LOCAL_FILE = "LOCAL_FILE"
    YFINANCE = "YFINANCE"
    MOCK = "MOCK"
    CACHE = "CACHE"
    FALLBACK = "FALLBACK"
    UNKNOWN = "UNKNOWN"

class ProviderStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    DISABLED = "DISABLED"
    UNKNOWN = "UNKNOWN"

class DataFetchStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    EMPTY = "EMPTY"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class DataImportStatus(str, Enum):
    IMPORTED = "IMPORTED"
    PARTIAL_IMPORTED = "PARTIAL_IMPORTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    VALIDATION_FAILED = "VALIDATION_FAILED"

class DataLineageSource(BaseModel):
    source_id: str
    provider_type: ProviderType
    provider_name: str
    symbol: str
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    fetched_at: datetime
    row_count: int
    checksum: Optional[str] = None
    source_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProviderRequest(BaseModel):
    symbols: List[str]
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    rows: Optional[int] = None
    prefer_cache: bool = True
    allow_network: bool = False
    provider_order: List[ProviderType] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        self.symbols = [s.upper().strip() for s in self.symbols]
        if not self.timeframe:
            from bist_signal_bot.core.exceptions import DataProviderV2Error
            raise DataProviderV2Error("timeframe cannot be empty.")
        if self.rows is not None and self.rows <= 0:
            from bist_signal_bot.core.exceptions import DataProviderV2Error
            raise DataProviderV2Error("rows must be positive.")

class ProviderResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    request: ProviderRequest
    status: DataFetchStatus
    data_by_symbol: Dict[str, pd.DataFrame]
    lineage: List[DataLineageSource]
    provider_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "symbols_requested": len(self.request.symbols),
            "symbols_returned": len(self.data_by_symbol),
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
            "elapsed_seconds": round(self.elapsed_seconds, 3)
        }

class ProviderHealthSnapshot(BaseModel):
    provider_type: ProviderType
    provider_name: str
    status: ProviderStatus
    success_count: int = 0
    failure_count: int = 0
    empty_count: int = 0
    average_latency_seconds: Optional[float] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ImportRequest(BaseModel):
    input_path: str
    symbol: Optional[str] = None
    timeframe: str
    format: str
    delimiter: Optional[str] = None
    date_column: Optional[str] = None
    column_mapping: Dict[str, str] = Field(default_factory=dict)
    save_to_cache: bool = True
    overwrite: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ImportResult(BaseModel):
    request: ImportRequest
    status: DataImportStatus
    symbol: str
    timeframe: str
    rows_imported: int = 0
    output_path: Optional[str] = None
    lineage: Optional[DataLineageSource] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FreshnessReport(BaseModel):
    symbols: List[str]
    timeframe: str
    max_age_hours: float
    fresh_symbols: List[str] = Field(default_factory=list)
    stale_symbols: List[str] = Field(default_factory=list)
    missing_symbols: List[str] = Field(default_factory=list)
    average_age_hours: Optional[float] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DataComparisonReport(BaseModel):
    symbol: str
    timeframe: str
    left_source: str
    right_source: str
    row_count_left: int
    row_count_right: int
    matching_dates: int = 0
    price_diff_count: int = 0
    volume_diff_count: int = 0
    max_close_diff_pct: Optional[float] = None
    max_volume_diff_pct: Optional[float] = None
    status: str
    warnings: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
