import subprocess
import time

from bist_signal_bot.quality.models import (
    QualityCheckResult,
    QualityCheckStatus,
    QualityTool
)

class StaticAnalysisRunner:
    def tool_available(self, name: str) -> bool:
        try:
            result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def run_ruff(self) -> QualityCheckResult:
        if not self.tool_available("ruff"):
            return QualityCheckResult(
                check_name="ruff",
                tool=QualityTool.RUFF,
                status=QualityCheckStatus.SKIP,
                message="Ruff tool not available"
            )

        start_time = time.time()
        command = ["ruff", "check", "bist_signal_bot", "tests"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="ruff",
                tool=QualityTool.RUFF,
                status=status,
                message=f"Ruff completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stdout_tail=result.stdout[-2000:],
                stderr_tail=result.stderr[-2000:]
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="ruff",
                tool=QualityTool.RUFF,
                status=QualityCheckStatus.ERROR,
                message=f"Ruff check failed: {str(e)}"
            )

    def run_black_check(self) -> QualityCheckResult:
        if not self.tool_available("black"):
            return QualityCheckResult(
                check_name="black",
                tool=QualityTool.BLACK,
                status=QualityCheckStatus.SKIP,
                message="Black tool not available"
            )

        start_time = time.time()
        command = ["black", "--check", "bist_signal_bot", "tests"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="black",
                tool=QualityTool.BLACK,
                status=status,
                message=f"Black completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stdout_tail=result.stdout[-2000:],
                stderr_tail=result.stderr[-2000:]
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="black",
                tool=QualityTool.BLACK,
                status=QualityCheckStatus.ERROR,
                message=f"Black check failed: {str(e)}"
            )

    def run_static_suite(self) -> list[QualityCheckResult]:
        return [self.run_ruff(), self.run_black_check()]
