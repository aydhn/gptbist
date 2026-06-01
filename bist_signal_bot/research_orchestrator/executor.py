import uuid
import time
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.research_orchestrator.models import (
    ResearchRunPlan,
    ResearchRun,
    ResearchTask,
    ResearchTaskResult,
    ResearchRunStatus,
    ResearchExecutionMode
)

class ResearchRunExecutor:
    def execute_plan(
        self,
        plan: ResearchRunPlan,
        dry_run: bool = True,
        save: bool = False,
        stop_on_fail: bool = True
    ) -> ResearchRun:
        run_id = str(uuid.uuid4())

        run = ResearchRun(
            run_id=run_id,
            plan=plan,
            started_at=datetime.now(timezone.utc),
            status=ResearchRunStatus.RUNNING,
            key_findings=[],
            warnings=[],
            errors=[]
        )

        # Simple execution: assume topological order is provided or execute sequentially for now
        # Integration with DAG builder is assumed to happen before or we just run them as they are
        for task in plan.tasks:
            if self.should_skip_task(task, run.task_results):
                res = ResearchTaskResult(
                    result_id=str(uuid.uuid4()),
                    task_id=task.task_id,
                    task_type=task.task_type,
                    started_at=datetime.now(timezone.utc),
                    finished_at=datetime.now(timezone.utc),
                    status=ResearchRunStatus.SKIPPED
                )
                run.task_results.append(res)
                continue

            res = self.execute_task(task, context={}, dry_run=dry_run)
            run.task_results.append(res)

            if stop_on_fail and res.status in (ResearchRunStatus.FAIL, ResearchRunStatus.ERROR, ResearchRunStatus.BLOCKED):
                if task.required and not task.allow_failure:
                    run.errors.append(f"Task {task.task_id} failed, stopping run.")
                    break

        run.finished_at = datetime.now(timezone.utc)
        run.status = self.run_status(run.task_results)

        return run

    def execute_task(self, task: ResearchTask, context: dict[str, Any], dry_run: bool = True) -> ResearchTaskResult:
        if task.command:
            return self.execute_command_task(task, dry_run)
        elif task.callable_ref:
            return self.execute_callable_task(task, context, dry_run)

        # Mock successful task
        start = datetime.now(timezone.utc)
        status = ResearchRunStatus.PASS if not dry_run else ResearchRunStatus.DRY_RUN

        return ResearchTaskResult(
            result_id=str(uuid.uuid4()),
            task_id=task.task_id,
            task_type=task.task_type,
            started_at=start,
            finished_at=datetime.now(timezone.utc),
            status=status,
            output_summary={"message": f"Task {task.name} completed (dry_run={dry_run})."}
        )

    def execute_command_task(self, task: ResearchTask, dry_run: bool = True) -> ResearchTaskResult:
        start = datetime.now(timezone.utc)

        if "broker" in (task.command or "").lower() or "order" in (task.command or "").lower() or "live" in (task.command or "").lower():
            return ResearchTaskResult(
                result_id=str(uuid.uuid4()),
                task_id=task.task_id,
                task_type=task.task_type,
                started_at=start,
                finished_at=datetime.now(timezone.utc),
                status=ResearchRunStatus.BLOCKED,
                errors=["Unsafe command blocked by executor."]
            )

        status = ResearchRunStatus.PASS if not dry_run else ResearchRunStatus.DRY_RUN

        return ResearchTaskResult(
            result_id=str(uuid.uuid4()),
            task_id=task.task_id,
            task_type=task.task_type,
            started_at=start,
            finished_at=datetime.now(timezone.utc),
            status=status,
            output_summary={"command": task.command, "executed": not dry_run}
        )

    def execute_callable_task(self, task: ResearchTask, context: dict[str, Any], dry_run: bool = True) -> ResearchTaskResult:
        start = datetime.now(timezone.utc)
        status = ResearchRunStatus.PASS if not dry_run else ResearchRunStatus.DRY_RUN

        return ResearchTaskResult(
            result_id=str(uuid.uuid4()),
            task_id=task.task_id,
            task_type=task.task_type,
            started_at=start,
            finished_at=datetime.now(timezone.utc),
            status=status,
            output_summary={"callable": task.callable_ref, "executed": not dry_run}
        )

    def should_skip_task(self, task: ResearchTask, previous_results: list[ResearchTaskResult]) -> bool:
        # Simple skipping logic based on failed required dependencies
        failed_tasks = {r.task_id for r in previous_results if r.status in (ResearchRunStatus.FAIL, ResearchRunStatus.ERROR, ResearchRunStatus.BLOCKED)}
        for dep in task.depends_on:
            if dep in failed_tasks:
                return True
        return False

    def run_status(self, results: list[ResearchTaskResult]) -> ResearchRunStatus:
        if not results:
            return ResearchRunStatus.PASS

        statuses = [r.status for r in results]
        if ResearchRunStatus.ERROR in statuses:
            return ResearchRunStatus.ERROR
        if ResearchRunStatus.FAIL in statuses:
            return ResearchRunStatus.FAIL
        if ResearchRunStatus.BLOCKED in statuses:
            return ResearchRunStatus.BLOCKED
        if ResearchRunStatus.WATCH in statuses:
            return ResearchRunStatus.WATCH
        if all(s == ResearchRunStatus.DRY_RUN for s in statuses) or ResearchRunStatus.DRY_RUN in statuses:
            return ResearchRunStatus.DRY_RUN
        if all(s in (ResearchRunStatus.PASS, ResearchRunStatus.SKIPPED) for s in statuses):
            return ResearchRunStatus.PASS

        return ResearchRunStatus.UNKNOWN
