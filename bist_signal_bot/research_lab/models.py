from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Literal

class ResearchJobType(str, Enum):
    DATA_UPDATE = "DATA_UPDATE"
    DATA_FRESHNESS_CHECK = "DATA_FRESHNESS_CHECK"
    BACKTEST = "BACKTEST"
    WALK_FORWARD = "WALK_FORWARD"
    OPTIMIZATION = "OPTIMIZATION"
    ML_RETRAIN = "ML_RETRAIN"
    ML_EVALUATE = "ML_EVALUATE"
    FEATURE_REFRESH = "FEATURE_REFRESH"
    DRIFT_CHECK = "DRIFT_CHECK"
    STRESS_TEST = "STRESS_TEST"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    ADAPTIVE_RECOMMEND = "ADAPTIVE_RECOMMEND"
    REPORT_GENERATE = "REPORT_GENERATE"
    SCENARIO_RUN = "SCENARIO_RUN"
    QUALITY_CHECK = "QUALITY_CHECK"
    SECURITY_CHECK = "SECURITY_CHECK"
    CUSTOM = "CUSTOM"

class ResearchJobStatus(str, Enum):
    PLANNED = "PLANNED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"

class ResearchJobPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

class ResearchJobTrigger(str, Enum):
    MANUAL = "MANUAL"
    ADAPTIVE_REFRESH_PLAN = "ADAPTIVE_REFRESH_PLAN"
    DRIFT_ACTION = "DRIFT_ACTION"
    MODEL_REFRESH = "MODEL_REFRESH"
    STRATEGY_DECAY = "STRATEGY_DECAY"
    DATA_FRESHNESS = "DATA_FRESHNESS"
    SIGNAL_DECAY = "SIGNAL_DECAY"
    STRESS_WARNING = "STRESS_WARNING"
    SCHEDULED = "SCHEDULED"
    RUNTIME = "RUNTIME"
    SCENARIO = "SCENARIO"
    UNKNOWN = "UNKNOWN"

class ResearchJobRiskLevel(str, Enum):
    SAFE = "SAFE"
    RESOURCE_HEAVY = "RESOURCE_HEAVY"
    WRITES_LOCAL_OUTPUT = "WRITES_LOCAL_OUTPUT"
    REQUIRES_CONFIRM = "REQUIRES_CONFIRM"
    UNKNOWN = "UNKNOWN"

class ResearchJob(BaseModel):
    job_id: str
    job_type: ResearchJobType
    status: ResearchJobStatus = ResearchJobStatus.PLANNED
    priority: ResearchJobPriority = ResearchJobPriority.NORMAL
    trigger: ResearchJobTrigger = ResearchJobTrigger.MANUAL
    title: str
    command_preview: List[str] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list)
    strategy_name: Optional[str] = None
    model_id: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    dedupe_key: str = ""
    risk_level: ResearchJobRiskLevel = ResearchJobRiskLevel.SAFE
    max_runtime_seconds: int = Field(gt=0, default=900)
    retry_count: int = Field(ge=0, default=0)
    max_retries: int = Field(ge=0, default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    output_refs: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("title")
    def validate_title(cls, v):
        if not v or not str(v).strip():
            raise ValueError("title cannot be empty")
        return v

    @validator("symbols")
    def validate_symbols(cls, v):
        if v is None:
            return []
        return sorted(list(set([str(s).upper().strip() for s in v if s])))

    @validator("command_preview", always=True)
    def validate_command_preview(cls, v, values):
        if not v and not values.get('metadata', {}).get('function'):
             pass
        return v

class ResearchJobResult(BaseModel):
    result_id: str
    job_id: str
    status: ResearchJobStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    exit_code: Optional[int] = None
    stdout_tail: Optional[str] = None
    stderr_tail: Optional[str] = None
    output_refs: Dict[str, str] = Field(default_factory=dict)
    produced_research_run_ids: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResearchBatchPlan(BaseModel):
    plan_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    trigger: ResearchJobTrigger
    jobs: List[ResearchJob] = Field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    estimated_runtime_seconds: Optional[float] = None
    estimated_memory_mb: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Research batch plan is research-only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResearchBatchRun(BaseModel):
    batch_id: str
    plan_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    status: ResearchJobStatus = ResearchJobStatus.RUNNING
    jobs: List[ResearchJob] = Field(default_factory=list)
    results: List[ResearchJobResult] = Field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    cancelled_count: int = 0
    elapsed_seconds: float = 0.0
    output_files: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Research batch run is research-only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "status": self.status.value,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "elapsed_seconds": self.elapsed_seconds,
            "warnings": len(self.warnings),
            "errors": len(self.errors)
        }

    def safe_public_dict(self) -> Dict[str, Any]:
        d = self.summary()
        d["disclaimer"] = self.disclaimer
        return d

class ResearchLabPolicy(BaseModel):
    max_jobs_per_batch: int = Field(default=20, gt=0)
    max_parallel_jobs: int = Field(default=1, ge=1)
    max_runtime_seconds_per_job: int = Field(default=900, gt=0)
    max_runtime_seconds_per_batch: int = Field(default=3600, gt=0)
    max_memory_mb: Optional[int] = Field(default=4096)
    allow_network: bool = Field(default=False)
    allow_telegram: bool = Field(default=False)
    allow_destructive: bool = Field(default=False)
    require_confirm_for_heavy_jobs: bool = Field(default=True)
    dedupe_window_hours: int = Field(default=24, gt=0)
    default_max_retries: int = Field(default=1, ge=0)
    retry_backoff_seconds: int = Field(default=30, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
