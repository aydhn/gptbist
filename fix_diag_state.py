with open("bist_signal_bot/monitoring/diagnostics.py", "r") as f:
    content = f.read()

# We need to import RuntimeStateStore inside check_runtime_state
if "from bist_signal_bot.runtime.state import RuntimeStateStore" not in content:
    content = "from bist_signal_bot.runtime.state import RuntimeStateStore\nfrom bist_signal_bot.runtime.locks import RuntimeLockManager\n" + content

with open("bist_signal_bot/monitoring/diagnostics.py", "w") as f:
    f.write(content)
