with open("bist_signal_bot/research/ledger.py", "r") as f:
    content = f.read()

# Mocking the missing ResearchEvent stuff that wasn't properly deleted or created in prior phases.
content = content.replace("    def log_whatif_run(self, result: Any, tags: list[str] | None = None) -> ResearchEvent:", "    def log_whatif_run(self, result: Any, tags: list[str] | None = None) -> Any:")
content = content.replace("        event = ResearchEvent(", "        event = dict(")

with open("bist_signal_bot/research/ledger.py", "w") as f:
    f.write(content)
