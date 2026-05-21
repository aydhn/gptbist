with open("bist_signal_bot/core/audit.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == "class AuditEventType:":
        break
    new_lines.append(line)

with open("bist_signal_bot/core/audit.py", "w") as f:
    f.writelines(new_lines)
