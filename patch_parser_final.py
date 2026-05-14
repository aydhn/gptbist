import sys

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Make sure setup_monitor_parser is called in build_parser
if "setup_monitor_parser(subparsers)" not in content.split("def build_parser()")[1]:
    content = content.replace("    setup_ml_train_parser(subparsers)", "    setup_ml_train_parser(subparsers)\n    setup_monitor_parser(subparsers)")

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
