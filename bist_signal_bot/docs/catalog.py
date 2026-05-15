from bist_signal_bot.docs.models import CLICommandDoc, CommandRiskLevel, DocsValidationFinding, DocsValidationStatus

class CommandCatalogBuilder:
    def build_command_catalog(self) -> list[CLICommandDoc]:
        commands = []
        commands.append(CLICommandDoc(
            command="healthcheck",
            description="Runs healthcheck",
            examples=["python -m bist_signal_bot healthcheck"],
            risk_level=CommandRiskLevel.SAFE,
            requires_network=False,
            sends_telegram=False,
            writes_files=False,
            requires_confirm=False,
            no_real_order_sent=True,
            module="healthcheck"
        ))
        commands.append(CLICommandDoc(
            command="runtime loop",
            description="Runs the runtime orchestrator loop",
            examples=["python -m bist_signal_bot runtime loop --max-iterations 5"],
            risk_level=CommandRiskLevel.LONG_RUNNING,
            requires_network=True,
            sends_telegram=True,
            writes_files=True,
            requires_confirm=False,
            no_real_order_sent=True,
            module="runtime"
        ))
        commands.append(CLICommandDoc(
            command="security kill-switch deactivate",
            description="Deactivates the kill-switch",
            examples=["python -m bist_signal_bot security kill-switch deactivate --confirm"],
            risk_level=CommandRiskLevel.DESTRUCTIVE_REQUIRES_CONFIRM,
            requires_network=False,
            sends_telegram=False,
            writes_files=True,
            requires_confirm=True,
            no_real_order_sent=True,
            module="security"
        ))
        commands.append(CLICommandDoc(
            command="paper reset",
            description="Resets the paper trading ledger",
            examples=["python -m bist_signal_bot paper reset --confirm"],
            risk_level=CommandRiskLevel.DESTRUCTIVE_REQUIRES_CONFIRM,
            requires_network=False,
            sends_telegram=False,
            writes_files=True,
            requires_confirm=True,
            no_real_order_sent=True,
            module="paper"
        ))
        return commands

    def command_to_markdown(self, commands: list[CLICommandDoc]) -> str:
        md = "| Command | Module | Description | Risk Level | Writes Files | Sends Telegram | Requires Confirm | No Real Order Sent | Example |\n"
        md += "|---|---|---|---|---|---|---|---|---|\n"
        for c in commands:
            example_str = "<br>".join([f"`{e}`" for e in c.examples])
            md += f"| `{c.command}` | {c.module} | {c.description} | {c.risk_level.value} | {c.writes_files} | {c.sends_telegram} | {c.requires_confirm} | {c.no_real_order_sent} | {example_str} |\n"
        return md

    def safe_examples(self) -> list[str]:
        return [
            "python -m bist_signal_bot healthcheck",
            "python -m bist_signal_bot docs validate",
            "python -m bist_signal_bot scan mock"
        ]

    def validate_command_doc(self, command_doc: CLICommandDoc) -> list[DocsValidationFinding]:
        findings = []
        if not command_doc.no_real_order_sent:
            findings.append(DocsValidationFinding(
                path="catalog",
                status=DocsValidationStatus.FAIL,
                severity="HIGH",
                message="no_real_order_sent must be True"
            ))
        if "live order" in command_doc.command.lower() or "broker" in command_doc.command.lower():
            findings.append(DocsValidationFinding(
                path="catalog",
                status=DocsValidationStatus.FAIL,
                severity="HIGH",
                message="Command contains real broker/live order terminology"
            ))
        if command_doc.risk_level == CommandRiskLevel.DESTRUCTIVE_REQUIRES_CONFIRM and not command_doc.requires_confirm:
            findings.append(DocsValidationFinding(
                path="catalog",
                status=DocsValidationStatus.FAIL,
                severity="HIGH",
                message="Destructive command must have requires_confirm=True"
            ))
        return findings
