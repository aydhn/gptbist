from bist_signal_bot.qa.models import SmokeTestResult, QAStatus
import subprocess
import uuid
from datetime import datetime
import shlex

class SmokeTestRunner:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def run_smoke_commands(self, commands: list[str] | None = None) -> list[SmokeTestResult]:
        cmds = commands or self.default_smoke_commands()
        return [self.run_command(c) for c in cmds]

    def default_smoke_commands(self) -> list[str]:
        return [
            "python -m bist_signal_bot healthcheck --qa",
            "python -m bist_signal_bot config show --safe"
        ]

    def run_command(self, command: str, timeout_seconds: int | None = None) -> SmokeTestResult:
        started = datetime.utcnow()
        try:
            res = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=timeout_seconds or 30)
            status = self.classify_exit_code(res.returncode)
            return SmokeTestResult(
                smoke_id=str(uuid.uuid4()),
                created_at=started,
                command=command,
                exit_code=res.returncode,
                status=status,
                stdout_excerpt=self.sanitize_output(res.stdout),
                stderr_excerpt=self.sanitize_output(res.stderr),
                elapsed_seconds=(datetime.utcnow() - started).total_seconds()
            )
        except Exception as e:
            return SmokeTestResult(
                smoke_id=str(uuid.uuid4()),
                created_at=started,
                command=command,
                exit_code=-1,
                status=QAStatus.ERROR,
                warnings=[str(e)]
            )

    def classify_exit_code(self, exit_code: int | None) -> QAStatus:
        if exit_code == 0: return QAStatus.PASS
        return QAStatus.FAIL

    def sanitize_output(self, text: str | None, max_chars: int = 2000) -> str | None:
        if not text: return None
        return text[:max_chars]
