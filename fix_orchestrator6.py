# Let's cleanly rebuild run_once instead of messing with strings
with open("bist_signal_bot/runtime/orchestrator.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def run_once(" in line:
        new_lines.append(line)
        new_lines.append("        return self._run_once_impl(config, trigger)\n")
        skip = True
    elif skip and "def _run_once_impl(" in line:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open("bist_signal_bot/runtime/orchestrator.py", "w") as f:
    f.writelines(new_lines)
