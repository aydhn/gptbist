from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

class PlatformType(Enum):
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()

class PythonEnvironmentType(Enum):
    VENV = auto()
    CONDA = auto()
    SYSTEM = auto()
    UNKNOWN = auto()

class DependencyStatus(Enum):
    INSTALLED = auto()
    MISSING = auto()
    VERSION_MISMATCH = auto()
    OPTIONAL_MISSING = auto()
    UNKNOWN = auto()

class EnvironmentCheckStatus(Enum):
    PASS = auto()
    WARN = auto()
    FAIL = auto()
    SKIP = auto()
    ERROR = auto()

class ReleaseBundleStatus(Enum):
    SUCCESS = auto()
    PARTIAL_SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()

class PackagingFormat(Enum):
    SOURCE = auto()
    ZIP = auto()
    MANIFEST_ONLY = auto()
    LOCAL_INSTALLER = auto()
    UNKNOWN = auto()

@dataclass
class DependencyCheckResult:
    package_name: str
    required_version: Optional[str]
    installed_version: Optional[str]
    status: DependencyStatus
    optional: bool
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class EnvironmentCheckResult:
    check_name: str
    status: EnvironmentCheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def summary(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status.name,
            "message": self.message,
            "recommendations": self.recommendations
        }

@dataclass
class EnvironmentDoctorReport:
    platform: PlatformType
    python_version: str
    python_executable: str
    environment_type: PythonEnvironmentType
    project_root: str
    checks: list[EnvironmentCheckResult]
    dependency_results: list[DependencyCheckResult]
    overall_status: EnvironmentCheckStatus
    warnings: list[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    disclaimer: str = "Environment doctor output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "platform": self.platform.name,
            "python_version": self.python_version,
            "environment_type": self.environment_type.name,
            "overall_status": self.overall_status.name,
            "checks_summary": [c.summary() for c in self.checks],
            "disclaimer": self.disclaimer
        }

@dataclass
class InstallerScriptSpec:
    platform: PlatformType
    script_name: str
    commands: list[str]
    requires_confirm: bool
    safe_to_run: bool
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReleaseManifest:
    release_id: str
    version: str
    created_at: datetime
    project_name: str
    python_requires: str
    included_files: list[str]
    excluded_patterns: list[str]
    dependency_files: list[str]
    cli_entrypoints: list[str]
    smoke_commands: list[list[str]]
    quality_summary: Optional[dict[str, Any]]
    security_summary: Optional[dict[str, Any]]
    environment_summary: Optional[dict[str, Any]]
    no_real_order_sent: bool = True
    disclaimer: str = "Release manifest output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "version": self.version,
            "project_name": self.project_name,
            "python_requires": self.python_requires,
            "disclaimer": self.disclaimer
        }

@dataclass
class ReleaseBundleResult:
    release_id: str
    status: ReleaseBundleStatus
    format: PackagingFormat
    manifest: ReleaseManifest
    output_files: dict[str, str]
    checks: list[EnvironmentCheckResult]
    issues: list[str]
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    disclaimer: str = "Release bundle output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "status": self.status.name,
            "format": self.format.name,
            "elapsed_seconds": self.elapsed_seconds,
            "output_files": self.output_files,
            "disclaimer": self.disclaimer
        }
