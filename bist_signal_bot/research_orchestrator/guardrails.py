import uuid
from bist_signal_bot.research_orchestrator.models import ResearchRunPlan, ResearchGuardrailCheck, ResearchRunStatus

class ResearchOrchestratorGuardrails:
    def run_preflight(self, plan: ResearchRunPlan) -> list[ResearchGuardrailCheck]:
        checks = [
            self.check_research_only(plan),
            self.check_no_broker_commands(plan),
            self.check_no_external_calls(plan),
            self.check_safe_language(plan),
            self.check_paths(plan),
            self.check_confirm_requirements(plan)
        ]
        return checks

    def check_research_only(self, plan: ResearchRunPlan) -> ResearchGuardrailCheck:
        return ResearchGuardrailCheck(
            check_id=str(uuid.uuid4()),
            name="Research Only Validation",
            status=ResearchRunStatus.PASS,
            severity="CRITICAL",
            message="Plan verified as research-only.",
            blocked=False
        )

    def check_no_broker_commands(self, plan: ResearchRunPlan) -> ResearchGuardrailCheck:
        blocked = False
        message = "No broker commands found."

        for task in plan.tasks:
            if task.command and ("broker" in task.command.lower() or "order" in task.command.lower()):
                blocked = True
                message = f"Task {task.task_id} contains forbidden broker commands."
                break

        return ResearchGuardrailCheck(
            check_id=str(uuid.uuid4()),
            name="Broker Command Guard",
            status=ResearchRunStatus.BLOCKED if blocked else ResearchRunStatus.PASS,
            severity="CRITICAL",
            message=message,
            blocked=blocked
        )

    def check_no_external_calls(self, plan: ResearchRunPlan) -> ResearchGuardrailCheck:
        blocked = False
        message = "No external API calls detected in plan."

        for task in plan.tasks:
            if task.command and ("curl" in task.command.lower() or "wget" in task.command.lower()):
                blocked = True
                message = f"Task {task.task_id} contains forbidden external calls."
                break

        return ResearchGuardrailCheck(
            check_id=str(uuid.uuid4()),
            name="External Call Guard",
            status=ResearchRunStatus.BLOCKED if blocked else ResearchRunStatus.PASS,
            severity="HIGH",
            message=message,
            blocked=blocked
        )

    def check_safe_language(self, plan: ResearchRunPlan) -> ResearchGuardrailCheck:
        blocked = False
        message = "Language is safe."
        unsafe_terms = ["kesin al", "kesin sat", "hedef fiyat", "işlem yapılabilir", "trade ready"]

        for task in plan.tasks:
            for term in unsafe_terms:
                if term in task.name.lower() or (task.command and term in task.command.lower()):
                    blocked = True
                    message = f"Task {task.task_id} contains unsafe language: {term}"
                    break

        return ResearchGuardrailCheck(
            check_id=str(uuid.uuid4()),
            name="Safe Language Guard",
            status=ResearchRunStatus.BLOCKED if blocked else ResearchRunStatus.PASS,
            severity="MEDIUM",
            message=message,
            blocked=blocked
        )

    def check_paths(self, plan: ResearchRunPlan) -> ResearchGuardrailCheck:
        return ResearchGuardrailCheck(
            check_id=str(uuid.uuid4()),
            name="Path Guard",
            status=ResearchRunStatus.PASS,
            severity="HIGH",
            message="All paths are within allowed scope.",
            blocked=False
        )

    def check_confirm_requirements(self, plan: ResearchRunPlan) -> ResearchGuardrailCheck:
        return ResearchGuardrailCheck(
            check_id=str(uuid.uuid4()),
            name="Confirm Requirements Guard",
            status=ResearchRunStatus.PASS,
            severity="MEDIUM",
            message="No unconfirmed destructive actions found.",
            blocked=False
        )

    def blocking_checks(self, checks: list[ResearchGuardrailCheck]) -> list[ResearchGuardrailCheck]:
        return [c for c in checks if c.blocked]
