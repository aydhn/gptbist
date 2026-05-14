with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == "return parser":
        lines.insert(i, "    setup_monitor_parser(subparsers)\n")
        break

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(lines)
