with open("bist_signal_bot/runtime/orchestrator.py", "r") as f:
    content = f.read()

import re
# Replace the whole if config.profile_runtime block
content = re.sub(
    r'if config\.profile_runtime and getattr\(self\.settings.*?perf_ctx\.record\(.*?\n\s+return result',
    'return result',
    content,
    flags=re.DOTALL
)
with open("bist_signal_bot/runtime/orchestrator.py", "w") as f:
    f.write(content)
