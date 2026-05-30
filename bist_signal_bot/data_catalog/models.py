from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

class DatasetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    MISSING = "MISSING"
    ARCHIVED = "ARCHIVED"
    UNKNOWN = "UNKNOWN"

class DatasetKind(str, Enum):
    OHLCV = "OHLCV"
    ADJUSTED_OHLCV = "ADJUSTED_OHLCV"
    INSTRUMENTS = "INSTRUMENTS"
    CORPORATE_ACTIONS = "CORPORATE_ACTIONS"
    EVENTS = "EVENTS"
    DISCLOSURES = "DISCLOSURES"
    FINANCIALS = "FINANCIALS"
    MACRO = "MACRO"
    VALUATION = "VALUATION"
    FACTORS = "FACTORS"
    BREADTH = "BREADTH"
    CONTEXT = "CONTEXT"
    REVIEW_WORKFLOW = "REVIEW_WORKFLOW"
    QA = "QA"
    OPS = "OPS"
    REPORTS = "REPORTS"
    CONFIG = "CONFIG"
    CUSTOM = "CUSTOM"

class DatasetFormat(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    JSONL = "JSONL"
    PARQUET = "PARQUET"
    SQLITE = "SQLITE"
    MARKDOWN = "MARKDOWN"
    DIRECTORY = "DIRECTORY"
    UNKNOWN = "UNKNOWN"

class DataQualityStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class SchemaDriftType(str, Enum):
    MISSING_COLUMN = "MISSING_COLUMN"
    EXTRA_COLUMN = "EXTRA_COLUMN"
    TYPE_CHANGED = "TYPE_CHANGED"
    NULLABILITY_CHANGED = "NULLABILITY_CHANGED"
    ENUM_CHANGED = "ENUM_CHANGED"
    DATE_FORMAT_CHANGED = "DATE_FORMAT_CHANGED"
    UNKNOWN = "UNKNOWN"

class LineageRelationType(str, Enum):
    IMPORTED_FROM = "IMPORTED_FROM"
    NORMALIZED_TO = "NORMALIZED_TO"
    DERIVED_FROM = "DERIVED_FROM"
    VALIDATED_BY = "VALIDATED_BY"
    USED_BY = "USED_BY"
    REPORTED_IN = "REPORTED_IN"
    LINKED_TO = "LINKED_TO"
    CUSTOM = "CUSTOM"

class DatasetContract(BaseModel):
    contract_id: str
    dataset_kind: DatasetKind
    name: str
    version: str
    required_columns: list[str] = Field(default_factory=list)
    optional_columns: list[str] = Field(default_factory=list)
    column_types: dict[str, str] = Field(default_factory=dict)
    primary_key_columns: list[str] = Field(default_factory=list)
    date_columns: list[str] = Field(default_factory=list)
    allowed_formats: list[DatasetFormat] = Field(default_factory=list)
    freshness_threshold_days: int | None = None
    max_null_ratio: float | None = None
    duplicate_policy: str = "WARN"
    quality_rules: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Dataset contract is local data governance metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DatasetRecord(BaseModel):
    dataset_id: str
    name: str = Field(min_length=1)
    dataset_kind: DatasetKind
    dataset_format: DatasetFormat
    path: str
    registered_at: datetime
    last_seen_at: datetime | None = None
    row_count: int | None = Field(default=None, ge=0)
    column_count: int | None = Field(default=None, ge=0)
    contract_id: str | None = None
    source_name: str | None = None
    source_ref: str | None = None
    status: DatasetStatus = DatasetStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DatasetProfile(BaseModel):
    profile_id: str
    dataset_id: str
    created_at: datetime
    row_count: int
    column_count: int
    columns: list[str] = Field(default_factory=list)
    null_ratios: dict[str, float] = Field(default_factory=dict)
    duplicate_count: int = 0
    min_dates: dict[str, str | None] = Field(default_factory=dict)
    max_dates: dict[str, str | None] = Field(default_factory=dict)
    numeric_ranges: dict[str, dict[str, float | None]] = Field(default_factory=dict)
    detected_format: DatasetFormat
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataQualityFinding(BaseModel):
    finding_id: str
    dataset_id: str
    rule_name: str
    status: DataQualityStatus
    severity: str
    message: str
    affected_columns: list[str] = Field(default_factory=list)
    affected_rows_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataQualityAssessment(BaseModel):
    assessment_id: str
    dataset_id: str
    created_at: datetime
    quality_score: float | None = None
    status: DataQualityStatus = DataQualityStatus.UNKNOWN
    findings: list[DataQualityFinding] = Field(default_factory=list)
    profile_ref: str | None = None
    contract_ref: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Data quality assessment is local data reliability metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class SchemaDriftFinding(BaseModel):
    drift_id: str
    dataset_id: str
    contract_id: str | None = None
    drift_type: SchemaDriftType
    column_name: str | None = None
    expected: str | None = None
    actual: str | None = None
    severity: str
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataLineageEdge(BaseModel):
    edge_id: str
    from_dataset_id: str
    to_dataset_id: str
    relation_type: LineageRelationType
    created_at: datetime
    process_name: str | None = None
    source_ref: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SourceProvenance(BaseModel):
    provenance_id: str
    dataset_id: str
    source_name: str
    source_type: str
    source_path: str | None = None
    source_ref: str | None = None
    imported_at: datetime | None = None
    imported_by: str | None = None
    checksum: str | None = None
    trust_level: str
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Source provenance is local lineage metadata only. It does not certify financial accuracy or investment suitability. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataQualityGateResult(BaseModel):
    gate_id: str
    dataset_id: str | None = None
    gate_name: str
    created_at: datetime
    status: DataQualityStatus
    required_score: float | None = None
    actual_score: float | None = None
    blocking_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Data quality gate is local software QA metadata only. It is not investment advice or a trading permission. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataCatalogReport(BaseModel):
    report_id: str
    generated_at: datetime
    datasets: list[DatasetRecord] = Field(default_factory=list)
    profiles: list[DatasetProfile] = Field(default_factory=list)
    assessments: list[DataQualityAssessment] = Field(default_factory=list)
    drift_findings: list[SchemaDriftFinding] = Field(default_factory=list)
    lineage_edges: list[DataLineageEdge] = Field(default_factory=list)
    provenance: list[SourceProvenance] = Field(default_factory=list)
    gates: list[DataQualityGateResult] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Data catalog report is local data governance reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
