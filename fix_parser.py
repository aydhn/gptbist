with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()
if "monitor" not in content:
    print("monitor NOT in parsers.py")
if "setup_monitor_parser(subparsers)" not in content:
    print("setup_monitor_parser not called")
