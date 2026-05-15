with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Let's see if there's an add_quality_parser already somewhere around line 869
import re
match = re.search(r'def add_quality_parser.*?def add_quality_parser', content, re.DOTALL)
if match:
    print("Yes, duplicate definition found.")

# We will just rewrite the file by grabbing up to the first 'def add_quality_parser'
# and ignoring the second one
parts = content.split("def add_quality_parser(subparsers):")
if len(parts) >= 3:
    new_content = parts[0] + "def add_quality_parser(subparsers):" + parts[1]
    with open("bist_signal_bot/cli/parsers.py", "w") as f:
        f.write(new_content)
