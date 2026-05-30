from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class FeatureStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    MISSING = "MISSING"
    ARCHIVED = "ARCHIVED"
    UNKNOWN = "UNKNOWN"

class FeatureKind(str, Enum):
    TECHNICAL = "TECHNICAL"
    PRICE_ACTION = "PRICE_ACTION"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    LIQUIDITY = "LIQUIDITY"
    VOLUME = "VOLUME"
    FUNDAMENTAL = "FUNDAMENTAL"
    VALUATION = "VALUATION"
    FACTOR = "FACTOR"
    BREADTH = "BREADTH"
    MACRO = "MACRO"
    EVENT = "EVENT"
    DISCLOSURE = "DISCLOSURE"
    PORTFOLIO = "PORTFOLIO"
    TARGET_LABEL = "TARGET_LABEL"
    CUSTOM = "CUSTOM"

class FeatureDataType(str, Enum):
    FLOAT = "FLOAT"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    CATEGORY = "CATEGORY"
    DATETIME = "DATETIME"
    ARRAY = "ARRAY"
    UNKNOWN = "UNKNOWN"

class FeatureQualityStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class FeatureDriftType(str, Enum):
    MEAN_SHIFT = "MEAN_SHIFT"
    VARIANCE_SHIFT = "VARIANCE_SHIFT"
    DISTRIBUTION_SHIFT = "DISTRIBUTION_SHIFT"
    MISSING_RATIO_SHIFT = "MISSING_RATIO_SHIFT"
    OUTLIER_RATIO_SHIFT = "OUTLIER_RATIO_SHIFT"
    CONSTANT_VALUE = "CONSTANT_VALUE"
    CATEGORY_SHIFT = "CATEGORY_SHIFT"
    UNKNOWN = "UNKNOWN"

class FeatureLeakageType(str, Enum):
    FUTURE_TIMESTAMP = "FUTURE_TIMESTAMP"
    TARGET_LEAKAGE = "TARGET_LEAKAGE"
    POST_EVENT_DATA = "POST_EVENT_DATA"
    LOOKAHEAD_WINDOW = "LOOKAHEAD_WINDOW"
    SAME_DAY_CLOSE_IN_INTRADAY_CONTEXT = "SAME_DAY_CLOSE_IN_INTRADAY_CONTEXT"
    UNKNOWN = "UNKNOWN"

class FeatureContract(BaseModel):
    contract_id: str
    feature_name: str
    feature_kind: FeatureKind
    dtype: FeatureDataType
    version: str
    description: str
    required_inputs: list[str] = Field(default_factory=list)
    allowed_null_ratio: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    lookback_days: int | None = None
    freshness_threshold_days: int | None = None
    point_in_time_required: bool = True
    leakage_sensitive: bool = False
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Feature contract is local research metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureDefinition(BaseModel):
    feature_id: str
    feature_name: str
    feature_kind: FeatureKind
    contract_id: str | None = None
    compute_fn_name: str | None = None
    source_datasets: list[str] = Field(default_factory=list)
    owner_module: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    status: FeatureStatus = FeatureStatus.ACTIVE
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureSet(BaseModel):
    feature_set_id: str
    name: str
    version: str
    feature_names: list[str] = Field(default_factory=list)
    created_at: datetime
    purpose: str
    owner_module: str | None = None
    status: FeatureStatus = FeatureStatus.ACTIVE
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Feature set is local research feature grouping only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureValue(BaseModel):
    value_id: str
    feature_name: str
    symbol: str
    timestamp: datetime
    as_of: datetime
    value: float | int | str | bool | None
    feature_set_id: str | None = None
    version: str | None = None
    source_ref: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureFrame(BaseModel):
    frame_id: str
    feature_set_id: str
    symbols: list[str] = Field(default_factory=list)
    as_of: datetime
    rows: list[dict[str, Any]] = Field(default_factory=list)
    feature_names: list[str] = Field(default_factory=list)
    row_count: int
    column_count: int
    point_in_time_safe: bool = True
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Feature frame is local research data only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureQualityFinding(BaseModel):
    finding_id: str
    feature_name: str
    feature_set_id: str | None = None
    rule_name: str
    status: FeatureQualityStatus
    severity: str
    message: str
    affected_symbols: list[str] = Field(default_factory=list)
    affected_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureQualityAssessment(BaseModel):
    assessment_id: str
    feature_set_id: str | None = None
    feature_name: str | None = None
    created_at: datetime
    quality_score: float | None = None
    status: FeatureQualityStatus
    findings: list[FeatureQualityFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Feature quality assessment is local software QA metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureDriftFinding(BaseModel):
    drift_id: str
    feature_name: str
    drift_type: FeatureDriftType
    baseline_window: str
    current_window: str
    baseline_value: float | None = None
    current_value: float | None = None
    drift_score: float | None = None
    status: FeatureQualityStatus
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureLeakageFinding(BaseModel):
    leakage_id: str
    feature_name: str
    leakage_type: FeatureLeakageType
    symbol: str | None = None
    timestamp: datetime | None = None
    as_of: datetime | None = None
    severity: str
    message: str
    status: FeatureQualityStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureLineageEdge(BaseModel):
    edge_id: str
    from_object_id: str
    to_object_id: str
    relation: str
    process_name: str | None = None
    created_at: datetime
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureVersion(BaseModel):
    version_id: str
    feature_name: str
    version: str
    created_at: datetime
    contract_id: str | None = None
    compute_hash: str | None = None
    input_contract_refs: list[str] = Field(default_factory=list)
    change_summary: str
    status: FeatureStatus = FeatureStatus.ACTIVE
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FeatureStoreReport(BaseModel):
    report_id: str
    generated_at: datetime
    features: list[FeatureDefinition] = Field(default_factory=list)
    feature_sets: list[FeatureSet] = Field(default_factory=list)
    quality_assessments: list[FeatureQualityAssessment] = Field(default_factory=list)
    drift_findings: list[FeatureDriftFinding] = Field(default_factory=list)
    leakage_findings: list[FeatureLeakageFinding] = Field(default_factory=list)
    lineage_edges: list[FeatureLineageEdge] = Field(default_factory=list)
    versions: list[FeatureVersion] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Feature store report is local feature governance reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
