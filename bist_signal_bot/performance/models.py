import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class PerformanceStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class BenchmarkType(str, Enum):
    SCANNER = "SCANNER"
    FEATURE_BUILDER = "FEATURE_BUILDER"
    ML_INFERENCE = "ML_INFERENCE"
    BACKTEST = "BACKTEST"
    OPTIMIZATION = "OPTIMIZATION"
    RUNTIME_RUN_ONCE = "RUNTIME_RUN_ONCE"
    KNOWLEDGE_INDEX = "KNOWLEDGE_INDEX"
    DRIFT_CHECK = "DRIFT_CHECK"
    STRESS_TEST = "STRESS_TEST"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    RESEARCH_LAB_JOB = "RESEARCH_LAB_JOB"
    SCHEDULER_JOB = "SCHEDULER_JOB"
    REPORT_GENERATION = "REPORT_GENERATION"
    CUSTOM = "CUSTOM"

class ResourceMetricType(str, Enum):
    WALL_TIME_SECONDS = "WALL_TIME_SECONDS"
    CPU_TIME_SECONDS = "CPU_TIME_SECONDS"
    MEMORY_RSS_MB = "MEMORY_RSS_MB"
    MEMORY_PEAK_MB = "MEMORY_PEAK_MB"
    CPU_PERCENT = "CPU_PERCENT"
    GPU_MEMORY_MB = "GPU_MEMORY_MB"
    GPU_UTILIZATION_PERCENT = "GPU_UTILIZATION_PERCENT"
    DISK_READ_MB = "DISK_READ_MB"
    DISK_WRITE_MB = "DISK_WRITE_MB"
    ROWS_PROCESSED = "ROWS_PROCESSED"
    SYMBOLS_PROCESSED = "SYMBOLS_PROCESSED"
    CACHE_HIT_RATE = "CACHE_HIT_RATE"
    CUSTOM = "CUSTOM"

class PerformanceSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PerformanceMetric(BaseModel):
    metric_id: str
    metric_type: ResourceMetricType
    name: str
    value: float | int | str | None
    unit: str
    status: PerformanceStatus
    threshold_warn: float | None = None
    threshold_fail: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResourceSnapshot(BaseModel):
    snapshot_id: str
    captured_at: datetime.datetime
    cpu_percent: float | None = None
    memory_rss_mb: float | None = None
    memory_available_mb: float | None = None
    disk_free_mb: float | None = None
    gpu_available: bool = False
    gpu_name: str | None = None
    gpu_memory_used_mb: float | None = None
    gpu_memory_total_mb: float | None = None
    gpu_utilization_percent: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ProfileSpan(BaseModel):
    span_id: str
    name: str
    module: str | None = None
    started_at: datetime.datetime
    finished_at: datetime.datetime | None = None
    elapsed_seconds: float = 0.0
    cpu_time_seconds: float | None = None
    memory_before_mb: float | None = None
    memory_after_mb: float | None = None
    memory_delta_mb: float | None = None
    children: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ProfileResult(BaseModel):
    profile_id: str
    benchmark_type: BenchmarkType
    started_at: datetime.datetime
    finished_at: datetime.datetime | None = None
    elapsed_seconds: float = 0.0
    spans: list[ProfileSpan] = Field(default_factory=list)
    resource_snapshots: list[ResourceSnapshot] = Field(default_factory=list)
    metrics: list[PerformanceMetric] = Field(default_factory=list)
    status: PerformanceStatus = PerformanceStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Performance profile is operational only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "benchmark_type": self.benchmark_type.value,
            "elapsed_seconds": self.elapsed_seconds,
            "status": self.status.value,
            "span_count": len(self.spans),
            "disclaimer": self.disclaimer
        }

class BenchmarkRequest(BaseModel):
    benchmark_type: BenchmarkType
    symbols: list[str] = Field(default_factory=list)
    strategy_name: str | None = None
    sample_size: int = Field(default=20, gt=0)
    iterations: int = Field(default=3, gt=0)
    warmup_iterations: int = Field(default=1, ge=0)
    use_synthetic_data: bool = True
    heavy: bool = False
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class BenchmarkRunResult(BaseModel):
    benchmark_id: str
    request: BenchmarkRequest
    status: PerformanceStatus
    profiles: list[ProfileResult] = Field(default_factory=list)
    aggregate_metrics: list[PerformanceMetric] = Field(default_factory=list)
    median_elapsed_seconds: float | None = None
    p95_elapsed_seconds: float | None = None
    max_memory_peak_mb: float | None = None
    throughput_items_per_second: float | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    output_files: dict[str, str] = Field(default_factory=dict)
    disclaimer: str = "Benchmark result is operational only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_type": self.request.benchmark_type.value,
            "status": self.status.value,
            "median_elapsed_seconds": self.median_elapsed_seconds,
            "max_memory_peak_mb": self.max_memory_peak_mb,
            "throughput_items_per_second": self.throughput_items_per_second,
            "disclaimer": self.disclaimer
        }

class PerformanceBaseline(BaseModel):
    baseline_id: str
    created_at: datetime.datetime
    benchmark_type: BenchmarkType
    environment_hash: str
    metrics: dict[str, float] = Field(default_factory=dict)
    sample_size: int = Field(default=20, gt=0)
    iterations: int = Field(default=3, gt=0)
    app_version: str = "1.0.0"
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class PerformanceRegressionResult(BaseModel):
    regression_id: str
    benchmark_id: str
    baseline_id: str
    status: PerformanceStatus
    metric_changes_pct: dict[str, float] = Field(default_factory=dict)
    regressions: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Performance regression result is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BottleneckFinding(BaseModel):
    finding_id: str
    name: str
    benchmark_type: BenchmarkType
    severity: PerformanceSeverity
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PerformanceRecommendation(BaseModel):
    recommendation_id: str
    title: str
    severity: PerformanceSeverity
    module: str | None = None
    action: str
    expected_impact: str | None = None
    risk: str | None = None
    requires_code_change: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
