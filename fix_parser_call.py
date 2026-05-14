with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()
if "setup_monitor_parser(" not in content:
    pass # Wait, we just added it to the end, but we need to call it in parse_args or setup_cli_parser
if "setup_ml_train_parser(subparsers)" in content:
    content = content.replace("setup_ml_train_parser(subparsers)", "setup_ml_train_parser(subparsers)\n    setup_monitor_parser(subparsers)")
with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
