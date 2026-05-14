with open("bist_signal_bot/cli/parsers.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_build_parser = False
for line in lines:
    new_lines.append(line)
    if "def build_parser()" in line:
        in_build_parser = True
    if in_build_parser and "setup_ml_train_parser(subparsers)" in line:
        new_lines.append("    setup_monitor_parser(subparsers)\n")
        in_build_parser = False

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.writelines(new_lines)
