import sys
from pathlib import Path
from typing import Any
import importlib.metadata

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.models import DependencyCheckResult, DependencyStatus

class DependencyChecker:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def parse_requirements_file(self, path: Path) -> list[str]:
        if not path.exists():
            return []

        reqs = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Basic strip of inline comments
                    reqs.append(line.split('#')[0].strip())
        return reqs

    def check_package(self, requirement: str, optional: bool = False) -> DependencyCheckResult:
        # Simple parsing for package name, e.g., "pandas>=1.0.0" -> "pandas"
        import re
        match = re.match(r'^([a-zA-Z0-9_\-]+).*', requirement)
        if not match:
            return DependencyCheckResult(requirement, None, None, DependencyStatus.UNKNOWN, optional, "Invalid requirement format")

        pkg_name = match.group(1)

        try:
            installed_version = importlib.metadata.version(pkg_name)
            return DependencyCheckResult(
                package_name=pkg_name,
                required_version=requirement.replace(pkg_name, '').strip(),
                installed_version=installed_version,
                status=DependencyStatus.INSTALLED,
                optional=optional,
                message=f"{pkg_name} is installed ({installed_version})"
            )
        except importlib.metadata.PackageNotFoundError:
            status = DependencyStatus.OPTIONAL_MISSING if optional else DependencyStatus.MISSING
            return DependencyCheckResult(
                package_name=pkg_name,
                required_version=requirement.replace(pkg_name, '').strip(),
                installed_version=None,
                status=status,
                optional=optional,
                message=f"{pkg_name} is missing"
            )

    def check_requirements(self, path: Path, optional: bool = False) -> list[DependencyCheckResult]:
        reqs = self.parse_requirements_file(path)
        return [self.check_package(req, optional) for req in reqs]

    def check_core_dependencies(self) -> list[DependencyCheckResult]:
        return self.check_requirements(Path("requirements.txt"), optional=False)

    def check_dev_dependencies(self) -> list[DependencyCheckResult]:
        return self.check_requirements(Path("requirements-dev.txt"), optional=True)

    def check_ml_dependencies(self) -> list[DependencyCheckResult]:
        return self.check_requirements(Path("requirements-ml.txt"), optional=True)

    def check_optional_dependencies(self) -> list[DependencyCheckResult]:
        return self.check_requirements(Path("requirements-optional.txt"), optional=True)

    def dependency_summary(self, results: list[DependencyCheckResult]) -> dict[str, Any]:
        return {
            "total": len(results),
            "installed": len([r for r in results if r.status == DependencyStatus.INSTALLED]),
            "missing": len([r for r in results if r.status == DependencyStatus.MISSING]),
            "optional_missing": len([r for r in results if r.status == DependencyStatus.OPTIONAL_MISSING])
        }
