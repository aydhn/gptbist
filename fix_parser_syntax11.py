with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Is there ANOTHER conflicting parser already defined somewhere else?
import re
# check for `subparsers.add_parser("quality"`
for i, line in enumerate(content.split('\n')):
    if 'add_parser("quality"' in line:
        print(f"Line {i+1}: {line}")
