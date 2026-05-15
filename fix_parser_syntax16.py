import re
with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Let's inspect where build_parser is actually calling subparsers
content = content.replace(
    'add_security_parser(subparsers)\n\n    add_validate_backtest_parser',
    'add_security_parser(subparsers)\n    add_quality_parser(subparsers)\n\n    add_validate_backtest_parser'
)

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
