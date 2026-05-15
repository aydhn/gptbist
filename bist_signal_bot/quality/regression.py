import subprocess
import time

from bist_signal_bot.quality.models import (
    QualityCheckResult,
    QualityCheckStatus,
    QualityTool,
    RegressionSmokeCommand
)

class RegressionSmokeRunner:
    def default_commands(self) -> list[RegressionSmokeCommand]:
        return [
            RegressionSmokeCommand(name="cli_help", command=["python", "-m", "bist_signal_bot", "--help"], timeout_seconds=10),
            RegressionSmokeCommand(name="healthcheck", command=["python", "-m", "bist_signal_bot", "healthcheck"], timeout_seconds=15),
            RegressionSmokeCommand(name="security_audit", command=["python", "-m", "bist_signal_bot", "security", "audit", "--json"], timeout_seconds=15),
            RegressionSmokeCommand(name="monitor_status", command=["python", "-m", "bist_signal_bot", "monitor", "status", "--json"], timeout_seconds=15),
            RegressionSmokeCommand(name="scan_symbols", command=["python", "-m", "bist_signal_bot", "scan", "symbols", "ASELS", "THYAO", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=30),
            RegressionSmokeCommand(name="backtest_run", command=["python", "-m", "bist_signal_bot", "backtest", "run", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=30),
            RegressionSmokeCommand(name="risk_evaluate", command=["python", "-m", "bist_signal_bot", "risk", "evaluate", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=30),
            RegressionSmokeCommand(name="regime_classify", command=["python", "-m", "bist_signal_bot", "regime", "classify", "ASELS", "--source", "mock", "--json"], timeout_seconds=30),
            RegressionSmokeCommand(name="ml_dataset", command=["python", "-m", "bist_signal_bot", "ml-dataset", "build", "ASELS", "--source", "mock", "--json"], timeout_seconds=45),
            RegressionSmokeCommand(name="runtime_dry_run", command=["python", "-m", "bist_signal_bot", "runtime", "dry-run", "--symbols", "ASELS", "THYAO", "--source", "mock", "--strategy", "moving_average_trend", "--json"], timeout_seconds=45),
        ]

    def run_smoke_commands(self, commands: list[RegressionSmokeCommand] | None = None) -> list[QualityCheckResult]:
        cmds = commands if commands is not None else self.default_commands()
        results = []

        for cmd in cmds:
            if not cmd.enabled:
                continue

            start_time = time.time()
            try:
                # Basic execution
                res = subprocess.run(
                    cmd.command,
                    capture_output=True,
                    text=True,
                    timeout=cmd.timeout_seconds
                )
                elapsed = time.time() - start_time
                status = QualityCheckStatus.PASS if res.returncode == cmd.expected_exit_code else QualityCheckStatus.FAIL

                results.append(QualityCheckResult(
                    check_name=f"smoke_{cmd.name}",
                    tool=QualityTool.REGRESSION_SMOKE,
                    status=status,
                    message=f"Command '{cmd.name}' exited with {res.returncode}",
                    elapsed_seconds=elapsed,
                    command=cmd.command,
                    exit_code=res.returncode,
                    stdout_tail=res.stdout[-1000:] if res.stdout else None,
                    stderr_tail=res.stderr[-1000:] if res.stderr else None
                ))
            except subprocess.TimeoutExpired as e:
                elapsed = time.time() - start_time
                results.append(QualityCheckResult(
                    check_name=f"smoke_{cmd.name}",
                    tool=QualityTool.REGRESSION_SMOKE,
                    status=QualityCheckStatus.ERROR,
                    message=f"Command '{cmd.name}' timed out after {cmd.timeout_seconds}s",
                    elapsed_seconds=elapsed,
                    command=cmd.command,
                    stdout_tail=e.stdout.decode()[-1000:] if e.stdout else None,
                    stderr_tail=e.stderr.decode()[-1000:] if e.stderr else None
                ))
            except Exception as e:
                elapsed = time.time() - start_time
                results.append(QualityCheckResult(
                    check_name=f"smoke_{cmd.name}",
                    tool=QualityTool.REGRESSION_SMOKE,
                    status=QualityCheckStatus.ERROR,
                    message=f"Command '{cmd.name}' failed: {str(e)}",
                    elapsed_seconds=elapsed,
                    command=cmd.command
                ))

        return results
