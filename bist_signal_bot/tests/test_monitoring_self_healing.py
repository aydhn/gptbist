import pytest
from bist_signal_bot.monitoring.self_healing import SelfHealingManager
from bist_signal_bot.monitoring.models import DiagnosticCheckResult, DiagnosticCheckStatus, MonitoringComponent, AlertSeverity, SelfHealingActionType

class MockLockManager:
    def __init__(self):
        self.cleared = False
    def clear_stale_lock(self, ttl):
        self.cleared = True

class MockStateStore:
    def __init__(self):
        self.reset = False
    def reset_state(self):
        self.reset = True

def test_self_healing_suggest_actions():
    shm = SelfHealingManager()

    checks = [
        DiagnosticCheckResult(
            check_name="Lock State", component=MonitoringComponent.LOCK,
            status=DiagnosticCheckStatus.FAIL, severity=AlertSeverity.ERROR,
            message="Stale", generated_at=__import__("datetime").datetime.utcnow()
        )
    ]

    actions = shm.suggest_actions(checks)
    assert len(actions) == 1
    assert actions[0].action_type == SelfHealingActionType.CLEAR_STALE_LOCK

def test_self_healing_execute_safe_action():
    lock_manager = MockLockManager()
    shm = SelfHealingManager(lock_manager=lock_manager)

    checks = [
        DiagnosticCheckResult(
            check_name="Lock State", component=MonitoringComponent.LOCK,
            status=DiagnosticCheckStatus.FAIL, severity=AlertSeverity.ERROR,
            message="Stale", generated_at=__import__("datetime").datetime.utcnow()
        )
    ]

    res = shm.run_safe_auto_healing(checks)
    assert lock_manager.cleared is True
    assert res.executed_count == 1
    assert res.success_count == 1

def test_self_healing_execute_requires_confirm():
    state_store = MockStateStore()
    shm = SelfHealingManager(state_store=state_store)

    checks = [
        DiagnosticCheckResult(
            check_name="Runtime State", component=MonitoringComponent.RUNTIME,
            status=DiagnosticCheckStatus.FAIL, severity=AlertSeverity.ERROR,
            message="Stuck", generated_at=__import__("datetime").datetime.utcnow()
        )
    ]

    res = shm.run_safe_auto_healing(checks)
    assert state_store.reset is False
    assert res.executed_count == 0

    action = shm.suggest_actions(checks)[0]
    res_action = shm.execute_action(action, confirm=False)
    assert res_action.executed is False
    assert state_store.reset is False

    res_action2 = shm.execute_action(action, confirm=True)
    assert res_action2.executed is True
    assert res_action2.success is True
    assert state_store.reset is True
