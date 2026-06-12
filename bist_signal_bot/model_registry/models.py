from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator, field_validator


class ModelRegistryStatus(str, Enum):
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    STAGING = "STAGING"
    CANDIDATE = "CANDIDATE"
    WATCH = "WATCH"
    FAILED_VALIDATION = "FAILED_VALIDATION"
    FAILED_CALIBRATION = "FAILED_CALIBRATION"
    BLOCKED_LEAKAGE = "BLOCKED_LEAKAGE"
    ARCHIVED = "ARCHIVED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class ModelKind(str, Enum):
    CLASSIFIER = "CLASSIFIER"
    REGRESSOR = "REGRESSOR"
    RANKER = "RANKER"
    ENSEMBLE = "ENSEMBLE"
    RULE_ASSISTED = "RULE_ASSISTED"
    CALIBRATOR = "CALIBRATOR"
    META_MODEL = "META_MODEL"
    BASELINE = "BASELINE"
    CUSTOM = "CUSTOM"


class ModelArtifactFormat(str, Enum):
    PICKLE = "PICKLE"
    JOBLIB = "JOBLIB"
    JSON = "JSON"
    ONNX = "ONNX"
    SKLEARN = "SKLEARN"
    XGBOOST = "XGBOOST"
    LIGHTGBM = "LIGHTGBM"
    CATBOOST = "CATBOOST"
    TORCH = "TORCH"
    TEXT = "TEXT"
    DIRECTORY = "DIRECTORY"
    UNKNOWN = "UNKNOWN"


class ExperimentStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"
    UNKNOWN = "UNKNOWN"


class ModelGovernanceStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class ModelPromotionStage(str, Enum):
    CANDIDATE = "CANDIDATE"
    STAGING = "STAGING"
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class ModelDriftType(str, Enum):
    PERFORMANCE_DECAY = "PERFORMANCE_DECAY"
    CALIBRATION_DECAY = "CALIBRATION_DECAY"
    FEATURE_DRIFT = "FEATURE_DRIFT"
    PREDICTION_DISTRIBUTION_SHIFT = "PREDICTION_DISTRIBUTION_SHIFT"
    CONFIDENCE_SHIFT = "CONFIDENCE_SHIFT"
    LABEL_DISTRIBUTION_SHIFT = "LABEL_DISTRIBUTION_SHIFT"
    UNKNOWN = "UNKNOWN"


class ModelRecord(BaseModel):
    model_id: str
    model_name: str
    model_kind: ModelKind
    version: str
    created_at: datetime
    updated_at: datetime | None = None
    status: ModelRegistryStatus
    artifact_id: str | None = None
    feature_set_id: str | None = None
    feature_set_version: str | None = None
    dataset_refs: list[str] = Field(default_factory=list)
    training_run_id: str | None = None
    validation_result_id: str | None = None
    calibration_result_id: str | None = None
    model_card_id: str | None = None
    owner_module: str | None = None
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model record is local research metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        if not v:
            raise ValueError("model_name cannot be empty")
        return v

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        if not v:
            raise ValueError("version cannot be empty")
        return v

    @field_validator('dataset_refs')
    @classmethod
    def validate_dataset_refs(cls, v: list[str]) -> list[str]:
        for ref in v:
            if 'token' in ref.lower() or 'secret' in ref.lower():
                raise ValueError("dataset_refs must not contain secrets")
        return v


class ExperimentRun(BaseModel):
    run_id: str
    experiment_name: str
    model_name: str
    model_kind: ModelKind
    status: ExperimentStatus
    started_at: datetime
    finished_at: datetime | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    feature_set_id: str | None = None
    feature_set_version: str | None = None
    dataset_refs: list[str] = Field(default_factory=list)
    random_seed: int | None = None
    code_ref: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Experiment run is local research experiment metadata only. It does not represent live trading performance or investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelArtifact(BaseModel):
    artifact_id: str
    model_id: str | None = None
    path: str
    artifact_format: ModelArtifactFormat
    created_at: datetime
    size_bytes: int | None = None
    checksum: str | None = None
    loadable: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('checksum')
    @classmethod
    def validate_checksum(cls, v: str | None) -> str | None:
        if v is not None and len(v) == 0:
            raise ValueError("checksum cannot be empty string if provided")
        return v

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        if 'token' in v.lower() or 'secret' in v.lower():
            raise ValueError("artifact path must not contain secrets")
        return v


