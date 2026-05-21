with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Replace return parser with add_drift_parser(subparsers)\n    return parser
if "add_drift_parser(subparsers)" not in content.split("def build_parser()")[1]:
    content = content.replace("    return parser", "    add_drift_parser(subparsers)\n    return parser", 1)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
