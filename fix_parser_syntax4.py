with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "def add_security_parser(subparsers):" in line:
        new_lines.append(line)
    elif "add_quality_parser(subparsers):" in line:
        continue # delete this line
    else:
        new_lines.append(line)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(new_lines)
