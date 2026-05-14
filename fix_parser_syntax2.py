with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == "setup_monitor_parser(subparsers):":
        new_lines.append(line.replace(":", ""))
    elif line.strip() == "def setup_ml_train_parser(subparsers)":
        new_lines.append(line + ":\n")
    else:
        new_lines.append(line)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(new_lines)
