import logging
import importlib
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.release.models import (
    ReleaseCheckResult, ReleaseCheckCategory, ReleaseCheckStatus, ReleaseBlockerSeverity
)

logger = logging.getLogger(__name__)

class ReleaseCheckRunner:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def _create_result(self, check_id: str, name: str, category: ReleaseCheckCategory) -> ReleaseCheckResult:
        return ReleaseCheckResult(
            check_id=check_id,
            name=name,
            category=category,
            status=ReleaseCheckStatus.SKIP,
            severity=ReleaseBlockerSeverity.LOW,
            message="Check skipped",
        )

    def run_import_checks(self) -> list[ReleaseCheckResult]:
        results = []
        modules_to_check = [
            ("bist_signal_bot", "core"),
            ("bist_signal_bot.data", "data"),
            ("bist_signal_bot.indicators", "indicators/features"),
            ("bist_signal_bot.strategies", "strategies"),
            ("bist_signal_bot.scanner", "scanner"),
            ("bist_signal_bot.backtesting", "backtesting"),
            ("bist_signal_bot.risk", "risk"),
            ("bist_signal_bot.portfolio", "portfolio"),
            ("bist_signal_bot.paper", "paper"),
            ("bist_signal_bot.ml", "ml"),
            ("bist_signal_bot.regime", "regime"),
            ("bist_signal_bot.runtime", "runtime"),
            ("bist_signal_bot.monitoring", "monitoring"),
            ("bist_signal_bot.security", "security"),
            ("bist_signal_bot.quality", "quality"),
            ("bist_signal_bot.packaging", "packaging"),
            ("bist_signal_bot.docs", "docs"),
            ("bist_signal_bot.performance", "performance"),
            ("bist_signal_bot.adaptive", "adaptive"),
            ("bist_signal_bot.research", "research"),
            ("bist_signal_bot.reports", "reports"),
            ("bist_signal_bot.scenarios", "scenarios"),
            ("bist_signal_bot.release", "release"),
        ]

        for mod_name, desc in modules_to_check:
            start_time = time.time()
            res = self._create_result(f"import_{mod_name.replace('.', '_')}", f"Import {desc}", ReleaseCheckCategory.IMPORTS)
            try:
                importlib.import_module(mod_name)
                res.status = ReleaseCheckStatus.PASS
                res.message = f"Successfully imported {mod_name}"
            except ImportError as e:
                res.status = ReleaseCheckStatus.FAIL
                res.severity = ReleaseBlockerSeverity.CRITICAL
                res.message = f"Failed to import {mod_name}: {e}"
                res.recommendations.append(f"Check if {mod_name} exists and has __init__.py")
            res.elapsed_seconds = time.time() - start_time
            results.append(res)
        return results

    def run_config_checks(self) -> list[ReleaseCheckResult]:
        results = []

        # Env file check
        start_time = time.time()
        res = self._create_result("config_env_example", ".env.example exists", ReleaseCheckCategory.CONFIG)
        if Path(".env.example").exists():
            res.status = ReleaseCheckStatus.PASS
            res.message = ".env.example file is present"
        else:
            res.status = ReleaseCheckStatus.FAIL
            res.severity = ReleaseBlockerSeverity.HIGH
            res.message = "Missing .env.example file"
        res.elapsed_seconds = time.time() - start_time
        results.append(res)

        # Settings defaults check
        start_time = time.time()
        res2 = self._create_result("config_safe_defaults", "Safe default settings", ReleaseCheckCategory.CONFIG)
        unsafe_findings = []

        if getattr(self.settings, "ENABLE_REAL_ORDERS", False):
            unsafe_findings.append("ENABLE_REAL_ORDERS should default to False")
        if getattr(self.settings, "TELEGRAM_ENABLED", False):
             unsafe_findings.append("TELEGRAM_ENABLED should default to False")

        if unsafe_findings:
            res2.status = ReleaseCheckStatus.FAIL
            res2.severity = ReleaseBlockerSeverity.CRITICAL
            res2.message = "Found unsafe default settings"
            res2.details["unsafe_findings"] = unsafe_findings
        else:
            res2.status = ReleaseCheckStatus.PASS
            res2.message = "Default settings appear safe"

        res2.elapsed_seconds = time.time() - start_time
        results.append(res2)

        return results

    def run_storage_checks(self) -> list[ReleaseCheckResult]:
        results = []

        start_time = time.time()
        res = self._create_result("storage_tmp_write", "Storage write access", ReleaseCheckCategory.STORAGE)
        try:
            from bist_signal_bot.storage.paths import get_data_dir
            data_dir = get_data_dir(self.settings)
            test_file = data_dir / ".release_test_write"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("test")
            test_file.unlink()
            res.status = ReleaseCheckStatus.PASS
            res.message = "Can write to storage dir safely"
        except Exception as e:
            res.status = ReleaseCheckStatus.FAIL
            res.severity = ReleaseBlockerSeverity.HIGH
            res.message = f"Storage write check failed: {e}"
        res.elapsed_seconds = time.time() - start_time
        results.append(res)

        return results

    def run_safety_checks(self) -> list[ReleaseCheckResult]:
        results = []
        start_time = time.time()
        res = self._create_result("safety_forbidden_actions", "Forbidden Action Guard check", ReleaseCheckCategory.SAFETY)

        try:
            # We mock the usage of ForbiddenActionGuard here as a smoke test
            from bist_signal_bot.security.forbidden_actions import ForbiddenActionGuard
            guard = ForbiddenActionGuard(self.settings)

            # test a forbidden action
            guard.check_action("place_real_order")

            # If it didn't raise, the guard is broken
            res.status = ReleaseCheckStatus.FAIL
            res.severity = ReleaseBlockerSeverity.CRITICAL
            res.message = "ForbiddenActionGuard allowed a forbidden action"
        except ImportError:
            res.status = ReleaseCheckStatus.SKIP
            res.message = "Security module not importable"
        except Exception as e:
            # Expected a SecurityException or similar
            if "Forbidden action" in str(e) or "Security" in type(e).__name__:
                res.status = ReleaseCheckStatus.PASS
                res.message = "ForbiddenActionGuard successfully blocked dangerous actions"
            else:
                res.status = ReleaseCheckStatus.FAIL
                res.severity = ReleaseBlockerSeverity.CRITICAL
                res.message = f"Unexpected error in ForbiddenActionGuard: {e}"

        res.elapsed_seconds = time.time() - start_time
        results.append(res)
        return results

    def run_runtime_checks(self) -> list[ReleaseCheckResult]:
        results = []
        start_time = time.time()
        res = self._create_result("runtime_safe_config", "Runtime Safe Profile", ReleaseCheckCategory.RUNTIME)

        try:
            from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
            orch = RuntimeOrchestrator(self.settings)
            if hasattr(orch, "get_safe_dry_run_config"):
                cfg = orch.get_safe_dry_run_config()
                if cfg:
                    res.status = ReleaseCheckStatus.PASS
                    res.message = "Runtime Orchestrator can generate safe dry run config"
                else:
                    res.status = ReleaseCheckStatus.WARN
                    res.severity = ReleaseBlockerSeverity.MEDIUM
                    res.message = "Dry run config returned None"
            else:
                 res.status = ReleaseCheckStatus.SKIP
                 res.message = "RuntimeOrchestrator missing get_safe_dry_run_config method"
        except ImportError:
             res.status = ReleaseCheckStatus.SKIP
             res.message = "Runtime module not importable"
        except Exception as e:
             res.status = ReleaseCheckStatus.FAIL
             res.severity = ReleaseBlockerSeverity.HIGH
             res.message = f"Failed runtime check: {e}"

        res.elapsed_seconds = time.time() - start_time
        results.append(res)
        return results

    def run_reports_checks(self) -> list[ReleaseCheckResult]:
        results = []
        start_time = time.time()
        res = self._create_result("reports_safe_claim", "Reports safe claim guard", ReleaseCheckCategory.REPORTS)

        try:
            from bist_signal_bot.security.claims_guard import UnsafeClaimGuard
            guard = UnsafeClaimGuard(self.settings)
            if guard.contains_unsafe_claims("This will generate 10% guaranteed profit"):
                res.status = ReleaseCheckStatus.PASS
                res.message = "UnsafeClaimGuard correctly identified unsafe claim"
            else:
                 res.status = ReleaseCheckStatus.FAIL
                 res.severity = ReleaseBlockerSeverity.HIGH
                 res.message = "UnsafeClaimGuard failed to identify unsafe claim"
        except ImportError:
            res.status = ReleaseCheckStatus.SKIP
            res.message = "Security/Reports module not importable"
        except Exception as e:
            res.status = ReleaseCheckStatus.FAIL
            res.severity = ReleaseBlockerSeverity.HIGH
            res.message = f"Failed reports safety check: {e}"

        res.elapsed_seconds = time.time() - start_time
        results.append(res)
        return results

    def run_all_basic_checks(self) -> list[ReleaseCheckResult]:
        return (
            self.run_import_checks() +
            self.run_config_checks() +
            self.run_storage_checks() +
            self.run_safety_checks() +
            self.run_runtime_checks() +
            self.run_reports_checks()
        )
