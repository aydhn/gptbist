from bist_signal_bot.docs.models import TroubleshootingItem

class TroubleshootingBuilder:
    def build_troubleshooting_items(self) -> list[TroubleshootingItem]:
        return [
            TroubleshootingItem(
                problem="CLI command not found",
                likely_causes=["Virtualenv not active"],
                diagnostic_commands=["which python"],
                fix_steps=["source venv/bin/activate"]
            )
        ]

    def render_troubleshooting_markdown(self, items: list[TroubleshootingItem]) -> str:
        md = "# Troubleshooting\n\n"
        for item in items:
            md += f"## {item.problem}\n"
            md += f"**Likely Causes:** {', '.join(item.likely_causes)}\n"
            md += f"**Diagnostic Commands:** {', '.join(item.diagnostic_commands)}\n"
        return md
