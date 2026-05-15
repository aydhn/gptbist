import subprocess
import time

from bist_signal_bot.quality.models import (
    QualityCheckResult,
    QualityCheckStatus,
    QualityTool
)

class TypeCheckRunner:
    def _tool_available(self, name: str) -> bool:
        try:
            result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def run_mypy(self) -> QualityCheckResult:
        if not self._tool_available("mypy"):
            return QualityCheckResult(
                check_name="mypy",
                tool=QualityTool.MYPY,
                status=QualityCheckStatus.SKIP,
                message="Mypy tool not available"
            )

        start_time = time.time()
        command = ["mypy", "bist_signal_bot"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="mypy",
                tool=QualityTool.MYPY,
                status=status,
                message=f"Mypy completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stdout_tail=result.stdout[-2000:],
                stderr_tail=result.stderr[-2000:]
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="mypy",
                tool=QualityTool.MYPY,
                status=QualityCheckStatus.ERROR,
                message=f"Mypy check failed: {str(e)}"
            )

    def run_pyright_if_available(self) -> QualityCheckResult:
        if not self._tool_available("pyright"):
            return QualityCheckResult(
                check_name="pyright",
                tool=QualityTool.MYPY, # Reusing MYPY tool enum for generic type check
                status=QualityCheckStatus.SKIP,
                message="Pyright tool not available"
            )

        start_time = time.time()
        command = ["pyright", "bist_signal_bot"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="pyright",
                tool=QualityTool.MYPY,
                status=status,
                message=f"Pyright completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stdout_tail=result.stdout[-2000:],
                stderr_tail=result.stderr[-2000:]
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="pyright",
                tool=QualityTool.MYPY,
                status=QualityCheckStatus.ERROR,
                message=f"Pyright check failed: {str(e)}"
            )
