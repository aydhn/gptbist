import shlex
import uuid
from pathlib import Path
from typing import Any
from bist_signal_bot.bootstrap.models import OfflineDemoRun, BootstrapStatus, RunProfileName


class OfflineDemoRunner:
    """Runs a short sequence of real CLI commands offline to prove the bot works
    end to end (no real broker, no real orders). Previously this returned
    ``{"status": "simulated_success"}`` for every command without running
    anything; it now dispatches each command through the real CLI and records the
    actual outcome.
    """

    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def run_demo(self, profile_name: RunProfileName = RunProfileName.DEMO, base_dir: Path | None = None, save: bool = False) -> OfflineDemoRun:
        cmds = self.demo_commands(profile_name)
        results = [self.run_demo_command(c, base_dir) for c in cmds]
        failed = [r for r in results if r.get("status") != "success"]
        status = BootstrapStatus.PASS if not failed else BootstrapStatus.WATCH
        return OfflineDemoRun(
            demo_id=str(uuid.uuid4()),
            profile=profile_name,
            commands_run=cmds,
            command_results=results,
            artifacts_created={"report": "data/reports/demo.md"} if save else {},
            status=status,
        )

    def demo_commands(self, profile_name: RunProfileName = RunProfileName.DEMO) -> list[str]:
        # Ordered so the always-safe checks run first, then capability demos.
        return [
            "version",
            "healthcheck",
            "qa fixtures build-synthetic",
            "scan symbols ASELS THYAO --source local_file --strategy moving_average_trend --json",
        ]

    def run_demo_command(self, command: str, base_dir: Path | None = None) -> dict[str, Any]:
        """Dispatch a single command through the real CLI, tolerant of failures."""
        from bist_signal_bot.cli.main import run_cli

        argv = shlex.split(command)
        try:
            code = run_cli(argv)
            exit_code = 0 if code is None else int(code)
        except SystemExit as exc:  # some subcommands call sys.exit()
            exit_code = 0 if exc.code is None else (exc.code if isinstance(exc.code, int) else 1)
        except Exception as exc:  # never let one demo command abort the whole demo
            return {"command": command, "status": "error", "error": str(exc)}
        return {
            "command": command,
            "status": "success" if exit_code == 0 else "failed",
            "exit_code": exit_code,
        }

    def collect_demo_artifacts(self, base_dir: Path | None = None) -> dict[str, str]:
        return {}

    def demo_summary(self, run: OfflineDemoRun) -> list[str]:
        ok = sum(1 for r in run.command_results if r.get("status") == "success")
        total = len(run.command_results)
        lines = [f"Offline demo: {ok}/{total} commands succeeded (status: {run.status.value})."]
        for r in run.command_results:
            mark = "OK " if r.get("status") == "success" else "!! "
            detail = "" if r.get("status") == "success" else f" -> {r.get('error') or r.get('exit_code')}"
            lines.append(f"  {mark}{r['command']}{detail}")
        return lines
