import uuid
from bist_signal_bot.research_orchestrator.models import (
    ResearchRunPlan,
    ResearchDependency,
    ResearchTask,
    ResearchDependencyStatus,
    ResearchTaskResult,
    ResearchRunStatus,
    ResearchGuardrailCheck
)

class ResearchDependencyResolver:
    def resolve_dependencies(self, plan: ResearchRunPlan) -> list[ResearchDependency]:
        task_map = {t.task_id: t for t in plan.tasks}
        resolved = []

        for task in plan.tasks:
            for dep_id in task.depends_on:
                if dep_id in task_map:
                    resolved.append(self.check_task_dependency(task, task_map[dep_id]))

        return resolved

    def check_task_dependency(self, task: ResearchTask, dependency_task: ResearchTask) -> ResearchDependency:
        return ResearchDependency(
            dependency_id=str(uuid.uuid4()),
            from_task_id=dependency_task.task_id,
            to_task_id=task.task_id,
            status=ResearchDependencyStatus.SATISFIED, # Mock as satisfied during resolution
            required=dependency_task.required
        )

    def check_external_requirements(self, task: ResearchTask) -> list[ResearchGuardrailCheck]:
        # Simple mock of external checks based on task type
        checks = []
        if task.task_type.value == "DATA_CATALOG_GATE":
            checks.append(ResearchGuardrailCheck(
                check_id=str(uuid.uuid4()),
                name="Data Catalog Availability",
                status=ResearchRunStatus.PASS,
                severity="HIGH",
                message="Data catalog is available.",
                blocked=False
            ))
        return checks

    def dependency_status_from_result(self, result: ResearchTaskResult | None, required: bool = True) -> ResearchDependencyStatus:
        if not result:
            return ResearchDependencyStatus.MISSING if required else ResearchDependencyStatus.OPTIONAL_MISSING

        if result.status in (ResearchRunStatus.PASS, ResearchRunStatus.SKIPPED, ResearchRunStatus.DRY_RUN):
            return ResearchDependencyStatus.SATISFIED
        elif result.status in (ResearchRunStatus.FAIL, ResearchRunStatus.ERROR):
            return ResearchDependencyStatus.FAILED
        elif result.status == ResearchRunStatus.BLOCKED:
            return ResearchDependencyStatus.BLOCKED

        return ResearchDependencyStatus.UNKNOWN

    def missing_required_dependencies(self, dependencies: list[ResearchDependency]) -> list[ResearchDependency]:
        return [d for d in dependencies if d.status in (ResearchDependencyStatus.MISSING, ResearchDependencyStatus.FAILED, ResearchDependencyStatus.BLOCKED) and d.required]
