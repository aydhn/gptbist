with open("bist_signal_bot/monitoring/diagnostics.py", "r") as f:
    content = f.read()

# Fix __init__ defaults
content = content.replace("self.runtime_state_store = runtime_state_store or RuntimeStateStore(self.settings)", "self.runtime_state_store = runtime_state_store")
content = content.replace("self.lock_manager = lock_manager or RuntimeLockManager(self.settings)", "self.lock_manager = lock_manager")

with open("bist_signal_bot/monitoring/diagnostics.py", "w") as f:
    f.write(content)
