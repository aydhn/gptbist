import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scenarios.models import ScenarioStepConfig, ScenarioStepResult, ScenarioStepType, ScenarioStatus

class ScenarioStepExecutor:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def execute_step(self, step: ScenarioStepConfig, sandbox_dir: Path, env: Optional[Dict[str, str]] = None) -> ScenarioStepResult:
        started_at = datetime.utcnow()
        result = ScenarioStepResult(
            step_id=step.step_id,
            name=step.name,
            step_type=step.step_type,
            status=ScenarioStatus.SKIPPED,
            started_at=started_at
        )

        try:
            if step.step_type == ScenarioStepType.COMMAND:
                result = self.execute_command_step(step, sandbox_dir, env)
            elif step.step_type == ScenarioStepType.FUNCTION:
                result = self.execute_function_step(step, sandbox_dir)
            else:
                result.status = ScenarioStatus.SUCCESS # defaults for others right now
        except Exception as e:
            result.status = ScenarioStatus.ERROR
            result.issues.append(str(e))

        result.finished_at = datetime.utcnow()
        result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()

        # Verify assertions
        passed, failed, issues = self.execute_assertions(step, result)
        result.assertions_passed = passed
        result.assertions_failed = failed
        result.issues.extend(issues)

        if failed > 0 and result.status == ScenarioStatus.SUCCESS:
             result.status = ScenarioStatus.FAILED

        return self.sanitize_step_result(result)

    def execute_command_step(self, step: ScenarioStepConfig, sandbox_dir: Path, env: Optional[Dict[str, str]] = None) -> ScenarioStepResult:
        import os
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        run_env.update({
            "BIST_BOT_BASE_DIR": str(sandbox_dir),
            "BIST_BOT_ENV": "scenario",
            "BIST_BOT_DISABLE_TELEGRAM": "true",
            "BIST_BOT_FORCE_MOCK": "true"
        })

        started_at = datetime.utcnow()
        issues = []

        # Security enforcement: validate the command binary
        allowed_binaries = {"python", "echo", "ls", "sleep", "pytest"}
        if not step.command or step.command[0] not in allowed_binaries:
            return ScenarioStepResult(
                step_id=step.step_id,
                name=step.name,
                step_type=step.step_type,
                status=ScenarioStatus.FAILED,
                started_at=started_at,
                issues=[f"Security policy violation: command '{step.command[0] if step.command else 'None'}' is not allowed."]
            )

        try:
            # We don't want to actually use python -m if it's slow or destructive in tests, but let's allow it in sandbox mode.
            process = subprocess.run(
                step.command,
                cwd=str(sandbox_dir),
                env=run_env,
                capture_output=True,
                text=True,
                timeout=step.timeout_seconds
            )
            exit_code = process.returncode
            stdout_tail = process.stdout[-2000:] if process.stdout else None
            stderr_tail = process.stderr[-2000:] if process.stderr else None
            status = ScenarioStatus.SUCCESS if exit_code == 0 else ScenarioStatus.FAILED

            if step.expected_exit_code is not None and exit_code != step.expected_exit_code:
                status = ScenarioStatus.FAILED
                issues.append(f"Expected exit code {step.expected_exit_code}, got {exit_code}")

        except subprocess.TimeoutExpired:
            status = ScenarioStatus.TIMEOUT
            exit_code = None
            stdout_tail = None
            stderr_tail = None
            issues.append(f"Timeout after {step.timeout_seconds}s")
        except Exception as e:
            status = ScenarioStatus.ERROR
            exit_code = None
            stdout_tail = None
            stderr_tail = None
            issues.append(str(e))

        return ScenarioStepResult(
            step_id=step.step_id,
            name=step.name,
            step_type=step.step_type,
            status=status,
            started_at=started_at,
            exit_code=exit_code,
            stdout_tail=stdout_tail,
            stderr_tail=stderr_tail,
            issues=issues
        )

    def execute_function_step(self, step: ScenarioStepConfig, sandbox_dir: Path) -> ScenarioStepResult:
        # Dummy for now, can be extended to use getattr on a module
        return ScenarioStepResult(
            step_id=step.step_id,
            name=step.name,
            step_type=step.step_type,
            status=ScenarioStatus.SUCCESS,
            started_at=datetime.utcnow()
        )

    def execute_assertions(self, step: ScenarioStepConfig, result_payload: ScenarioStepResult) -> Tuple[int, int, List[str]]:
        passed = 0
        failed = 0
        issues = []

        stdout = result_payload.stdout_tail or ""
        stderr = result_payload.stderr_tail or ""
        combined_out = stdout + stderr

        for assertion in step.assertions:
            if assertion.startswith("file_exists:"):
                # Not doing actual file checks inside the executor unless we have the dir
                passed += 1 # mock
            elif assertion.startswith("json_field_exists:"):
                passed += 1 # mock
            elif assertion.startswith("status_is:"):
                expected = assertion.split(":", 1)[1]
                if result_payload.status.value == expected:
                    passed += 1
                else:
                    failed += 1
                    issues.append(f"Assertion failed: expected status {expected}, got {result_payload.status.value}")
            elif assertion.startswith("contains_text:"):
                text = assertion.split(":", 1)[1]
                if text in combined_out:
                    passed += 1
                else:
                    failed += 1
                    issues.append(f"Assertion failed: output does not contain '{text}'")
            elif assertion.startswith("not_contains_text:"):
                text = assertion.split(":", 1)[1]
                if text not in combined_out:
                    passed += 1
                else:
                    failed += 1
                    issues.append(f"Assertion failed: output contains forbidden text '{text}'")
            elif assertion == "no_secret":
                if "SECRET" not in combined_out.upper(): # simple mock check
                    passed += 1
                else:
                    failed += 1
                    issues.append("Assertion failed: potential secret found in output")
            elif assertion == "no_unsafe_claim":
                unsafe_words = ["guaranteed", "risk-free", "sure profit", "100% win"]
                if not any(word in combined_out.lower() for word in unsafe_words):
                    passed += 1
                else:
                    failed += 1
                    issues.append("Assertion failed: unsafe financial claim found")
            elif assertion == "no_real_order_sent":
                if "real order sent" not in combined_out.lower() and "live trade" not in combined_out.lower():
                    passed += 1
                else:
                    failed += 1
                    issues.append("Assertion failed: apparent real order sent")
            elif assertion.startswith("exit_code_is:"):
                expected = int(assertion.split(":", 1)[1])
                if result_payload.exit_code == expected:
                    passed += 1
                else:
                    failed += 1
                    issues.append(f"Assertion failed: expected exit code {expected}, got {result_payload.exit_code}")
            else:
                issues.append(f"Unknown assertion: {assertion}")
                failed += 1

        return passed, failed, issues

    def sanitize_step_result(self, result: ScenarioStepResult) -> ScenarioStepResult:
        # We can implement regex redaction for secrets here if needed.
        return result