class ModelCard(BaseModel):

    # Phase 106: Explainability Integration
    supported_explanation_methods: list[str] = Field(default_factory=list)
    top_feature_importance: dict[str, float] = Field(default_factory=dict)
    explanation_caveats: list[str] = Field(default_factory=list)
    unsupported_method_warnings: list[str] = Field(default_factory=list)
    card_id: str
    model_id: str
    model_name: str
    version: str
    created_at: datetime
    intended_use: str
    not_intended_use: str
    input_features: list[str]
    training_data_summary: str
    validation_summary: str
    calibration_summary: str
    known_limitations: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    governance_status: ModelGovernanceStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model card is local research documentation only. It is not investment advice, a recommendation, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('not_intended_use')
    @classmethod
    def validate_not_intended_use(cls, v: str) -> str:
        n_i_u = v.lower()
        if "real order execution" not in n_i_u or "investment advice" not in n_i_u:
            # We'll just append it to enforce the rule, or we could raise ValueError. Let's raise.
            raise ValueError("not_intended_use must state that 'real order execution' and 'investment advice' are not intended.")
        return v


class ModelValidationSummary(BaseModel):
    validation_id: str
    model_id: str
    created_at: datetime
    validation_method: str
    sample_count: int | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    walk_forward_summary: dict[str, Any] = Field(default_factory=dict)
    robustness_summary: dict[str, Any] = Field(default_factory=dict)
    overfit_warnings: list[str] = Field(default_factory=list)
    leakage_status: ModelGovernanceStatus
    feature_quality_score: float | None = None
    status: ModelGovernanceStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model validation summary is research-only statistical metadata. It is not investment advice or a live trading approval. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelCalibrationSummary(BaseModel):
    calibration_id: str
    model_id: str
    created_at: datetime
    calibration_method: str
    reliability_score: float | None = None
    brier_score: float | None = None
    expected_calibration_error: float | None = None
    calibration_bucket_count: int | None = None
    sample_count: int | None = None
    status: ModelGovernanceStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model calibration summary is research-only. It does not guarantee future model performance. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelPromotionRequest(BaseModel):
    promotion_id: str
    model_id: str
    requested_stage: ModelPromotionStage
    current_stage: ModelPromotionStage
    requested_at: datetime
    requested_by: str | None = None
    reason: str
    validation_status: ModelGovernanceStatus | None = None
    calibration_status: ModelGovernanceStatus | None = None
    leakage_status: ModelGovernanceStatus | None = None
    governance_decision: ModelGovernanceStatus
    approved: bool
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model promotion is research registry metadata only. It is not live deployment approval or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelDriftFinding(BaseModel):
    drift_id: str
    model_id: str
    drift_type: ModelDriftType
    baseline_window: str
    current_window: str
    baseline_value: float | None = None
    current_value: float | None = None
    drift_score: float | None = None
    status: ModelGovernanceStatus
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelLineageEdge(BaseModel):
    edge_id: str
    from_object_id: str
    to_object_id: str
    relation: str
    process_name: str | None = None
    created_at: datetime
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelGovernanceAssessment(BaseModel):
    assessment_id: str
    model_id: str
    created_at: datetime
    status: ModelGovernanceStatus
    validation_status: ModelGovernanceStatus | None = None
    calibration_status: ModelGovernanceStatus | None = None
    feature_quality_status: ModelGovernanceStatus | None = None
    leakage_status: ModelGovernanceStatus | None = None
    artifact_status: ModelGovernanceStatus | None = None
    model_card_status: ModelGovernanceStatus | None = None
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model governance assessment is local software governance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelRegistryReport(BaseModel):
    report_id: str
    generated_at: datetime
    models: list[ModelRecord] = Field(default_factory=list)
    experiments: list[ExperimentRun] = Field(default_factory=list)
    artifacts: list[ModelArtifact] = Field(default_factory=list)
    cards: list[ModelCard] = Field(default_factory=list)
    validation_summaries: list[ModelValidationSummary] = Field(default_factory=list)
    calibration_summaries: list[ModelCalibrationSummary] = Field(default_factory=list)
    promotion_requests: list[ModelPromotionRequest] = Field(default_factory=list)
    drift_findings: list[ModelDriftFinding] = Field(default_factory=list)
    lineage_edges: list[ModelLineageEdge] = Field(default_factory=list)
    governance_assessments: list[ModelGovernanceAssessment] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Model registry report is local research governance reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
