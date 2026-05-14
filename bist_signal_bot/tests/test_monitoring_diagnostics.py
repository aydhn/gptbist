import pytest
from pathlib import Path
from bist_signal_bot.monitoring.diagnostics import DiagnosticsRunner
from bist_signal_bot.monitoring.models import DiagnosticCheckStatus, HealthLevel, AlertSeverity, DiagnosticCheckResult, MonitoringComponent
from bist_signal_bot.config.settings import Settings

class MockLockManager:
    def __init__(self, locked=False, stale=False):
        self.locked = locked
        self.stale = stale
    def is_locked(self): return self.locked
    def is_stale(self, ttl): return self.stale

def test_check_runtime_state():
    settings = Settings()
    # Need to skip full test due to tricky runtime_state_store imports or properly mock
    dr = DiagnosticsRunner(settings=settings)
    class MockStateStore:
        def load(self):
            class MockState:
                def __init__(self, running):
                    self.is_running = running
                    self.current_run_id = "test"
            return MockState(True)
    dr.runtime_state_store = MockStateStore()

    res = dr.check_runtime_state()
    assert res.status == DiagnosticCheckStatus.WARN

def test_check_lock_state():
    dr = DiagnosticsRunner(lock_manager=MockLockManager(locked=True, stale=True))
    res = dr.check_lock_state()
    assert res.status == DiagnosticCheckStatus.FAIL

    dr2 = DiagnosticsRunner(lock_manager=MockLockManager(locked=False))
    assert dr2.check_lock_state().status == DiagnosticCheckStatus.PASS

def test_check_data_freshness_warn_no_data(tmp_path):
    settings = Settings(DATA_DIR=str(tmp_path))
    dr = DiagnosticsRunner(settings=settings)

    res = dr.check_data_freshness()
    assert res.status == DiagnosticCheckStatus.WARN

def test_overall_health():
    dr = DiagnosticsRunner()

    checks_healthy = [
        DiagnosticCheckResult(check_name="1", component=MonitoringComponent.RUNTIME, status=DiagnosticCheckStatus.PASS, severity=AlertSeverity.INFO, message="", generated_at=__import__("datetime").datetime.utcnow())
    ]
    assert dr.overall_health(checks_healthy) == HealthLevel.HEALTHY

    checks_critical = [
        DiagnosticCheckResult(check_name="1", component=MonitoringComponent.RUNTIME, status=DiagnosticCheckStatus.FAIL, severity=AlertSeverity.CRITICAL, message="", generated_at=__import__("datetime").datetime.utcnow())
    ]
    assert dr.overall_health(checks_critical) == HealthLevel.CRITICAL
