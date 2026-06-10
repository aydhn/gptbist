import re
from pathlib import Path
from bist_signal_bot.docs.models import DocsValidationReport, DocsValidationStatus, DocsValidationFinding

_INLINE_CMD_RE = re.compile(r'`(python -m bist_signal_bot[^`]*)`')
_BLOCK_CMD_RE = re.compile(r'```(?:bash|sh)?\n(.*?)\n```', re.DOTALL)

class DocsExampleRunner:
    def extract_commands_from_markdown(self, path: Path) -> list[str]:
        text = path.read_text(encoding="utf-8")
        # find backticks
        commands = []
        for match in _INLINE_CMD_RE.finditer(text):
            commands.append(match.group(1).strip())
        for match in _BLOCK_CMD_RE.finditer(text):
            lines = match.group(1).splitlines()
            for line in lines:
                if line.startswith("python -m bist_signal_bot"):
                    commands.append(line.strip())
        return commands

    def is_safe_to_execute(self, command: str) -> tuple[bool, str]:
        if "runtime loop" in command and "--max-iterations" not in command:
            return False, "runtime loop needs max-iterations"
        if "kill-switch deactivate" in command and "--confirm" not in command:
            return False, "destructive requires confirm"
        if "paper reset" in command and "--confirm" not in command:
            return False, "destructive requires confirm"
        if "live order" in command or "broker" in command:
            return False, "contains live order phrasing"
        return True, "Safe"

    def run_safe_examples(self, docs_dir: Path, max_commands: int | None = None) -> DocsValidationReport:
        report = DocsValidationReport()
        return report
