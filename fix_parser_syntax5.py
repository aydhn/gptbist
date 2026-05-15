with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Ah I accidentally appended add_quality_parser while it was already there but maybe missing from scope or something?
# Let's see how many add_quality_parser definitions there are
import re
count = content.count("def add_quality_parser(subparsers):")
print(f"Found {count} definitions of add_quality_parser")

if count > 1:
    # Let's remove the second one
    parts = content.split("def add_quality_parser(subparsers):")
    # First part + "def add_quality_parser(subparsers):" + second part
    new_content = parts[0] + "def add_quality_parser(subparsers):" + parts[1]
    with open("bist_signal_bot/cli/parsers.py", "w") as f:
        f.write(new_content)
