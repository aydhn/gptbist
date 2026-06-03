from bist_signal_bot.maintenance_automation.models import (
    MaintenanceCadencePolicy, MaintenanceCadenceKind, MaintenanceAction, MaintenanceActionType
)

class MaintenanceCadenceRegistry:
    def default_policies(self) -> list[MaintenanceCadencePolicy]:
        return [
            MaintenanceCadencePolicy(
                policy_id="daily_operator_self_audit_v1",
                name="Daily Operator Self Audit",
                cadence=MaintenanceCadenceKind.DAILY,
                actions=[
                    MaintenanceAction(action_id="act_1", action_type=MaintenanceActionType.HEALTHCHECK, name="Run Healthcheck"),
                    MaintenanceAction(action_id="act_2", action_type=MaintenanceActionType.DOCTOR, name="Run Doctor"),
                    MaintenanceAction(action_id="act_3", action_type=MaintenanceActionType.OPS_READINESS, name="Run Ops Readiness")
                ]
            ),
            MaintenanceCadencePolicy(
                policy_id="weekly_quality_and_performance_v1",
                name="Weekly Quality and Performance",
                cadence=MaintenanceCadenceKind.WEEKLY,
                actions=[
                    MaintenanceAction(action_id="act_4", action_type=MaintenanceActionType.QA_GATE, name="Run QA Release Gate"),
                    MaintenanceAction(action_id="act_5", action_type=MaintenanceActionType.PERFORMANCE_BENCHMARK, name="Run Benchmark")
                ]
            )
        ]

    def get_policy(self, policy_id: str) -> MaintenanceCadencePolicy:
        for p in self.default_policies():
            if p.policy_id == policy_id: return p
        return None

    def policies_by_cadence(self, cadence: MaintenanceCadenceKind) -> list[MaintenanceCadencePolicy]:
        return [p for p in self.default_policies() if p.cadence == cadence]
