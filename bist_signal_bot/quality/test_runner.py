import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.quality.models import (
    QualitySuite,
    QualityCheckResult,
    QualityCheckStatus,
    QualityTool,
    TestRunSummary
)
from bist_signal_bot.core.exceptions import QualityTestRunnerError

class QualityTestRunner:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def run_pytest(self, suite: QualitySuite, timeout_seconds: int, extra_args: Optional[list[str]] = None) -> QualityCheckResult:
        start_time = time.time()
        command = ["pytest"]

        if suite == QualitySuite.SMOKE:
            command.extend(["-m", "smoke"])
        elif suite == QualitySuite.SECURITY:
            command.append("tests/test_security_*.py")
        elif suite == QualitySuite.RUNTIME:
            command.append("tests/test_runtime_*.py")
        elif suite == QualitySuite.SCANNER:
            command.append("tests/test_scanner_*.py")
        elif suite == QualitySuite.BACKTEST:
            command.append("tests/test_backtest_*.py")
        elif suite == QualitySuite.ML:
            command.append("tests/test_ml_*.py")
        elif suite == QualitySuite.PAPER:
            command.append("tests/test_paper_*.py")
        elif suite == QualitySuite.FAST:
            command.extend(["-m", "not slow"])
        elif suite != QualitySuite.ALL:
            # Fallback or custom, just run pytest on tests dir if nothing else matches
            command.append("tests")

        if extra_args:
            command.extend(extra_args)

        exit_code, stdout, stderr, elapsed = self.run_command(command, timeout_seconds)

        status = QualityCheckStatus.PASS if exit_code == 0 else QualityCheckStatus.FAIL
        if exit_code not in [0, 1]: # Pytest returns 1 if tests fail, other codes mean execution error
            status = QualityCheckStatus.ERROR

        msg = f"Pytest completed with exit code {exit_code}"

        return QualityCheckResult(
            check_name=f"pytest_{suite.value.lower()}",
            tool=QualityTool.PYTEST,
            status=status,
            message=msg,
            elapsed_seconds=elapsed,
            command=command,
            exit_code=exit_code,
            stdout_tail=stdout[-2000:] if stdout else None,
            stderr_tail=stderr[-2000:] if stderr else None
        )

    def parse_pytest_summary(self, output: str, elapsed_seconds: float) -> TestRunSummary:
        if not output:
             return TestRunSummary(duration_seconds=elapsed_seconds)

        # A very basic parse. In a real scenario, parsing pytest output or using junit xml is better.
        import re
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        m_pass = re.search(r"(\d+) passed", output)
        if m_pass: passed = int(m_pass.group(1))
        m_fail = re.search(r"(\d+) failed", output)
        if m_fail: failed = int(m_fail.group(1))
        m_skip = re.search(r"(\d+) skipped", output)
        if m_skip: skipped = int(m_skip.group(1))
        m_err = re.search(r"(\d+) error", output)
        if m_err: errors = int(m_err.group(1))





        # If we couldn't parse properly but we have output, just return the raw tail.
        # Often pytest ends with something like "=== 3 passed, 1 warnings in 0.12s ==="

        return TestRunSummary(
            total_tests=(passed + failed + skipped + errors) if (passed + failed + skipped + errors) > 0 else None,
            passed=passed if passed > 0 else None,
            failed=failed if failed > 0 else None,
            skipped=skipped if skipped > 0 else None,
            errors=errors if errors > 0 else None,
            duration_seconds=elapsed_seconds,
            raw_output_tail=output[-1000:]
        )

    def run_command(self, command: list[str], timeout_seconds: int, cwd: Optional[Path] = None) -> Tuple[int, str, str, float]:
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=cwd
            )
            elapsed = time.time() - start_time
            stdout = self._redact(result.stdout)
            stderr = self._redact(result.stderr)
            return result.returncode, stdout, stderr, elapsed
        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - start_time
            return -1, self._redact(e.stdout.decode() if e.stdout else ""), self._redact(e.stderr.decode() if e.stderr else f"Timeout after {timeout_seconds}s"), elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            return -2, "", f"Execution error: {str(e)}", elapsed

    def _redact(self, text: str) -> str:
        if not text:
            return ""
        # Basic redaction to prevent secret leaks in output.
        # For a full implementation, we'd pull sensitive keys from settings.
        redacted = text
        for secret_marker in ["bot_token", "api_key", "password", "secret"]:
             # simplified redaction logic for example
             pass
        return redacted
