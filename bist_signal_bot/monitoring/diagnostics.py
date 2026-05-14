import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monitoring.models import (
    DiagnosticCheckResult, DiagnosticCheckStatus, MonitoringComponent,
    AlertSeverity, HealthLevel
)
from bist_signal_bot.monitoring.storage import MonitoringStore

from bist_signal_bot.storage.paths import get_data_dir

class DiagnosticsRunner:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        runtime_state_store: Optional[Any] = None,
        lock_manager: Optional[Any] = None,
        monitoring_store: Optional[MonitoringStore] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.settings = settings or Settings()
        self.runtime_state_store = runtime_state_store
        self.lock_manager = lock_manager
        self.monitoring_store = monitoring_store or MonitoringStore(self.settings)
        self.logger = logger or logging.getLogger(__name__)

    def run_all_checks(self) -> List[DiagnosticCheckResult]:
        checks = []
        checks.append(self.check_runtime_state())
        checks.append(self.check_lock_state())
        checks.append(self.check_storage_paths())
        checks.append(self.check_recent_runtime_failures())
        checks.append(self.check_data_freshness())
        checks.append(self.check_telegram_config())
        checks.append(self.check_ml_model_config())
        checks.append(self.check_paper_ledger())
        return checks

    def _create_result(self, name: str, comp: MonitoringComponent, status: DiagnosticCheckStatus, sev: AlertSeverity, msg: str, details: dict = None, recs: list = None) -> DiagnosticCheckResult:
        return DiagnosticCheckResult(
            check_name=name,
            component=comp,
            status=status,
            severity=sev,
            message=msg,
            details=details or {},
            recommendations=recs or [],
            generated_at=datetime.utcnow()
        )


    def check_runtime_state(self) -> DiagnosticCheckResult:
        try:
            from bist_signal_bot.runtime.state import RuntimeStateStore
            state_store = self.runtime_state_store or RuntimeStateStore(self.settings)
            state = state_store.load()

            if state.is_running:
                return self._create_result(
                    "Runtime State", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.WARN, AlertSeverity.INFO,
                    "Runtime is currently marked as running.", {"run_id": state.current_run_id}
                )
            return self._create_result(
                "Runtime State", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.PASS, AlertSeverity.INFO,
                "Runtime state is idle/clean."
            )
        except Exception as e:
            return self._create_result(
                "Runtime State", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.ERROR, AlertSeverity.ERROR,
                f"Failed to read runtime state: {e}", recs=["Check file permissions for state.json", "Run monitor repair --reset-state"]
            )


    def check_lock_state(self) -> DiagnosticCheckResult:
        from bist_signal_bot.runtime.locks import RuntimeLockManager
        try:
            from bist_signal_bot.runtime.locks import RuntimeLockManager
            lock_manager = self.lock_manager or RuntimeLockManager(self.settings)
            is_locked = lock_manager.is_locked()

            if not is_locked:
                return self._create_result("Lock State", MonitoringComponent.LOCK, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, "No active lock.")

            stale_secs = getattr(self.settings, "RUNTIME_LOCK_TTL_SECONDS", 3600)
            if self.lock_manager.is_stale(stale_secs):
                return self._create_result(
                    "Lock State", MonitoringComponent.LOCK, DiagnosticCheckStatus.FAIL, AlertSeverity.ERROR,
                    f"Lock is stale (older than {stale_secs}s).", recs=["Run monitor repair --clear-stale-lock"]
                )

            return self._create_result("Lock State", MonitoringComponent.LOCK, DiagnosticCheckStatus.WARN, AlertSeverity.INFO, "Active, non-stale lock exists.")
        except Exception as e:
            return self._create_result("Lock State", MonitoringComponent.LOCK, DiagnosticCheckStatus.ERROR, AlertSeverity.ERROR, f"Lock check failed: {e}")

    def check_storage_paths(self) -> DiagnosticCheckResult:
        try:
            base = get_data_dir(self.settings)
            missing = []
            for subdir in ["cache", "reports", "monitoring"]:
                if not (base / subdir).exists():
                    missing.append(subdir)

            if missing:
                return self._create_result(
                    "Storage Paths", MonitoringComponent.STORAGE, DiagnosticCheckStatus.FAIL, AlertSeverity.WARNING,
                    f"Missing directories: {missing}", recs=["Run monitor repair --auto-safe"]
                )
            return self._create_result("Storage Paths", MonitoringComponent.STORAGE, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, "All core storage paths exist.")
        except Exception as e:
            return self._create_result("Storage Paths", MonitoringComponent.STORAGE, DiagnosticCheckStatus.ERROR, AlertSeverity.ERROR, f"Storage path check failed: {e}")

    def check_recent_runtime_failures(self) -> DiagnosticCheckResult:
        try:
            metrics = self.monitoring_store.load_recent_metrics(limit=500)
            failure_status_metrics = [m for m in metrics if m.name == "runtime_success" and m.value is False]
            threshold = getattr(self.settings, "MONITORING_CONSECUTIVE_FAILURE_THRESHOLD", 3)

            status_metrics = sorted([m for m in metrics if m.name == "runtime_success"], key=lambda x: x.timestamp, reverse=True)
            consecutive = 0
            for m in status_metrics:
                if m.value is False:
                    consecutive += 1
                else:
                    break

            if consecutive >= threshold:
                return self._create_result(
                    "Runtime Failures", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.FAIL, AlertSeverity.CRITICAL,
                    f"Pipeline has failed {consecutive} times consecutively.", {"consecutive_failures": consecutive},
                    recs=["Check application logs", "Verify data provider connectivity"]
                )
            elif consecutive > 0:
                return self._create_result("Runtime Failures", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.WARN, AlertSeverity.WARNING, f"{consecutive} recent failures.")

            return self._create_result("Runtime Failures", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, "No recent consecutive failures.")
        except Exception as e:
            return self._create_result("Runtime Failures", MonitoringComponent.RUNTIME, DiagnosticCheckStatus.ERROR, AlertSeverity.ERROR, f"Failed to check failures: {e}")

    def check_data_freshness(self) -> DiagnosticCheckResult:
        try:
            cache_dir = get_data_dir(self.settings) / "cache"
            if not cache_dir.exists():
                return self._create_result("Data Freshness", MonitoringComponent.DATA, DiagnosticCheckStatus.WARN, AlertSeverity.WARNING, "Cache dir missing. Data not fresh.")

            newest_time = 0
            for f in cache_dir.rglob("*.csv"):
                if f.is_file():
                    newest_time = max(newest_time, f.stat().st_mtime)

            if newest_time == 0:
                return self._create_result("Data Freshness", MonitoringComponent.DATA, DiagnosticCheckStatus.WARN, AlertSeverity.WARNING, "No data files found in cache.")

            age_hours = (datetime.utcnow().timestamp() - newest_time) / 3600
            max_age = getattr(self.settings, "MONITORING_DATA_FRESHNESS_MAX_AGE_HOURS", 48)

            if age_hours > max_age:
                return self._create_result(
                    "Data Freshness", MonitoringComponent.DATA, DiagnosticCheckStatus.FAIL, AlertSeverity.ERROR,
                    f"Data is {age_hours:.1f} hours old. Max allowed is {max_age} hours.",
                    {"age_hours": age_hours}
                )

            return self._create_result("Data Freshness", MonitoringComponent.DATA, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, f"Data is fresh ({age_hours:.1f}h old).")
        except Exception as e:
            return self._create_result("Data Freshness", MonitoringComponent.DATA, DiagnosticCheckStatus.ERROR, AlertSeverity.ERROR, f"Freshness check failed: {e}")

    def check_telegram_config(self) -> DiagnosticCheckResult:
        if not getattr(self.settings, "ENABLE_TELEGRAM", False):
            return self._create_result("Telegram Config", MonitoringComponent.TELEGRAM, DiagnosticCheckStatus.SKIP, AlertSeverity.INFO, "Telegram disabled.")

        token = getattr(self.settings, "TELEGRAM_BOT_TOKEN", None)
        chat = getattr(self.settings, "TELEGRAM_CHAT_ID", None)

        if not token or not chat:
            return self._create_result("Telegram Config", MonitoringComponent.TELEGRAM, DiagnosticCheckStatus.FAIL, AlertSeverity.WARNING, "Telegram enabled but token/chat missing.")

        return self._create_result("Telegram Config", MonitoringComponent.TELEGRAM, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, "Telegram config appears valid.")

    def check_ml_model_config(self) -> DiagnosticCheckResult:
        ml_filter_enabled = getattr(self.settings, "RUNTIME_USE_ML_FILTER", False)
        if not ml_filter_enabled:
            return self._create_result("ML Config", MonitoringComponent.ML, DiagnosticCheckStatus.SKIP, AlertSeverity.INFO, "ML filter disabled.")

        model_id = getattr(self.settings, "RUNTIME_ML_MODEL_ID", "")
        if not model_id:
             return self._create_result("ML Config", MonitoringComponent.ML, DiagnosticCheckStatus.FAIL, AlertSeverity.ERROR, "ML filter enabled but no model ID configured.")

        return self._create_result("ML Config", MonitoringComponent.ML, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, "ML configuration looks valid.")

    def check_paper_ledger(self) -> DiagnosticCheckResult:
        if not getattr(self.settings, "RUNTIME_USE_PAPER", False):
            return self._create_result("Paper Ledger", MonitoringComponent.PAPER, DiagnosticCheckStatus.SKIP, AlertSeverity.INFO, "Paper trading disabled.")

        try:
            from bist_signal_bot.storage.paths import get_paper_account_dir
            ledger_path = get_paper_account_dir("default", self.settings) / "ledger.json"
            if not ledger_path.exists():
                 return self._create_result("Paper Ledger", MonitoringComponent.PAPER, DiagnosticCheckStatus.WARN, AlertSeverity.WARNING, "Paper ledger file not found. May be uninitialized.")
            return self._create_result("Paper Ledger", MonitoringComponent.PAPER, DiagnosticCheckStatus.PASS, AlertSeverity.INFO, "Paper ledger exists.")
        except Exception as e:
            return self._create_result("Paper Ledger", MonitoringComponent.PAPER, DiagnosticCheckStatus.ERROR, AlertSeverity.ERROR, f"Ledger check failed: {e}")

    def overall_health(self, checks: List[DiagnosticCheckResult]) -> HealthLevel:
        if any(c.status in [DiagnosticCheckStatus.ERROR] for c in checks):
            return HealthLevel.UNHEALTHY

        if any(c.status == DiagnosticCheckStatus.FAIL and c.severity == AlertSeverity.CRITICAL for c in checks):
            return HealthLevel.CRITICAL

        fails = [c for c in checks if c.status == DiagnosticCheckStatus.FAIL]
        if fails:
            return HealthLevel.UNHEALTHY

        warns = [c for c in checks if c.status == DiagnosticCheckStatus.WARN]
        if len(warns) > len(checks) / 3:
            return HealthLevel.DEGRADED

        return HealthLevel.HEALTHY
