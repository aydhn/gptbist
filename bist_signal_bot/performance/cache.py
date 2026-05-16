import os
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bist_signal_bot.performance.models import (
    CacheEntryInfo, CacheReport, CachePolicy
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import (
    get_data_dir, get_scans_dir, get_backtest_results_dir, get_optimization_dir,
    get_ml_feature_store_dir, get_runtime_runs_dir, get_monitoring_dir,
    get_quality_dir, get_packaging_dir, get_docs_reports_dir
)
from bist_signal_bot.security.path_guard import PathGuard

class CacheInspector:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_data_dir(self.settings)
        self.logger = logging.getLogger("bist_signal_bot.performance.cache")
        self.path_guard = PathGuard([self.base_dir])

    def _get_target_dirs(self) -> list[Path]:
        return [
            self.base_dir / "cache",
            get_scans_dir(self.settings),
            get_backtest_results_dir(self.settings),
            get_optimization_dir(self.settings),
            get_ml_feature_store_dir(self.settings),
            get_runtime_runs_dir(self.settings),
            get_monitoring_dir(self.settings) / "snapshots",
            get_monitoring_dir(self.settings) / "reports",
            get_quality_dir(self.settings),
            get_packaging_dir(self.settings),
            get_docs_reports_dir(self.settings)
        ]

    def _is_protected(self, path: Path) -> bool:
        name = path.name.lower()
        if name in [".env", "config.json"]:
            return True
        if path.suffix == ".py":
            return True

        if self.settings.PERFORMANCE_PROTECT_MODEL_ARTIFACTS and "model" in name and path.suffix in [".pkl", ".joblib", ".pt"]:
            return True
        if self.settings.PERFORMANCE_PROTECT_PAPER_LEDGER and "ledger" in name:
            return True
        if self.settings.PERFORMANCE_PROTECT_RUNTIME_STATE and "state" in name:
            return True
        if self.settings.PERFORMANCE_PROTECT_AUDIT_LOGS and "audit" in name:
            return True

        return False

    def classify_cache_entry(self, path: Path) -> CacheEntryInfo:
        try:
            stat = path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            age_days = (datetime.now(timezone.utc) - mod_time).total_seconds() / (24 * 3600)

            safe_to_delete = True
            reason = None

            if self._is_protected(path):
                safe_to_delete = False
                reason = "Protected file type or name"

            category = "unknown"
            if "scans" in path.parts:
                category = "scans"
            elif "backtest" in path.parts:
                category = "backtest"
            elif "optimization" in path.parts:
                category = "optimization"
            elif "ml" in path.parts:
                category = "ml_features"
            elif "runtime" in path.parts:
                category = "runtime"
            elif "cache" in path.parts:
                category = "cache"
            elif "monitoring" in path.parts:
                category = "monitoring"

            return CacheEntryInfo(
                path=str(path),
                size_mb=size_mb,
                modified_at=mod_time,
                age_days=age_days,
                category=category,
                safe_to_delete=safe_to_delete,
                reason=reason
            )
        except Exception as e:
            return CacheEntryInfo(str(path), 0, None, None, "error", False, str(e))

    def scan_cache_dirs(self) -> CacheReport:
        report = CacheReport(
            policy=CachePolicy[self.settings.PERFORMANCE_CACHE_POLICY] if isinstance(self.settings.PERFORMANCE_CACHE_POLICY, str) else self.settings.PERFORMANCE_CACHE_POLICY,
            dry_run=True
        )

        target_dirs = self._get_target_dirs()
        for t_dir in target_dirs:
            if not t_dir.exists() or not t_dir.is_dir():
                continue

            for root, _, files in os.walk(t_dir):
                for file in files:
                    p = Path(root) / file
                    info = self.classify_cache_entry(p)
                    report.entries.append(info)

                    report.total_size_mb += info.size_mb
                    report.entry_count += 1

                    if info.safe_to_delete:
                        report.safe_delete_size_mb += info.size_mb
                        report.safe_delete_count += 1

        return report

    def cleanup(self, policy: CachePolicy, max_age_days: int, max_total_size_mb: float | None = None, dry_run: bool = True, confirm: bool = False) -> CacheReport:
        if not dry_run and not confirm:
            raise ValueError("confirm must be True when dry_run is False")

        report = CacheReport(policy=policy, dry_run=dry_run)

        target_dirs = self._get_target_dirs()

        all_entries = []
        for t_dir in target_dirs:
            if not t_dir.exists() or not t_dir.is_dir():
                continue
            for root, _, files in os.walk(t_dir):
                for file in files:
                    p = Path(root) / file
                    info = self.classify_cache_entry(p)
                    all_entries.append(info)
                    report.total_size_mb += info.size_mb
                    report.entry_count += 1

        # Filter entries to delete
        to_delete = []
        for info in all_entries:
            if not info.safe_to_delete:
                continue

            should_delete = False
            if policy == CachePolicy.CLEAN_OLD:
                if info.age_days and info.age_days >= max_age_days:
                    should_delete = True
            elif policy == CachePolicy.CLEAN_TEMP_ONLY:
                if "temp" in info.path.lower() or info.path.endswith(".tmp"):
                    should_delete = True
            elif policy == CachePolicy.KEEP_ALL:
                should_delete = False
            elif policy == CachePolicy.DRY_RUN_ONLY:
                should_delete = False

            if should_delete:
                to_delete.append(info)

        # Handle CLEAN_LARGE policy
        if policy == CachePolicy.CLEAN_LARGE and max_total_size_mb is not None:
            # Sort by age oldest first
            safe_entries = [e for e in all_entries if e.safe_to_delete]
            safe_entries.sort(key=lambda x: x.age_days or 0, reverse=True)

            current_size = report.total_size_mb
            for info in safe_entries:
                if current_size <= max_total_size_mb:
                    break
                to_delete.append(info)
                current_size -= info.size_mb

        for info in to_delete:
            p = Path(info.path)
            try:
                self.path_guard.ensure_safe_path(p)
            except Exception as e:
                report.issues.append(f"Unsafe path {p}: {e}")
                report.skipped_files.append(str(p))
                continue

            if not dry_run:
                try:
                    p.unlink()
                    report.deleted_files.append(str(p))
                    report.safe_delete_count += 1
                    report.safe_delete_size_mb += info.size_mb
                except Exception as e:
                    report.issues.append(f"Failed to delete {p}: {e}")
                    report.skipped_files.append(str(p))
            else:
                report.deleted_files.append(str(p))
                report.safe_delete_count += 1
                report.safe_delete_size_mb += info.size_mb

        # Clean empty dirs if not dry run
        if not dry_run:
            for t_dir in target_dirs:
                if t_dir.exists():
                    try:
                        for dirpath, dirnames, filenames in os.walk(t_dir, topdown=False):
                            if not dirnames and not filenames and dirpath != str(t_dir):
                                os.rmdir(dirpath)
                    except Exception as e:
                        report.issues.append(f"Failed to remove empty dir in {t_dir}: {e}")

        return report
