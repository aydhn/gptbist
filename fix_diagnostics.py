with open("bist_signal_bot/monitoring/diagnostics.py", "r") as f:
    content = f.read()

# Fix circular import correctly for the main binary run
content = content.replace("from bist_signal_bot.runtime.state import RuntimeStateStore\nfrom bist_signal_bot.runtime.locks import RuntimeLockManager", "")

inject_imports = """
    def check_runtime_state(self) -> DiagnosticCheckResult:
        try:
            from bist_signal_bot.runtime.state import RuntimeStateStore
            state_store = self.runtime_state_store or RuntimeStateStore(self.settings)
            state = state_store.load()
"""
content = content.replace("    def check_runtime_state(self) -> DiagnosticCheckResult:\n        try:\n            state = self.runtime_state_store.load()", inject_imports)

inject_locks = """
    def check_lock_state(self) -> DiagnosticCheckResult:
        try:
            from bist_signal_bot.runtime.locks import RuntimeLockManager
            lock_manager = self.lock_manager or RuntimeLockManager(self.settings)
            is_locked = lock_manager.is_locked()
"""
content = content.replace("    def check_lock_state(self) -> DiagnosticCheckResult:\n        try:\n            is_locked = self.lock_manager.is_locked()", inject_locks)

with open("bist_signal_bot/monitoring/diagnostics.py", "w") as f:
    f.write(content)
