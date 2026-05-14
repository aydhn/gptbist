with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

content = content.replace("    setup_monitor_parser(subparsers)\n    ml_train_parser = subparsers.add_parser(", "    ml_train_parser = subparsers.add_parser(")
content = content.replace("    setup_ml_train_parser(subparsers)\n", "    setup_ml_train_parser(subparsers)\n    setup_monitor_parser(subparsers)\n")

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
