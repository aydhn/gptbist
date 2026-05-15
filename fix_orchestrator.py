with open("bist_signal_bot/runtime/orchestrator.py", "r") as f:
    content = f.read()

# Add quality check to start method
if "self.run_quality_preflight()" not in content and "def start(" in content:
    content = content.replace(
        "if not self.run_security_preflight():\n            return",
        "if not self.run_security_preflight():\n            return\n        if not self.run_quality_preflight():\n            return"
    )

with open("bist_signal_bot/runtime/orchestrator.py", "w") as f:
    f.write(content)
