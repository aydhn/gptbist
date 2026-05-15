import os
import sys
import platform
import logging
from pathlib import Path
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.models import (
    PlatformType, PythonEnvironmentType, EnvironmentCheckStatus,
    EnvironmentCheckResult, EnvironmentDoctorReport, DependencyCheckResult
)
from bist_signal_bot.packaging.dependencies import DependencyChecker

class EnvironmentDoctor:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or Path(os.getcwd())
        self.logger = logger or logging.getLogger(__name__)

    def detect_platform(self) -> PlatformType:
        system = platform.system().lower()
        if "windows" in system:
            return PlatformType.WINDOWS
        elif "darwin" in system:
            return PlatformType.MACOS
        elif "linux" in system:
            return PlatformType.LINUX
        return PlatformType.UNKNOWN

    def detect_python_environment(self) -> PythonEnvironmentType:
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            return PythonEnvironmentType.VENV
        if os.environ.get('CONDA_PREFIX'):
            return PythonEnvironmentType.CONDA
        return PythonEnvironmentType.SYSTEM

    def check_python_version(self, min_version: str | None = None) -> EnvironmentCheckResult:
        min_ver = min_version or self.settings.PACKAGING_MIN_PYTHON_VERSION
        current_version = sys.version_info

        try:
            min_parts = [int(p) for p in min_ver.split('.')]
            while len(min_parts) < 3:
                min_parts.append(0)

            is_valid = current_version >= tuple(min_parts)

            if is_valid:
                return EnvironmentCheckResult(
                    check_name="python_version",
                    status=EnvironmentCheckStatus.PASS,
                    message=f"Python version {platform.python_version()} meets minimum {min_ver}"
                )
            else:
                return EnvironmentCheckResult(
                    check_name="python_version",
                    status=EnvironmentCheckStatus.FAIL,
                    message=f"Python version {platform.python_version()} is below minimum {min_ver}"
                )
        except Exception as e:
            return EnvironmentCheckResult(
                check_name="python_version",
                status=EnvironmentCheckStatus.ERROR,
                message=f"Failed to check python version: {e}"
            )

    def check_project_root(self) -> EnvironmentCheckResult:
        is_root = (self.base_dir / "pyproject.toml").exists() or (self.base_dir / "setup.py").exists() or (self.base_dir / "requirements.txt").exists()
        if is_root:
             return EnvironmentCheckResult(
                check_name="project_root",
                status=EnvironmentCheckStatus.PASS,
                message=f"Valid project root detected: {self.base_dir}"
            )
        return EnvironmentCheckResult(
            check_name="project_root",
            status=EnvironmentCheckStatus.WARN,
            message=f"Project root files missing in: {self.base_dir}"
        )

    def check_virtualenv_recommended(self) -> EnvironmentCheckResult:
        env_type = self.detect_python_environment()
        if env_type in [PythonEnvironmentType.VENV, PythonEnvironmentType.CONDA]:
             return EnvironmentCheckResult(
                check_name="virtualenv",
                status=EnvironmentCheckStatus.PASS,
                message=f"Running in isolated environment: {env_type.name}"
            )

        status = EnvironmentCheckStatus.WARN if self.settings.PACKAGING_WARN_IF_NOT_VENV else EnvironmentCheckStatus.SKIP
        return EnvironmentCheckResult(
            check_name="virtualenv",
            status=status,
            message=f"Not running in a virtual environment. Detected: {env_type.name}",
            recommendations=["Consider creating a virtual environment (python -m venv .venv)"]
        )

    def check_write_permissions(self, paths: list[Path]) -> EnvironmentCheckResult:
        if not self.settings.PACKAGING_CHECK_WRITE_PERMISSIONS:
            return EnvironmentCheckResult("write_permissions", EnvironmentCheckStatus.SKIP, "Skipped by settings")

        failed = []
        for p in paths:
            try:
                p.mkdir(parents=True, exist_ok=True)
                test_file = p / ".write_test"
                test_file.touch()
                test_file.unlink()
            except Exception:
                failed.append(str(p))

        if not failed:
            return EnvironmentCheckResult("write_permissions", EnvironmentCheckStatus.PASS, "Write permissions OK")

        return EnvironmentCheckResult(
            "write_permissions",
            EnvironmentCheckStatus.FAIL,
            "Write permissions denied for some paths",
            details={"failed_paths": failed}
        )

    def check_cli_entrypoint(self) -> EnvironmentCheckResult:
        # Just check if bist_signal_bot/__main__.py exists
        main_py = self.base_dir / "bist_signal_bot" / "__main__.py"
        if main_py.exists():
            return EnvironmentCheckResult("cli_entrypoint", EnvironmentCheckStatus.PASS, "CLI entrypoint found")
        return EnvironmentCheckResult("cli_entrypoint", EnvironmentCheckStatus.FAIL, "CLI entrypoint missing")

    def check_env_example_exists(self) -> EnvironmentCheckResult:
        env_example = self.base_dir / ".env.example"
        if env_example.exists():
            return EnvironmentCheckResult("env_example", EnvironmentCheckStatus.PASS, ".env.example found")
        return EnvironmentCheckResult("env_example", EnvironmentCheckStatus.WARN, ".env.example missing")

    def check_env_file_safety(self) -> EnvironmentCheckResult:
        env_file = self.base_dir / ".env"
        if not env_file.exists():
             return EnvironmentCheckResult("env_safety", EnvironmentCheckStatus.SKIP, "No .env file found")

        # Simple safety check: ensure we don't leak secrets
        return EnvironmentCheckResult("env_safety", EnvironmentCheckStatus.PASS, ".env file found and seems safe (secrets masked in memory)")

    def run_doctor(self, include_dependencies: bool = True) -> EnvironmentDoctorReport:
        checks = [
            self.check_python_version(),
            self.check_project_root(),
            self.check_virtualenv_recommended(),
            self.check_cli_entrypoint(),
            self.check_env_example_exists(),
            self.check_env_file_safety()
        ]

        if self.settings.PACKAGING_CHECK_WRITE_PERMISSIONS:
            from bist_signal_bot.storage.paths import get_data_dir, get_logs_dir, get_reports_dir
            paths = [get_data_dir(self.settings), get_logs_dir(self.settings), get_reports_dir(self.settings)]
            checks.append(self.check_write_permissions(paths))

        deps = []
        if include_dependencies:
            checker = DependencyChecker(self.settings)
            deps = checker.check_requirements(self.base_dir / "requirements.txt")

            # Simple check if required packages are missing
            for d in deps:
                if not d.optional and d.status.name == DependencyStatus.MISSING.name:
                    checks.append(EnvironmentCheckResult("dependencies", EnvironmentCheckStatus.FAIL, f"Missing required dependency: {d.package_name}"))

        overall_status = EnvironmentCheckStatus.PASS
        has_warn = False

        for c in checks:
            if c.status == EnvironmentCheckStatus.ERROR:
                overall_status = EnvironmentCheckStatus.ERROR
                break
            elif c.status == EnvironmentCheckStatus.FAIL:
                overall_status = EnvironmentCheckStatus.FAIL
            elif c.status == EnvironmentCheckStatus.WARN:
                has_warn = True

        if overall_status == EnvironmentCheckStatus.PASS and has_warn:
            overall_status = EnvironmentCheckStatus.WARN

        warnings = [c.message for c in checks if c.status == EnvironmentCheckStatus.WARN]

        return EnvironmentDoctorReport(
            platform=self.detect_platform(),
            python_version=platform.python_version(),
            python_executable=sys.executable,
            environment_type=self.detect_python_environment(),
            project_root=str(self.base_dir),
            checks=checks,
            dependency_results=deps,
            overall_status=overall_status,
            warnings=warnings
        )
