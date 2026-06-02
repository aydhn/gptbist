from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime

class ImportStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    DRY_RUN = "DRY_RUN"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class ImportSourceFormat(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    JSONL = "JSONL"
    PARQUET = "PARQUET"
    SQLITE = "SQLITE"
    EXCEL = "EXCEL"
    DIRECTORY = "DIRECTORY"
    UNKNOWN = "UNKNOWN"

class ImportDatasetType(str, Enum):
    OHLCV = "OHLCV"
    ADJUSTED_OHLCV = "ADJUSTED_OHLCV"
    INSTRUMENTS = "INSTRUMENTS"
    CORPORATE_ACTIONS = "CORPORATE_ACTIONS"
    DISCLOSURES = "DISCLOSURES"
    FINANCIALS = "FINANCIALS"
    MACRO = "MACRO"
    FACTORS = "FACTORS"
    BREADTH = "BREADTH"
    EVENTS = "EVENTS"
    CUSTOM = "CUSTOM"

class ColumnSemanticType(str, Enum):
    SYMBOL = "SYMBOL"
    DATE = "DATE"
    DATETIME = "DATETIME"
    OPEN = "OPEN"
    HIGH = "HIGH"
    LOW = "LOW"
    CLOSE = "CLOSE"
    ADJUSTED_CLOSE = "ADJUSTED_CLOSE"
    VOLUME = "VOLUME"
    TEXT = "TEXT"
    NUMERIC = "NUMERIC"
    CATEGORY = "CATEGORY"
    BOOLEAN = "BOOLEAN"
    UNKNOWN = "UNKNOWN"

class ImportAdapterCapability(str, Enum):
    PREVIEW = "PREVIEW"
    CHUNK_READ = "CHUNK_READ"
    SCHEMA_INFER = "SCHEMA_INFER"
    TYPE_INFER = "TYPE_INFER"
    WRITE_NORMALIZED = "WRITE_NORMALIZED"
    CHECKSUM = "CHECKSUM"
    CUSTOM = "CUSTOM"

class ImportSource(BaseModel):
    source_id: str
    path: str
    source_format: ImportSourceFormat
    dataset_type: ImportDatasetType
    created_at: datetime
    size_bytes: int | None = None
    checksum: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ColumnMapping(BaseModel):
    mapping_id: str
    source_column: str
    target_column: str
    semantic_type: ColumnSemanticType
    required: bool
    transform: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SchemaMapping(BaseModel):
    schema_mapping_id: str
    dataset_type: ImportDatasetType
    source_columns: list[str]
    column_mappings: list[ColumnMapping]
    unmapped_columns: list[str]
    missing_required_targets: list[str]
    confidence_score: float | None = None
    status: ImportStatus = ImportStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Schema mapping is local data import metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ImportPreview(BaseModel):
    preview_id: str
    source_id: str
    created_at: datetime
    row_count_estimate: int | None = None
    column_count: int
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    inferred_types: dict[str, str]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Import preview is local data inspection output only. It is not investment advice or data accuracy certification. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ImportValidationFinding(BaseModel):
    finding_id: str
    source_id: str
    rule_name: str
    status: ImportStatus
    severity: str
    message: str
    affected_columns: list[str] = Field(default_factory=list)
    affected_rows_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ImportValidationResult(BaseModel):
    validation_id: str
    source_id: str
    created_at: datetime
    status: ImportStatus
    findings: list[ImportValidationFinding] = Field(default_factory=list)
    schema_mapping_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Import validation is local software validation metadata only. It does not certify financial correctness or investment suitability. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class NormalizedImportResult(BaseModel):
    normalized_id: str
    source_id: str
    dataset_type: ImportDatasetType
    created_at: datetime
    output_path: str | None = None
    row_count: int
    column_count: int
    normalized_columns: list[str] = Field(default_factory=list)
    duplicate_rows_removed: int = 0
    invalid_rows_removed: int = 0
    status: ImportStatus = ImportStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Normalized import result is local data processing metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ImportJob(BaseModel):
    job_id: str
    source: ImportSource
    schema_mapping: SchemaMapping | None = None
    preview: ImportPreview | None = None
    validation: ImportValidationResult | None = None
    normalized_result: NormalizedImportResult | None = None
    dry_run: bool = True
    confirm: bool = False
    status: ImportStatus = ImportStatus.UNKNOWN
    started_at: datetime
    finished_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Import job is local data ingestion workflow metadata only. It is not investment advice, data accuracy certification, or trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DataImportReport(BaseModel):
    report_id: str
    generated_at: datetime
    sources: list[ImportSource] = Field(default_factory=list)
    previews: list[ImportPreview] = Field(default_factory=list)
    mappings: list[SchemaMapping] = Field(default_factory=list)
    validations: list[ImportValidationResult] = Field(default_factory=list)
    normalized_results: list[NormalizedImportResult] = Field(default_factory=list)
    jobs: list[ImportJob] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Data import report is local metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
