import subprocess
import time

from bist_signal_bot.quality.models import (
    QualityCheckResult,
    QualityCheckStatus,
    QualityTool
)

class ImportCheckRunner:
    def check_import_package(self) -> QualityCheckResult:
        start_time = time.time()
        command = ["python", "-c", "import bist_signal_bot"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="import_package",
                tool=QualityTool.IMPORT_CHECK,
                status=status,
                message=f"Package import test completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stderr_tail=result.stderr[-1000:] if result.stderr else None
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="import_package",
                tool=QualityTool.IMPORT_CHECK,
                status=QualityCheckStatus.ERROR,
                message=f"Package import test failed: {str(e)}"
            )

    def check_cli_entrypoint(self) -> QualityCheckResult:
        start_time = time.time()
        command = ["python", "-m", "bist_signal_bot", "--help"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="cli_entrypoint",
                tool=QualityTool.IMPORT_CHECK,
                status=status,
                message=f"CLI entrypoint test completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stderr_tail=result.stderr[-1000:] if result.stderr else None
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="cli_entrypoint",
                tool=QualityTool.IMPORT_CHECK,
                status=QualityCheckStatus.ERROR,
                message=f"CLI entrypoint test failed: {str(e)}"
            )

    def check_for_circular_import_smoke(self) -> QualityCheckResult:
        start_time = time.time()
        modules = [
            "config", "data", "strategies", "scanner", "backtesting",
            "risk", "portfolio", "paper", "ml", "regime", "runtime",
            "monitoring", "security", "quality"
        ]

        script = "\n".join([f"import bist_signal_bot.{m}" for m in modules])

        command = ["python", "-c", script]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            elapsed = time.time() - start_time

            status = QualityCheckStatus.PASS if result.returncode == 0 else QualityCheckStatus.FAIL

            return QualityCheckResult(
                check_name="circular_import_smoke",
                tool=QualityTool.IMPORT_CHECK,
                status=status,
                message=f"Circular import smoke test completed with exit code {result.returncode}",
                elapsed_seconds=elapsed,
                command=command,
                exit_code=result.returncode,
                stderr_tail=result.stderr[-1000:] if result.stderr else None
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="circular_import_smoke",
                tool=QualityTool.IMPORT_CHECK,
                status=QualityCheckStatus.ERROR,
                message=f"Circular import smoke test failed: {str(e)}"
            )

    def run_import_checks(self) -> list[QualityCheckResult]:
        return [
            self.check_import_package(),
            self.check_cli_entrypoint(),
            self.check_for_circular_import_smoke()
        ]
