with open("bist_signal_bot/monitoring/diagnostics.py", "r") as f:
    content = f.read()

content = content.replace("runtime_state_store: Optional[RuntimeStateStore]", "runtime_state_store: Optional[Any]")
content = content.replace("lock_manager: Optional[RuntimeLockManager]", "lock_manager: Optional[Any]")

with open("bist_signal_bot/monitoring/diagnostics.py", "w") as f:
    f.write(content)
