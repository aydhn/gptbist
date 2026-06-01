import re
with open("bist_signal_bot/runtime/orchestrator.py", "r") as f:
    lines = f.readlines()

with open("bist_signal_bot/runtime/orchestrator.py", "w") as f:
    for line in lines:
        if line.startswith("            result = self._run_once_impl(config, trigger)"):
            f.write("        result = self._run_once_impl(config, trigger)\n")
        elif line.startswith("            return result"):
            f.write("        return result\n")
        else:
            f.write(line)
