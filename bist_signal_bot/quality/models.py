from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class QualityCheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

class QualityGateLevel(str, Enum):
    RELAXED = "RELAXED"
    STANDARD = "STANDARD"
    STRICT = "STRICT"
    RELEASE = "RELEASE"

class QualityTool(str, Enum):
    PYTEST = "PYTEST"
    COVERAGE = "COVERAGE"
    RUFF = "RUFF"
    BLACK = "BLACK"
    MYPY = "MYPY"
    IMPORT_CHECK = "IMPORT_CHECK"
    SECURITY_GUARD = "SECURITY_GUARD"
    REGRESSION_SMOKE = "REGRESSION_SMOKE"
    CUSTOM = "CUSTOM"

class QualitySuite(str, Enum):
    ALL = "ALL"
    SMOKE = "SMOKE"
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    SECURITY = "SECURITY"
    RUNTIME = "RUNTIME"
    SCANNER = "SCANNER"
    BACKTEST = "BACKTEST"
    ML = "ML"
    PAPER = "PAPER"
    FAST = "FAST"

class QualityCheckResult(BaseModel):
    check_name: str
    tool: QualityTool
    status: QualityCheckStatus
    message: str = ""
    elapsed_seconds: float = 0.0
    command: list[str] = Field(default_factory=list)
    exit_code: Optional[int] = None
    stdout_tail: Optional[str] = None
    stderr_tail: Optional[str] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "tool": self.tool.value,
            "status": self.status.value,
            "message": self.message,
            "elapsed_seconds": self.elapsed_seconds,
            "exit_code": self.exit_code,
            "issues_count": len(self.issues)
        }

class TestRunSummary(BaseModel):
    total_tests: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None
    errors: Optional[int] = None
    duration_seconds: float = 0.0
    raw_output_tail: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class CoverageSummary(BaseModel):
    enabled: bool = False
    measured: bool = False
    total_coverage_pct: Optional[float] = None
    threshold_pct: float = 0.0
    passed_threshold: Optional[bool] = None
    report_path: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class StaticAnalysisSummary(BaseModel):
    ruff_status: QualityCheckStatus = QualityCheckStatus.SKIP
    black_status: QualityCheckStatus = QualityCheckStatus.SKIP
    mypy_status: QualityCheckStatus = QualityCheckStatus.SKIP
    issue_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

class RegressionSmokeCommand(BaseModel):
    name: str = Field(min_length=1)
    command: list[str] = Field(min_length=1)
    timeout_seconds: int = Field(gt=0)
    expected_exit_code: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class QualityRunConfig(BaseModel):
    suite: QualitySuite = QualitySuite.FAST
    gate_level: QualityGateLevel = QualityGateLevel.STANDARD
    run_tests: bool = True
    run_coverage: bool = False
    run_static: bool = True
    run_type_check: bool = False
    run_import_checks: bool = True
    run_security_checks: bool = True
    run_regression_smoke: bool = False
    fail_on_warning: bool = False
    coverage_threshold_pct: float = Field(default=60.0, ge=0.0, le=100.0)
    timeout_seconds: int = Field(default=300, gt=0)
    save_report: bool = True
    formats: list[str] = Field(default_factory=lambda: ["json", "markdown", "csv"])
    metadata: dict[str, Any] = Field(default_factory=dict)

class QualityRunResult(BaseModel):
    run_id: str
    config: QualityRunConfig
    status: QualityCheckStatus
    checks: list[QualityCheckResult] = Field(default_factory=list)
    test_summary: Optional[TestRunSummary] = None
    coverage_summary: Optional[CoverageSummary] = None
    static_summary: Optional[StaticAnalysisSummary] = None
    regression_commands: list[RegressionSmokeCommand] = Field(default_factory=list)
    output_files: dict[str, str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Quality gate output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "gate_level": self.config.gate_level.value,
            "suite": self.config.suite.value,
            "checks_total": len(self.checks),
            "checks_passed": len([c for c in self.checks if c.status == QualityCheckStatus.PASS]),
            "checks_warn": len([c for c in self.checks if c.status == QualityCheckStatus.WARN]),
            "checks_failed": len([c for c in self.checks if c.status in [QualityCheckStatus.FAIL, QualityCheckStatus.ERROR]]),
            "checks_skipped": len([c for c in self.checks if c.status == QualityCheckStatus.SKIP]),
            "elapsed_seconds": self.elapsed_seconds,
            "output_files": self.output_files
        }

    def failed_checks(self) -> list[QualityCheckResult]:
        return [c for c in self.checks if c.status in [QualityCheckStatus.FAIL, QualityCheckStatus.ERROR]]

    def passed(self) -> bool:
        return self.status in [QualityCheckStatus.PASS, QualityCheckStatus.WARN]
