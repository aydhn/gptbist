with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Make sure add_quality_parser is correctly called
content = content.replace("    add_security_parser(subparsers)\n", "    add_security_parser(subparsers)\n    add_quality_parser(subparsers)\n")

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
