import uuid
import logging
from datetime import datetime
from typing import Any, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monitoring.models import (
    SelfHealingAction, SelfHealingActionType, SelfHealingResult,
    DiagnosticCheckResult, DiagnosticCheckStatus, MonitoringComponent
)
from bist_signal_bot.monitoring.storage import MonitoringStore
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope
from bist_signal_bot.storage.paths import get_data_dir

from bist_signal_bot.runtime.state import RuntimeStateStore
from bist_signal_bot.runtime.locks import RuntimeLockManager
from bist_signal_bot.storage.paths import ensure_directories_exist

class SelfHealingManager:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        lock_manager: Optional[RuntimeLockManager] = None,
        state_store: Optional[RuntimeStateStore] = None,
        monitoring_store: Optional[MonitoringStore] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.settings = settings or Settings()
        self.lock_manager = lock_manager or RuntimeLockManager(self.settings)
        self.state_store = state_store or RuntimeStateStore(self.settings)
        self.monitoring_store = monitoring_store or MonitoringStore(self.settings)
        self.kill_switch = KillSwitchManager(self.settings, get_data_dir(self.settings))
        self.logger = logger or logging.getLogger(__name__)

    def _create_action(self, atype: SelfHealingActionType, comp: MonitoringComponent, desc: str, req_conf: bool, safe_auto: bool) -> SelfHealingAction:
        return SelfHealingAction(
            action_id=str(uuid.uuid4()),
            action_type=atype,
            component=comp,
            description=desc,
            requires_confirm=req_conf,
            safe_to_auto_run=safe_auto,
            generated_at=datetime.utcnow()
        )

    def suggest_actions(self, checks: List[DiagnosticCheckResult]) -> List[SelfHealingAction]:
        actions = []

        for check in checks:
            if check.status in [DiagnosticCheckStatus.FAIL, DiagnosticCheckStatus.ERROR]:
                if check.check_name == "Lock State":
                    actions.append(self._create_action(
                        SelfHealingActionType.CLEAR_STALE_LOCK, MonitoringComponent.LOCK,
                        "Clear stale lock file to allow new runs.", False, getattr(self.settings, "MONITORING_AUTO_CLEAR_STALE_LOCK", True)
                    ))
                elif check.check_name == "Runtime State":
                    actions.append(self._create_action(
                        SelfHealingActionType.RESET_RUNTIME_STATE, MonitoringComponent.RUNTIME,
                        "Reset runtime state if it is stuck.", True, False
                    ))
                elif check.check_name == "Storage Paths":
                    actions.append(self._create_action(
                        SelfHealingActionType.VALIDATE_STORAGE, MonitoringComponent.STORAGE,
                        "Create missing base directories.", False, getattr(self.settings, "MONITORING_AUTO_VALIDATE_STORAGE", True)
                    ))
                elif check.check_name == "Runtime Failures":
                    actions.append(self._create_action(
                        SelfHealingActionType.DISABLE_RUNTIME_LOOP, MonitoringComponent.SCHEDULER,
                        "Disable scheduler loop to prevent further failures.", True, False
                    ))

        return actions

    def execute_action(self, action: SelfHealingAction, confirm: bool = False) -> SelfHealingAction:
        if self.kill_switch.is_active(KillSwitchScope.SELF_HEALING):
            return SelfHealingResult(action=action, success=False, message="Kill switch active for SELF_HEALING")

        if action.executed:
            return action

        if action.requires_confirm and not confirm:
            action.executed = False
            action.message = "Requires confirmation."
            return action

        try:
            if action.action_type == SelfHealingActionType.CLEAR_STALE_LOCK:
                self.repair_stale_lock()
                action.success = True
                action.message = "Stale lock cleared successfully."
            elif action.action_type == SelfHealingActionType.VALIDATE_STORAGE:
                self.validate_storage_paths()
                action.success = True
                action.message = "Storage paths validated/created."
            elif action.action_type == SelfHealingActionType.RESET_RUNTIME_STATE:
                self.reset_runtime_state(confirm=confirm)
                action.success = True
                action.message = "Runtime state reset successfully."
            else:
                action.success = False
                action.message = f"Action {action.action_type.value} not implemented."

        except Exception as e:
            self.logger.error(f"Self-healing failed: {e}")
            action.success = False
            action.message = str(e)

        action.executed = True
        action.executed_at = datetime.utcnow()
        return action

    def run_safe_auto_healing(self, checks: List[DiagnosticCheckResult]) -> SelfHealingResult:
        suggestions = self.suggest_actions(checks)
        safe_actions = [a for a in suggestions if a.safe_to_auto_run]

        executed = 0
        success = 0
        failed = 0

        for action in safe_actions:
            res = self.execute_action(action, confirm=False)
            if res.executed:
                executed += 1
                if res.success:
                    success += 1
                else:
                    failed += 1

        return SelfHealingResult(
            actions=suggestions,
            executed_count=executed,
            success_count=success,
            failed_count=failed,
            skipped_count=len(suggestions) - executed,
            generated_at=datetime.utcnow()
        )

    def repair_stale_lock(self):
        stale_secs = getattr(self.settings, "RUNTIME_LOCK_TTL_SECONDS", 3600)
        self.lock_manager.clear_stale_lock(stale_secs)

    def validate_storage_paths(self):
        ensure_directories_exist()

    def reset_runtime_state(self, confirm: bool = False):
        if not confirm:
            raise ValueError("Must confirm to reset state.")
        self.state_store.reset_state()
