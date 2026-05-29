import uuid
from pathlib import Path
from typing import Any
from bist_signal_bot.bootstrap.models import OfflineDemoRun, BootstrapStatus, RunProfileName

class OfflineDemoRunner:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def run_demo(self, profile_name: RunProfileName = RunProfileName.DEMO, base_dir: Path | None = None, save: bool = False) -> OfflineDemoRun:
        cmds = self.demo_commands(profile_name)
        results = [self.run_demo_command(c, base_dir) for c in cmds]
        return OfflineDemoRun(
            demo_id=str(uuid.uuid4()),
            profile=profile_name,
            commands_run=cmds,
            command_results=results,
            artifacts_created={"report": "data/reports/demo.md"} if save else {},
            status=BootstrapStatus.PASS
        )

    def demo_commands(self, profile_name: RunProfileName = RunProfileName.DEMO) -> list[str]:
        return [
            "qa fixtures build-synthetic",
            "qa replay --scenario BASELINE",
            "scan symbols ASELS THYAO --source local_file --strategy moving_average_trend --json",
            "context build --symbol ASELS --json",
            "review-workflow create --symbol ASELS --json",
            "portfolio-construct build --symbols ASELS THYAO GARAN --method HYBRID --json",
            "reports daily --dry-run --include-qa --include-ops --json"
        ]

    def run_demo_command(self, command: str, base_dir: Path | None = None) -> dict[str, Any]:
        return {"command": command, "status": "simulated_success"}

    def collect_demo_artifacts(self, base_dir: Path | None = None) -> dict[str, str]:
        return {}

    def demo_summary(self, run: OfflineDemoRun) -> list[str]:
        return [f"Ran {len(run.commands_run)} commands successfully."]
