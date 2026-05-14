with open("bist_signal_bot/monitoring/diagnostics.py", "r") as f:
    content = f.read()

content = content.replace("    def check_runtime_state(self) -> DiagnosticCheckResult:", "    def check_runtime_state(self) -> DiagnosticCheckResult:\n        from bist_signal_bot.runtime.state import RuntimeStateStore")
content = content.replace("    def check_lock_state(self) -> DiagnosticCheckResult:", "    def check_lock_state(self) -> DiagnosticCheckResult:\n        from bist_signal_bot.runtime.locks import RuntimeLockManager")

with open("bist_signal_bot/monitoring/diagnostics.py", "w") as f:
    f.write(content)
