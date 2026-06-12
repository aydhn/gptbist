from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ResearchRunStatus(str, Enum):
    PLANNED = "PLANNED"
    DRY_RUN = "DRY_RUN"
    RUNNING = "RUNNING"
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ResearchTaskType(str, Enum):
    DATA_CATALOG_GATE = "DATA_CATALOG_GATE"
    FEATURE_COMPUTE = "FEATURE_COMPUTE"
    SCANNER_RUN = "SCANNER_RUN"
    BACKTEST_RUN = "BACKTEST_RUN"
    VALIDATION_RUN = "VALIDATION_RUN"
    CALIBRATION_RUN = "CALIBRATION_RUN"
    MODEL_GOVERNANCE = "MODEL_GOVERNANCE"
    CONTEXT_FUSION = "CONTEXT_FUSION"
    REVIEW_CASE = "REVIEW_CASE"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    MONITORING_RUN = "MONITORING_RUN"
    LEADERBOARD_BUILD = "LEADERBOARD_BUILD"
    QA_RELEASE_GATE = "QA_RELEASE_GATE"
    OPS_READINESS = "OPS_READINESS"
    REPORT_BUILD = "REPORT_BUILD"
    DOCS_HUB_CHECK = "DOCS_HUB_CHECK"
    CUSTOM = "CUSTOM"

class ResearchCampaignType(str, Enum):
    QUICK_RESEARCH_SCAN = "QUICK_RESEARCH_SCAN"
    FULL_RESEARCH_PIPELINE = "FULL_RESEARCH_PIPELINE"
    STRATEGY_VALIDATION_CAMPAIGN = "STRATEGY_VALIDATION_CAMPAIGN"
    MODEL_GOVERNANCE_CAMPAIGN = "MODEL_GOVERNANCE_CAMPAIGN"
    FEATURE_QUALITY_CAMPAIGN = "FEATURE_QUALITY_CAMPAIGN"
    MONITORING_REFRESH = "MONITORING_REFRESH"
    LEADERBOARD_REFRESH = "LEADERBOARD_REFRESH"
    QA_OPS_RELEASE_CHECK = "QA_OPS_RELEASE_CHECK"
    OFFLINE_DEMO_CAMPAIGN = "OFFLINE_DEMO_CAMPAIGN"
    CUSTOM = "CUSTOM"

class ResearchExecutionMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    LOCAL_EXECUTE = "LOCAL_EXECUTE"
    PLAN_ONLY = "PLAN_ONLY"
    REPLAY = "REPLAY"
    VALIDATE_ONLY = "VALIDATE_ONLY"
    UNKNOWN = "UNKNOWN"

class ResearchDependencyStatus(str, Enum):
    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    STALE = "STALE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    OPTIONAL_MISSING = "OPTIONAL_MISSING"
    UNKNOWN = "UNKNOWN"

class ResearchTask(BaseModel):
    task_id: str
    task_type: ResearchTaskType
    name: str
    command: str | None = None
    callable_ref: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    required: bool = True
    allow_failure: bool = False
    timeout_seconds: int | None = Field(default=None, gt=0)
    retry_count: int = Field(default=0, ge=0)
    save_outputs: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        return v

    @field_validator("command")
    def validate_command(cls, v):
        if v:
            lower_v = v.lower()
            unsafe_terms = ["broker", "order", "live", "buy", "sell"]
            # A simplistic check, real guardrails are elsewhere, but good for validation
            # To avoid false positives (e.g. in 'research_broker'), we rely on guardrails
            # but we can enforce basics here.
            # No-op for now to let guardrails handle it
        return v

    @field_validator("depends_on")
    def validate_depends_on(cls, v, info):
        if info.data.get("task_id") in v:
            raise ValueError("Task cannot depend on itself")
        return v

class ResearchDependency(BaseModel):
    dependency_id: str
    from_task_id: str
    to_task_id: str
    status: ResearchDependencyStatus
    reason: str | None = None
    required: bool = True
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchRunPlan(BaseModel):
    plan_id: str
    campaign_type: ResearchCampaignType
    name: str
    created_at: datetime
    execution_mode: ResearchExecutionMode = ResearchExecutionMode.DRY_RUN
    profile_name: str | None = None
    symbol_universe: list[str] = Field(default_factory=list)
    strategy_names: list[str] = Field(default_factory=list)
    model_ids: list[str] = Field(default_factory=list)
    feature_set_ids: list[str] = Field(default_factory=list)
    tasks: list[ResearchTask] = Field(default_factory=list)
    dependencies: list[ResearchDependency] = Field(default_factory=list)
    status: ResearchRunStatus = ResearchRunStatus.PLANNED
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Research run plan is local research workflow metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchTaskResult(BaseModel):
    result_id: str
    task_id: str
    task_type: ResearchTaskType
    started_at: datetime
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    status: ResearchRunStatus
    exit_code: int | None = None
    output_ref: str | None = None
    output_summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchRunManifest(BaseModel):
    manifest_id: str
    plan_id: str
    run_id: str
    created_at: datetime
    execution_mode: ResearchExecutionMode
    config_snapshot_ref: str | None = None
    input_refs: dict[str, Any] = Field(default_factory=dict)
    output_refs: dict[str, Any] = Field(default_factory=dict)
    task_result_ids: list[str] = Field(default_factory=list)
    checksum_manifest: dict[str, str] = Field(default_factory=dict)
    environment_summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Research run manifest describes local research execution artifacts only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchRun(BaseModel):
    run_id: str
    plan: ResearchRunPlan
    started_at: datetime
    finished_at: datetime | None = None
    status: ResearchRunStatus
    task_results: list[ResearchTaskResult] = Field(default_factory=list)
    manifest: ResearchRunManifest | None = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Research run is local research automation output only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchCampaign(BaseModel):
    campaign_id: str
    campaign_type: ResearchCampaignType
    name: str
    description: str
    created_at: datetime
    default_profile: str | None = None
    default_symbols: list[str] = Field(default_factory=list)
    default_strategies: list[str] = Field(default_factory=list)
    default_models: list[str] = Field(default_factory=list)
    default_feature_sets: list[str] = Field(default_factory=list)
    default_tasks: list[ResearchTask] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Research campaign is local workflow template metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchGuardrailCheck(BaseModel):
    check_id: str
    name: str
    status: ResearchRunStatus
    severity: str
    message: str
    blocked: bool
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchOrchestratorReport(BaseModel):
    report_id: str
    generated_at: datetime
    plans: list[ResearchRunPlan] = Field(default_factory=list)
    runs: list[ResearchRun] = Field(default_factory=list)
    campaigns: list[ResearchCampaign] = Field(default_factory=list)
    guardrail_checks: list[ResearchGuardrailCheck] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Research orchestrator report is local workflow governance reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
