with open("bist_signal_bot/reports/collector.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("    if include_orchestrator:"):
        new_lines.append("    if include_orchestrator:\n        res['orchestrator_section'] = 'included'\n")
    elif line.startswith("        res['orchestrator_section'] = 'included'"):
        continue
    else:
        new_lines.append(line)

with open("bist_signal_bot/reports/collector.py", "w") as f:
    f.writelines(new_lines)
