import uuid
from typing import List, Optional
from bist_signal_bot.cli_ux.models import CLIAlias

class CLIAliasRegistry:
    def __init__(self, settings=None):
        self.settings = settings
        self.prefix = getattr(self.settings, "CLI_ALIAS_PREFIX", "bt") if self.settings else "bt"
        self._aliases = {a.alias: a for a in self.default_aliases()}

    def default_aliases(self) -> List[CLIAlias]:
        return [
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} health",
                target_command="healthcheck",
                description="Run system healthcheck"
            ),
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} scan",
                target_command="scan symbols",
                description="Run signal scanner"
            ),
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} ctx",
                target_command="context build",
                description="Build context fusion"
            ),
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} review",
                target_command="review-workflow",
                description="Run review workflow"
            ),
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} qa",
                target_command="qa release-gate",
                description="Run QA release gate"
            ),
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} ops",
                target_command="ops status",
                description="Check ops status"
            ),
            CLIAlias(
                alias_id=str(uuid.uuid4()),
                alias=f"{self.prefix} demo",
                target_command="bootstrap demo",
                description="Run offline demo"
            )
        ]

    def resolve_alias(self, alias: str) -> Optional[str]:
        a = self._aliases.get(alias)
        if a:
            return a.target_command
        return None

    def is_alias(self, command: str) -> bool:
        return command in self._aliases

    def validate_alias(self, alias: CLIAlias) -> List[str]:
        errors = []
        if "buy" in alias.alias or "sell" in alias.alias or "trade" in alias.alias:
            errors.append("Alias cannot contain unsafe keywords like buy/sell/trade.")
        return errors

    def alias_help_text(self) -> str:
        lines = ["Available Aliases:"]
        for a in self._aliases.values():
            lines.append(f"  {a.alias} -> {a.target_command} ({a.description})")
        return "\n".join(lines)
