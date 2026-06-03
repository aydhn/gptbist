import uuid
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import MaintenancePlan, MaintenanceCadenceKind, MaintenanceCadencePolicy, MaintenanceAction, MaintenanceStatus

class MaintenancePlanner:
    def plan_from_policy(self, policy: MaintenanceCadencePolicy, dry_run: bool = True, confirm: bool = False) -> MaintenancePlan:
        destructive_count = self.estimate_destructive_actions(policy.actions)
        return MaintenancePlan(
            plan_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            cadence=policy.cadence,
            policy_id=policy.policy_id,
            actions=policy.actions,
            dry_run=dry_run,
            confirm=confirm,
            estimated_destructive_actions=destructive_count,
            status=MaintenanceStatus.PASS if (confirm or not destructive_count) else MaintenanceStatus.WATCH
        )

    def estimate_destructive_actions(self, actions: list[MaintenanceAction]) -> int:
        return sum(1 for a in actions if a.destructive)

    def create_plan(self, cadence: MaintenanceCadenceKind, policy_id: str | None = None, dry_run: bool = True, confirm: bool = False) -> MaintenancePlan:
        # In a full implementation, this would look up the policy by id or cadence.
        # Returning a mock plan for now to satisfy structural requirements.
        return MaintenancePlan(
            plan_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            cadence=cadence,
            policy_id=policy_id or "mock",
            actions=[],
            dry_run=dry_run,
            confirm=confirm
        )
