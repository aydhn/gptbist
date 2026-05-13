from enum import Enum
from typing import Any
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field

class MLTaskType(str, Enum):
    CLASSIFICATION = "CLASSIFICATION"
    REGRESSION = "REGRESSION"
    RANKING = "RANKING"
    UNKNOWN = "UNKNOWN"

class LabelType(str, Enum):
    FORWARD_RETURN = "FORWARD_RETURN"
    BINARY_DIRECTION = "BINARY_DIRECTION"
    MULTICLASS_DIRECTION = "MULTICLASS_DIRECTION"
    THRESHOLD_EVENT = "THRESHOLD_EVENT"
    VOLATILITY_ADJUSTED_RETURN = "VOLATILITY_ADJUSTED_RETURN"
    RISK_ADJUSTED_RETURN = "RISK_ADJUSTED_RETURN"

class FeatureSetLevel(str, Enum):
    BASIC = "BASIC"
    ADVANCED = "ADVANCED"
    FULL = "FULL"
    CUSTOM = "CUSTOM"

class DatasetSplitMode(str, Enum):
    NONE = "NONE"
    TRAIN_TEST = "TRAIN_TEST"
    WALK_FORWARD = "WALK_FORWARD"
    EXPANDING = "EXPANDING"
    ROLLING = "ROLLING"

class FeatureStoreFormat(str, Enum):
    PARQUET = "PARQUET"
    CSV = "CSV"
    JSON = "JSON"

class MLDatasetStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    EMPTY = "EMPTY"

class LabelConfig(BaseModel):
    label_type: LabelType
    horizon_bars: int = Field(gt=0)
    positive_threshold: float = Field(ge=0.0, default=0.02)
    negative_threshold: float = Field(le=0.0, default=-0.02)
    neutral_class_enabled: bool = True
    volatility_adjust: bool = False
    cost_adjust: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def validate_thresholds(self):
        if self.positive_threshold <= self.negative_threshold:
            raise ValueError("positive_threshold must be greater than negative_threshold")
        return self

class FeatureConfig(BaseModel):
    feature_set_level: FeatureSetLevel
    include_trend: bool = True
    include_momentum: bool = True
    include_volatility: bool = True
    include_volume: bool = True
    include_patterns: bool = True
    include_divergence: bool = True
    include_mtf: bool = False
    include_raw_ohlcv: bool = False
    include_returns: bool = True
    include_regime: bool = True
    custom_features: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PreprocessingConfig(BaseModel):
    drop_na_labels: bool = True
    drop_na_features: bool = False
    fill_method: str = "median"
    winsorize: bool = False
    winsorize_lower_pct: float = Field(ge=0.0, le=1.0, default=0.01)
    winsorize_upper_pct: float = Field(ge=0.0, le=1.0, default=0.99)
    standardize: bool = False
    robust_scale: bool = False
    remove_inf: bool = True
    max_missing_feature_pct: float = Field(ge=0.0, le=1.0, default=0.50)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def validate_winsorize(self):
        if self.fill_method not in ["none", "ffill", "bfill", "zero", "median"]:
            raise ValueError("Invalid fill_method")
        if self.winsorize_lower_pct >= self.winsorize_upper_pct:
            raise ValueError("winsorize_lower_pct must be less than winsorize_upper_pct")
        return self

class MLDatasetRequest(BaseModel):
    symbols: list[str]
    source: str
    timeframe: str
    rows: int | None = None
    period: str | None = None
    task_type: MLTaskType
    label_config: LabelConfig
    feature_config: FeatureConfig
    preprocessing_config: PreprocessingConfig
    split_mode: DatasetSplitMode
    train_ratio: float = Field(ge=0.0, le=1.0, default=0.7)
    save: bool = False
    formats: list[FeatureStoreFormat] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def validate_request(self):
        if not self.symbols:
            raise ValueError("symbols cannot be empty")
        self.symbols = [s.upper() for s in self.symbols]
        if self.source not in ["mock", "local"]:
            raise ValueError("source must be mock or local")
        if not self.formats:
            self.formats = [FeatureStoreFormat.PARQUET, FeatureStoreFormat.CSV]
        return self

class MLDatasetSchema(BaseModel):
    symbol_col: str
    timestamp_col: str
    feature_cols: list[str]
    label_cols: list[str]
    target_col: str | None = None
    metadata_cols: list[str]
    excluded_cols: list[str]
    generated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol_col": self.symbol_col,
            "timestamp_col": self.timestamp_col,
            "feature_count": len(self.feature_cols),
            "label_count": len(self.label_cols),
            "metadata_count": len(self.metadata_cols),
            "excluded_count": len(self.excluded_cols),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }

class MLDatasetResult(BaseModel):
    request: MLDatasetRequest
    status: MLDatasetStatus
    data: Any # pd.DataFrame
    schema_: MLDatasetSchema # use schema_ as schema is reserved
    train_data: Any | None = None # pd.DataFrame
    test_data: Any | None = None # pd.DataFrame
    issues: list[str] = Field(default_factory=list)
    output_files: dict[str, str] = Field(default_factory=dict)
    row_count: int = 0
    feature_count: int = 0
    label_count: int = 0
    symbol_count: int = 0
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float = 0.0
    disclaimer: str = "ML dataset research output only. Labels use future returns as targets; this is not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "symbols": len(self.request.symbols),
            "row_count": self.row_count,
            "feature_count": self.feature_count,
            "label_count": self.label_count,
            "train_rows": len(self.train_data) if self.train_data is not None else 0,
            "test_rows": len(self.test_data) if self.test_data is not None else 0,
            "output_files": self.output_files,
            "issues": self.issues,
            "elapsed_seconds": self.elapsed_seconds,
        }

    def safe_public_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "symbols": len(self.request.symbols),
            "row_count": self.row_count,
            "feature_count": self.feature_count,
            "label_count": self.label_count,
            "elapsed_seconds": self.elapsed_seconds,
            "disclaimer": self.disclaimer
        }
