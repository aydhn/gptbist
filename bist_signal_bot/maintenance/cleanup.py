import time
from pathlib import Path
from datetime import datetime, timezone
from bist_signal_bot.maintenance.models import (
    CleanupCandidate,
    CleanupResult,
    MaintenanceStatus,
    RetentionPolicy,
    RetentionTarget
)
from bist_signal_bot.maintenance.retention import RetentionPolicyManager
from bist_signal_bot.maintenance.manifest import BackupManifestBuilder
from bist_signal_bot.core.exceptions import CleanupError
from bist_signal_bot.config.settings import get_settings

class CleanupManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.settings = get_settings()

    def is_safe_to_delete(self, path: Path, target: RetentionTarget) -> tuple[bool, list[str]]:
        warnings = []
        is_safe = True

        is_excluded, reason = BackupManifestBuilder.should_exclude(path)
        if is_excluded:
             is_safe = False
             warnings.append(f"Not safe to delete: matching exclude/secret rules ({reason})")

        if target == RetentionTarget.RESEARCH_LEDGER and not getattr(self.settings, "CLEANUP_DELETE_RESEARCH_LEDGER_DEFAULT", False):
             is_safe = False
             warnings.append("Not safe: Research ledger deletion is disabled by default")

        if target == RetentionTarget.MARKET_DATA and not getattr(self.settings, "CLEANUP_DELETE_MARKET_DATA_DEFAULT", False):
             is_safe = False
             warnings.append("Not safe: Market data deletion is disabled by default")

        if '.lock' in path.name:
             is_safe = False
             warnings.append("Not safe: Appears to be a lock file")

        return is_safe, warnings

    def _get_files_for_target(self, target: RetentionTarget) -> list[Path]:
        # MVP basic directory mapping
        mapping = {
            RetentionTarget.LOGS: self.base_dir / "logs",
            RetentionTarget.REPORTS: self.base_dir / "reports",
            RetentionTarget.SCENARIOS: self.base_dir / "scenarios",
            RetentionTarget.STRESS_RESULTS: self.base_dir / "stress",
            RetentionTarget.DRIFT_RESULTS: self.base_dir / "drift",
            RetentionTarget.RESEARCH_LAB_RUNS: self.base_dir / "research_lab",
            RetentionTarget.TEMP: self.base_dir / "temp",
            RetentionTarget.SIGNALS: self.base_dir / "signals",
            RetentionTarget.CACHE: self.base_dir / "cache",
            RetentionTarget.RELEASE_RUNS: self.base_dir / "release",
            RetentionTarget.RESEARCH_LEDGER: self.base_dir / "research_ledger",
            RetentionTarget.MARKET_DATA: self.base_dir / "market_data",
            RetentionTarget.MODEL_ARTIFACTS: self.base_dir / "models",
        }

        dir_path = mapping.get(target)
        if not dir_path or not dir_path.exists():
            return []

        files = []
        for p in dir_path.rglob('*'):
             if p.is_file():
                  files.append(p)
        return files

    def find_candidates(self, policy: RetentionPolicy) -> list[CleanupCandidate]:
        if not policy.enabled:
            return []

        candidates = []
        now = datetime.now(timezone.utc).timestamp()

        files = self._get_files_for_target(policy.target)
        # Sort files by modification time (newest first)
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for i, file_path in enumerate(files):
            stat = file_path.stat()
            age_days = (now - stat.st_mtime) / (24 * 3600)

            # Keep minimum count regardless of age
            if i < policy.keep_min_count:
                continue

            if age_days > policy.keep_days:
                rel_path = str(file_path.relative_to(self.base_dir))
                is_safe, warnings = self.is_safe_to_delete(file_path, policy.target)

                candidates.append(CleanupCandidate(
                    relative_path=rel_path,
                    target=policy.target,
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                    reason=f"Exceeds age limit ({age_days:.1f} > {policy.keep_days} days)",
                    safe_to_delete=is_safe,
                    warnings=warnings
                ))

        return candidates

    def analyze(self, policies: list[RetentionPolicy] | None = None, targets: list[RetentionTarget] | None = None) -> CleanupResult:
        start_time = time.time()
        candidates = []
        policies = policies or RetentionPolicyManager.default_policies()

        if targets:
            policies = [p for p in policies if p.target in targets]

        for policy in policies:
            candidates.extend(self.find_candidates(policy))

        return CleanupResult(
            cleanup_id=f"cln_{int(time.time())}",
            status=MaintenanceStatus.SUCCESS,
            dry_run=True,
            candidates=candidates,
            elapsed_seconds=time.time() - start_time
        )

    def apply_cleanup(self, result: CleanupResult, confirm: bool = False) -> CleanupResult:
        if not confirm:
            raise CleanupError("Cleanup is destructive. 'confirm' must be True to proceed.")

        start_time = time.time()
        deleted = 0
        freed = 0
        errors = []
        warnings = []

        for candidate in result.candidates:
            if not candidate.safe_to_delete:
                warnings.append(f"Skipped unsafe candidate: {candidate.relative_path}")
                continue

            file_path = self.base_dir / candidate.relative_path
            if not file_path.exists():
                warnings.append(f"File already gone: {candidate.relative_path}")
                continue

            try:
                file_path.unlink()
                deleted += 1
                freed += candidate.size_bytes
            except Exception as e:
                errors.append(f"Failed to delete {candidate.relative_path}: {e}")

        status = MaintenanceStatus.SUCCESS
        if errors:
            status = MaintenanceStatus.PARTIAL_SUCCESS if deleted > 0 else MaintenanceStatus.FAILED

        return CleanupResult(
            cleanup_id=result.cleanup_id,
            status=status,
            dry_run=False,
            candidates=result.candidates,
            deleted_files=deleted,
            freed_bytes=freed,
            warnings=warnings,
            errors=errors,
            elapsed_seconds=time.time() - start_time
        )
