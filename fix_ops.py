with open("bist_signal_bot/ops/readiness.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("    if include_orchestrator:"):
        new_lines.append("    if include_orchestrator:\n        res['research_orchestrator'] = 'PASS'\n")
    elif line.startswith("        res[\"research_orchestrator\"] = \"PASS\""):
        continue
    else:
        new_lines.append(line)

with open("bist_signal_bot/ops/readiness.py", "w") as f:
    f.writelines(new_lines)
