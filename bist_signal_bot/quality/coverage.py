import subprocess
import time
from typing import Optional

from bist_signal_bot.quality.models import (
    QualitySuite,
    QualityCheckResult,
    QualityCheckStatus,
    QualityTool,
    CoverageSummary
)

class CoverageRunner:
    def is_coverage_available(self) -> bool:
        try:
            result = subprocess.run(["coverage", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def run_coverage(self, suite: QualitySuite, threshold_pct: float, timeout_seconds: int) -> QualityCheckResult:
        if not self.is_coverage_available():
            return QualityCheckResult(
                check_name="coverage_run",
                tool=QualityTool.COVERAGE,
                status=QualityCheckStatus.SKIP,
                message="Coverage tool not available"
            )

        start_time = time.time()
        command = ["coverage", "run", "-m", "pytest"]

        if suite == QualitySuite.SMOKE:
            command.extend(["-m", "smoke"])
        elif suite == QualitySuite.FAST:
            command.extend(["-m", "not slow"])

        try:
            # Run coverage
            subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)

            # Generate report
            report_cmd = ["coverage", "report"]
            report_result = subprocess.run(report_cmd, capture_output=True, text=True, timeout=30)

            elapsed = time.time() - start_time

            summary = self.parse_coverage_output(report_result.stdout, threshold_pct)

            status = QualityCheckStatus.PASS
            msg = "Coverage measured successfully."
            if summary.passed_threshold is False:
                status = QualityCheckStatus.FAIL
                msg = f"Coverage {summary.total_coverage_pct}% is below threshold {threshold_pct}%."
            elif report_result.returncode != 0:
                status = QualityCheckStatus.ERROR
                msg = "Coverage report command failed."

            return QualityCheckResult(
                check_name="coverage_run",
                tool=QualityTool.COVERAGE,
                status=status,
                message=msg,
                elapsed_seconds=elapsed,
                command=command,
                exit_code=report_result.returncode,
                stdout_tail=report_result.stdout[-2000:],
                stderr_tail=report_result.stderr[-2000:]
            )
        except subprocess.TimeoutExpired:
            return QualityCheckResult(
                check_name="coverage_run",
                tool=QualityTool.COVERAGE,
                status=QualityCheckStatus.ERROR,
                message=f"Coverage run timed out after {timeout_seconds}s"
            )
        except Exception as e:
            return QualityCheckResult(
                check_name="coverage_run",
                tool=QualityTool.COVERAGE,
                status=QualityCheckStatus.ERROR,
                message=f"Coverage run failed: {str(e)}"
            )

    def parse_coverage_output(self, output: str, threshold_pct: float) -> CoverageSummary:
        if not output:
            return CoverageSummary()

        # Very basic parsing of `coverage report` output
        # Look for the TOTAL line
        total_pct = None
        for line in output.splitlines():
            if line.startswith("TOTAL"):
                parts = line.split()
                if len(parts) > 0:
                    pct_str = parts[-1].replace("%", "")
                    try:
                        total_pct = float(pct_str)
                    except ValueError:
                        pass

        if total_pct is not None:
            return CoverageSummary(
                enabled=True,
                measured=True,
                total_coverage_pct=total_pct,
                threshold_pct=threshold_pct,
                passed_threshold=total_pct >= threshold_pct
            )
        return CoverageSummary(enabled=True, measured=False)
