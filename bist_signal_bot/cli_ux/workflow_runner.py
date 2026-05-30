import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from bist_signal_bot.cli_ux.models import WorkflowRun, WorkflowStepResult, CLIStatus

class CLIWorkflowRunner:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def run_workflow(
        self,
        name: str,
        commands: List[str],
        profile_name: Optional[str] = None,
        dry_run: bool = True,
        stop_on_fail: bool = True,
        save: bool = False
    ) -> WorkflowRun:
        run_id = str(uuid.uuid4())
        steps = []
        errors = self.validate_commands(commands)

        if errors:
            return WorkflowRun(
                run_id=run_id,
                created_at=datetime.now(timezone.utc),
                workflow_name=name,
                profile_name=profile_name,
                status=CLIStatus.BLOCKED,
                exit_code=5,
                errors=errors
            )

        for i, cmd in enumerate(commands):
            step = self.run_step(f"step-{i+1}", i+1, cmd, dry_run)
            steps.append(step)

            if step.status in [CLIStatus.FAILED, CLIStatus.BLOCKED] and stop_on_fail:
                break

        status = self.workflow_status(steps)
        exit_code = 0 if status == CLIStatus.SUCCESS else 1

        run = WorkflowRun(
            run_id=run_id,
            created_at=datetime.now(timezone.utc),
            workflow_name=name,
            profile_name=profile_name,
            steps=steps,
            status=status,
            exit_code=exit_code
        )

        if save:
            pass # would save via store

        return run

    def run_step(self, step_id: str, order: int, command: str, dry_run: bool = True) -> WorkflowStepResult:
        started_at = datetime.now(timezone.utc)

        unsafe_keywords = ["live", "broker", "order", "execute"]
        if any(kw in command.lower() for kw in unsafe_keywords):
            return WorkflowStepResult(
                step_id=step_id,
                order=order,
                command=command,
                status=CLIStatus.BLOCKED,
                exit_code=5,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                errors=["Command contains unsafe keywords."]
            )

        destructive_keywords = ["delete", "clean", "reset", "restore"]
        if not dry_run and any(kw in command.lower() for kw in destructive_keywords) and "--confirm" not in command:
            return WorkflowStepResult(
                step_id=step_id,
                order=order,
                command=command,
                status=CLIStatus.BLOCKED,
                exit_code=6,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                errors=["Destructive command requires --confirm flag without dry-run."]
            )

        # Mock execution
        finished_at = datetime.now(timezone.utc)
        elapsed = (finished_at - started_at).total_seconds()

        return WorkflowStepResult(
            step_id=step_id,
            order=order,
            command=command,
            status=CLIStatus.SUCCESS,
            exit_code=0,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            output_ref=f"mocked_output_for_{step_id}"
        )

    def validate_commands(self, commands: List[str]) -> List[str]:
        errors = []
        for cmd in commands:
            if "live" in cmd.lower() or "broker" in cmd.lower():
                errors.append(f"Unsafe command blocked: {cmd}")
        return errors

    def collect_artifacts(self, run: WorkflowRun) -> Dict[str, str]:
        artifacts = {}
        for step in run.steps:
            if step.output_ref:
                artifacts[step.step_id] = step.output_ref
        return artifacts

    def workflow_status(self, steps: List[WorkflowStepResult]) -> CLIStatus:
        if not steps:
            return CLIStatus.UNKNOWN

        has_failed = any(s.status == CLIStatus.FAILED for s in steps)
        has_blocked = any(s.status == CLIStatus.BLOCKED for s in steps)
        has_warning = any(s.status == CLIStatus.WARNING for s in steps)

        if has_blocked:
            return CLIStatus.BLOCKED
        if has_failed:
            return CLIStatus.FAILED
        if has_warning:
            return CLIStatus.WARNING

        return CLIStatus.SUCCESS
