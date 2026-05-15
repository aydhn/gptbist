import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# I may have broken it by bad replacement.
# Let's clean it up by re-writing build_parser if it is broken.

# Wait, the error is: def add_security_parser(subparsers)
# Missing colon. Let's fix that directly.
content = content.replace("def add_security_parser(subparsers)\n", "def add_security_parser(subparsers):\n")

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
