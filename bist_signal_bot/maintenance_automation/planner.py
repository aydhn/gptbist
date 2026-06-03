import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import (
    MaintenancePlan,
    MaintenanceCadencePolicy,
    MaintenanceCadenceKind,
    MaintenanceAction,
    MaintenanceStatus
)
from bist_signal_bot.maintenance_automation.cadence import MaintenanceCadenceRegistry

class MaintenancePlanner:
    def __init__(self, registry: Optional[MaintenanceCadenceRegistry] = None):
        self.registry = registry or MaintenanceCadenceRegistry()

    def create_plan(self, cadence: MaintenanceCadenceKind, policy_id: Optional[str] = None, dry_run: bool = True, confirm: bool = False) -> MaintenancePlan:
        if policy_id:
            policy = self.registry.get_policy(policy_id)
            if not policy:
                raise ValueError(f"Policy {policy_id} not found.")
            policies = [policy]
        else:
            policies = self.registry.policies_by_cadence(cadence)

        if not policies:
            raise ValueError(f"No policies found for cadence {cadence}.")

        policy = policies[0]
        return self.plan_from_policy(policy, dry_run, confirm)

    def plan_from_policy(self, policy: MaintenanceCadencePolicy, dry_run: bool = True, confirm: bool = False) -> MaintenancePlan:
        estimated_destructive = self.estimate_destructive_actions(policy.actions)

        status = MaintenanceStatus.PASS
        warnings = []
        if estimated_destructive > 0 and not confirm:
            warnings.append(f"Plan contains {estimated_destructive} destructive actions but confirm=False. They will be skipped.")
            status = MaintenanceStatus.WATCH

        plan = MaintenancePlan(
            plan_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            cadence=policy.cadence,
            policy_id=policy.policy_id,
            actions=policy.actions,
            dry_run=dry_run,
            confirm=confirm,
            estimated_destructive_actions=estimated_destructive,
            status=status,
            warnings=warnings
        )
        return plan

    def estimate_destructive_actions(self, actions: List[MaintenanceAction]) -> int:
        return sum(1 for a in actions if a.destructive)

    def validate_plan(self, plan: MaintenancePlan) -> List[str]:
        errors = []
        for action in plan.actions:
            if action.destructive and not plan.confirm:
                pass # it will be skipped at runtime, not an invalid plan
            action_errors = action.validate_action()
            if action_errors:
                errors.append(f"Action {action.action_id} errors: {', '.join(action_errors)}")
        return errors

    def safe_plan_summary(self, plan: MaintenancePlan) -> Dict[str, Any]:
        return {
            "plan_id": plan.plan_id,
            "cadence": plan.cadence.value,
            "policy_id": plan.policy_id,
            "action_count": len(plan.actions),
            "estimated_destructive": plan.estimated_destructive_actions,
            "dry_run": plan.dry_run,
            "confirm": plan.confirm,
            "status": plan.status.value,
            "warnings": plan.warnings
        }
