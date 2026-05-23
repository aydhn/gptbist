import sys
from typing import List, Dict, Any

class PlatformCommandBuilder:
    def detect_platform(self) -> str:
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("darwin"):
            return "macos"
        return "linux"

    def safe_shell_command(self, command: List[str]) -> str:
        # Avoid injection, simply join as this is for documentation
        return " ".join(command)

    def windows_task_scheduler_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "description": "Run Scheduler (Dry-Run)",
                "action": "schtasks /create /tn \"BISTBotScheduler\" /tr \"python -m bist_signal_bot scheduler run-due --dry-run\" /sc minute /mo 15"
            },
            {
                "description": "Run Healthcheck",
                "action": "schtasks /create /tn \"BISTBotHealthcheck\" /tr \"python -m bist_signal_bot healthcheck\" /sc daily /st 09:00"
            }
        ]

    def linux_cron_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "description": "Run Scheduler every 15 minutes (Dry-Run)",
                "action": "*/15 * * * * cd /path/to/project && python -m bist_signal_bot scheduler run-due --dry-run >> data/logs/cron.log 2>&1"
            }
        ]

    def macos_launchd_examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "description": "Run Scheduler (Dry-Run)",
                "action": "Create plist file in ~/Library/LaunchAgents running: python -m bist_signal_bot scheduler run-due --dry-run"
            }
        ]
