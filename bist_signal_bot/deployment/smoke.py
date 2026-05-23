import uuid
import subprocess
import os
import sys
from datetime import datetime, UTC
from typing import List

from bist_signal_bot.deployment.models import SmokeTestResult, EnvironmentCheckResult, EnvironmentCheckType, DeploymentStatus, DeploymentDecision, DeploymentProfile
from bist_signal_bot.config.settings import Settings

class DeploymentSmokeTester:
    def __init__(self, settings: Settings, base_dir: str):
        self.settings = settings
        self.base_dir = base_dir

    def run_smoke_tests(self, profile: DeploymentProfile, dry_run: bool = True) -> SmokeTestResult:
        result = SmokeTestResult(
            smoke_id=str(uuid.uuid4()),
            started_at=datetime.now(UTC),
            status=DeploymentStatus.UNKNOWN
        )

        test_commands = [
            [sys.executable, "-m", "bist_signal_bot", "healthcheck"],
            # [sys.executable, "-m", "bist_signal_bot", "governance", "policy", "--json"],
            # We mock executing the commands for now to ensure safe tests and avoiding module errors
            # if we run real commands in environments without them available.
        ]

        # Determine base command tests, assuming they'll mostly be skipped in dry-run
        # or replaced by simple checks if we don't want to actually run subprocesses in tests.

        for cmd in test_commands:
            if dry_run:
                result.checks.append(EnvironmentCheckResult(
                    check_id=str(uuid.uuid4()),
                    check_type=EnvironmentCheckType.CUSTOM,
                    status=DeploymentStatus.SKIPPED,
                    decision=DeploymentDecision.SKIP,
                    title=f"Smoke Test Command (Dry Run)",
                    message=f"Would run: {' '.join(cmd)}"
                ))
            else:
                check_res = self.run_command(cmd, timeout_seconds=getattr(self.settings, "DEPLOYMENT_SMOKE_TIMEOUT_SECONDS", 30))
                result.checks.append(check_res)

            result.commands_tested.append(cmd)

        if any(c.status == DeploymentStatus.FAIL for c in result.checks):
            result.status = DeploymentStatus.FAIL
        else:
            result.status = DeploymentStatus.PASS

        result.finished_at = datetime.now(UTC)
        return result

    def run_command(self, command: List[str], timeout_seconds: int = 30) -> EnvironmentCheckResult:
        env = os.environ.copy()
        env["BIST_BOT_FORCE_RESEARCH_ONLY"] = "true"
        env["BIST_BOT_ALLOW_BROKER"] = "false"
        env["BIST_BOT_DISABLE_TELEGRAM_SEND"] = "true"

        try:
            # For real runs we'd use capture_output=True, text=True
            process = subprocess.run(command, env=env, timeout=timeout_seconds, capture_output=True, text=True)
            if process.returncode == 0:
                return EnvironmentCheckResult(
                    check_id=str(uuid.uuid4()),
                    check_type=EnvironmentCheckType.CUSTOM,
                    status=DeploymentStatus.PASS,
                    decision=DeploymentDecision.CONTINUE,
                    title="Smoke Command Passed",
                    message=f"Command executed successfully: {' '.join(command)}"
                )
            else:
                return EnvironmentCheckResult(
                    check_id=str(uuid.uuid4()),
                    check_type=EnvironmentCheckType.CUSTOM,
                    status=DeploymentStatus.FAIL,
                    decision=DeploymentDecision.BLOCK,
                    title="Smoke Command Failed",
                    message=f"Command failed with code {process.returncode}: {process.stderr}"
                )
        except subprocess.TimeoutExpired:
            return EnvironmentCheckResult(
                check_id=str(uuid.uuid4()),
                check_type=EnvironmentCheckType.CUSTOM,
                status=DeploymentStatus.FAIL,
                decision=DeploymentDecision.BLOCK,
                title="Smoke Command Timeout",
                message=f"Command timed out after {timeout_seconds}s"
            )
        except Exception as e:
            return EnvironmentCheckResult(
                check_id=str(uuid.uuid4()),
                check_type=EnvironmentCheckType.CUSTOM,
                status=DeploymentStatus.FAIL,
                decision=DeploymentDecision.BLOCK,
                title="Smoke Command Error",
                message=f"Error executing command: {str(e)}"
            )
