from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class RuntimeMode(str, Enum):
    RUN_ONCE = "RUN_ONCE"
    LOOP = "LOOP"
    DRY_RUN = "DRY_RUN"
    STATUS_ONLY = "STATUS_ONLY"
    DISABLED = "DISABLED"

class RuntimeJobType(str, Enum):
    DATA_REFRESH = "DATA_REFRESH"
    SIGNAL_SCAN = "SIGNAL_SCAN"
    REGIME_ANALYSIS = "REGIME_ANALYSIS"
    ML_INFERENCE = "ML_INFERENCE"
    RISK_EVALUATION = "RISK_EVALUATION"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    PAPER_RUN = "PAPER_RUN"
    HEALTHCHECK = "HEALTHCHECK"
    CLEANUP = "CLEANUP"
    TELEGRAM_SUMMARY = "TELEGRAM_SUMMARY"
    CUSTOM = "CUSTOM"

class RuntimeJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"

class RuntimePipelineStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    LOCKED = "LOCKED"
    DISABLED = "DISABLED"

class RuntimeTrigger(str, Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    CLI = "CLI"
    TEST = "TEST"
    RECOVERY = "RECOVERY"

class SessionPolicy(str, Enum):
    RUN_ALWAYS = "RUN_ALWAYS"
    ONLY_DURING_SESSION = "ONLY_DURING_SESSION"
    ONLY_AFTER_CLOSE = "ONLY_AFTER_CLOSE"
    SKIP_DURING_SESSION = "SKIP_DURING_SESSION"
    DRY_RUN_OUTSIDE_SESSION = "DRY_RUN_OUTSIDE_SESSION"

class RuntimeJobConfig(BaseModel):
    job_type: RuntimeJobType
    enabled: bool = True
    interval_minutes: Optional[int] = None
    max_retries: int = Field(default=1, ge=0)
    retry_delay_seconds: int = Field(default=5, ge=0)
    timeout_seconds: Optional[int] = Field(default=0, ge=0)
    session_policy: SessionPolicy = SessionPolicy.ONLY_DURING_SESSION
    continue_on_error: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RuntimePipelineConfig(BaseModel):
    config_gate_before_run: bool = False
    runtime_profile: str | None = None
    profile_runtime: bool = False
    performance_budget_enabled: bool = False
    build_research_portfolio: bool = False
    portfolio_allocation_method: str | None = None
    portfolio_max_items: int | None = None
    mode: RuntimeMode = RuntimeMode.RUN_ONCE
    strategy_name: str
    universe_mode: str = "GROUP"
    symbols: List[str] = Field(default_factory=list)
    watchlist_name: Optional[str] = None
    group_name: Optional[str] = None
    source: str = "mock"
    timeframe: str = "1d"
    rows: Optional[int] = None
    top_n: int = Field(default=10, gt=0)
    use_trade_risk: bool = True
    use_portfolio_risk: bool = True
    use_ml_filter: bool = False
    ml_model_id: Optional[str] = None
    use_regime_filter: bool = False
    use_paper: bool = False
    send_telegram: bool = False
    save_reports: bool = True
    dry_run: bool = False
    session_policy: SessionPolicy = SessionPolicy.ONLY_DURING_SESSION
    continue_on_error: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RuntimeJobResult(BaseModel):
    job_id: str
    job_type: RuntimeJobType
    status: RuntimeJobStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    attempts: int = 1
    summary: Dict[str, Any] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    output_files: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "elapsed": self.elapsed_seconds,
            "issues": len(self.issues)
        }

class RuntimePipelineResult(BaseModel):
    config_gate_status: str | None = None
    config_snapshot_id: str | None = None
    performance_profile_id: str | None = None
    memory_peak_mb: float | None = None
    slowest_stage: str | None = None
    run_id: str
    trigger: RuntimeTrigger
    config: RuntimePipelineConfig
    status: RuntimePipelineStatus
    job_results: List[RuntimeJobResult] = Field(default_factory=list)
    scan_report_summary: Optional[Dict[str, Any]] = None
    paper_result_summary: Optional[Dict[str, Any]] = None
    regime_summary: Optional[Dict[str, Any]] = None
    ml_summary: Optional[Dict[str, Any]] = None
    healthcheck_summary: Optional[Dict[str, Any]] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    output_files: Dict[str, str] = Field(default_factory=dict)
    disclaimer: str = "Runtime pipeline research output only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "jobs_total": len(self.job_results),
            "jobs_success": self.success_count(),
            "elapsed": self.elapsed_seconds
        }

    def success_count(self) -> int:
        return sum(1 for j in self.job_results if j.status == RuntimeJobStatus.SUCCESS)

    def failed_count(self) -> int:
        return sum(1 for j in self.job_results if j.status == RuntimeJobStatus.FAILED)

    def safe_public_dict(self) -> Dict[str, Any]:
        return self.summary()

class RuntimeState(BaseModel):
    last_run_id: Optional[str] = None
    last_started_at: Optional[datetime] = None
    last_finished_at: Optional[datetime] = None
    last_status: Optional[RuntimePipelineStatus] = None
    total_runs: int = 0
    success_runs: int = 0
    failed_runs: int = 0
    consecutive_failures: int = 0
    is_running: bool = False
    active_lock_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "last_status": self.last_status.value if self.last_status else None,
            "total_runs": self.total_runs,
            "is_running": self.is_running,
            "consecutive_failures": self.consecutive_failures
        }

class RuntimeScheduleConfig(BaseModel):
    enabled: bool = False
    interval_minutes: int = Field(default=60, gt=0)
    run_immediately: bool = False
    max_iterations: Optional[int] = Field(default=None, ge=0)
    sleep_seconds: int = Field(default=5, ge=0)
    session_policy: SessionPolicy = SessionPolicy.ONLY_DURING_SESSION
    stop_on_failure: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
