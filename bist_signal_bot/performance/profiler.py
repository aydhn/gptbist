import pstats
import cProfile
import io
import subprocess
import logging
from typing import Callable, Any

from bist_signal_bot.performance.models import ProfiledFunctionResult, PerformanceStatus
from bist_signal_bot.config.settings import Settings

class FunctionProfiler:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.performance.profiler")

    def profile_callable(self, name: str, func: Callable[[], Any], top_n: int = 20) -> ProfiledFunctionResult:
        pr = cProfile.Profile()
        pr.enable()

        status = PerformanceStatus.PASS
        issues = []
        try:
            func()
        except Exception as e:
            status = PerformanceStatus.ERROR
            issues.append(f"Function raised exception: {e}")
            self.logger.error(f"Profiling error in {name}: {e}")

        pr.disable()

        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(top_n)

        top_functions = self.extract_top_functions(ps, top_n)

        return ProfiledFunctionResult(
            name=name,
            status=status,
            elapsed_seconds=ps.total_tt,
            top_functions=top_functions,
            stdout_tail=s.getvalue()[:2000], # Keep a snippet
            issues=issues
        )

    def profile_command(self, command: list[str], timeout_seconds: int = 300) -> ProfiledFunctionResult:
        import time
        start_time = time.perf_counter()

        status = PerformanceStatus.PASS
        issues = []
        stdout_tail = None

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            stdout_tail = result.stdout[-2000:] if result.stdout else ""
            if result.stderr:
                stdout_tail += "\nSTDERR:\n" + result.stderr[-1000:]

            if result.returncode != 0:
                status = PerformanceStatus.ERROR
                issues.append(f"Command returned non-zero exit code: {result.returncode}")

        except subprocess.TimeoutExpired:
            status = PerformanceStatus.ERROR
            issues.append(f"Command timed out after {timeout_seconds} seconds")
        except Exception as e:
            status = PerformanceStatus.ERROR
            issues.append(f"Command raised exception: {e}")

        elapsed = time.perf_counter() - start_time

        # Redact any secrets in stdout_tail
        # Simple string replace for common secret names if any were accidentally printed
        if stdout_tail:
            from bist_signal_bot.security.redaction import SecretRedactor
            redactor = SecretRedactor()
            stdout_tail = redactor.redact_string(stdout_tail)

        return ProfiledFunctionResult(
            name=" ".join(command[:2]) + "...",
            status=status,
            elapsed_seconds=elapsed,
            top_functions=[],
            stdout_tail=stdout_tail,
            issues=issues
        )

    def extract_top_functions(self, profile_stats: pstats.Stats, top_n: int) -> list[dict[str, Any]]:
        # This is a bit hacky, but parsing pstats programmatically
        results = []
        for i, func in enumerate(profile_stats.fcn_list):
            if i >= top_n:
                break
            cc, nc, tt, ct, callers = profile_stats.stats[func]
            file_name, line_num, func_name = func
            results.append({
                "function": func_name,
                "file": file_name.split("/")[-1],
                "ncalls": nc,
                "tottime": tt,
                "cumtime": ct
            })
        return results
