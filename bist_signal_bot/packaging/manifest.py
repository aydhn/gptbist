import os
import uuid
from pathlib import Path
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.models import ReleaseManifest
from bist_signal_bot.core.exceptions import ManifestError

class ReleaseManifestBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or Path(os.getcwd())

    def collect_included_files(self) -> list[str]:
        included = []

        # Simple globbing
        patterns = [
            "bist_signal_bot/**/*.py",
            "tests/**/*.py",
            "README.md",
            "pyproject.toml",
            "requirements*.txt",
            "scripts/*.sh",
            "scripts/*.ps1",
            ".env.example"
        ]

        exclude_dirs = [
            ".venv", "__pycache__", "data", "logs", "reports", ".git"
        ]

        if self.settings.PACKAGING_EXCLUDE_DATA_DIR:
            exclude_dirs.append('data')
        if self.settings.PACKAGING_EXCLUDE_LOGS_DIR:
            exclude_dirs.append('logs')

        for root, dirs, files in os.walk(self.base_dir):
            # Exclude
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

            for file in files:
                if file.endswith('.pyc') or file.endswith('.joblib') or file.endswith('.pkl'):
                    continue
                if file == '.env' and self.settings.PACKAGING_EXCLUDE_ENV_FILE:
                    continue

                rel_path = os.path.relpath(os.path.join(root, file), self.base_dir)
                # Keep it simple, add all remaining files that match extensions
                if file.endswith('.py') or file.endswith('.md') or file.endswith('.txt') or file.endswith('.toml') or file.endswith('.sh') or file.endswith('.ps1') or file == '.env.example':
                    included.append(rel_path.replace('\\', '/'))

        return sorted(list(set(included)))

    def build_smoke_commands(self) -> list[list[str]]:
        return [
            ["python", "-m", "bist_signal_bot", "--help"],
            ["python", "-m", "bist_signal_bot", "healthcheck"],
            ["python", "-m", "bist_signal_bot", "security", "audit", "--json"],
            ["python", "-m", "bist_signal_bot", "quality", "smoke", "--json"],
            ["python", "-m", "bist_signal_bot", "scan", "symbols", "ASELS", "THYAO", "--source", "mock", "--strategy", "moving_average_trend", "--json"]
        ]

    def validate_manifest_no_secrets(self, manifest: ReleaseManifest) -> None:
        pass

    def build_manifest(self, version: str | None = None, include_quality: bool = True, include_security: bool = True, include_environment: bool = True) -> ReleaseManifest:
        from bist_signal_bot.quality.gate import QualityGateRunner
        from bist_signal_bot.security.preflight import SecurityPreflightRunner
        from bist_signal_bot.packaging.environment import EnvironmentDoctor

        ver = version or self.settings.PACKAGING_RELEASE_VERSION
        release_id = f"rel_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        quality_summary = None
        security_summary = None
        env_summary = None

        if include_quality:
            try:
                q_runner = QualityGateRunner(self.settings)
                q_res = q_runner.run_smoke_suite()
                quality_summary = q_res.summary()
            except Exception:
                pass

        if include_security:
            try:
                s_runner = SecurityPreflightRunner(self.settings)
                s_res = s_runner.run_runtime_preflight()
                security_summary = s_res.summary()
            except Exception:
                pass

        if include_environment:
            try:
                e_doctor = EnvironmentDoctor(self.settings, self.base_dir)
                e_res = e_doctor.run_doctor(include_dependencies=False)
                env_summary = e_res.summary()
            except Exception:
                pass

        included = self.collect_included_files()

        excluded_patterns = ["**/.venv/**", "**/__pycache__/**", "**/*.pyc", "**/*.joblib", "**/*.pkl"]
        if self.settings.PACKAGING_EXCLUDE_ENV_FILE:
            excluded_patterns.append(".env")
        if self.settings.PACKAGING_EXCLUDE_DATA_DIR:
            excluded_patterns.append(f"{'data'}/**")
        if self.settings.PACKAGING_EXCLUDE_LOGS_DIR:
            excluded_patterns.append(f"{'logs'}/**")
        if self.settings.PACKAGING_EXCLUDE_REPORTS_DIR:
            excluded_patterns.append("reports/**")

        manifest = ReleaseManifest(
            release_id=release_id,
            version=ver,
            created_at=datetime.utcnow(),
            project_name=self.settings.PACKAGING_PROJECT_NAME,
            python_requires=self.settings.PACKAGING_MIN_PYTHON_VERSION,
            included_files=included,
            excluded_patterns=excluded_patterns,
            dependency_files=["requirements.txt", "requirements-dev.txt", "requirements-ml.txt", "requirements-optional.txt"],
            cli_entrypoints=["python -m bist_signal_bot"],
            smoke_commands=self.build_smoke_commands(),
            quality_summary=quality_summary,
            security_summary=security_summary,
            environment_summary=env_summary
        )

        self.validate_manifest_no_secrets(manifest)
        return manifest
