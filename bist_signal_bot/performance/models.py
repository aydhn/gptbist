from datetime import datetime
from enum import Enum
from typing import Any
from dataclasses import dataclass, field
from pydantic import BaseModel, ConfigDict, Field

class PerformanceStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ResourceLevel(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class WorkloadType(str, Enum):
    DATA_REFRESH = "DATA_REFRESH"
    SCANNER = "SCANNER"
    BACKTEST = "BACKTEST"
    OPTIMIZATION = "OPTIMIZATION"
    ML_DATASET = "ML_DATASET"
    ML_TRAINING = "ML_TRAINING"
    REGIME = "REGIME"
    RUNTIME = "RUNTIME"
    QUALITY = "QUALITY"
    CUSTOM = "CUSTOM"

class ConcurrencyMode(str, Enum):
    SERIAL = "SERIAL"
    THREADS = "THREADS"
    PROCESSES = "PROCESSES"
    AUTO = "AUTO"

class CachePolicy(str, Enum):
    KEEP_ALL = "KEEP_ALL"
    CLEAN_OLD = "CLEAN_OLD"
    CLEAN_LARGE = "CLEAN_LARGE"
    CLEAN_TEMP_ONLY = "CLEAN_TEMP_ONLY"
    DRY_RUN_ONLY = "DRY_RUN_ONLY"

@dataclass
class PerformanceMetric:
    metric_name: str
    value: float | int | str | bool | None
    unit: str | None = None
    status: PerformanceStatus = PerformanceStatus.UNKNOWN
    threshold: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceSnapshot:
    timestamp: datetime
    cpu_count: int | None = None
    cpu_percent: float | None = None
    memory_total_mb: float | None = None
    memory_used_mb: float | None = None
    memory_available_mb: float | None = None
    memory_percent: float | None = None
    disk_total_mb: float | None = None
    disk_used_mb: float | None = None
    disk_free_mb: float | None = None
    disk_percent: float | None = None
    gpu_detected: bool = False
    gpu_name: str | None = None
    gpu_memory_total_mb: float | None = None
    gpu_memory_used_mb: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "gpu_detected": self.gpu_detected
        }

@dataclass
class TimerResult:
    name: str
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProfiledFunctionResult:
    name: str
    status: PerformanceStatus
    elapsed_seconds: float
    top_functions: list[dict[str, Any]] = field(default_factory=list)
    stdout_tail: str | None = None
    issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

class WorkloadProfileRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    workload_type: WorkloadType
    symbols: list[str] = Field(default_factory=list)
    source: str = "mock"
    strategy_name: str | None = None
    rows: int | None = None
    iterations: int = Field(default=1, gt=0)
    use_risk: bool = False
    use_ml: bool = False
    use_regime: bool = False
    concurrency_mode: ConcurrencyMode = ConcurrencyMode.SERIAL
    max_workers: int = Field(default=1, gt=0)
    save_report: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

@dataclass
class WorkloadProfileResult:
    request: WorkloadProfileRequest
    status: PerformanceStatus
    timer_results: list[TimerResult] = field(default_factory=list)
    function_profiles: list[ProfiledFunctionResult] = field(default_factory=list)
    resource_before: ResourceSnapshot | None = None
    resource_after: ResourceSnapshot | None = None
    metrics: list[PerformanceMetric] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    output_files: dict[str, str] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime = field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Performance profiling output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "workload_type": self.request.workload_type.value,
            "status": self.status.value,
            "elapsed_seconds": self.elapsed_seconds,
            "recommendations_count": len(self.recommendations)
        }

@dataclass
class CacheEntryInfo:
    path: str
    size_mb: float
    modified_at: datetime | None
    age_days: float | None
    category: str
    safe_to_delete: bool
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CacheReport:
    total_size_mb: float = 0.0
    entry_count: int = 0
    safe_delete_size_mb: float = 0.0
    safe_delete_count: int = 0
    entries: list[CacheEntryInfo] = field(default_factory=list)
    policy: CachePolicy = CachePolicy.DRY_RUN_ONLY
    dry_run: bool = True
    deleted_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    disclaimer: str = "Cache report output only. Operational file maintenance only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchTuningRecommendation:
    workload_type: WorkloadType
    recommended_batch_size: int
    recommended_max_workers: int
    recommended_concurrency_mode: ConcurrencyMode
    reason: str
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceBenchmarkResult:
    benchmark_id: str
    workload_type: WorkloadType
    status: PerformanceStatus
    iterations: int
    average_seconds: float
    median_seconds: float
    min_seconds: float
    max_seconds: float
    throughput_per_second: float | None = None
    metrics: list[PerformanceMetric] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    disclaimer: str = "Performance profiling output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)
