from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import datetime

class PerformanceStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    SLOW = "SLOW"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class ResourceKind(str, Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    RUNTIME = "RUNTIME"
    IO = "IO"
    CACHE = "CACHE"
    CUSTOM = "CUSTOM"

class CacheStatus(str, Enum):
    HIT = "HIT"
    MISS = "MISS"
    STALE = "STALE"
    INVALID = "INVALID"
    BYPASS = "BYPASS"
    DISABLED = "DISABLED"
    UNKNOWN = "UNKNOWN"

class BenchmarkScenario(str, Enum):
    BOOTSTRAP_VALIDATE = "BOOTSTRAP_VALIDATE"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    DATA_CATALOG_GATE = "DATA_CATALOG_GATE"
    FEATURE_COMPUTE = "FEATURE_COMPUTE"
    FEATURE_SERVE = "FEATURE_SERVE"
    MODEL_GOVERNANCE = "MODEL_GOVERNANCE"
    MONITORING_STATUS = "MONITORING_STATUS"
    LEADERBOARD_BUILD = "LEADERBOARD_BUILD"
    ORCHESTRATOR_DRY_RUN = "ORCHESTRATOR_DRY_RUN"
    REPORT_DAILY_DRY_RUN = "REPORT_DAILY_DRY_RUN"
    FINAL_AUDIT_GO_NO_GO = "FINAL_AUDIT_GO_NO_GO"
    CUSTOM = "CUSTOM"

class TimingMeasurement(BaseModel):
    timing_id: str
    name: str
    started_at: datetime.datetime
    finished_at: datetime.datetime | None = None
    elapsed_seconds: float | None = None
    status: PerformanceStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResourceMeasurement(BaseModel):
    measurement_id: str
    resource_kind: ResourceKind
    module_name: str
    command: str | None = None
    value: float | None = None
    unit: str
    threshold: float | None = None
    status: PerformanceStatus
    measured_at: datetime.datetime
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResourceBudget(BaseModel):
    budget_id: str
    module_name: str
    max_runtime_seconds: float | None = None
    max_memory_mb: float | None = None
    max_disk_mb: float | None = None
    max_rows: int | None = None
    max_cache_age_seconds: int | None = None
    status: PerformanceStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Resource budget is local software performance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CacheEntry(BaseModel):
    cache_id: str
    key: str
    namespace: str
    path: str
    created_at: datetime.datetime
    expires_at: datetime.datetime | None = None
    checksum: str | None = None
    status: CacheStatus
    size_bytes: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class CacheLookupResult(BaseModel):
    lookup_id: str
    key: str
    namespace: str
    status: CacheStatus
    entry: CacheEntry | None = None
    reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PerformanceProfile(BaseModel):
    profile_id: str
    created_at: datetime.datetime
    module_name: str
    command: str | None = None
    timings: list[TimingMeasurement] = Field(default_factory=list)
    resources: list[ResourceMeasurement] = Field(default_factory=list)
    cache_results: list[CacheLookupResult] = Field(default_factory=list)
    status: PerformanceStatus
    bottleneck_summary: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Performance profile is local software diagnostics output only. It is not investment advice or trading guidance. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BenchmarkResult(BaseModel):
    benchmark_id: str
    scenario: BenchmarkScenario
    created_at: datetime.datetime
    command: str | None = None
    elapsed_seconds: float | None = None
    memory_mb: float | None = None
    disk_mb: float | None = None
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    status: PerformanceStatus
    output_refs: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Benchmark result is local software performance metadata only. It does not indicate financial performance. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BottleneckFinding(BaseModel):
    finding_id: str
    module_name: str
    resource_kind: ResourceKind
    severity: str
    message: str
    evidence_refs: list[str] = Field(default_factory=list)
    suggested_action: str | None = None
    status: PerformanceStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PerformanceRegressionFinding(BaseModel):
    regression_id: str
    scenario: BenchmarkScenario
    baseline_value: float | None = None
    current_value: float | None = None
    delta_pct: float | None = None
    threshold_pct: float
    status: PerformanceStatus
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PerformanceReport(BaseModel):
    report_id: str
    generated_at: datetime.datetime
    profiles: list[PerformanceProfile] = Field(default_factory=list)
    benchmarks: list[BenchmarkResult] = Field(default_factory=list)
    bottlenecks: list[BottleneckFinding] = Field(default_factory=list)
    regressions: list[PerformanceRegressionFinding] = Field(default_factory=list)
    resource_budgets: list[ResourceBudget] = Field(default_factory=list)
    cache_entries: list[CacheEntry] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Performance report is local software optimization reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
