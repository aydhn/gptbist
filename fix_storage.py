with open("bist_signal_bot/factors/storage.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == '\")':
        continue
    new_lines.append(line)

with open("bist_signal_bot/factors/storage.py", "w") as f:
    f.writelines(new_lines)
